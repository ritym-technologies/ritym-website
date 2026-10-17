import time
import unittest
from src.api.studio import PedalState, StudioRack


class TestReferenceReceiver(unittest.TestCase):
    def test_no_optimistic_state(self):
        state = PedalState().snapshot()
        self.assertIsNone(state['program'])
        self.assertIsNone(state['measured_bpm'])
        self.assertEqual(state['received'], 0)

    def test_received_bank_and_program(self):
        pedal = PedalState()
        for packet in ('B0 00 01', 'B0 20 02', 'C0 18'):
            pedal.receive(bytes.fromhex(packet))
        state = pedal.snapshot()
        self.assertEqual((state['bank_msb'], state['bank_lsb'], state['program']), (1, 2, 24))
        self.assertEqual([e['bytes'] for e in state['events']], [[176, 0, 1], [176, 32, 2], [192, 24]])

    def test_wrong_channel_not_accepted(self):
        pedal = PedalState()
        pedal.receive(bytes.fromhex('C0 18'), channel=2)
        self.assertIsNone(pedal.snapshot()['program'])
        pedal.receive(bytes.fromhex('C1 19'), channel=2)
        self.assertEqual(pedal.snapshot()['program'], 25)

    def test_cc_mapping_is_received_data(self):
        pedal = PedalState()
        pedal.receive(bytes.fromhex('B0 0B 60'))
        self.assertEqual(pedal.snapshot()['cc'][11], 96)

    def test_clock_estimate_and_bounded_history(self):
        pedal = PedalState()
        start = time.perf_counter()
        for i in range(140):
            pedal.receive(b'\xf8', now=start + i / 48)
        self.assertAlmostEqual(pedal.snapshot()['measured_bpm'], 120, places=1)
        self.assertEqual(len(pedal.snapshot()['intervals_ms']), 96)
        for i in range(200):
            pedal.receive(b'\xc0\x18')
        self.assertEqual(len(pedal.snapshot()['events']), 96)

    def test_transport_is_not_inferred_from_program(self):
        pedal = PedalState()
        pedal.receive(b'\xfa')
        pedal.receive(b'\xc0\x18')
        self.assertEqual(pedal.snapshot()['transport'], 'RUNNING')
        pedal.receive(b'\xfc')
        self.assertEqual(pedal.snapshot()['transport'], 'STOPPED')


class TestKeybedOwnership(unittest.TestCase):
    def test_note_off_and_failure_ownership(self):
        class Adapter:
            def __init__(self):
                self.sent = []
                self.accept = True
            def send_bytes(self, port, packet):
                self.sent.append(packet)
                return self.accept
        adapter = Adapter()
        rack = StudioRack(adapter=adapter)
        rack.keyboard_id = 'test-only'
        rack.note(60, 2, 100, True)
        rack.note(60, 2, 100, True)
        rack.note(60, 2, 100, False)
        self.assertEqual(adapter.sent, [bytes.fromhex('91 3C 64'), bytes.fromhex('81 3C 00')])
        rack.release_notes()
        self.assertEqual(len(adapter.sent), 2, 'Idle cleanup must not flood MIDI with controller messages')
        adapter.accept = False
        with self.assertRaises(RuntimeError):
            rack.note(61, 2, 100, True)
        self.assertFalse(rack.notes)

    def test_native_features_explicitly_disabled_in_simulation(self):
        rack = StudioRack(enabled=False, transport_mode='loopmidi')
        with self.assertRaises(RuntimeError):
            rack.connect('keyboard')
        self.assertFalse(rack.state()['native_enabled'])



class TestInternalPracticeTransport(unittest.TestCase):
    def test_internal_keybed_note_dispatched_to_callback(self):
        received = []
        def on_input(port, data, ts):
            received.append((port, list(data)))

        rack = StudioRack(enabled=True, transport_mode='internal')
        rack.internal_input_cb = on_input
        rack.connect('keyboard')
        rack.note(60, 1, 100, True)
        rack.note(60, 1, 100, False)

        self.assertEqual(len(received), 2)
        self.assertEqual(received[0][1], [0x90, 60, 100])
        self.assertEqual(received[1][1], [0x80, 60, 0])

    def test_internal_pedal_receives_direct_dispatch(self):
        rack = StudioRack(enabled=True, transport_mode='internal')
        rack.connect('pedal')
        rack.pedal.receive(bytes([0xC0, 24]))
        rack.pedal.receive(bytes([0xB0, 11, 96]))
        rack.pedal.receive(bytes([0xB0, 64, 127]))

        snap = rack.pedal.snapshot()
        self.assertEqual(snap['program'], 24)
        self.assertEqual(snap['cc'][11], 96)
        self.assertEqual(snap['cc'][64], 127)

    def test_mode_switching(self):
        rack = StudioRack(enabled=True, transport_mode='internal')
        self.assertEqual(rack.transport_mode, 'internal')
        rack.set_mode('loopmidi')
        self.assertEqual(rack.transport_mode, 'loopmidi')
        rack.set_mode('internal')
        self.assertEqual(rack.transport_mode, 'internal')


if __name__ == '__main__':
    unittest.main()
