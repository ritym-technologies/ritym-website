"""
Tests for MIDI Clock Generator, Monotonic Scheduling, and Drift Elimination
"""
import time
import unittest
from src.core.models import MessageType
from src.engine.clock import MidiClock, TransportState


class TestMidiClock(unittest.TestCase):
    def test_bpm_clamping(self):
        clock = MidiClock(send_callback=lambda b: True)
        clock.set_bpm(10)  # Below 40
        self.assertEqual(clock.bpm, 40.0)
        clock.set_bpm(400) # Above 300
        self.assertEqual(clock.bpm, 300.0)
        clock.set_bpm(133.5)
        self.assertEqual(clock.bpm, 133.5)

    def test_tap_tempo_outlier_rejection(self):
        clock = MidiClock(send_callback=lambda b: True)
        clock.set_bpm(120.0)
        t0 = time.perf_counter()
        # 4 steady taps at 120 BPM (interval = 0.5 sec)
        clock._tap_history = [t0, t0 + 0.5, t0 + 1.0, t0 + 1.5]
        bpm = clock.tap_tempo()
        self.assertTrue(118.0 <= bpm <= 122.0)

        # Accidental double-tap 50 ms later must be REJECTED!
        clock._tap_history.append(t0 + 1.55)
        bpm_after_glitch = clock.tap_tempo()
        self.assertTrue(118.0 <= bpm_after_glitch <= 122.0, f"Glitch tap distorted BPM to {bpm_after_glitch}!")

    def test_continuous_group_boundary_timing(self):
        intervals = []
        t_last = None

        def _record(b):
            nonlocal t_last
            if b == bytes([0xF8]):
                now = time.perf_counter()
                if t_last is not None:
                    intervals.append((now - t_last) * 1000.0)
                t_last = now
            return True

        clock = MidiClock(send_callback=_record)
        clock.set_bpm(120.0)
        # Expected interval per 24 PPQN tick = 20.833 ms
        clock.start()
        time.sleep(1.2)  # Capture ~50 ticks spanning multiple 24-tick beats
        clock.stop()

        self.assertGreater(len(intervals), 40)
        # Verify NO group boundary collapse (< 2 ms)
        short_intervals = [x for x in intervals if x < 2.0]
        self.assertEqual(len(short_intervals), 0, f"Found {len(short_intervals)} collapsed boundary intervals!")

        # Verify mean interval is within 0.5 ms of theoretical 20.833 ms
        mean_int = sum(intervals) / len(intervals)
        self.assertAlmostEqual(mean_int, 20.833, delta=0.5)


if __name__ == "__main__":
    unittest.main()
