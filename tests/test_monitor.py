"""
Tests for Diagnostic Monitor Bounded Queues and Formatting
"""
import unittest
from src.core.models import MidiMessage, MessageType, Direction
from src.engine.monitor import MidiMonitor, MonitorFilter


class TestMonitor(unittest.TestCase):
    def test_ring_buffer_capacity(self):
        monitor = MidiMonitor(capacity=10)
        for i in range(25):
            msg = MidiMessage(
                channel=1,
                message_type=MessageType.CONTROL_CHANGE,
                data1=i,
                data2=100,
            )
            monitor.record_message(msg)

        # Buffer should be bounded to capacity 10
        all_msgs = monitor.get_messages(MonitorFilter(show_raw_clock=True))
        self.assertEqual(len(all_msgs), 10)
        # Oldest should have dropped, newest data1 should be 24
        self.assertEqual(all_msgs[-1].data1, 24)

    def test_clock_collapsing_filter(self):
        monitor = MidiMonitor(capacity=50)
        # Record 30 clock ticks and 2 control changes
        for _ in range(30):
            monitor.record_message(MidiMessage(message_type=MessageType.CLOCK))
        monitor.record_message(MidiMessage(channel=1, message_type=MessageType.CONTROL_CHANGE, data1=7, data2=100))
        monitor.record_message(MidiMessage(channel=1, message_type=MessageType.PROGRAM_CHANGE, data1=12))

        # Default filter should hide raw clock ticks but update counter
        filtered = monitor.get_messages()
        self.assertEqual(len(filtered), 2)
        self.assertEqual(monitor.clock_tick_counter, 30)

        # Enabling raw clock returns all
        with_clock = monitor.get_messages(MonitorFilter(show_raw_clock=True))
        self.assertEqual(len(with_clock), 32)

    def test_export_formats(self):
        monitor = MidiMonitor(capacity=10)
        monitor.record_message(MidiMessage(channel=1, message_type=MessageType.PROGRAM_CHANGE, data1=5))

        json_out = monitor.export_json()
        self.assertIn('"application": "PulseStage MIDI"', json_out)

        csv_out = monitor.export_csv()
        self.assertIn("PROGRAM_CHANGE", csv_out)

        txt_out = monitor.export_text()
        self.assertIn("PULSESTAGE MIDI", txt_out)


if __name__ == "__main__":
    unittest.main()
