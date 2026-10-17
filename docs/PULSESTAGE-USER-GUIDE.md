# PulseStage 1.1 desktop update

The dedicated desktop now bundles its renderer and does not start a localhost server. The current instructions below supersede older browser/loopback installation sections retained later for reference.

# PulseStage 1.1 — dedicated Windows desktop

PulseStage 1.1 bundles Python, its application packages and a Qt WebEngine renderer. Edge, Chrome, WebView2, Python and pip are not required as separately installed applications. The desktop shell loads packaged local assets through an internal resource scheme and calls the MIDI engine through Qt WebChannel IPC. It does not start Uvicorn, an HTTP server, a WebSocket server or an application TCP listening port. Users never enter a localhost address or IP.

The renderer is still web technology inside a native window. Bundling that engine makes the installer and installed footprint larger than the former browser-dependent build. Chromium renderer helper processes belong to PulseStage; they are not an installed browser. Standard Windows system libraries and supported graphics drivers remain operating-system prerequisites. Keep Qt/Chromium patched in future releases.

## Install and open

Install `PulseStage-Setup-1.1.0-x64.exe`, then use the PulseStage shortcut. Windows 10/11 x64 is the intended target; qualification is limited to the recorded test environment. The installer contains the UI engine and requires no renderer download. The build is unsigned unless accompanied by a verified signing record.

The title bar belongs to PulseStage. Closing the window shuts down the MIDI engine and releases owned notes/handles. Launching a second copy for the same user-data directory activates the existing window using a user-scoped Windows named pipe. There is no browser-process lifetime dependency or port-conflict selection. Help > User guide opens the offline guide inside the application.

Settings and actions remain under `%APPDATA%\PulseStage\config\user_config.json`. Renderer cache/state is under `%APPDATA%\PulseStage\renderer`; logs are under `logs`. Export opens a native Save dialog, initially in the `exports` folder. Installation/upgrade must preserve these user files. The desktop renderer's theme storage is separate from the old external browser's storage; choose the theme once in the new window. The dedicated desktop saves the theme through native Windows settings (HKCU/Software/PulseStage/PulseStage), avoiding browser local storage.

## Practice without hardware or extra drivers

Open Test bench and use Internal Practice Lab. Connect the keybed and reference receiver. No loopMIDI or MIDI-OX installation is needed for this mode. The paths are separate: keybed -> internal input monitor; command station -> internal reference receiver. Incoming notes are not automatically forwarded to the chosen output.

Run the guided note, preset, parameter and clock checks. They require received evidence in the active transport. A changing editor value alone is not a send: click Send command. The reference knobs display received settings. The metal footswitch sends a CC64 test message; its lamp and readout confirm received state. They do not process audio. The keybed has adjustable velocity; this is not a pressure-sensitive physical piano.

Switch to Windows loopMIDI mode only for independent OS-port inspection or inter-application testing. Create `PulseStage Keyboard` and `PulseStage Pedal Test` in separately installed/running loopMIDI, then connect. The mode switch stops engine activity, releases notes and clears input/output selections. Missing ports produce an error. Never describe internal practice as Windows-driver or physical-hardware qualification.


## Reference footswitch controls

The metal footswitch is a received-state display with a separate amber lamp and ON/OFF readout. Click the small metal button to toggle CC64 values 127 and 0 on the selected channel to the reference receiver only. The cap depresses after an ON message is received. OFFLINE means the receiver is disconnected. Real hardware may use another mapping; consult its manual.

## Physical equipment

Compatible USB-MIDI hardware uses Windows-exposed MIDI ports; some devices need their manufacturer's driver. DIN equipment needs a USB-MIDI interface/cables. Select the actual port, match channel and documented PC/CC/bank mapping, and enable external MIDI clock if supported. Direct hardware operation does not need loopMIDI or MIDI-OX. An ordinary audio instrument/cable/footswitch is not automatically a MIDI endpoint. Sound requires the instrument's own sound generator and audio path. Physical hardware was not verified in this desktop conversion.

## Development and build

Normal source launch: `python run_app.py` after installing the pinned build environment. Developer tools are not operator prerequisites. For reproducible packaging, install `requirements-build.lock`, run `python -m PyInstaller --clean --noconfirm pulsestage.spec`, then compile `installer.iss` with Inno Setup 6. Build files resolve the checkout directory instead of hard-coding a developer drive. Source-only HTTP development is explicitly separate: `python -m src.launcher.development_server`; it is not started by the desktop product.

