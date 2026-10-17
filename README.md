# PulseStage — MIDI Studio

Windows 10/11 x64 · Dedicated desktop · Internal practice lab

**PulseStage** is a precision Windows application engineered for stage musicians, keyboardists, guitarists, and studio engineers who need reliable, direct control over their MIDI equipment. It manages preset changes, continuous controllers, master tempo clocks, and custom performance sequences while offering real-time diagnostic monitoring and driver-free practice.

---

## Key Features

1. **Precision Command Station**
   - Transmit Program Change (PC) with live byte preview (`0x18` etc.).
   - Support for both 0–127 and 1–128 indexing conventions without corrupting wire data.
   - Bank Select: CC0 (MSB) + CC32 (LSB) followed by Program Change.
   - Tactile rotary and numeric Control Change (CC 0–127) editing with explicit transmission.

2. **Master MIDI Clock & Transport**
   - 24-PPQN (pulses per quarter note) MIDI timing engine.
   - Real-time Start (`0xFA`), Continue (`0xFB`), and Stop (`0xFC`) transport commands.
   - Tap tempo and fractional BPM control (40.0 – 300.0 BPM).

3. **Diagnostic Event Monitor & Data Graphs**
   - Live bidirectional packet inspection (IN / OUT), timestamps, channels, and hex representations.
   - Real-time CC value activity graph (last 96 events).
   - Clock arrival interval graph visualizing jitter and tempo stability.
   - Export monitor history to CSV, JSON, and formatted diagnostic text.

4. **Dual-Mode Practice Lab**
   - **Internal Practice Lab (Driver-Free)**: Works out of the box with zero third-party drivers or loopback cables.
   - **Integrated Velocity Keybed**: Mouse and keyboard control (A–;) with octave shift and auto-release watchdog.
   - **Reference Pedal Display**: Read-only diagnostic receiver displaying program, CC11 (Expression), CC7 (Volume), CC12/13, CC64 (Footswitch), and measured BPM.
   - **loopMIDI Compatibility Mode**: Toggle to Windows loopMIDI mode for external routing and MIDI-OX diagnostics.

5. **Receiver-Verified Test Bench**
   - Four automated diagnostic tests: Keybed Note On/Off, Preset Change, CC Parameter Control, and 120 BPM Clock tracking.
   - Tests only PASS when matching arrival bytes are confirmed at the receiver.

6. **Macro Actions & MIDI Utilities**
   - Build multi-step preset and parameter chains with ordered steps and requested millisecond delays.
   - 14-bit bipolar Pitch Bend (-8192 to +8191), Channel Pressure (Aftertouch), and raw SysEx tools.

---

## Quick Start & Installation

### Windows Setup Executable
Download the standalone installer:
- **Installer**: `PulseStage-Setup-1.1.0-x64.exe`
- **Integrity**: See the matching `.sha256` file supplied beside the installer.
- **Requirements**: Windows 10 or 11 (64-bit). The installer bundles Python, application packages and Qt WebEngine. No separate browser, localhost server, Python, loopMIDI or MIDI-OX installation is required for internal practice. External devices may need their manufacturer’s driver.

User presets and configuration are safely stored in `%APPDATA%\PulseStage\config\user_config.json`.

---

## Documentation

Comprehensive operator guidance is included:
- **[Operator Guide (Markdown)](docs/PULSESTAGE-USER-GUIDE.md)**
- **[Operator Guide (Offline HTML)](docs/PULSESTAGE-USER-GUIDE.html)**

---

## License

See LICENSE.txt and docs/THIRD-PARTY-NOTICES.txt.

See [Desktop architecture and qualification limits](docs/PULSESTAGE-DESKTOP.md). Physical device response and clean-machine qualification are distinct from internal simulation.
