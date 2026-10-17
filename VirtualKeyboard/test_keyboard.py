"""Regression checks for note ownership and the native loopMIDI path."""
import ctypes as C
from ctypes import wintypes as W
import json
from pathlib import Path
import threading
import time
import unittest
from midi_backend import KeyboardSession, MidiOutput


class SessionTests(unittest.TestCase):
    def setUp(self):
        self.sent = []
        self.session = KeyboardSession(self.sent.append)

    def test_overlap_and_release(self):
        self.session.press('typing', 60, 2, 90)
        self.session.press('typing', 60, 2, 90)
        self.session.press('mouse', 60, 2, 100)
        self.session.release('typing')
        self.assertEqual(self.sent, [bytes.fromhex('91 3C 5A')])
        self.session.release('mouse')
        self.assertEqual(self.sent[-1], bytes.fromhex('81 3C 00'))

    def test_release_original_channel_and_note(self):
        self.session.press('mouse', 60, 1)
        self.session.press('mouse', 64, 2)
        self.session.release('mouse')
        self.assertEqual(self.sent, [bytes.fromhex(h) for h in ('90 3C 64', '80 3C 00', '91 40 64', '81 40 00')])

    def test_panic_releases_notes_and_all_channels(self):
        self.session.press('a', 60)
        self.session.panic()
        self.assertFalse(self.session.held)
        self.assertEqual(len(self.sent), 50)
        self.assertEqual(self.sent[-1], bytes.fromhex('BF 78 00'))

    def test_failed_send_not_recorded_as_pressed(self):
        def fail(packet):
            raise RuntimeError('disconnected')
        session = KeyboardSession(fail)
        with self.assertRaises(RuntimeError):
            session.press('a', 60)
        self.assertFalse(session.held)

    def test_validation(self):
        for note, channel, velocity in ((128, 1, 100), (60, 0, 100), (60, 1, 0)):
            with self.assertRaises(ValueError):
                self.session.press('x', note, channel, velocity)
        self.assertEqual(self.sent, [])

    def test_stale_handle_does_not_block_reconnect(self):
        calls = []
        class Driver:
            def midiOutReset(self, handle):
                calls.append('reset')
                return 6
            def midiOutClose(self, handle):
                calls.append('close')
                return 6
        output = object.__new__(MidiOutput)
        output.dll, output.handle, output.port = Driver(), object(), object()
        output.close()
        self.assertEqual(calls, ['reset', 'close'])
        self.assertIsNone(output.handle)
        self.assertIsNone(output.port)


def native_loopback():
    # Only the dedicated software port is opened: no physical or synth output.
    output = MidiOutput()
    matches = [p for p in output.ports() if p.name == 'PulseStage Keyboard']
    if len(matches) != 1:
        raise RuntimeError('Expected exactly one PulseStage Keyboard loopMIDI port')
    class InCaps(C.Structure):
        _fields_ = [('mid', W.WORD), ('pid', W.WORD), ('version', W.UINT),
                    ('name', W.WCHAR * 32), ('support', W.DWORD)]
    dll = output.dll
    dll.midiInGetNumDevs.restype = W.UINT
    dll.midiInGetDevCapsW.argtypes = [C.c_size_t, C.POINTER(InCaps), W.UINT]
    callback_type = C.WINFUNCTYPE(None, C.c_void_p, W.UINT, C.c_size_t, C.c_size_t, C.c_size_t)
    dll.midiInOpen.argtypes = [C.POINTER(C.c_void_p), W.UINT, callback_type, C.c_size_t, W.DWORD]
    for name in ('midiInStart', 'midiInStop', 'midiInReset', 'midiInClose'):
        getattr(dll, name).argtypes = [C.c_void_p]
    received = []
    done = threading.Event()
    expected = ['913c64', '813c00', 'b10b40']
    @callback_type
    def callback(handle, message, instance, data, timestamp):
        if message == 0x3C3:
            received.append(int(data).to_bytes(4, 'little')[:3].hex())
            if len(received) >= len(expected):
                done.set()
    inputs = []
    for index in range(dll.midiInGetNumDevs()):
        caps = InCaps()
        output.check(dll.midiInGetDevCapsW(index, C.byref(caps), C.sizeof(caps)))
        if caps.name == 'PulseStage Keyboard':
            inputs.append(index)
    if len(inputs) != 1:
        raise RuntimeError('Expected dedicated virtual MIDI input')
    handle = C.c_void_p()
    output.check(dll.midiInOpen(C.byref(handle), inputs[0], callback, 0, 0x30000))
    try:
        output.check(dll.midiInStart(handle))
        output.open(matches[0])
        session = KeyboardSession(output.send)
        session.press('test', 60, 2, 100)
        session.release('test')
        output.send(bytes.fromhex('B1 0B 40'))
        done.wait(2)
        result = {'port': matches[0].name, 'expected': expected,
                  'received_before_cleanup': list(received), 'passed': received == expected,
                  'physical_hardware_tested': False}
    finally:
        output.close()
        dll.midiInStop(handle)
        dll.midiInReset(handle)
        dll.midiInClose(handle)
    Path(__file__).with_name('native-test-results.json').write_text(json.dumps(result, indent=2))
    assert result['passed'], result
    print(json.dumps(result))


if __name__ == '__main__':
    import sys
    if '--native' in sys.argv:
        native_loopback()
    else:
        unittest.main()
