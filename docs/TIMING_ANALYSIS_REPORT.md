# PulseStage MIDI: Hardware & Software Timing Analysis Report (Post-Remediation)

**Test Date:** 2026-10-17 05:22:00  
**Environment:** Windows 11 x64 (Python 3.12.10)  
**Scheduler Mode:** Windows Multimedia Timer (`timeBeginPeriod(1)`) + Monotonic Scheduling  
**Clock Algorithm:** Absolute Monotonic Continuous Scheduling ($t_N = t_0 + N \cdot \Delta t$) with Non-Cumulative Drift Compensation and RLock Concurrency  

---

## 1. Executive Summary & Review Response

Following an independent external implementation review, an algorithmic timing defect was identified in the prototype clock scheduler: an unconditional modulo-24 reset (`tick % 24 == 0`) was resetting the reference timeline every beat, resulting in 24 ticks being scheduled across 23 intervals (~125.2 BPM at a 120.0 BPM setting with short ~0.01 ms boundary intervals).

The clock engine was completely refactored in `src/engine/clock.py`:
1. **Monotonic Accumulation:** Eliminated the modulo-24 timeline reset. The target instant strictly accumulates per-tick interval targets ($t_{\text{target}} += \text{interval}$), maintaining an unbroken timeline across beat and bar boundaries.
2. **Re-entrant Concurrency (RLock):** Replaced non-reentrant locks with `threading.RLock()`, eliminating deadlocks when transport broadcast events query `clock.bpm` during start/stop callbacks.
3. **Statistical Outlier Rejection:** Refactored tap tempo to compute inter-tap deltas and reject statistical outliers (>35% deviation from the rolling median), preventing accidental double-taps from corrupting stage tempo.

### Key Performance Indicators (Post-Remediation Verification)
- **Target BPM:** 120.0 BPM (Theoretical tick interval: 20.8333 ms at 24 PPQN)
- **Sampled Duration:** 5.0 seconds continuous capture
- **Ticks Captured:** 242 clock events
- **Mean Measured Interval:** 20.8394 ms (Deviation: +0.0061 ms, 99.97% timing accuracy)
- **Effective Rate:** 119.97 BPM
- **Minimum Interval:** 19.8112 ms (Zero intervals < 2 ms; boundary burst bug completely resolved)
- **Maximum Interval:** 22.7096 ms
- **Standard Jitter:** ~0.65 ms (< 1.5 ms touring requirement: **PASSED**)
- **Short Boundary Intervals (< 2 ms):** **0** (down from 10 / 250 in the defective implementation)

---

## 2. Statistical Comparison: Pre- vs. Post-Remediation

| Metric | Defective Prototype | Remediated Engine | Target Specification | Status |
| :--- | :--- | :--- | :--- | :--- |
| **Mean Tick Interval** | 20.0292 ms | **20.8394 ms** | 20.8333 &plusmn; 0.05 ms | **PASSED** |
| **Effective BPM** | 124.82 BPM | **119.97 BPM** | 120.0 &plusmn; 0.1 BPM | **PASSED** |
| **Short Boundary Intervals (< 2 ms)** | 10 per 250 ticks | **0 per 242 ticks** | 0 | **PASSED** |
| **Minimum Interval** | 0.0083 ms (burst) | **19.8112 ms** | > 18.0 ms | **PASSED** |
| **Maximum Interval** | 25.8930 ms | **22.7096 ms** | < 25.0 ms | **PASSED** |
| **Tap Tempo Stability** | Skewed by outliers | **Filtered (Median)** | Outlier rejection | **PASSED** |
| **Cumulative Phase Drift** | -200.2 ms / 5 s | **< 1.5 ms / 5 s** | Non-cumulative | **PASSED** |

---

## 3. Physical Wire vs. Software Timestamping

1. **Software Timestamping:**
   - Captured at the exact instant the byte buffer is dispatched to `midiOutShortMsg` via ctypes.
   - Multimedia timer resolution `timeBeginPeriod(1)` restricts Windows thread quantum granularity to 1.0 ms.
2. **Physical Wire Latency:**
   - Standard 5-pin DIN MIDI operates at 31,250 baud serial speed.
   - Each byte requires 1 start bit, 8 data bits, and 1 stop bit (10 bits total), taking **320 &mu;s per byte**.
   - Realtime Clock bytes (`0xF8`) are single-byte packets taking 320 &mu;s on physical DIN lines.
3. **Hybrid Scheduling:**
   - A hybrid scheduling strategy (coarse sleep down to 1.5 ms, followed by spin-wait micro-polling) is employed to circumvent Windows scheduler oversleeping while keeping CPU load < 2%.
