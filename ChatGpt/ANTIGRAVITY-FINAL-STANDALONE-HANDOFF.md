# Antigravity implementation prompt — PulseStage standalone Windows release

Owner requirements and development handoff, 17 October 2026.

Copy this entire document into Antigravity. This consolidates the latest owner decisions; where older handoffs differ, follow this document. Inspect the current repository before changing anything. Historical test evidence is not proof that the current checkout or installed build passes.

---

Act as the senior Windows desktop engineer, MIDI systems engineer, product designer, release engineer and technical writer for **PulseStage**, located at `D:\Projects\MIDI`.

Complete the working development application as a professionally installed, approachable Windows product. Implement the remaining work, update the user guide, build a real Windows setup executable and test the installed product. Do not stop at a plan, mockup, source ZIP, batch file or packaging instructions.

## 1. The owner's intent — read this first

The owner is not a musician or developer and is building this for a musician, Vimal. They need explanations and workflows that do not assume prior MIDI knowledge. They expected a standalone Windows application, not a website requiring them to install Python, packages, a browser and multiple test programs manually.

The intended experience is:

1. Download and run `PulseStage-Setup-<version>-x64.exe`.
2. Open **PulseStage** from the Start menu or shortcut.
3. Use one dedicated desktop window containing the MIDI controls, virtual keyboard, reference pedal, monitor and guided tests.
4. Try the basic integrated practice/test lab without developer tools, terminal commands or opening several applications.
5. Connect compatible real MIDI equipment when available, select the correct MIDI port/channel and verify its actual response.

Use **PulseStage** as the product name everywhere. An optional descriptor is **MIDI Studio**. There is no parent brand. Align window titles, UI, icons, executable metadata, installer, shortcuts, guide, screenshots and demo filenames with that name. Historical backups are for traceability; do not ship them or reinstate their superseded branding.

PulseStage is currently a MIDI control and diagnostics application, not an audio DAW, synthesizer or effects processor. MIDI messages carry instructions; they do not contain instrument audio. Do not add fake waveforms or claim that changing a reference-pedal setting changes audible sound. A silent MIDI test can pass.

## 2. What is already implemented, and who changed it

Preserve the existing Antigravity engine work and unrelated changes. ChatGPT's later iteration replaced the web UI and added integrated native-MIDI test instruments. The separate reference-pedal desktop application was existing Antigravity work; do not credit the entire engine or that earlier pedal implementation to ChatGPT.

Review these actual files:

- `src/ui/index.html`: sidebar views, connection strip, command station, equipment-style displays, reference pedal, master transport, integrated keyboard, event monitor, test bench, performance actions and MIDI utilities.
- `src/ui/css/style.css`: professional Dark Console and alternate Light Console, system fonts/local assets, restrained amber/sage indicators, physical-style knobs, buttons and keyboard, responsive layout and focus treatments.
- `src/ui/js/app.js`: REST/WebSocket integration, theme persistence, explicit-send commands, received-data visualizations, keyboard ownership/cleanup, receipt-based guided tests, bounded monitor and action editing.
- `src/api/studio.py`: new `StudioRack` and `PedalState`, separate native adapter for test instruments, actual input callback updates, tracked notes, heartbeat watchdog and bounded receiver histories.
- `src/api/server.py`: Studio route registration and rack shutdown alongside the existing engine.
- `tests/test_studio.py`: eight instrument/receiver tests.
- `VirtualKeyboard/`: earlier standalone Python/Tk keyboard created during this work; includes native MIDI backend and tests. It is an optional diagnostic utility, not the required normal UI.
- `VirtualPedal/`: existing separate reference receiver; the normal integrated workflow must not require opening it.
- `docs/PULSESTAGE-USER-GUIDE.md`: updated explanation of routing, read-only indicators, physical ports and current dependencies.
- `docs/PULSESTAGE-STUDIO-VERIFICATION.md` and its copy in `ChatGpt/`: recorded implementation and test evidence, including limitations.
- `docs/ANTIGRAVITY-STUDIO-INSTALLER-HANDOFF.md`: earlier detailed technical handoff, subordinate to the latest standalone-install requirements here.
- `ChatGpt/studio-evidence-2026-10-17/`: native smoke script/results and previous UI evidence. Inspect files to locate the exact artifacts rather than inventing filenames or results.
- `ChatGpt/Demo/`: current narrated demo, source captures, captions, transcript, written steps and verification record.

ChatGPT also installed MIDI-OX and loopMIDI on the development computer and created the dedicated virtual test ports. Their presence on this machine does not mean the final installer includes them. Source backups are under `DesignBackups/`. The normal development server address is `http://127.0.0.1:8765`; the earlier isolated preview used port 18795 and should not be assumed to be running.

