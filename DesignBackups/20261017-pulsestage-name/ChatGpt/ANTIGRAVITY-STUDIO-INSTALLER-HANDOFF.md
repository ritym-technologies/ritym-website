# Antigravity handoff prompt — RITYM PulseStage, integration, guide and Windows installer

Copy this complete prompt into Antigravity. Inspect the current repository rather than assuming a previous snapshot is unchanged.

---

Act as the senior Windows product engineer, MIDI systems engineer, release engineer, documentation author and professional music-software designer for `D:\Projects\MIDI`. Finish release engineering for **RITYM PulseStage — MIDI Studio**, preserving the new UI and verified MIDI paths. Update the operator guide and produce an actual professional Windows setup executable, not merely installer instructions or a batch file.

## Product intent and audience

The owner is a non-musician creating a MIDI application for a musician. The core is approachable Windows MIDI control and diagnostics: Program Change, Control Change, bank selection, MIDI Clock, input inspection and ordered performance actions. Future hardware integration is an extension point, not a fabricated foot-controller protocol.

The application handles control data. It does not currently record/process audio, synthesize instruments, edit audio waveforms or act as a complete DAW. An installed virtual MIDI port is not a physical USB device. Silent loopback tests are valid. Incoming monitoring does not imply MIDI thru/routing.

## What ChatGPT changed in this iteration

ChatGPT replaced the web interface with an original equipment-console design and added integrated instruments. Earlier audit work did not repair the main application source; this later UI/integration iteration does make source changes. Preserve Antigravity's existing codec, clock, device and action work, and check for concurrent changes before applying anything.

Files to inspect:

* `src/ui/index.html`: new app structure, sidebar navigation, connection strip, command station, recessed displays, master transport, receiver, keybed, monitor, test bench, utilities and action dialog.
* `src/ui/css/style.css`: complete Light Console and Dark Console visual systems, tactile rotary-control treatment, faders/buttons, LCDs, piano, responsive breakpoints, focus states and reduced-motion support. Uses local system fonts and code-native graphics; no Google Fonts/CDN dependency.
* `src/ui/js/app.js`: new UI controller, existing REST/WebSocket integration, persistent local theme choice, explicit-send command editing, actual MIDI-driven visualizations, bounded event display, input-only keyboard shortcuts, new guided tests and action CRUD.
* `src/api/studio.py`: new `StudioRack` and `PedalState`; owns a separate native adapter for test instruments, releases tracked notes, has a heartbeat watchdog and holds bounded receiver history.
* `src/api/server.py`: imports/registers the Studio routes and closes the rack in lifespan shutdown. Existing engine API paths remain available.
* `tests/test_studio.py`: eight new receiver/ownership tests.
* `docs/RITYM-STUDIO-USER-GUIDE.md`: current operator-guide draft.
* `ChatGpt/RITYM-STUDIO-VERIFICATION.md`, accompanying evidence and native smoke script: review commands, results and limits.

The separate `VirtualKeyboard` and `VirtualPedal` desktop tools remain in the repository. They were not replaced or embedded as Tkinter windows. The new web keybed/receiver operate through native Windows MIDI calls in the Python engine. Retain standalone tools as optional diagnostics rather than requiring several windows for the normal integrated workflow.

## Branding and design direction

Use **RITYM** as the parent mark, **PulseStage** as the product, and **MIDI Studio** as the descriptor. Correct the earlier spelling “PuleStage.” Branding is a design choice, not a claim of trademark clearance.

The visual intent is a professional lab console: graphite housing, legible neutral typography, restrained amber for transmission/control, sage receiver displays, precise spacing and tactile hardware-style controls. Light Console remains available; Dark Console is the initial choice. The theme button remembers the user's choice in localStorage for that app address. It must never affect MIDI state.

Avoid emoji navigation, neon gradient cards, oversized marketing claims, fake VU meters and decorative waveforms. The data views are **CC value history** and **received clock intervals**, not audio oscilloscopes. Empty graphs must stay empty/awaiting data. Preserve accessibility: focus outlines, meaningful control names, numeric entry/keyboard alternatives to dragging, reduced motion, readable text and status text in addition to color. Validate contrast and DPI scaling before release; the redesign is not a formal accessibility certification.

Research references that informed the direction: Ableton's Routing and I/O manual (`https://www.ableton.com/en/manual/routing-and-i-o/`) for explicit input/output roles; Native Instruments Kontakt Classic View documentation (`https://docs.native-instruments.com/ni-tech-manuals/kontakt-manual/en/classic-view`) for instrument rack and keyboard organization; Steinberg's Input and Output Monitor documentation for distinct directional diagnostics. The owner supplied `https://www.soundonsound.com/techniques/midi-recording-studio-one`; its full page returned403 to the review tools, so do not claim a complete reading or copy its content/assets. Indexed material and other primary references were available.