`PulseStage.exe --self-check --report result.json` exercises the socket-free application transport with temporary configuration and simulated hardware. It checks internal RX note-on/off and received PC24, and shuts down. It is not a visual renderer, installer or physical-device test.

## Known limits

Actual physical instrument response, a clean Windows VM without any browsers installed, long-duration physical timing, broad accessibility/high-DPI coverage and every supported GPU remain separate qualification work. The architecture does not discover/launch installed browsers or expose a network-control server in desktop mode. The existing video predates this conversion and describes the old loopMIDI-based demo; follow this guide for the new internal default. Do not distribute that video as an exact 1.1 installation walkthrough without updating it.


---

# PulseStage — MIDI Studio Operator Guide

*Version 1.0.0 — Production Release Manual*

---

## 1. What PulseStage Does (And What It Does Not)

**PulseStage** is a precision Windows application engineered for stage musicians, keyboardists, guitarists, and studio engineers who need reliable, direct control over their MIDI equipment. It manages preset changes, continuous controllers, master tempo clocks, and custom performance sequences while offering real-time diagnostic monitoring.

### What PulseStage Is:
- **A MIDI Control Command Station**: Transmits Program Change (PC), Bank Select (MSB CC0 / LSB CC32), and Control Change (CC) messages to hardware synthesizers, digital guitar modelers, vocal processors, and outboard gear.
- **A Master MIDI Clock Source**: Generates stable 24-PPQN (pulses per quarter note) MIDI timing with Start, Continue, and Stop transport commands.
- **An Inspection and Diagnostic Monitor**: Captures, decodes, timestamps, and graphs every incoming and outgoing byte stream across all 16 MIDI channels.
- **A Macro Action Engine**: Executes custom multi-step preset and parameter chains with deterministic millisecond delays.
- **An Integrated Practice Lab**: Features an on-screen velocity-sensitive keybed and a reference receiving pedal for driver-free testing.

### What PulseStage Is NOT:
- **It is NOT a Digital Audio Workstation (DAW)**: PulseStage does not record, mix, or edit multi-track audio.
- **It is NOT an Audio Synthesizer or Sampler**: PulseStage processes digital control data (MIDI bytes), not sound waves. A successful transmission does not produce sound unless routed to an active hardware synthesizer or software instrument.
- **A Silent Test Is Valid**: Because MIDI is pure control information, successful parameter changes and preset selections are completely silent unless an external sound generator is connected.

---

## 2. Installation and First Launch

### 2.1 The Standalone Windows Setup Executable
PulseStage is distributed as a self-contained Windows setup executable:
`PulseStage-Setup-1.0.0-x64.exe`

