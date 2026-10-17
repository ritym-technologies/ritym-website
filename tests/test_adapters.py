"""
Tests for Platform Adapters and Status Byte Lengths
"""
import unittest
from src.adapters.virtual_adapter import VirtualMidiAdapter
from src.adapters.winmm_adapter import get_midi_message_length


class TestAdapters(unittest.TestCase):
    def test_status_byte_length_resolution(self):
        # Channel Voice
        self.assertEqual(get_midi_message_length(0x90), 3)  # Note On
        self.assertEqual(get_midi_message_length(0xB0), 3)  # CC
        self.assertEqual(get_midi_message_length(0xC0), 2)  # Program Change
        # System Common
        self.assertEqual(get_midi_message_length(0xF1), 2)  # MTC Quarter Frame
        self.assertEqual(get_midi_message_length(0xF2), 3)  # Song Position Pointer
        self.assertEqual(get_midi_message_length(0xF3), 2)  # Song Select
        self.assertEqual(get_midi_message_length(0xF6), 1)  # Tune Request
        # Realtime
        self.assertEqual(get_midi_message_length(0xF8), 1)  # Clock
        self.assertEqual(get_midi_message_length(0xFA), 1)  # Start
        self.assertEqual(get_midi_message_length(0xFC), 1)  # Stop

    def test_virtual_adapter_lifecycle(self):
        adapter = VirtualMidiAdapter(echo_loopback=True)
        outputs = adapter.get_output_ports()
        inputs = adapter.get_input_ports()

        self.assertGreater(len(outputs), 0)
        self.assertGreater(len(inputs), 0)

        out_id = outputs[0].id
        in_id = inputs[0].id

        received = []
        def _cb(port, data, ts):
            received.append(data)

        self.assertTrue(adapter.open_output(out_id))
        self.assertTrue(adapter.open_input(in_id, _cb))

        test_payload = bytes([0xC0, 0x14])
        self.assertTrue(adapter.send_bytes(out_id, test_payload))
        self.assertEqual(len(adapter.sent_history), 1)
        self.assertEqual(len(received), 1)
        self.assertEqual(received[0], test_payload)


    def test_winmm_sysex_delayed_completion_buffer_retention(self):
        from unittest.mock import MagicMock
        from src.adapters.winmm_adapter import WinMMMidiAdapter, MMSYSERR_NOERROR
        import ctypes

        adapter = WinMMMidiAdapter()
        mock_winmm = MagicMock()
        mock_winmm.midiOutPrepareHeader.return_value = MMSYSERR_NOERROR
        mock_winmm.midiOutLongMsg.return_value = MMSYSERR_NOERROR
        mock_winmm.midiOutUnprepareHeader.return_value = 69
        mock_winmm.midiOutReset.return_value = MMSYSERR_NOERROR
        mock_winmm.midiOutClose.return_value = MMSYSERR_NOERROR

        adapter._winmm = mock_winmm
        dummy_h = ctypes.c_void_p(0x1234)
        adapter._open_out_handles["test_port"] = dummy_h

        sysex_data = bytes([0xF0, 0x7E, 0x7F, 0x06, 0x01, 0xF7])
        res = adapter.send_bytes("test_port", sysex_data)
        self.assertTrue(res)
        self.assertEqual(len(adapter._pending_sysex), 1)
        buf, hdr, h = adapter._pending_sysex[0]
        self.assertEqual(buf.raw[:len(sysex_data)], sysex_data)

        adapter.close_output("test_port")
        mock_winmm.midiOutReset.assert_called_with(dummy_h)
        self.assertEqual(len(adapter._pending_sysex), 0)


if __name__ == "__main__":
    unittest.main()