## Exact MIDI integration logic

loopMIDI must run with these exact dedicated cables:

    Web keybed MIDI OUT → “PulseStage Keyboard” → main PulseStage MIDI IN
    Command station MIDI OUT → “PulseStage Pedal Test” → reference receiver MIDI IN

`Connect keybed` opens only the dedicated keyboard output, then selects its matching input in the main engine. `Connect receiver` opens only the dedicated pedal input, then selects its matching command output. These are explicit user actions. Missing, ambiguous, busy or unavailable test ports cause an error; there is no first-device fallback.

Run native Windows mode, without `--virtual`. The in-process Virtual Adapter cannot be observed by MIDI-OX or another Windows application. In simulation mode the Studio rack explains that native mode is required instead of claiming a working driver loopback.

The web keybed sends note-on/off through the real WinMM driver. The main RX monitor receives them. Keyboard channel/velocity and octave are independent of Command station settings. Browser note requests are serialized; stale pending sends are invalidated on release/stop. Focus loss, channel/octave changes, page exit and Release notes request cleanup. The backend tracks channel/note ownership and releases abandoned held notes after a missed heartbeat. Latest cleanup sends only for channels with tracked notes, avoiding floods of cleanup traffic when nothing is held.

Reference pedal state is updated only inside its MIDI input callback, not from the composer's intended value or a successful Send response. It tracks PC, bank MSB/LSB, demonstration CC11/7/12/13/64, real-time transport and clock intervals. Its program display is1–128; wire values remain0–127. CC64 is a labelled test-switch mapping, not a universal pedal bypass definition. The receiver's footswitch/knobs are received-state indicators, not fake local effects controls.

Receiver events and interval history are bounded at96 each. The event table retains150 rows and controller graph96 points. A measured BPM is available only with enough recent received ticks. Clock estimates use host callback arrival times; they cannot certify physical-wire jitter. The existing clock engine still determines its actual Start/Continue/Stop behavior.

Studio endpoints under `/api/studio`:

* GET `/state`
* POST `/connect/keyboard`, `/connect/pedal`
* POST `/note` with note0–127, channel1–16, velocity1–127 and boolean on
* POST `/release`, `/heartbeat`
* POST `/pedal-channel` with0=omni or1–16 (backend capability; not presently exposed as a full UI selector)

## Test bench truthfulness

Four current guided tests require received evidence:

1. Keyboard: matching fresh Note On AND Note Off on `PulseStage Keyboard` in the main RX stream.
2. Preset: exact post-baseline PC24 bytes on the selected send channel at the reference receiver.
3. Parameter: exact post-baseline CC11/value96 on the selected send channel at the receiver.
4. Clock: Start plus at least96 received ticks and measured BPM within3 of120; the test then stops the clock. This is a short functional check, not a professional timing tolerance specification.

Old test cards could label a successful send as PASS and claim a pedal moved without observing the receiver. Do not reintroduce that behavior. The UI now distinguishes waiting, failed and receiver-verified. Physical equipment still requires its own feedback/observation.

Performance actions now expose create/edit/duplicate/delete, explicit destinations, step reorder/removal, bank fields, post-step delay and advertised engine message types. Running an action reports transmission separately from receiver verification. MIDI utilities retain pitch bend, channel pressure and raw/SysEx sending. The rotary CC control edits a value and requires explicit Send; it is not an automatic live-streaming knob in this revision. Escape maps to Stop all in the new UI; document that accurately instead of copying old shortcut tables.

## Verified results and unresolved release work

The isolated source copy passed **33 unit tests:25 existing plus8 new**. Native loopback smoke tests verified PC/bank/CC packets, a wrong-destination negative case, integrated keybed input, invalid-note rejection and received clock around120 BPM. Four guided UI tests reached receiver-verified state. A new action was saved through the UI using isolated preview configuration. Browser errors were checked, and desktop/narrow-window layouts were inspected. Evidence is supplied; do not replace it with a claimed59/59 score.

During live setup the newly created second loopMIDI port accepted sends but delivered no data. Restarting loopMIDI and reopening its input/output handles restored delivery. The smoke test initially failed with500 on a cached old output handle after this restart. The passing run deliberately reopens handles. **This reveals a remaining driver-restart/reconnect qualification requirement**, not permission to hide failures or to automatically replay rejected messages. Existing names may reappear while old handles are invalid. General hotplug, duplicate identities, origin/Host security, slow clients, native SysEx lifetime and long-duration timing still need current-source release review.