The latest naming changes removed the former parent brand from active UI, docs and demo. The theme storage key is now `pulsestage-theme`; static assets were revisioned to avoid stale cached UI. No MIDI backend redesign was performed as part of that naming change.

## 3. Preserve the exact current MIDI behavior

The currently verified native virtual-port configuration is:

    Integrated keybed OUT -> PulseStage Keyboard -> main engine IN -> RX monitor
    Command station OUT -> PulseStage Pedal Test -> reference receiver IN

The owner asked, “Input is keyboard and output is pedal test?” For this specific demo, yes. Explain this directly in the guide and onboarding. These are two separate paths. There is **no automatic MIDI thru** forwarding keyboard input to the selected command output.

`Connect keybed` opens the dedicated keyboard output and selects its matching main-engine input. `Connect receiver` opens the dedicated pedal input and selects its matching command output. These explicit actions may change the displayed port selections. Missing, busy or ambiguous ports must produce understandable errors, not fallback to the first available device.

Keyboard channel, velocity and octave belong to the keyboard. Composer settings do not transform received keyboard notes. Key presses/releases send Note On/Off, and the main monitor must show actual RX evidence. Preserve serialized note requests, stale-request invalidation and release on focus loss/channel or octave changes/page exit. Preserve the backend note-ownership watchdog. Idle cleanup must not flood all channels with unnecessary messages.

The command knob/numeric field edits a value. **Send command** transmits it. Do not imply the current editor continuously sends while turning the knob. A successful transmission response means the driver accepted a send; it does not prove the target acted on it.

The reference pedal's displays change from received MIDI, not optimistic updates from the editor:

| Display | Current demonstration mapping |
| --- | --- |
| Expression | CC 11 |
| Volume | CC 7 |
| Parameter A | CC 12 |
| Parameter B | CC 13 |
| Metal footswitch indicator | CC 64: >=64 on, <64 off; demo uses 127 and 0 |
| Program | MIDI PC 0–127, shown as preset 1–128 |
| Bank | CC 0 MSB and CC 32 LSB |
| Transport / tempo | Received Start/Continue/Stop and clock ticks |

The four receiver knobs and screw-like metal footswitch are **read-only received-state indicators** in the present UI. The owner mistook them for broken interactive controls. Add clear, professional visible wording such as “Received settings” and “Footswitch indicator · CC64 test mapping,” plus useful tooltips/accessibility labels. Do not solve this by making indicators animate without receiving messages. A real device may assign completely different meanings to these controller numbers; CC64 is not a universal effects bypass.

Program wire value 24 displays as preset 025 on this receiver. Preserve the distinction between numbering labels and wire values, including bank selection ordering. Master clock uses 24 timing ticks per quarter note. Measured receiver BPM requires enough recent ticks and returns to dashes when stale. Callback arrival timing is not a physical-wire jitter certification.

Keep monitor/chart histories bounded. The existing receiver histories are 96 entries, table display 150 rows, and CC history 96 points. Charts represent controller values and received clock intervals, not audio waveforms.

Current Studio API under `/api/studio`: GET `/state`; POST `/connect/keyboard`, `/connect/pedal`, `/note`, `/release`, `/heartbeat`, `/pedal-channel`. Read the current models for validation and semantics before extending them. Native Studio mode currently requires Windows without `--virtual`. The existing in-process simulation is not an OS MIDI port and cannot be observed by MIDI-OX.

## 4. Make installation genuinely standalone

The current source application still needs Python, the packages in `requirements.txt` (FastAPI, Uvicorn, WebSockets, Pydantic and transitive dependencies), and a browser for its interface. `run_app.py` tries Edge/Chrome app mode and falls back to the default browser. It is not an embedded desktop shell or a completed setup package. Do not confuse “integrated UI” with “dependencies bundled.”

For the release:

1. Bundle the Python runtime and every application runtime package. The musician must not install Python, run pip, configure PATH or use a terminal. Pin build dependencies and keep reproducible build/installer scripts and license notices.
2. Ship a dedicated application window. Prefer a practical desktop shell containing the existing interface, with its web runtime included or automatically handled by setup. A web technology implementation is acceptable; relying on the user to install/open Chrome is not the intended experience. If WebView2 or another runtime is selected, test its absence and handle offline installation deliberately. Do not describe a dependency as eliminated merely because it is usually present on developer PCs.
3. Bundle local UI assets, icons and an offline guide; verify frozen executable/resource paths. Avoid remote fonts/CDNs or login requirements for normal operation.
4. Keep the engine bound to loopback. Validate local API/WebSocket access boundaries. Implement clean startup/shutdown, single-instance behavior, occupied-port handling and useful diagnostics without terminating unrelated processes or leaving orphan servers.
5. Install binaries in an appropriate Windows application location. Store settings, actions, logs and captures under appropriate user-data/AppData locations, not the source directory or protected installation folder. Preserve settings through upgrades and normal uninstall/reinstall; define deliberate data removal separately. Check migration, permission errors and unsupported configuration versions.
6. Produce a versioned x64 Windows setup EXE with Start-menu shortcut, optional desktop shortcut, uninstall entry, consistent version metadata and multi-size icon. A toolchain such as PyInstaller plus Inno Setup is reasonable if it fits the inspected source. Verify code signing honestly; do not claim unsigned files are signed.

