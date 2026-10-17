"""
Tests for Validation, Boundaries, and Preset Numbering
"""
import unittest
from src.core.models import (
    validate_channel,
    validate_7bit,
    MidiMessage,
    PresetNumbering,
    ActionStep,
    CommandType,
)
from src.core.codec import decode_message


class TestModelsAndBoundaries(unittest.TestCase):
    def test_channel_boundaries(self):
        self.assertEqual(validate_channel(1), 1)
        self.assertEqual(validate_channel(16), 16)
        with self.assertRaises(ValueError):
            validate_channel(0)
        with self.assertRaises(ValueError):
            validate_channel(17)

    def test_7bit_boundaries(self):
        self.assertEqual(validate_7bit(0), 0)
        self.assertEqual(validate_7bit(127), 127)
        with self.assertRaises(ValueError):
            validate_7bit(-1)
        with self.assertRaises(ValueError):
            validate_7bit(128)

    def test_preset_convention_display(self):
        # Wire byte is 19 (0-indexed)
        raw = bytes([0xC0, 19])

        # 0-indexed display: shows Preset [19]
        msg_0 = decode_message(raw, preset_convention=PresetNumbering.ZERO_INDEXED)
        self.assertIn("Preset [19]", msg_0.friendly_text)

        # 1-indexed display: shows Preset [20]
        msg_1 = decode_message(raw, preset_convention=PresetNumbering.ONE_INDEXED)
        self.assertIn("Preset [20]", msg_1.friendly_text)

    def test_action_step_validation(self):
        step = ActionStep(
            id="s1",
            target_port_name="TestPort",
            channel=1,
            command_type=CommandType.CONTROL_CHANGE,
            data1=11,
            data2=100,
            delay_ms=50,
        )
        self.assertEqual(step.channel, 1)
        self.assertEqual(step.delay_ms, 50)

        with self.assertRaises(Exception):
            ActionStep(channel=20)


if __name__ == "__main__":
    unittest.main()
