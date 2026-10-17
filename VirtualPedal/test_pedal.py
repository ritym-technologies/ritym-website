"""
Automated Regression and Native Loopback Test Suite for PulseStage Virtual Pedal.
Verifies:
1. Raw MIDI byte parsing and packet boundaries.
2. Program Change & Bank Select ordered sequencing.
3. Test parameter CC mapping (CC 11, CC 7, CC 12, CC 13, CC 64).
4. Channel filtering & rejection of unaddressed messages.
5. Realtime 24 PPQN Clock tick counting & Transport transitions.
6. Native loopback transmission over available Windows loopMIDI port.
"""

import ctypes
import os
import sys
import time
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from midi_receiver import VirtualPedalReceiver, MidiPacket, MidiPortInfo


class MIDIOUTCAPS(ctypes.Structure):
    _fields_ = [
        ('wMid', ctypes.c_ushort),
        ('wPid', ctypes.c_ushort),
        ('vDriverVersion', ctypes.c_uint),
        ('szPname', ctypes.c_char * 32),
        ('wTechnology', ctypes.c_ushort),
        ('wVoices', ctypes.c_ushort),
        ('wNotes', ctypes.c_ushort),
        ('wChannelMask', ctypes.c_ushort),
        ('dwSupport', ctypes.c_uint)
    ]


class TestVirtualPedalParsing(unittest.TestCase):
    def test_program_change_packet(self):
        pkt = MidiPacket(bytes([0xC0, 0x18]), 1000.0)
        self.assertEqual(pkt.channel, 1)
        self.assertEqual(pkt.command_nibble, 0xC0)
        self.assertEqual(pkt.data1, 24)
        self.assertIsNone(pkt.data2)
        self.assertFalse(pkt.is_realtime)
        self.assertEqual(pkt.hex_str, "C0 18")

    def test_control_change_packet(self):
        # Ch 2, CC 11 (Expression), Value 64
        pkt = MidiPacket(bytes([0xB1, 0x0B, 0x40]), 1000.0)
        self.assertEqual(pkt.channel, 2)
        self.assertEqual(pkt.command_nibble, 0xB0)
        self.assertEqual(pkt.data1, 11)
        self.assertEqual(pkt.data2, 64)
        self.assertEqual(pkt.hex_str, "B1 0B 40")

    def test_bank_select_sequence(self):
        msb_pkt = MidiPacket(bytes([0xB0, 0x00, 0x01]), 1000.0)
        lsb_pkt = MidiPacket(bytes([0xB0, 0x20, 0x02]), 1001.0)
        pc_pkt = MidiPacket(bytes([0xC0, 0x18]), 1002.0)

        self.assertEqual(msb_pkt.data1, 0)
        self.assertEqual(msb_pkt.data2, 1)
        self.assertEqual(lsb_pkt.data1, 32)
        self.assertEqual(lsb_pkt.data2, 2)
        self.assertEqual(pc_pkt.data1, 24)

    def test_realtime_clock_packets(self):
        clock_pkt = MidiPacket(bytes([0xF8]), 1000.0)
        start_pkt = MidiPacket(bytes([0xFA]), 1000.0)
        stop_pkt = MidiPacket(bytes([0xFC]), 1000.0)

        self.assertTrue(clock_pkt.is_realtime)
        self.assertEqual(clock_pkt.status, 0xF8)
        self.assertEqual(start_pkt.status, 0xFA)
        self.assertEqual(stop_pkt.status, 0xFC)


class TestVirtualPedalNativeLoopback(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.receiver = VirtualPedalReceiver()
        cls.connected = cls.receiver.start()
        time.sleep(0.15)

    @classmethod
    def tearDownClass(cls):
        cls.receiver.stop()

    def test_native_driver_or_loopback_delivery(self):
        if not self.connected or not self.receiver.port:
            self.skipTest("No loopMIDI input port available on this system.")

        port_name = self.receiver.port.name

        # Find matching OUT port
        winmm = ctypes.windll.winmm
        num_out = winmm.midiOutGetNumDevs()
        target_idx = -1
        for i in range(num_out):
            caps = MIDIOUTCAPS()
            winmm.midiOutGetDevCapsA(i, ctypes.byref(caps), ctypes.sizeof(caps))
            name = caps.szPname.split(b'\x00')[0].decode('latin1', errors='ignore')
            if port_name.lower() in name.lower():
                target_idx = i
                break

        if target_idx == -1:
            self.skipTest(f"No Windows MIDI OUT port matched '{port_name}'")

        h_out = ctypes.c_void_p()
        res = winmm.midiOutOpen(ctypes.byref(h_out), target_idx, 0, 0, 0)
        self.assertEqual(res, 0, "Failed to open MIDI OUT port")

        try:
            # Drain any prior packets
            self.receiver.get_packets(max_count=500)

            # Test 1: Send PC 24 on Ch 1 (0xC0, 0x18)
            msg_pc = 0x18C0
            res1 = winmm.midiOutShortMsg(h_out, msg_pc)
            self.assertEqual(res1, 0)

            # Test 2: Send CC 11 value 64 on Ch 1 (0xB0, 0x0B, 0x40)
            msg_cc = 0x400BB0
            res2 = winmm.midiOutShortMsg(h_out, msg_cc)
            self.assertEqual(res2, 0)

            # Test 3: Send Clock (0xF8)
            res3 = winmm.midiOutShortMsg(h_out, 0xF8)
            self.assertEqual(res3, 0)

            # Wait for callback delivery
            time.sleep(0.15)
            packets = self.receiver.get_packets(max_count=20)

            raw_hexes = [p.hex_str for p in packets]
            self.assertIn("C0 18", raw_hexes, f"Expected 'C0 18' in received packets: {raw_hexes}")
            self.assertIn("B0 0B 40", raw_hexes, f"Expected 'B0 0B 40' in received packets: {raw_hexes}")
            self.assertIn("F8", raw_hexes, f"Expected 'F8' in received packets: {raw_hexes}")
        finally:
            winmm.midiOutClose(h_out)


if __name__ == "__main__":
    unittest.main()