The redesign was tested with isolated preview configuration on18795, separately from the user's normal config. Do not distribute that preview's temporary QA actions, captures, internal paths or settings as user defaults. No actual physical pedal/instrument was qualified. No Windows installer has been produced by ChatGPT in this iteration.

## Required Windows installer delivery

Produce a versioned x64 Windows10/11 setup executable, for example `RITYM-PulseStage-Setup-<version>-x64.exe`. Choose and justify a practical toolchain such as PyInstaller onedir plus Inno Setup; actually build and smoke-test the resulting installer. A source ZIP, Python script or renamed batch file is not the deliverable.

1. Bundle the Python runtime and runtime dependencies. The musician should not need Python, pip, a compiler or developer tools. Bundle static HTML/CSS/JS and icons explicitly; verify frozen/resource paths. Keep a reproducible build spec and installer script in the repository, with pinned versions and license notices.
2. Provide a branded application window/launcher. If using WebView2, handle its runtime dependency deliberately and test its absence. If retaining Edge/Chrome app mode, document and check that dependency, provide a clear fallback, and do not claim it is an embedded WebView. Bind the local engine to loopback only; never expose it to the LAN by default. Support clean shutdown and avoid orphan servers. Handle occupied ports and single-instance launches without killing unrelated processes.
3. Install binaries read-only under a proper per-user Programs or Program Files location. Move writable settings, logs, captures and backups to appropriate AppData/user-data locations. The current development launcher writes config under the project tree; that must be corrected for an installed app. Version and migrate configuration safely; upgrades and default uninstall must preserve user presets/settings. Test future-version rejection and failed writes.
4. Supply consistent product/file versions, RITYM/PulseStage naming, a proper multi-size Windows icon, Start-menu shortcut, optional desktop shortcut and uninstall entry. Remove console windows from normal operation but retain an accessible diagnostics mode and readable errors. Do not label an unsigned binary as signed; sign only if a legitimate certificate is available and record signing status.
5. **loopMIDI is third-party proprietary freeware with a driver.** Verify redistribution and silent-install rights before bundling anything. Do not redistribute its driver/DLL or use private SDK components merely because they are installed on this computer. If bundling is not licensed, provide an honest optional first-run path to the official vendor installer and clear port-creation steps. Driver installation can need Windows administrator approval. Do not bypass security prompts. Normal physical MIDI operation must remain possible without the optional virtual lab driver.
6. MIDI-OX is an optional independent test utility, not an application runtime dependency. Keep it out of the required product installation unless redistribution is explicitly permitted and it serves an intentional optional workflow. Do not bundle its executable blindly.
7. Test a clean Windows environment with no Python/developer tools, fresh install, upgrade, uninstall/reinstall, standard-user operation, offline launch, missing driver/runtime, paths with spaces/non-ASCII names, occupied ports and high-DPI displays. Verify actual installed MIDI paths, both themes, theme persistence, exports, settings retention, keyboard focus cleanup and the guided negative cases. Keep build logs and installation-test evidence.
8. Place the real setup EXE and SHA256 checksum in a documented `dist` location, with release notes, supported environment and known limitations. If a signing certificate, vendor redistribution license, VM or external tool is unavailable, state the exact limitation. Do not claim installation validation that was not run.

## Required user-guide update

Start with `docs/RITYM-STUDIO-USER-GUIDE.md`, then update all conflicting README/beginner-guide/shortcut references. Ship a polished offline HTML guide in the installer, with Markdown source and optionally a shareable PDF. Use screenshots of the actual final Dark and Light themes, not concept art.

Cover installation and first launch; a non-musician MIDI primer; input versus output and RX/TX; silent data versus audio; native versus simulation mode; the two cable routes; creating/reconnecting ports; independent keyboard and composer channels; program-number conventions and bank order; clocks/transport and measurement limits; test mappings; action editing and delays; pitch/pressure/raw utilities; Stop all/Panic differences; exports; common failures; and MIDI-OX comparisons. Explain every visible switch/knob and its actual behavior. Do not describe proposed features as implemented, and do not promise universal pedal mappings or hardware responses.

Also include a short musician quick-start using a real compatible device, with documented device-channel/mapping examples that were actually checked. Keep developer build commands in a separate developer document rather than forcing them into normal operator flows.

## Deliver the handoff response

Save the release dossier in `D:\Projects\MIDI\Antigravity`: change list, final architecture/routing diagram, current concern matrix, reproducible tests/raw logs, dark/light screenshots, updated guide paths, build instructions/specs, actual setup EXE path/hash, signing status, installation-test matrix and unverified hardware items. Preserve the new visual identity and receipt-driven logic. Packaging must not turn uncertain behavior into marketing claims of stage readiness.

---
