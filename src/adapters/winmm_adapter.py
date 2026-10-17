"""
Native Windows Multimedia (WinMM) Adapter using ctypes
Zero external compiler dependencies. Works on all Windows 10/11 installations.
"""
import ctypes
import ctypes.wintypes as wintypes
import sys
import time
from typing import List, Dict, Optional, Callable
from .base import MidiAdapterBase, MidiPortInfo, PortDirection, MidiInputCallback

# Windows Multimedia Types & Constants
CALLBACK_FUNCTION = 0x00030000
MIM_OPEN = 0x3C1
MIM_CLOSE = 0x3C2
MIM_DATA = 0x3C3
MIM_LONGDATA = 0x3C4
MIM_ERROR = 0x3C5
MIM_LONGERROR = 0x3C6
MIM_MOREDATA = 0x3CC

MMSYSERR_NOERROR = 0
MMSYSERR_BADDEVICEID = 2
MMSYSERR_ALLOCATED = 4
MMSYSERR_NOMEM = 7


def get_midi_message_length(status_byte: int) -> int:
    """Accurately calculates wire length for any MIDI 1.0 status byte."""
    if status_byte < 0x80:
        return 0
    if 0x80 <= status_byte <= 0xBF:  # Note Off, Note On, Poly Pressure, CC
        return 3
    if 0xC0 <= status_byte <= 0xDF:  # Program Change, Channel Pressure
        return 2
    if 0xE0 <= status_byte <= 0xEF:  # Pitch Bend
        return 3
    if status_byte >= 0xF8:          # Realtime (Clock 0xF8, Start 0xFA, Stop 0xFC, etc.)
        return 1
    # System Common:
    if status_byte in (0xF1, 0xF3):  # Time Code, Song Select
        return 2
    if status_byte == 0xF2:          # Song Position Pointer
        return 3
    if status_byte in (0xF6, 0xF7):  # Tune Request, EOX
        return 1
    return 1


class MIDIINCAPSW(ctypes.Structure):
    _fields_ = [
        ("wMid", wintypes.WORD),
        ("wPid", wintypes.WORD),
        ("vDriverVersion", wintypes.UINT),
        ("szPname", wintypes.WCHAR * 32),
        ("dwSupport", wintypes.DWORD),
    ]


class MIDIOUTCAPSW(ctypes.Structure):
    _fields_ = [
        ("wMid", wintypes.WORD),
        ("wPid", wintypes.WORD),
        ("vDriverVersion", wintypes.UINT),
        ("szPname", wintypes.WCHAR * 32),
        ("wTechnology", wintypes.WORD),
        ("wVoices", wintypes.WORD),
        ("wNotes", wintypes.WORD),
        ("wChannelMask", wintypes.WORD),
        ("dwSupport", wintypes.DWORD),
    ]


class MIDIHDR(ctypes.Structure):
    pass


MIDIHDR._fields_ = [
    ("lpData", ctypes.c_char_p),
    ("dwBufferLength", wintypes.DWORD),
    ("dwBytesRecorded", wintypes.DWORD),
    ("dwUser", ctypes.c_void_p),
    ("dwFlags", wintypes.DWORD),
    ("lpNext", ctypes.POINTER(MIDIHDR)),
    ("reserved", ctypes.c_void_p),
    ("dwOffset", wintypes.DWORD),
    ("dwReserved", ctypes.c_void_p * 8),
]

# Callback signature for midiInOpen
MidiInProc = ctypes.WINFUNCTYPE(
    None,
    ctypes.c_void_p,  # hMidiIn
    wintypes.UINT,    # wMsg
    ctypes.c_void_p,  # dwInstance
    ctypes.c_void_p,  # dwParam1
    ctypes.c_void_p,  # dwParam2
)


