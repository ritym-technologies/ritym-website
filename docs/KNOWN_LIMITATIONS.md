# PulseStage MIDI: Known Limitations and Compatibility

## 1. Operating System Real-Time Constraints

- **General-Purpose OS Scheduling:**
  Windows 10 and Windows 11 are general-purpose operating systems, not hard real-time operating systems (RTOS). While PulseStage utilizes Windows Multimedia high-resolution timers (`timeBeginPeriod(1)`) and cumulative drift compensation to maintain average timing accuracy within < 1 ms, unexpected DPC/ISR spikes (caused by faulty Wi-Fi or GPU drivers) may produce brief timing jitter.
- **Physical vs. Software Timestamps:**
  Software timestamps in the Diagnostic Monitor reflect the moment the packet was passed to the Windows kernel driver. Physical pin transitions on a 5-pin DIN cable occur at standard 31.25 kbaud (320 microseconds per byte).

---

## 2. Hardware and Protocol Limitations

- **Simplex (One-Way) Feedback Reality:**
  Standard MIDI connections to pedals (e.g., Strymon, Eventide, Boss) over 5-pin DIN or standard USB-MIDI Class 1.0 are unidirectional unless the pedal provides dedicated bidirectional USB communication. PulseStage **does not claim** that a pedal has changed preset or altered its parameter unless verified feedback is received.
- **Preset Numbering Offsets:**
  The MIDI specification enforces 0–127 for Program Change numbers. Certain manufacturers label presets 1–128. PulseStage provides a display selector (`0–127` vs `1–128`) to eliminate confusion, but users must verify the offset in their pedal's manual.
- **All Notes Off vs. Effects Bypass:**
  The Emergency Panic button transmits CC 123 (All Notes Off) and CC 120 (All Sound Off). While this silences synthesizers and samplers, effects pedals do not treat CC 123 as a bypass switch unless specifically configured in their custom CC mapping table.
- **SysEx and Proprietary Configurations:**
  Firmware updates and proprietary pedal configuration editors (e.g. Strymon Nixie, Line 6 HX Edit) require vendor-specific protocols. PulseStage does not attempt unverified firmware flashing on third-party hardware.
