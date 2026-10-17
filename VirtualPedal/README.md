# PulseStage Stomp — Virtual Multi-Effects Pedal & Tempo Receiver

**PulseStage Stomp** is a boutique virtual guitar multi-effects processor and MIDI receiver for Windows. It provides a visual, real-world receiver for testing PulseStage MIDI output, validating Program Change, Bank Select, Parameter Control Change (CC), and 24 PPQN Realtime Clock.

---

## 1. Quick Start

1. Double-click `Start Pedal.bat` (or run `python pedal.py`).
2. The pedal will launch and automatically create or connect to the Windows MIDI port:
   `PulseStage Pedal Test`
3. In **PulseStage MIDI**:
   - Click **Refresh** in Device Connections.
   - Select **Output Destination**: `PulseStage Pedal Test`.
4. Now, any commands sent from PulseStage will immediately affect the pedal!

---

## 2. Signal Routing Architecture

```
                     ┌───────────────────────┐
                     │    PulseStage MIDI    │
                     │  (Command Composer)   │
                     └──────────┬────────────┘
                                │ Transmit (TX)
                                ▼
                     ┌───────────────────────┐
                     │ PulseStage Pedal Test │ (teVirtualMIDI / loopMIDI)
                     └──────────┬────────────┘
                                │ Receive (RX)
                                ▼
                     ┌───────────────────────┐
                     │   PulseStage Stomp    │
                     │    Virtual Pedal      │
                     └───────────────────────┘
```

> **Crucial Rule:**
> All animations, preset numbers, knob rotations, and tempo flashes on this pedal are driven **strictly by received MIDI wire bytes**.
> If PulseStage sends to a different port or wrong channel, the pedal will **not** animate. This prevents false positives and ensures actual end-to-end delivery.

---

## 3. Features & Test Mappings

### A. Preset Display (LED / LCD)
- **Program Change (PC):** Sending PC `24` displays `PRESET 025` (in 1–128 mode) or `PRESET 024` (in 0–127 mode) along with raw hex `C0 18`.
- **Bank Select:** Sending Bank MSB (CC 0) and Bank LSB (CC 32) displays the current bank in sequence.
- **Toggle Display Convention:** Click the **1-128 / 0-127** button to switch between musician preset numbering and zero-indexed engineering numbering.

### B. Interactive Parameter Knobs (Test Mappings)
- **Expression / Delay Time:** Controlled by **CC 11** (Values 0–127).
- **Master Volume / Level:** Controlled by **CC 7** (Values 0–127).
- **Param / Feedback:** Controlled by **CC 12** (Values 0–127).
- **Tone / Filter Cutoff:** Controlled by **CC 13** (Values 0–127).
*(Note: These are designated test mappings for demonstration purposes; individual hardware pedals define their own CC mappings in their user manuals).*

### C. Stompbox Footswitch (Bypass / Engaged)
- Controlled by **CC 64** (Sustain) or **CC 102** (Stompbox Switch).
- Values >= 64 engage the pedal (green LED). Values < 64 switch to bypass (dim amber LED).

### D. Tempo & Beat Receiver (24 PPQN Realtime Clock)
- **Beat Light (LED):** Pulses in synchronization with every quarter-note beat (every 24 clock ticks of `0xF8`).
- **Measured BPM:** Calculates instantaneous BPM in real-time using a sliding window of clock tick timestamps.
- **Transport State:** Detects Realtime Start (`0xFA`), Continue (`0xFB`), and Stop (`0xFC`).
- **Telemetry Disclaimer:** Timings are measured via Windows driver callback arrivals. Software measurements demonstrate signal delivery and do not certify sub-millisecond physical wire hardware jitter.

### E. Wire Telemetry & Diagnostic Inspector
- Shows full timestamp, delta timing (ms), channel, message type, and raw hexadecimal bytes.
- Highlights unaddressed channel messages (e.g. if the pedal is configured for Channel 1 and an event arrives on Channel 2).

---

## 4. Running Regression Tests

To verify the parser, channel filtering, and native driver loopback:

```cmd
python test_pedal.py
```
