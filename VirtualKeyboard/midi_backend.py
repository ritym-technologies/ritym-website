"""Small Windows MIDI 1.0 output adapter; no third-party Python dependencies."""
import ctypes as C
from ctypes import wintypes as W
from dataclasses import dataclass


class OutCaps(C.Structure):
    _fields_ = [('mid', W.WORD), ('pid', W.WORD), ('version', W.UINT),
                ('name', W.WCHAR * 32), ('technology', W.WORD),
                ('voices', W.WORD), ('notes', W.WORD), ('channels', W.WORD),
                ('support', W.DWORD)]


@dataclass(frozen=True)
class Port:
    index: int
    name: str


class MidiOutput:
    def __init__(self):
        self.dll = C.WinDLL('winmm')
        self.handle = None
        self.port = None
        self.dll.midiOutGetNumDevs.restype = W.UINT
        self.dll.midiOutGetDevCapsW.argtypes = [C.c_size_t, C.POINTER(OutCaps), W.UINT]
        self.dll.midiOutOpen.argtypes = [C.POINTER(C.c_void_p), W.UINT, C.c_size_t, C.c_size_t, W.DWORD]
        self.dll.midiOutShortMsg.argtypes = [C.c_void_p, W.DWORD]
        self.dll.midiOutReset.argtypes = [C.c_void_p]
        self.dll.midiOutClose.argtypes = [C.c_void_p]
        self.dll.midiOutGetErrorTextW.argtypes = [W.UINT, W.LPWSTR, W.UINT]
        for name in ('midiOutGetDevCapsW', 'midiOutOpen', 'midiOutShortMsg',
                     'midiOutReset', 'midiOutClose', 'midiOutGetErrorTextW'):
            getattr(self.dll, name).restype = W.UINT

    def check(self, code):
        if code:
            message = C.create_unicode_buffer(256)
            self.dll.midiOutGetErrorTextW(code, message, len(message))
            raise RuntimeError(message.value or f'Windows MIDI error {code}')

    def ports(self):
        ports = []
        for index in range(self.dll.midiOutGetNumDevs()):
            caps = OutCaps()
            if not self.dll.midiOutGetDevCapsW(index, C.byref(caps), C.sizeof(caps)):
                ports.append(Port(index, caps.name))
        return ports

    def open(self, port):
        if port not in self.ports():
            raise RuntimeError('That MIDI port has disappeared. Refresh and select it again.')
        self.close()
        handle = C.c_void_p()
        self.check(self.dll.midiOutOpen(C.byref(handle), port.index, 0, 0, 0))
        self.handle, self.port = handle, port

    def send(self, packet):
        packet = bytes(packet)
        if not self.handle:
            raise RuntimeError('Connect a MIDI output first.')
        if not 1 <= len(packet) <= 3 or packet[0] < 0x80 or any(v > 127 for v in packet[1:]):
            raise ValueError('Invalid short MIDI message.')
        self.check(self.dll.midiOutShortMsg(self.handle, int.from_bytes(packet, 'little')))

    def close(self):
        if self.handle:
            # A removed/restarted driver can invalidate a still-stored handle.
            # Attempt close even if reset fails, so reconnect is not trapped.
            reset_result = self.dll.midiOutReset(self.handle)
            close_result = self.dll.midiOutClose(self.handle)
            if close_result not in (0, 5, 6):
                self.check(close_result)
            self.handle = self.port = None
            if reset_result not in (0, 5, 6):
                self.check(reset_result)


class KeyboardSession:
    """Own note lifetimes, including overlapping mouse/typing sources."""
    def __init__(self, send):
        self.send = send
        self.held = {}

    def press(self, source, note, channel=1, velocity=100):
        if not 0 <= note <= 127 or not 1 <= channel <= 16 or not 1 <= velocity <= 127:
            raise ValueError('Invalid note, channel or velocity.')
        target = (note, channel)
        if self.held.get(source) == target:
            return
        self.release(source)
        if target not in self.held.values():
            self.send(bytes([0x90 + channel - 1, note, velocity]))
        self.held[source] = target

    def release(self, source):
        target = self.held.get(source)
        if target is None:
            return
        if list(self.held.values()).count(target) == 1:
            self.send(bytes([0x80 + target[1] - 1, target[0], 0]))
        self.held.pop(source, None)

    def panic(self):
        errors = []
        for source in list(self.held):
            try:
                self.release(source)
            except Exception as error:
                errors.append(str(error))
        self.held.clear()
        for channel in range(16):
            for controller in (64, 123, 120):
                try:
                    self.send(bytes([0xB0 + channel, controller, 0]))
                except Exception as error:
                    errors.append(str(error))
        if errors:
            raise RuntimeError(errors[0])
