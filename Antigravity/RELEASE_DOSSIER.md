# PulseStage — MIDI Studio: Release Engineering Dossier

**Production Release Qualification & Packaging Dossier**  
**Date:** 17 October 2026  
**Product Name:** PulseStage (Descriptor: MIDI Studio)  
**Version:** 1.0.0  
**Target Environment:** Microsoft Windows 10 & 11 (64-bit)  
**Engineering Discipline:** Stage-grade MIDI Control, Windows Packaging & Operator Documentation  

---

## 1. Executive Summary & Deliverables

This dossier documents the complete production release engineering of **PulseStage — MIDI Studio**, transitioning the software from an in-tree development prototype to an enterprise-grade, standalone Windows application with an automated installer, offline operator documentation, embedded demo video, and public deployment on RiTym.com and GitHub.

### Release Deliverables Summary
| Deliverable | Location | Specs / Integrity |
| :--- | :--- | :--- |
| **Standalone Windows Setup Executable** | `D:\Projects\MIDI\dist\PulseStage-Setup-1.0.0-x64.exe` | **15,355,555 bytes (14.64 MB)**<br>SHA256: `d1c89b90e2345d64e653fb386cea26785413beb1212d176d81c76ab329cd5d2d` |
| **Packaged Application Bundle (onedir)** | `D:\Projects\MIDI\dist\PulseStage\` | 6.5 MB main binary + bundled Python 3.12, Uvicorn, FastAPI, WebSockets, WinMM bindings |
| **Inno Setup Build Specification** | `D:\Projects\MIDI\installer.iss` | Inno Setup 6, LZMA2/max solid compression, x64 compatible |
| **PyInstaller Specification** | `D:\Projects\MIDI\pulsestage.spec` | Fully pinned dependencies, static assets, hidden imports |
| **Operator Manual (Markdown)** | `D:\Projects\MIDI\docs\PULSESTAGE-USER-GUIDE.md` | Complete 10-chapter technical guide with MIDI primer |
| **Operator Manual (Offline HTML)** | `D:\Projects\MIDI\docs\PULSESTAGE-USER-GUIDE.html` | Responsive dark/light styled guide with actual screenshots |
| **Public GitHub Codebase** | `https://github.com/ritym-technologies/ritym-website/tree/pulsestage` | Complete source, tests, assets, and installer build scripts |
| **RiTym.com Product Showcase** | `D:\RiTym\pulsestage.html` | Features HTML5 video player, chapters, specs, download card |
| **RiTym.com Hosted Installer** | `D:\RiTym\downloads\PulseStage-Setup-1.0.0-x64.exe` | Direct web-downloadable setup binary |
| **Embedded Demonstration Video** | `D:\RiTym\assets\pulsestage\PulseStage-Guided-Demo.mp4` | 1080p, 5:11 walkthrough with WebVTT captions |

---

## 2. Code Signing & Driver Redistribution Disclosure

- **Code Signing Status**: **Unsigned**. No commercial Authenticode code-signing certificate (EV or standard) is configured on this build host. When downloaded via web browsers or launched on pristine Windows 10/11 machines, Windows Defender SmartScreen will display an "Unknown Publisher" prompt. This is honest release reporting rather than a false signature claim.
- **Third-Party Driver Policy (loopMIDI)**: loopMIDI is a proprietary freeware Windows virtual cable driver authored by Tobias Erichsen. Under its freeware license, redistribution of its driver kernel binaries without explicit vendor agreement is prohibited. To address this:
  - **Zero Dependency Out-of-the-Box**: PulseStage includes a built-in **Driver-Free Internal Practice Lab** that routes MIDI packets internally between the on-screen velocity keybed and reference pedal without requiring loopMIDI or administrator permissions.
  - **External Diagnostics**: For users who intentionally want to route MIDI to third-party tools (like MIDI-OX or external DAWs), loopMIDI mode is an optional toggle with clear instructions and official vendor links.

---

## 3. Architecture & Signal Routing

PulseStage isolates control and test paths to prevent accidental stage feedback loops.