- **Zero Prerequisites**: You do **not** need Python, `pip`, C++ compilers, or developer command-line tools installed. The entire runtime and dependencies are securely bundled.
- **Installation Path**: By default, PulseStage installs to your system Program Files directory (`C:\Program Files\PulseStage` or `%LOCALAPPDATA%\Programs\PulseStage`).
- **User Presets & Configuration Isolation**: To protect your personal settings during application updates, all user configurations, custom action chains, activity logs, and capture exports are stored in your Windows user profile:
  `%APPDATA%\PulseStage\`
  - `config\user_config.json`: Persistent user preferences and saved actions.
  - `logs\`: System activity logs.
  - `exports\`: Exported MIDI monitor CSV/JSON session files.
- **Clean Uninstallation**: The standard Windows "Installed Apps" / "Add or Remove Programs" uninstaller cleanly removes all application binaries and shortcuts while preserving your saved presets in AppData.

### 2.2 Launching the Application
Double-click the **PulseStage** icon on your Desktop or select it from your Start Menu.
PulseStage launches as a dedicated, frameless desktop application window powered by your system's hardware-accelerated engine. It automatically binds to a secure local loopback address (`127.0.0.1`) and never exposes control ports to your local network.

---

## 3. Non-Musician MIDI Primer

For non-musicians configuring PulseStage for a performer:

| Concept | What It Does | Real-World Analogy |
| :--- | :--- | :--- |
| **MIDI Note On / Off** | Triggers and releases a musical pitch with an associated velocity (volume/hardness). | Pressing and releasing a piano key. |
| **Program Change (PC)** | Switches the active sound patch, preset, or rig (values 0–127 or 1–128). | Selecting "Acoustic Grand" or "Overdrive Lead" on a keyboard or guitar pedal. |
| **Bank Select (CC0 / CC32)** | Expands presets beyond 128 by grouping patches into banks (MSB = coarse bank, LSB = fine bank). | Flipping to a new page or folder of presets before picking the patch number. |
| **Control Change (CC)** | Adjusts continuous parameters like volume, filter cutoff, delay mix, or toggles switches. | Turning a knob or pressing an expression/sustain pedal. |
| **MIDI Clock** | Synchronizes tempo across devices by sending 24 clock pulses per quarter note (PPQN). | A digital conductor's metronome keeping delay pedals and arpeggiators in lockstep. |
| **Transport** | Real-time Start, Continue, and Stop commands. | Pressing play or stop on a sequencer or drum machine. |

### Indexing Conventions: 0–127 vs. 1–128
MIDI wire protocol strictly uses 7-bit numbers from `0` to `127`. However, many musical instruments (such as Roland synthesizers and Line 6 pedalboards) label their presets starting at `1` up to `128`.
- In **0–127 mode**, preset 24 sends byte `0x18` (decimal 24).
- In **1–128 mode**, selecting preset 25 sends the identical wire byte `0x18` (decimal 24).
PulseStage allows you to toggle this display mode seamlessly in the Command Station without corrupting the transmitted wire bytes.

---

## 4. Hardware Discovery & Directionality

### 4.1 Connecting Physical Gear
1. Connect your class-compliant USB-MIDI keyboard, synthesizer, or guitar floorboard directly to a USB port on your PC. For traditional 5-pin DIN equipment, use a dedicated USB-MIDI interface (e.g., Roland UM-ONE, CME U6MIDI).
2. Allow Windows to finish recognizing the device driver.
3. In PulseStage's top connection bar, click **Refresh MIDI ports**.
4. Select your device from the **Input Source** or **Output Destination** dropdown.

### 4.2 Understanding Signal Direction (TX vs. RX)
- **Input Source (RX - Receive)**: Listens to incoming data from hardware controllers, keyboard pedals, or external sequencers.
- **Output Destination (TX - Transmit)**: Sends outgoing PC/CC commands and clock pulses to your sound modules or pedals.
- **No Automatic Thru**: PulseStage does **not** automatically echo incoming notes to the output destination. This prevents dangerous feedback loops on stage.

> **Important**: An ordinary 1/4" guitar cable or 3.5mm headphone jack carries analog audio, not MIDI data. Connecting an audio cable to your computer's sound card does not create a MIDI port.

---

## 5. Dual-Mode Practice Lab

PulseStage includes an integrated testing laboratory allowing you to practice and verify commands without needing physical instruments.

### Mode A: Driver-Free Internal Practice Lab (Default)
Out of the box, PulseStage operates in **Internal Practice Lab** mode.
- **Zero Drivers Required**: You do not need loopMIDI or virtual cable utilities.
- **Instant Two-Way Communication**:
  - The **Integrated Keybed** dispatches real MIDI notes directly into PulseStage's input monitor.
  - The **Command Station** dispatches Program Changes, CCs, and Clock directly to the on-screen **Reference Pedal**.
- Click **Practice Lab (Driver-Free)** in the connection strip to activate this mode at any time.

### Mode B: Windows loopMIDI Loopback (For External Software / MIDI-OX)
If you wish to test communication with third-party software (such as MIDI-OX, Reaper, Ableton Live, or external diagnostic bridges), click **Toggle Practice Mode** to switch to **loopMIDI Mode**.
1. Install and launch the free [loopMIDI utility](https://www.tobias-erichsen.de/software/loopmidi.html).
2. Create two ports with these exact names:
   - `PulseStage Keyboard`
   - `PulseStage Pedal Test`
3. Click **Connect Keybed** and **Connect Receiver** in the Control Room.

---

## 6. Console Tour & Operational Guide

### 6.1 Top Bar & Visual Console System
- **Theme Switcher**: Choose between **Dark Console** (initial high-contrast stage view) and **Light Console** (bright daylight studio view). Theme selection is persisted in local storage and never interrupts active MIDI data.
- **Port Selectors & Counters**: Displays active Input (RX) and Output (TX) packet counts in real time.
- **Emergency Stop All vs. Panic**:
  - **Stop All (Esc)**: Immediately halts active clock pulses, stops macro actions, and sends note-off commands for any currently held keys.
  - **Panic**: Transmits an all-notes-off emergency routine (CC123 All Notes Off, CC120 All Sound Off, and CC64 Sustain Off) across all 16 MIDI channels to eliminate stuck notes.

### 6.2 Command Station
- **Channel Selector**: Explicitly select MIDI channels 1 through 16.
- **Command Types**:
  - **Program Change**: Send instant patch changes with live hex byte preview (e.g., `C0 18`).
  - **Control Change**: Adjust parameters using the tactile rotary knob or numeric entry. The knob edits a value locally; click **Send Command** to explicitly transmit.
  - **Bank + Program**: Transmit CC0 (Bank MSB), CC32 (Bank LSB), followed immediately by the Program Change byte.

### 6.3 Master Clock & Transport
- **Tempo Adjustment**: Adjust BPM from 40.0 to 300.0 via slider, numeric entry, or the **Tap Tempo** button.
- **Transport Buttons**:
  - **Start**: Initiates 24-PPQN clock ticks preceded by a `0xFA` (Start) real-time byte.
  - **Continue**: Resumes clock transmission with `0xFB` (Continue).
  - **Stop**: Halts clock transmission with `0xFC` (Stop).

### 6.4 Integrated Keybed
- **Mouse & Keyboard Triggering**: Play notes with your mouse or computer keyboard (keys `A W S E D F T G Y H U J K O L P ;`).
- **Independent Channel & Velocity**: The keybed maintains its own velocity slider (1–127), channel selector, and octave shift buttons independent of the Command Station.
- **Watchdog Protection**: Notes are automatically released when switching octaves, un-focusing the browser window, or upon missed engine heartbeats.

### 6.5 Reference Pedal Display
- The on-screen pedal is a **pure diagnostic receiver**. Its knobs, switches, and 7-segment displays update **only** when matching MIDI bytes arrive on its port.
- **Read-Only Status**:
  - Program display (1–128)
  - Expression (CC11), Volume (CC7), Parameter A (CC12), Parameter B (CC13)
  - Footswitch indicator (CC64)
  - Measured received BPM calculated from real arrival intervals.

---

## 7. Event Monitor & Real-Time Diagnostics

Select **Event Monitor** from the sidebar to inspect complete session data:
- **Directional Inspection**: Every row clearly displays direction (`IN` / `OUT`), millisecond timestamp, port name, channel, message type, and raw hexadecimal bytes.
- **Channel Filters & Clock Suppression**: Filter by specific MIDI channels (1–16) and toggle raw clock visibility to prevent clock floods from obscuring preset commands.
- **Controller Activity Graph**: Plots the last 96 received CC values over time.
- **Clock Interval Graph**: Visualizes timing consistency (delta milliseconds between received ticks).
- **Session Export**: Export complete capture logs as structured JSON, CSV, or formatted diagnostic text.

---

## 8. Test Bench: Receiver-Verified Diagnostics

The Test Bench provides four automated diagnostic checks:
1. **Play a Note**: Verifies that Note On and matching Note Off packets traverse the keybed input route.
2. **Change a Preset**: Transmits program 24 and verifies arrival at the receiver.
3. **Move a Parameter**: Transmits CC11 / value 96 and verifies receiver receipt.
4. **Follow the Clock**: Verifies 96 consecutive clock ticks at 120 BPM within ±3 BPM tolerance.

> **Receipt-Driven Guarantee**: A test only turns green (PASS) when confirmed arrival bytes are parsed at the receiving port. A successful server send request alone is never marked as a test pass.

---

## 9. Performance Actions & Utilities

- **Action Macro Chains**: Build complex cues containing multiple Program Changes, Bank selects, CC parameters, and custom pauses.
- **Deterministic Delays**: Specify post-step delays in milliseconds to allow slow hardware synthesizers to load patches before receiving controller updates.
- **MIDI Utilities**:
  - **Pitch Bend**: 14-bit pitch wheel control with bipolar display (-8192 to +8191).
  - **Channel Pressure (Aftertouch)**: Monophonic pressure control (0–127).
  - **Raw / SysEx**: Direct transmission of manufacturer-specific System Exclusive strings.

---

## 10. Troubleshooting & FAQ

**Q: PulseStage says "Sent", but my synthesizer doesn't change sound.**
1. Check that the hardware is set to the same MIDI channel selected in PulseStage.
2. Verify that your USB-MIDI interface cable is connected properly (the interface's **MIDI OUT** must connect to the synth's **MIDI IN**).
3. Confirm whether your synthesizer requires Bank Select (CC0/CC32) before recognizing Program Changes.

**Q: Can I use PulseStage with MIDI-OX simultaneously?**
Yes. In Windows, traditional WinMM MIDI drivers allow only one application to open a physical hardware port at a time. To monitor PulseStage in MIDI-OX, use **loopMIDI mode** and select the loopback port as MIDI-OX's input.

**Q: Where are my saved presets located?**
All user data is stored in `%APPDATA%\PulseStage\config\user_config.json`. You can back up or migrate this file to another computer at any time.