### Integrated test lab and external drivers

The owner wants the keyboard and pedal experience included in PulseStage, rather than a collection of separate applications. The current lab widgets are integrated, but their native virtual-port path depends on loopMIDI installed and running with both named ports.

Make the basic integrated practice lab work immediately after installing PulseStage, without manual Python, browser or virtual-port setup. Choose a technically sound implementation:

- Prefer an explicitly labelled **internal practice/test transport** for the default no-hardware lab if a separately installed virtual driver would otherwise be necessary. The receiver must still consume actual dispatched messages through that transport; do not update it from the composer's intended values. Test the real dispatch/receive path, not a shared visual variable.
- Retain an optional **Windows MIDI loopback** mode using loopMIDI for independent OS-port and MIDI-OX verification. It has different evidentiary value from an internal test. Show the active mode and prerequisites clearly. Do not rename internal messages as native-driver verification or invent Windows input devices.
- Alternatively, if a native virtual driver is included, establish lawful redistribution/install rights and package/test it correctly. Do not copy proprietary loopMIDI driver files merely because they exist on this computer. Driver setup may require Windows elevation. If rights or offline deployment cannot be resolved, keep that mode optional and explain the limitation.

This internal-lab change is required to meet the owner's out-of-box expectation, not a claim that it is already implemented. Preserve the proven external routing behavior and make any mode transition explicit. Avoid accidental feedback, automatic destination changes and replaying failed/stale commands.

MIDI-OX is an optional independent inspector, not an application dependency. Physical MIDI operation must not require loopMIDI. Manufacturer drivers for particular hardware are separate from bundling PulseStage's own dependencies; it is not realistic to promise every instrument driver inside one installer.

## 5. Physical instruments: truthful discovery and guidance

Support and document compatible Windows-exposed MIDI ports. A powered USB-MIDI instrument, or a MIDI interface for DIN-connected equipment, should appear after Windows recognizes its driver and the application refreshes enumeration. Confirm current hotplug behavior in source and tests. Let the user explicitly select input/output and channel. Do not silently switch a live session to a newly connected device.

An audio-only guitar/microphone or an ordinary sustain pedal connected by an audio-style cable is not a standalone USB-MIDI endpoint. Some controllers expose input only; some hardware needs a manufacturer driver. Recognition does not prove correct channel, mapping, clock mode or response.

Verify hardware only when the actual device is available. Record make/model, driver, connection type, channel, documented mapping, exact messages and observed response. Otherwise label hardware compatibility and hotplug checks unverified and provide a practical test checklist. Never claim physical certification from the virtual demo.

## 6. Professional UI and beginner-friendly user guide

Retain the equipment-console aesthetic and Dark Console default, with Light Console available. Refine rather than gratuitously replace working controls. Use readable professional typography, restrained color, clear labels, realistic tactile controls and precise spacing. Preserve keyboard access, numeric alternatives to knobs, meaningful focus and status text, reduced-motion behavior and sensible scaling.

Update `docs/PULSESTAGE-USER-GUIDE.md` and ship a polished offline HTML version with actual final screenshots. Separate musician/operator instructions from developer build instructions. Explain:

- What MIDI does, and why a silent test can work.
- First launch after installation and any optional driver setup.
- Internal practice mode versus Windows loopback versus physical equipment.
- Input/output, RX/TX and the absence of automatic MIDI thru.
- Every knob, switch, display and button, including read-only receiver indicators.
- Keyboard channels/velocity, press/release and stuck-note recovery.
- CC, program numbering, bank selection, tempo/clock and external-clock requirements.
- Performance actions, destinations and step delays; utilities and documented SysEx use.
- Stop all versus Panic, verified against the actual implementation. In the new UI Escape maps to Stop all; do not copy obsolete shortcut labels.
- Monitor filters/pause/export, missing ports, busy ports, reconnect, missing driver/runtime and how to get useful diagnostics.
- The optional MIDI-OX workflow, including safe input-only inspection initially to avoid feedback.