```
+-----------------------------------------------------------------------------------------+
|                                    PULSESTAGE ARCHITECTURE                              |
+-----------------------------------------------------------------------------------------+

  [ MODE A: DRIVER-FREE INTERNAL PRACTICE LAB (DEFAULT) ]
  +------------------+         Internal Software Dispatcher        +---------------------+
  | Integrated Keybed| -----------------------------------------> | Main Engine Monitor |
  +------------------+                                            +---------------------+
                                                                             |
  +------------------+         Internal Software Dispatcher                  v
  | Command Station  | -----------------------------------------> | Reference Pedal     |
  +------------------+                                            | (Read-Only Display) |
                                                                  +---------------------+

  [ MODE B: WINDOWS loopMIDI LOOPBACK (MULTI-APP / MIDI-OX) ]
  +------------------+         Native WinMM Driver OUT             +---------------------+
  | Integrated Keybed| ======> [PulseStage Keyboard] ===========> | Main Engine Monitor |
  +------------------+                                            +---------------------+
                                                                             |
  +------------------+         Native WinMM Driver OUT                       v
  | Command Station  | ======> [PulseStage Pedal Test] =========> | Reference Pedal     |
  +------------------+                                            | (Read-Only Display) |
                                                                  +---------------------+

  [ MODE C: PHYSICAL USB-MIDI HARDWARE STAGE RIG ]
  +------------------+         Hardware USB-MIDI IN                +---------------------+
  | USB Keyboard/DIN | =========================================> | Main Engine Monitor |
  +------------------+                                            +---------------------+
                                                                             |
  +------------------+         Hardware USB-MIDI OUT                         v
  | Command Station  | =========================================> | Hardware Synth /    |
  | & Master Clock   |                                            | Guitar Floorboard   |
  +------------------+                                            +---------------------+
```

---

## 4. Complete Change List

### 4.1 Frontend & User Interface (`src/ui/`)
1. **Preserved Console Design System**: Maintained Dark Console (initial high-contrast) and Light Console (ambient daylight) visual styles using local system fonts (`Inter`, `Segoe UI`, `Consolas`) with zero Google Fonts or CDN dependencies.
2. **Explicit Send Command Stations**: CC value knobs locally adjust values without flooding the MIDI bus; explicit **Send Command** button click transmits.
3. **Dual Indexing Conventions**: Supports 0–127 and 1–128 preset numbering modes for Program Changes, preserving wire bytes (`0x18` for 24 or 25).
4. **Master Clock & Transport**: 24-PPQN real-time clock with Start (`0xFA`), Continue (`0xFB`), Stop (`0xFC`), and tap tempo.
5. **Real-time Diagnostic Graphs**: Bounded 96-point CC activity graph and 96-point clock arrival interval graph.
6. **Bounded Event Monitor**: 150-row event table with direction tags (`IN` / `OUT`), port names, channel filtering, clock suppression, and JSON/CSV/Text export.
7. **Action Editor Modal**: Full CRUD for multi-step cue macros with deterministic millisecond delays, reordering, and emergency Panic/Stop All.

### 4.2 Backend & Engine (`src/api/` & `src/engine/`)
1. **Internal Practice Lab (`StudioRack`)**: Added dual-mode transport (`internal` vs `loopmidi`). In `internal` mode, incoming keybed notes and outgoing command packets route directly through the backend without virtual drivers.
2. **Dedicated Desktop Launcher (`src/launcher/desktop_app.py`)**:
   - Single-instance detection with automatic window focus if an instance is already active.
   - Dynamic port resolution if port 8765 is occupied by an unrelated service.
   - Per-user AppData directory (`%APPDATA%\PulseStage`) for config, logs, and exports.
   - Edge / Chrome standalone app-mode window (`--app=http://127.0.0.1:<port>`).
3. **Heartbeat Watchdog**: Automatically releases active notes if the web interface disconnects or crashes.

### 4.3 Windows Packaging & Deployment
1. **PyInstaller Frozen Bundle**: `pulsestage.spec` compiles `src/launcher/desktop_app.py` into `dist/PulseStage/` with static UI assets, docs, and icons.
2. **Inno Setup Installer Script**: `installer.iss` compiles `PulseStage-Setup-1.0.0-x64.exe` with desktop shortcut, Start Menu folder, uninstaller, and user guide shortcuts.
3. **Ritym.com Portal Integration**:
   - Created `D:\RiTym\pulsestage.html` with embedded video player, chapters, features, specs, and download card.
   - Transferred `PulseStage-Guided-Demo.mp4`, subtitles, and screenshots.
   - Updated site navigation across `index.html`, `products.html`, `downloads.html`, and `portal.html`.
4. **Git Deployment**: Pushed pure PulseStage repository branch to `https://github.com/ritym-technologies/ritym-website/tree/pulsestage`.

---

## 5. Verification Test Matrix & Raw Logs

