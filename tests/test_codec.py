"""
Tests for MIDI Message Encoding and Decoding
"""
import unittest
from src.core.models import MessageType, Direction, PresetNumbering
from src.core.codec import (
    encode_program_change,
    encode_control_change,
    encode_bank_select,
    encode_realtime,
    decode_message,
)


class TestMidiCodec(unittest.TestCase):
    def test_encode_program_change(self):
        # Ch 1, PC 0
        b = encode_program_change(1, 0)
        self.assertEqual(b, bytes([0xC0, 0x00]))

        # Ch 16, PC 127
        b16 = encode_program_change(16, 127)
        self.assertEqual(b16, bytes([0xCF, 0x7F]))

    def test_encode_control_change(self):
        # Ch 1, CC 64 (Sustain), Val 127
        b = encode_control_change(1, 64, 127)
        self.assertEqual(b, bytes([0xB0, 0x40, 0x7F]))

        # Ch 5, CC 11 (Expression), Val 64
        b5 = encode_control_change(5, 11, 64)
        self.assertEqual(b5, bytes([0xB4, 0x0B, 0x40]))

    def test_encode_bank_select(self):
        # Bank MSB 2, LSB 1, PC 10 on Ch 1
        pkts = encode_bank_select(1, 2, 1, 10)
        self.assertEqual(len(pkts), 3)
        self.assertEqual(pkts[0], bytes([0xB0, 0x00, 0x02]))  # CC 0 (MSB)
        self.assertEqual(pkts[1], bytes([0xB0, 0x20, 0x01]))  # CC 32 (LSB)
        self.assertEqual(pkts[2], bytes([0xC0, 0x0A]))        # PC

    def test_encode_realtime(self):
        self.assertEqual(encode_realtime(MessageType.CLOCK), bytes([0xF8]))
        self.assertEqual(encode_realtime(MessageType.START), bytes([0xFA]))
        self.assertEqual(encode_realtime(MessageType.CONTINUE), bytes([0xFB]))
        self.assertEqual(encode_realtime(MessageType.STOP), bytes([0xFC]))

    def test_decode_channel_messages(self):
        # Decode PC 24 on Ch 2
        raw = bytes([0xC1, 0x18])
        msg = decode_message(raw, port_name="TestPort", direction=Direction.RX)
        self.assertEqual(msg.message_type, MessageType.PROGRAM_CHANGE)
        self.assertEqual(msg.channel, 2)
        self.assertEqual(msg.data1, 24)
        self.assertIn("Program Change 24", msg.friendly_text)

        # Decode CC 64 on Ch 1
        raw_cc = bytes([0xB0, 0x40, 0x7F])
        msg_cc = decode_message(raw_cc, port_name="TestPort")
        self.assertEqual(msg_cc.message_type, MessageType.CONTROL_CHANGE)
        self.assertEqual(msg_cc.data1, 64)
        self.assertEqual(msg_cc.data2, 127)
        self.assertIn("Sustain", msg_cc.friendly_text)

    def test_decode_realtime(self):
        raw_clk = bytes([0xF8])
        msg = decode_message(raw_clk)
        self.assertEqual(msg.message_type, MessageType.CLOCK)
        self.assertIn("24 PPQN", msg.friendly_text)


if __name__ == "__main__":
    unittest.main()
