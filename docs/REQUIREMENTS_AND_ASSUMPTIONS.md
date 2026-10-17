# PulseStage MIDI: Requirements Summary and Assumptions

**Application Name:** PulseStage MIDI  
**Target Platform:** Windows 10/11 (with modular architecture for macOS and Android expansion)  
**Target Audience:** Touring musicians, guitarists/bassists using MIDI-controlled pedals, synthesists, and live audio engineers.

---

## 1. Confirmed Requirements vs. Proposals

| Requirement / Proposal | Status | Engineering Decision & Rationale |
| :--- | :--- | :--- |
| **Windows Application** | **Confirmed** | Primary target. Implemented using native Windows Multimedia WinMM API (`winmm.dll`) for universal compatibility without requiring SDK or compiler installations. |
| **Simpler than MIDI-OX** | **Confirmed** | Modern stage-ready UX; plain-language parameter naming; clear 5-step quick send workflow; no cryptic hex tables required for everyday tasks. |
| **Program Change (PC)** | **Confirmed** | Strict range checking (0–127). Transparent display toggle for 0-indexed (0–127) vs 1-indexed (1–128) naming. |
| **Control Change (CC)** | **Confirmed** | Continuous slider and direct numeric input (0–127). Friendly parameter names from verified device profiles. Rate-limited continuous transmission to prevent buffer overruns. |
| **Bank Select** | **Confirmed** | Explicit configuration of CC 0 (MSB) and CC 32 (LSB) followed by Program Change with customizable inter-message pacing delay. |
| **MIDI Clock Generation** | **Confirmed** | 24 pulses per quarter note (PPQN). Dedicated high-priority thread using high-resolution monotonic timer with zero cumulative drift. Distinct Start, Continue, and Stop transport controls. |
| **MIDI Monitor & Diagnostics** | **Confirmed** | Real-time traffic inspection with plain-language interpretation, raw hex bytes, directional indicators (TX/RX), smart clock tick collapsing, pause display, clear, and bounded export. |
| **Multi-Command Actions** | **Confirmed** | Saved macro presets (e.g. "Solo Boost") sending ordered PC/CC sequences to explicit destinations with safety cancellation. |
| **Emergency Safeguards** | **Confirmed** | Panic button sending safe CC 123 (All Notes Off), CC 120 (All Sound Off), and CC 64 (Sustain Off). Immediate Emergency Transmission Halt. |
| **Hardware Controller Protocol** | *Proposed / Prepared* | Formal architecture and specification defined for future hardware companion; no fake non-functional UI controls. |
| **Input-to-Output Routing** | *Proposed / Post-v1* | Evaluated and deferred to Milestone 3 to ensure strict feedback loop detection safeguards before live stage deployment. |
| **macOS & Android Expansion** | *Proposed / Post-v1* | Core models, codec, and protocol engine decoupled from OS platform adapters, enabling CoreMIDI and Android MIDI adapters in future milestones. |
| **Firmware Update Utility** | *Proposed / Milestone 3* | Reserved for dedicated hardware integration once hardware handshake, framing, and recovery protocols are verified. |

---

## 2. Explicit Assumptions

1. **Hardware & Driver Environment:**
   - Standard 5-pin DIN and USB-MIDI 1.0 connections are exposed by Windows through the Windows Multimedia subsystem (`winmm.dll`).
   - USB is treated strictly as a transport layer. Proprietary pedal protocols are not assumed without vendor documentation.
2. **Device State Feedback:**
   - Standard MIDI transmission is unidirectional (simplex). Unless a device provides verified bidirectional feedback (e.g., via SysEx Identity or dual-port loopback), the software will explicitly mark messages as **Transmitted (Unverified Device State)** to avoid false confidence on stage.
3. **Preset Numbering Transparency:**
   - The MIDI wire format specifies `0x00` through `0x7F` (0–127).
   - Some pedals (e.g. Strymon, Boss, Line 6) label patches 1–128 or Bank 01A–32D. PulseStage displays both the friendly user index and the exact wire byte.
4. **Desktop Operating System Clock Timing:**
   - Windows is a non-real-time general-purpose OS. Jitter is minimized through multimedia timer resolution (`timeBeginPeriod(1)`) and cumulative drift compensation ($t_N = t_0 + N \cdot \Delta t$).
   - Touring musicians are clearly informed that receiving devices must be configured in their own internal menus to follow external MIDI Clock.
5. **Connection Persistence:**
   - The application remembers device names, not transient OS indices. If an unplugged device is missing on launch, PulseStage highlights the port as **Disconnected** rather than silently routing commands to an unintended instrument.