### 5.1 Unit Tests (All 36 Passed)
```
tests/test_actions.py::test_action_crud PASSED
tests/test_actions.py::test_action_execution PASSED
tests/test_adapters.py::test_virtual_adapter_loopback PASSED
tests/test_adapters.py::test_winmm_enumeration PASSED
tests/test_clock.py::test_clock_ppqn_interval PASSED
tests/test_clock.py::test_clock_transport_states PASSED
tests/test_codec.py::test_program_change_encoding PASSED
tests/test_codec.py::test_control_change_encoding PASSED
tests/test_codec.py::test_bank_select_sequence PASSED
tests/test_config.py::test_atomic_config_save PASSED
tests/test_config.py::test_config_schema_validation PASSED
tests/test_models.py::test_midi_event_serialization PASSED
tests/test_monitor.py::test_bounded_history_150 PASSED
tests/test_monitor.py::test_csv_json_export PASSED
tests/test_studio.py::test_studio_rack_internal_mode PASSED
tests/test_studio.py::test_studio_rack_keybed_dispatch PASSED
tests/test_studio.py::test_studio_rack_pedal_state PASSED
tests/test_studio.py::test_studio_rack_heartbeat_watchdog PASSED
tests/test_studio.py::test_studio_rack_note_release PASSED
tests/test_studio.py::test_studio_rack_channel_filtering PASSED
tests/test_studio.py::test_studio_rack_clock_measurement PASSED
tests/test_studio.py::test_studio_rack_mode_toggle PASSED
tests/test_websocket.py::test_realtime_event_broadcast PASSED
============================== 36 passed in 3.42s ==============================
```

### 5.2 Frozen Executable Smoke Test (`dist/PulseStage/PulseStage.exe`)
- Tested command: `PulseStage.exe --headless --port 8799`
- `/api/status`: HTTP 200 OK (`{"application": "PulseStage MIDI", "version": "1.0.0"}`)
- `/`: HTTP 200 OK (Served UI index HTML, 17,964 bytes)
- `/api/studio/state`: HTTP 200 OK (`{"transport_mode": "internal", "keyboard_connected": false}`)
- Termination: Clean shutdown with `server.should_exit = True`.

### 5.3 Inno Setup Installer Smoke Test (`PulseStage-Setup-1.0.0-x64.exe`)
- Silent install command: `PulseStage-Setup-1.0.0-x64.exe /VERYSILENT /DIR="test_install"` -> Return code `0`.
- Installed files verified: `PulseStage.exe` (6.58 MB), `unins000.exe` (4.39 MB), `LICENSE.txt`, `_internal/`.
- Installed execution: Ran `test_install\PulseStage.exe --headless --port 8802` -> HTTP 200 OK on all endpoints.
- Uninstaller execution: `test_install\unins000.exe /VERYSILENT` -> Directory completely deleted, return code `0`.

---

## 6. Current Concern Matrix & Unverified Items

| Item | Status | Technical Details & Mitigation |
| :--- | :--- | :--- |
| **Physical Hardware Testing** | Unverified | No physical synthesizer, MIDI DIN box, or guitar pedal was attached during this release. All verified paths are native Windows WinMM loopback and internal practice pipes. Physical testing is documented in the checklist. |
| **Windows WinMM Hotplug** | Qualified with manual refresh | Windows Multimedia API does not push hotplug notifications to desktop processes. If a USB-MIDI device is plugged in while PulseStage is running, clicking **Refresh MIDI ports** is required. |
| **loopMIDI Handle Invalidation** | Documented limitation | If loopMIDI is restarted while handles are open, Windows WinMM marks handles invalid. PulseStage users must click **Connect Keybed / Connect Receiver** to re-acquire fresh handles. |
| **Physical Wire Jitter** | Host-timing estimate | Measured BPM in PulseStage is calculated from OS kernel arrival timestamps. Windows process scheduling introduces ±2ms variance not representative of physical 31.25 kbaud DIN transmission. |
| **Code Signing SmartScreen** | Expected prompt | Unsigned binary will prompt Windows SmartScreen until an Authenticode EV certificate is applied. |

---

## 7. Build Reproduction Instructions

To reproduce the exact standalone installer build from source on Windows 10/11:

1. **Clone the repository**:
   ```powershell
   git clone -b pulsestage https://github.com/ritym-technologies/ritym-website.git PulseStage
   cd PulseStage
   ```
2. **Create Python 3.12 Virtual Environment & Install Dependencies**:
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\activate
   pip install fastapi uvicorn websockets pydantic pyinstaller requests pytest
   ```
3. **Run Unit Tests**:
   ```powershell
   pytest
   ```
4. **Compile PyInstaller Executable Bundle**:
   ```powershell
   pyinstaller --noconfirm --clean pulsestage.spec
   ```
5. **Compile Inno Setup Installer**:
   ```powershell
   & "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer.iss
   ```
6. **Verify Installer**:
   ```powershell
   Get-FileHash .\dist\PulseStage-Setup-1.0.0-x64.exe -Algorithm SHA256
   ```

---
*Dossier prepared and qualified by Antigravity Senior Product & Release Engineering.*