The current demo is `ChatGpt/Demo/PulseStage-Guided-Demo.mp4`, about 5:11 in Full HD. The same folder contains `Watch-Demo.html`, SRT/VTT captions, `NARRATION-TRANSCRIPT.md`, `DEMO-GUIDE.md`, `VERIFICATION.json` and source materials. A shareable bundle is `ChatGpt/PulseStage-Demo.zip`.

It opens with the challenge, explains the solution, demonstrates connections/keyboard/monitor/CC/footswitch/presets/clock, then explains hardware and dependencies. The voice is a calm American male synthetic preset at slower speed. Visuals are actual application still captures with before/after edits and explanatory graphics, not a continuous screen recording or human voice recording. Preserve a natural conversational style and unhurried explanations; do not misrepresent provenance. The existing video says packaging is unfinished and loopMIDI is currently needed, so update those sections and recapture final UI if your implementation changes them. Ship a demo that matches the installed release.

## 7. Evidence available — do not inflate it

Recorded earlier verification:

- Existing 25 tests passed in an isolated source/config copy; with eight new Studio tests the suite passed 33 tests. After the final idle-cleanup adjustment, the eight instrument tests were rerun successfully; JavaScript syntax checks passed.
- Native smoke checked PC/bank/CC ordering and exact bytes, wrong-output negative behavior, keybed Note On/Off, invalid note 128 rejection and a short received clock sample near 120 BPM.
- Four guided UI tests reached receiver-verified state. Temporary action editing was exercised only in isolated preview configuration.
- Dark/light themes, persistence and sampled desktop/narrow layouts were inspected. This was not comprehensive accessibility/high-DPI certification.
- Latest demo capture verified received CC11 20 then 100, CC64 on/off, PC24 displayed as 025, received clock near 120 BPM followed by Stop, and RX note60 on/off. Video/audio full decode and saved-file hash comparison passed.

No actual physical instrument/pedal was qualified. No clean-machine installer was built/tested in this work. Short host-arrival clock measurements do not establish long-duration stage timing. Rerun appropriate checks against your final source and installed package; report the real counts and evidence.

## 8. Remaining concerns to resolve or explicitly report

An actual observed failure: a new second loopMIDI port accepted sends without delivering data until loopMIDI and handles were restarted. A cached output handle then failed with HTTP 500; explicitly deselecting/reopening it restored operation. Refreshing names alone is not proof of valid handles. Qualify driver restart, disconnect/reconnect and recovery without replaying stale commands.

Review the previously flagged areas against current source rather than assuming defects are fixed: port identity/duplicates and enumeration changes, connection/handle synchronization, native SysEx buffer lifetime, local API origin/Host/WebSocket boundaries, slow-client behavior, shutdown cleanup and long-duration clock behavior. Keep a concern matrix distinguishing fixed-and-tested, implemented-but-unverified, deferred and blocked.

Never display PASS solely because an HTTP send succeeded. Existing guided checks require matching fresh received events. Internal transport tests and native loopback tests must remain clearly distinct. Add meaningful regression tests for the packaging/transport changes and real failure cases; avoid tests that only mirror the implementation.

## 9. Completion and deliverables

Run relevant regression, negative and installed-app tests. Validate on clean supported Windows without Python/developer tools: fresh install, offline first launch, basic internal keyboard/receiver lab, optional native-loopback setup, standard-user launch, upgrade, uninstall/reinstall, settings retention, runtime/driver absence, occupied ports, paths with spaces/non-ASCII characters and high-DPI layouts. Verify both themes, note cleanup, source/destination isolation, exports and failure messages. Add real hardware tests if available; otherwise disclose that specific gap.

Put the actual setup EXE and checksum under a documented `dist/` path. Put the release dossier in `D:\Projects\MIDI\Antigravity` with:

1. Changes made, architecture and routing diagrams, and dependency table separating bundled components from optional external drivers/tools.
2. Updated concern matrix and test results/raw logs, separating unit, internal transport, Windows loopback, installer and physical-hardware evidence.
3. Actual final dark/light screenshots, updated offline user guide and matching demo paths.
4. Reproducible build specification, installer script, pinned dependencies, third-party notices and driver redistribution decisions.
5. Actual setup EXE path, version, SHA256, signing status, installation results and known limitations.

If a release tool, redistribution right, certificate, clean Windows test environment or hardware is unavailable, complete independent work and state exactly what remains unverified or blocked. Do not substitute claims for missing evidence. Do not call the task complete until the installer exists and its real verification status is reported.

The musician-facing goal is one understandable installed application. Preserve reliable MIDI behavior and honest diagnostics while removing developer setup from the user's experience.
