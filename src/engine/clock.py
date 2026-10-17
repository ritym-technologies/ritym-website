"""
MIDI Clock Engine: 24 PPQN High-Precision Monotonic Clock Generator.
Windows Multimedia Timer with Generation-Tracked Thread Ownership and Outlier-Rejecting Tap Tempo.
"""
import ctypes
import threading
import time
from typing import Callable, List, Optional
from enum import Enum

from ..core.models import MessageType
from ..core.codec import encode_realtime

# Windows Multimedia high-resolution timer access
_timeBeginPeriod = None
_timeEndPeriod = None
try:
    _winmm = ctypes.WinDLL("winmm.dll")
    _timeBeginPeriod = _winmm.timeBeginPeriod
    _timeEndPeriod = _winmm.timeEndPeriod
    _timeBeginPeriod.argtypes = [ctypes.c_uint]
    _timeBeginPeriod.restype = ctypes.c_uint
    _timeEndPeriod.argtypes = [ctypes.c_uint]
    _timeEndPeriod.restype = ctypes.c_uint
except Exception:
    pass


class TransportState(str, Enum):
    STOPPED = "STOPPED"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"


class MidiClock:
    """
    24 PPQN MIDI Clock Generator with True Monotonic Continuous Scheduling
    and Generation-Tracked Thread Ownership.
    Guarantees:
    - 24 ticks span exactly 24 intervals per beat (no modulo-24 reset bug).
    - An old worker blocked on a driver callback can never resume transmitting alongside a new worker.
    """

    def __init__(
        self,
        send_callback: Callable[[bytes], bool],
        error_callback: Optional[Callable[[str], None]] = None,
    ):
        self._send_cb = send_callback
        self._error_cb = error_callback
        self._bpm: float = 120.0
        self._state: TransportState = TransportState.STOPPED
        self._lock = threading.RLock()
        self._thread: Optional[threading.Thread] = None

        # Generation token: increments on every start/stop to invalidate old blocked workers
        self._generation: int = 0
        self._active_stop_event: Optional[threading.Event] = None

        # Tap Tempo State
        self._tap_history: List[float] = []
        self._last_tap_time: float = 0.0

        # Telemetry
        self.tick_count: int = 0
        self.last_tick_time: float = 0.0
        self.jitter_max_ms: float = 0.0

    @property
    def bpm(self) -> float:
        with self._lock:
            return self._bpm

    @property
    def state(self) -> TransportState:
        with self._lock:
            return self._state

    def set_bpm(self, bpm: float) -> None:
        try:
            val = float(bpm)
        except (ValueError, TypeError):
            val = 120.0
        clamped = max(40.0, min(300.0, val))
        with self._lock:
            self._bpm = clamped

    def tap_tempo(self) -> float:
        """
        Calculates BPM based on consecutive taps with statistical outlier rejection.
        """
        now = time.perf_counter()
        with self._lock:
            if self._last_tap_time > 0 and (now - self._last_tap_time) > 2.5:
                self._tap_history.clear()

            self._tap_history.append(now)
            self._last_tap_time = now

            if len(self._tap_history) > 6:
                self._tap_history.pop(0)

            if len(self._tap_history) < 2:
                return self.bpm

            intervals = [
                self._tap_history[i] - self._tap_history[i - 1]
                for i in range(1, len(self._tap_history))
            ]

            # Outlier rejection using rolling median
            if len(intervals) >= 3:
                sorted_ints = sorted(intervals)
                median_int = sorted_ints[len(sorted_ints) // 2]
                valid = [x for x in intervals if abs(x - median_int) / median_int <= 0.35]
                if valid:
                    intervals = valid

            avg_interval = sum(intervals) / len(intervals)
            # 40 BPM is 1.5s interval; 300 BPM is 0.2s interval
            if 0.20 <= avg_interval <= 1.50:
                calc_bpm = round(60.0 / avg_interval, 1)
                self.set_bpm(calc_bpm)
                return self.bpm

        return self.bpm

    def start(self) -> None:
        """
        Starts clock transmission and transmits MIDI Start (0xFA).
        Spawns a new worker thread bound to an incremented generation ID.
        """
        with self._lock:
            if self._state == TransportState.RUNNING:
                return

            # Invalidate any prior workers
            self._generation += 1
            gen = self._generation

            stop_evt = threading.Event()
            self._active_stop_event = stop_evt
            self._state = TransportState.RUNNING
            self.tick_count = 0

            # Transmit 0xFA (Start)
            try:
                self._send_cb(encode_realtime(MessageType.START))
            except Exception as e:
                print(f"Error transmitting MIDI Start: {e}")

            self._thread = threading.Thread(
                target=self._run_clock_loop,
                args=(gen, stop_evt),
                daemon=True,
            )
            self._thread.start()

    def continue_transport(self) -> None:
        """
        Resumes clock transmission and transmits MIDI Continue (0xFB).
        """
        with self._lock:
            if self._state == TransportState.RUNNING:
                return

            self._generation += 1
            gen = self._generation

            stop_evt = threading.Event()
            self._active_stop_event = stop_evt
            self._state = TransportState.RUNNING

            # Transmit 0xFB (Continue)
            try:
                self._send_cb(encode_realtime(MessageType.CONTINUE))
            except Exception as e:
                print(f"Error transmitting MIDI Continue: {e}")

            self._thread = threading.Thread(
                target=self._run_clock_loop,
                args=(gen, stop_evt),
                daemon=True,
            )
            self._thread.start()

    def stop(self) -> None:
        """
        Stops clock transmission, invalidates generation token, and sends MIDI Stop (0xFC).
        """
        old_thread = None
        with self._lock:
            if self._state == TransportState.STOPPED:
                return
            self._state = TransportState.STOPPED
            self._generation += 1
            if self._active_stop_event:
                self._active_stop_event.set()
            old_thread = self._thread

        if old_thread and old_thread.is_alive() and threading.current_thread() != old_thread:
            old_thread.join(timeout=0.3)

        # Transmit 0xFC (Stop)
        try:
            self._send_cb(encode_realtime(MessageType.STOP))
        except Exception as e:
            print(f"Error transmitting MIDI Stop: {e}")

    def emergency_stop(self) -> None:
        """Immediate silent halt for panic situations, invalidating generation and stopping thread."""
        old_thread = None
        with self._lock:
            self._state = TransportState.STOPPED
            self._generation += 1
            if self._active_stop_event:
                self._active_stop_event.set()
            old_thread = self._thread

        if old_thread and old_thread.is_alive() and threading.current_thread() != old_thread:
            old_thread.join(timeout=0.3)

    def _run_clock_loop(self, my_gen: int, stop_event: threading.Event) -> None:
        """
        Continuous monotonic tick scheduler with generation ownership validation.
        """
        if _timeBeginPeriod:
            try:
                _timeBeginPeriod(1)
            except Exception:
                pass

        clock_byte = encode_realtime(MessageType.CLOCK)

        try:
            with self._lock:
                current_bpm = self._bpm

            tick_interval = (60.0 / current_bpm) / 24.0
            t_target = time.perf_counter() + tick_interval

            while True:
                # 1. Generation & Stop check
                if stop_event.is_set() or self._generation != my_gen:
                    return

                # 2. Dynamic tempo changes
                with self._lock:
                    if self._generation != my_gen:
                        return
                    if self._bpm != current_bpm:
                        current_bpm = self._bpm
                        tick_interval = (60.0 / current_bpm) / 24.0

                # 3. Sleep until close to target
                t_now = time.perf_counter()
                delay = t_target - t_now
                if delay > 0.002:
                    time.sleep(delay - 0.001)

                # 4. Spin-wait remainder
                while time.perf_counter() < t_target:
                    if stop_event.is_set() or self._generation != my_gen:
                        return

                if stop_event.is_set() or self._generation != my_gen:
                    return

                # 5. Send clock tick
                t_sent = time.perf_counter()
                jitter = abs(t_sent - t_target) * 1000.0
                if jitter > self.jitter_max_ms:
                    self.jitter_max_ms = jitter

                try:
                    result = self._send_cb(clock_byte)
                    # Immediate post-send generation check
                    if self._generation != my_gen:
                        return

                    if result is False:
                        with self._lock:
                            if self._generation == my_gen:
                                self._state = TransportState.STOPPED
                                self._generation += 1
                                stop_event.set()
                        if self._error_cb:
                            self._error_cb("MIDI Clock destination port failed or disconnected.")
                        return

                    self.tick_count += 1
                    self.last_tick_time = t_sent
                except Exception as e:
                    print(f"Clock transmission error: {e}")
                    break

                # Advance target monotonically
                t_target += tick_interval

                # Overdue check
                t_after = time.perf_counter()
                if t_after - t_target > (tick_interval * 2.0):
                    t_target = t_after + tick_interval

        finally:
            if _timeEndPeriod:
                try:
                    _timeEndPeriod(1)
                except Exception:
                    pass