class WinMMMidiAdapter(MidiAdapterBase):
    def __init__(self):
        self._is_windows = sys.platform == "win32"
        self._winmm = None
        if self._is_windows:
            try:
                self._winmm = ctypes.windll.winmm
                self._setup_function_signatures()
            except Exception as e:
                print(f"Error initializing winmm.dll: {e}")

        self._inputs: Dict[str, MidiPortInfo] = {}
        self._outputs: Dict[str, MidiPortInfo] = {}
        self._open_out_handles: Dict[str, ctypes.c_void_p] = {}
        self._open_in_handles: Dict[str, ctypes.c_void_p] = {}
        self._in_callbacks: Dict[str, MidiInputCallback] = {}
        self._c_callback_refs: Dict[str, Any] = {}
        self._pending_sysex = []

        self.refresh_ports()

    def _setup_function_signatures(self):
        if not self._winmm:
            return
        # Output functions
        self._winmm.midiOutGetNumDevs.restype = wintypes.UINT
        self._winmm.midiOutGetDevCapsW.argtypes = [wintypes.UINT, ctypes.POINTER(MIDIOUTCAPSW), wintypes.UINT]
        self._winmm.midiOutGetDevCapsW.restype = wintypes.UINT

        self._winmm.midiOutOpen.argtypes = [
            ctypes.POINTER(ctypes.c_void_p), wintypes.UINT, ctypes.c_void_p, ctypes.c_void_p, wintypes.DWORD
        ]
        self._winmm.midiOutOpen.restype = wintypes.UINT

        self._winmm.midiOutShortMsg.argtypes = [ctypes.c_void_p, wintypes.DWORD]
        self._winmm.midiOutShortMsg.restype = wintypes.UINT

        self._winmm.midiOutClose.argtypes = [ctypes.c_void_p]
        self._winmm.midiOutClose.restype = wintypes.UINT

        self._winmm.midiOutPrepareHeader.argtypes = [ctypes.c_void_p, ctypes.POINTER(MIDIHDR), wintypes.UINT]
        self._winmm.midiOutPrepareHeader.restype = wintypes.UINT

        self._winmm.midiOutUnprepareHeader.argtypes = [ctypes.c_void_p, ctypes.POINTER(MIDIHDR), wintypes.UINT]
        self._winmm.midiOutUnprepareHeader.restype = wintypes.UINT

        self._winmm.midiOutLongMsg.argtypes = [ctypes.c_void_p, ctypes.POINTER(MIDIHDR), wintypes.UINT]
        self._winmm.midiOutLongMsg.restype = wintypes.UINT

        self._winmm.midiOutReset.argtypes = [ctypes.c_void_p]
        self._winmm.midiOutReset.restype = wintypes.UINT

        # Input functions
        self._winmm.midiInGetNumDevs.restype = wintypes.UINT
        self._winmm.midiInGetDevCapsW.argtypes = [wintypes.UINT, ctypes.POINTER(MIDIINCAPSW), wintypes.UINT]
        self._winmm.midiInGetDevCapsW.restype = wintypes.UINT

        self._winmm.midiInOpen.argtypes = [
            ctypes.POINTER(ctypes.c_void_p), wintypes.UINT, ctypes.c_void_p, ctypes.c_void_p, wintypes.DWORD
        ]
        self._winmm.midiInOpen.restype = wintypes.UINT

        self._winmm.midiInStart.argtypes = [ctypes.c_void_p]
        self._winmm.midiInStart.restype = wintypes.UINT

        self._winmm.midiInStop.argtypes = [ctypes.c_void_p]
        self._winmm.midiInStop.restype = wintypes.UINT

        self._winmm.midiInClose.argtypes = [ctypes.c_void_p]
        self._winmm.midiInClose.restype = wintypes.UINT

    def refresh_ports(self) -> None:
        if not self._winmm:
            return

        # 1. Enumerate Outputs
        num_out = self._winmm.midiOutGetNumDevs()
        new_outputs = {}
        for idx in range(num_out):
            caps = MIDIOUTCAPSW()
            res = self._winmm.midiOutGetDevCapsW(idx, ctypes.byref(caps), ctypes.sizeof(caps))
            if res == MMSYSERR_NOERROR:
                name = caps.szPname.strip()
                port_id = f"winmm_out_{idx}_{name.replace(' ', '_')}"
                major = caps.vDriverVersion >> 8
                minor = caps.vDriverVersion & 0xFF
                new_outputs[port_id] = MidiPortInfo(
                    id=port_id,
                    name=name,
                    direction=PortDirection.OUTPUT,
                    is_virtual=False,
                    is_connected=True,
                    system_index=idx,
                    manufacturer="Windows Multimedia",
                    driver_version=f"{major}.{minor}",
                )
        self._outputs = new_outputs

        # 2. Enumerate Inputs
        num_in = self._winmm.midiInGetNumDevs()
        new_inputs = {}
        for idx in range(num_in):
            caps = MIDIINCAPSW()
            res = self._winmm.midiInGetDevCapsW(idx, ctypes.byref(caps), ctypes.sizeof(caps))
            if res == MMSYSERR_NOERROR:
                name = caps.szPname.strip()
                port_id = f"winmm_in_{idx}_{name.replace(' ', '_')}"
                major = caps.vDriverVersion >> 8
                minor = caps.vDriverVersion & 0xFF
                new_inputs[port_id] = MidiPortInfo(
                    id=port_id,
                    name=name,
                    direction=PortDirection.INPUT,
                    is_virtual=False,
                    is_connected=True,
                    system_index=idx,
                    manufacturer="Windows Multimedia",
                    driver_version=f"{major}.{minor}",
                )
        self._inputs = new_inputs

    def get_input_ports(self) -> List[MidiPortInfo]:
        return list(self._inputs.values())

    def get_output_ports(self) -> List[MidiPortInfo]:
        return list(self._outputs.values())

    def open_output(self, port_id: str) -> bool:
        if not self._winmm or port_id not in self._outputs:
            return False

        if port_id in self._open_out_handles:
            return True

        info = self._outputs[port_id]
        h_out = ctypes.c_void_p()
        res = self._winmm.midiOutOpen(ctypes.byref(h_out), info.system_index, 0, 0, 0)
        if res == MMSYSERR_NOERROR:
            self._open_out_handles[port_id] = h_out
            return True
        elif res == MMSYSERR_ALLOCATED:
            info.is_busy = True
            info.error_message = "Port is already open by another application."
            return False
        else:
            info.error_message = f"WinMM error opening output port: code {res}"
            return False

    def _cleanup_pending_sysex(self, h_target=None, force_reset: bool = False) -> None:
        if not self._winmm or not self._pending_sysex:
            return
        remaining = []
        for raw_buf, hdr, h_out in self._pending_sysex:
            if h_target is not None and getattr(h_out, 'value', h_out) != getattr(h_target, 'value', h_target):
                remaining.append((raw_buf, hdr, h_out))
                continue
            if force_reset:
                try:
                    self._winmm.midiOutReset(h_out)
                except Exception:
                    pass
            if (hdr.dwFlags & 1) or force_reset:
                unprep = self._winmm.midiOutUnprepareHeader(h_out, ctypes.byref(hdr), ctypes.sizeof(hdr))
                if unprep == MMSYSERR_NOERROR or force_reset:
                    continue
            remaining.append((raw_buf, hdr, h_out))
        self._pending_sysex = remaining

    def close_output(self, port_id: str) -> None:
        if port_id in self._open_out_handles:
            h = self._open_out_handles.pop(port_id)
            if self._winmm:
                self._cleanup_pending_sysex(h_target=h, force_reset=True)
                self._winmm.midiOutClose(h)

    def open_input(self, port_id: str, callback: MidiInputCallback) -> bool:
        if not self._winmm or port_id not in self._inputs:
            return False

        if port_id in self._open_in_handles:
            self._in_callbacks[port_id] = callback
            return True

        info = self._inputs[port_id]
        self._in_callbacks[port_id] = callback

        def _native_callback(h_midi_in, w_msg, dw_instance, dw_param1, dw_param2):
            if w_msg == MIM_DATA:
                status = dw_param1 & 0xFF
                data1 = (dw_param1 >> 8) & 0xFF
                data2 = (dw_param1 >> 16) & 0xFF
                ts = time.time() * 1000.0

                length = get_midi_message_length(status)
                if length == 1:
                    msg_bytes = bytes([status])
                elif length == 2:
                    msg_bytes = bytes([status, data1])
                elif length == 3:
                    msg_bytes = bytes([status, data1, data2])
                else:
                    msg_bytes = bytes([status])

                cb = self._in_callbacks.get(port_id)
                if cb:
                    cb(port_id, msg_bytes, ts)

        c_proc = MidiInProc(_native_callback)
        self._c_callback_refs[port_id] = c_proc

        h_in = ctypes.c_void_p()
        res = self._winmm.midiInOpen(
            ctypes.byref(h_in),
            info.system_index,
            c_proc,
            0,
            CALLBACK_FUNCTION,
        )
        if res == MMSYSERR_NOERROR:
            self._open_in_handles[port_id] = h_in
            self._winmm.midiInStart(h_in)
            return True
        else:
            info.error_message = f"WinMM error opening input port: code {res}"
            return False

    def close_input(self, port_id: str) -> None:
        if port_id in self._open_in_handles:
            h = self._open_in_handles.pop(port_id)
            if self._winmm:
                self._winmm.midiInStop(h)
                self._winmm.midiInClose(h)
            self._c_callback_refs.pop(port_id, None)
            self._in_callbacks.pop(port_id, None)

    def send_bytes(self, port_id: str, data: bytes) -> bool:
        if not self._winmm or port_id not in self._open_out_handles:
            if not self.open_output(port_id):
                return False

        h_out = self._open_out_handles.get(port_id)
        if not h_out:
            return False

        length = len(data)
        if length == 0:
            return False

        # Short message (1-3 bytes)
        if length <= 3:
            b0 = data[0]
            b1 = data[1] if length > 1 else 0
            b2 = data[2] if length > 2 else 0
            dword = b0 | (b1 << 8) | (b2 << 16)
            res = self._winmm.midiOutShortMsg(h_out, dword)
            return res == MMSYSERR_NOERROR
        else:
            self._cleanup_pending_sysex()
            # Long / SysEx message with safe buffer retention
            raw_buf = ctypes.create_string_buffer(data)
            hdr = MIDIHDR()
            hdr.lpData = ctypes.cast(raw_buf, ctypes.c_char_p)
            hdr.dwBufferLength = length
            hdr.dwFlags = 0

            prep_res = self._winmm.midiOutPrepareHeader(h_out, ctypes.byref(hdr), ctypes.sizeof(hdr))
            if prep_res != MMSYSERR_NOERROR:
                return False

            send_res = self._winmm.midiOutLongMsg(h_out, ctypes.byref(hdr), ctypes.sizeof(hdr))
            if send_res != MMSYSERR_NOERROR:
                self._winmm.midiOutUnprepareHeader(h_out, ctypes.byref(hdr), ctypes.sizeof(hdr))
                return False

            # Wait for transmission completion flag MHDR_DONE (0x00000001)
            t_start = time.perf_counter()
            done = False
            while time.perf_counter() - t_start < 0.5:
                if hdr.dwFlags & 1:
                    done = True
                    break
                time.sleep(0.002)

            if done:
                unprep = self._winmm.midiOutUnprepareHeader(h_out, ctypes.byref(hdr), ctypes.sizeof(hdr))
                if unprep == MMSYSERR_NOERROR:
                    return True

            # Delayed completion or still playing: retain buffer and header references to prevent use-after-free
            self._pending_sysex.append((raw_buf, hdr, h_out))
            return True

    def close_all(self) -> None:
        for p in list(self._open_out_handles.keys()):
            self.close_output(p)
        for p in list(self._open_in_handles.keys()):
            self.close_input(p)
        self._cleanup_pending_sysex(force_reset=True)
