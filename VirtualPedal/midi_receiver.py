"""
Virtual Pedal MIDI Receiver Backend.
Provides robust WinMM and driver MIDI input handling for the Virtual Effects-Pedal & Tempo Receiver.
Decouples MIDI callback execution from GUI rendering via thread-safe queues.
"""

import ctypes
from ctypes import wintypes
import os
import queue
import threading
import time
from typing import Callable, List, Optional, Tuple

CALLBACK_FUNCTION = 0x00030000
MIM_OPEN = 0x3C1
MIM_CLOSE = 0x3C2
MIM_DATA = 0x3C3
MIM_LONGDATA = 0x3C4
MIM_ERROR = 0x3C5
MIM_LONGERROR = 0x3C6
MIM_MOREDATA = 0x3CC


class MidiPortInfo:
    def __init__(self, index: int, name: str):
        self.index = index
        self.name = name

    def __repr__(self) -> str:
        return f"{self.name} [port {self.index}]"


class MidiPacket:
    def __init__(self, raw_bytes: bytes, timestamp_ms: float):
        self.raw_bytes = raw_bytes
        self.timestamp_ms = timestamp_ms

    @property
    def hex_str(self) -> str:
        return " ".join(f"{b:02X}" for b in self.raw_bytes)

    @property
    def status(self) -> int:
        return self.raw_bytes[0] if self.raw_bytes else 0

    @property
    def is_realtime(self) -> bool:
        return self.status >= 0xF8

    @property
    def channel(self) -> Optional[int]:
        if self.status < 0xF0:
            return (self.status & 0x0F) + 1
        return None

    @property
    def command_nibble(self) -> int:
        return self.status & 0xF0

    @property
    def data1(self) -> Optional[int]:
        return self.raw_bytes[1] if len(self.raw_bytes) > 1 else None

    @property
    def data2(self) -> Optional[int]:
        return self.raw_bytes[2] if len(self.raw_bytes) > 2 else None


class VirtualPedalReceiver:
    def __init__(self, default_port_name: str = "PulseStage Pedal Test"):
        self.default_port_name = default_port_name
        self.port: Optional[MidiPortInfo] = None
        self.packet_queue: queue.Queue = queue.Queue(maxsize=4096)
        self.is_connected = False
        self.driver_type = "None"

        self._winmm = ctypes.windll.winmm
        self._winmm_handle = None
        self._winmm_cb_ref = None
        self._lock = threading.RLock()

    def list_ports(self) -> List[MidiPortInfo]:
        """Lists all Windows WinMM MIDI Input devices."""
        ports = []
        num_devs = self._winmm.midiInGetNumDevs()
        class MIDIINCAPS(ctypes.Structure):
            _fields_ = [
                ('wMid', ctypes.c_ushort),
                ('wPid', ctypes.c_ushort),
                ('vDriverVersion', ctypes.c_uint),
                ('szPname', ctypes.c_char * 32),
                ('dwSupport', ctypes.c_uint)
            ]
        for i in range(num_devs):
            caps = MIDIINCAPS()
            self._winmm.midiInGetDevCapsA(i, ctypes.byref(caps), ctypes.sizeof(caps))
            name = caps.szPname.split(b'\x00')[0].decode('latin1', errors='ignore')
            ports.append(MidiPortInfo(i, name))
        return ports

    def open(self, port_info: MidiPortInfo) -> bool:
        """Opens a specific MIDI In port by MidiPortInfo."""
        with self._lock:
            self.stop()

            CB_TYPE = ctypes.WINFUNCTYPE(
                None, ctypes.c_void_p, ctypes.c_uint, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p
            )

            def winmm_callback(hMidiIn, wMsg, dwInstance, dwParam1, dwParam2):
                if wMsg == MIM_DATA:
                    status = dwParam1 & 0xFF
                    d1 = (dwParam1 >> 8) & 0xFF
                    d2 = (dwParam1 >> 16) & 0xFF
                    if status < 0xC0 or status == 0xE0 or (status >= 0xB0 and status <= 0xBF):
                        raw = bytes([status, d1, d2])
                    elif status in (0xC0, 0xD0, 0xF1, 0xF3):
                        raw = bytes([status, d1])
                    else:
                        raw = bytes([status])
                    pkt = MidiPacket(raw, time.perf_counter() * 1000.0)
                    try:
                        self.packet_queue.put_nowait(pkt)
                    except queue.Full:
                        pass

            self._winmm_cb_ref = CB_TYPE(winmm_callback)
            h_in = ctypes.c_void_p()
            res = self._winmm.midiInOpen(
                ctypes.byref(h_in),
                port_info.index,
                self._winmm_cb_ref,
                0,
                CALLBACK_FUNCTION
            )
            if res == 0:
                self._winmm.midiInStart(h_in)
                self._winmm_handle = h_in
                self.port = port_info
                self.is_connected = True
                self.driver_type = "Windows WinMM Loopback Driver"
                return True
            return False

    def start(self, preferred_name: Optional[str] = None) -> bool:
        """Auto-connects to preferred_name, default_port_name, or first available port."""
        target_name = preferred_name or self.default_port_name
        available = self.list_ports()

        # Match exact or partial preferred name
        match = next((p for p in available if target_name.lower() in p.name.lower()), None)
        if not match and available:
            match = available[0]

        if match:
            return self.open(match)

        return False

    def get_packets(self, max_count: int = 50) -> List[MidiPacket]:
        """Drains up to max_count packets from the thread-safe queue."""
        packets = []
        for _ in range(max_count):
            try:
                packets.append(self.packet_queue.get_nowait())
            except queue.Empty:
                break
        return packets

    def stop(self) -> None:
        """Cleanly releases handles and stops MIDI reception."""
        with self._lock:
            if self._winmm_handle:
                try:
                    self._winmm.midiInStop(self._winmm_handle)
                    self._winmm.midiInReset(self._winmm_handle)
                    self._winmm.midiInClose(self._winmm_handle)
                except Exception:
                    pass
                self._winmm_handle = None

            self.is_connected = False
            self.driver_type = "None"
            self.port = None
