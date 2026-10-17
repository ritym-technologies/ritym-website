# PulseStage release approach review

Reviewed 17 October 2026 against the supplied Antigravity release summary and current files under `D:\Projects\MIDI`.

## Verdict

The architecture is a good direction: bundle the application runtime, provide an internal practice transport, and retain optional Windows MIDI loopback plus direct physical-device operation. loopMIDI is not necessary for the internal lab or direct hardware MIDI. However, calling this a fully qualified, zero-prerequisite production release is premature. The package exists and works in headless internal-path checks, but there are functional integration defects and unresolved desktop/runtime qualification items.

No application source was changed during this review. Tests used an isolated source copy and the packaged executable used separate AppData. No physical MIDI messages were sent, no installer was installed/uninstalled, and no physical hardware or normal desktop-window lifecycle was tested. Portal/GitHub deployment was not independently verified.

## What I independently verified

- Setup exists: `dist/PulseStage-Setup-1.0.0-x64.exe`. Its SHA256 matches the supplied summary: `d1c89b90e2345d64e653fb386cea26785413beb1212d176d81c76ab329cd5d2d`.
- Windows reports the installer as NotSigned.
- PyInstaller's onedir bundle includes `python312.dll`, application packages and UI assets. A normal user should not need a separate Python/pip installation for that bundle.
- The packaged JavaScript has the same hash as the current source JavaScript, so the UI findings below are relevant to the supplied bundle too.
- Current source suite: **36 passed in 3.26 seconds** in an isolated copy with local socket access. An earlier sandbox attempt blocked the WebSocket connection; that environmental restriction was resolved before reporting the passing result. This is not a clean-Windows certification.
- Packaged `PulseStage.exe --headless` started with isolated AppData and an unused local port. The internal keyboard produced two RX messages for note60 on/off. Sending PC24 and CC11=96 to the internal receiver resulted in receiver program24 and expression96.
- The smoke process was deliberately terminated after the checks; that does not verify normal app-window shutdown or the claimed absence of orphan processes after closing a browser window.

## Findings requiring Antigravity follow-up

### High: practice-mode switch and guided tests are not fully wired

`src/ui/index.html` supplies `btn-toggle-lab-mode`; `src/ui/js/app.js` updates its label, but no click handler or request to `/api/studio/mode` exists in the current UI scripts. The backend mode endpoint exists, so a backend-only mode-switch unit test can pass while the user-facing switch does nothing.

The same JavaScript still hard-codes `PulseStage Keyboard` in `checkKeyboardTest`, and `PulseStage Pedal Test` in `prepareReceiver`. Internal endpoints now use `PulseStage Practice Keybed [Internal]` and `PulseStage Reference Pedal [Internal]`. As written, the normal internal receiver selection is rejected by those guided tests; the internal keyboard's messages do not meet the hard-coded keyboard-port condition. Route labels and some errors also still demand loopMIDI in internal mode.

Required fix: wire the mode button, reset/invalidate held notes and armed tests safely on mode changes, use the actual mode/port identity consistently, and test all four guided workflows through the real UI in both modes. Internal PASS must be labelled internal verification, not Windows-driver or hardware verification.

### High: input selection does not isolate internal keyboard delivery

In `src/engine/manager.py`, selecting the internal keyboard stores `rack.internal_input_cb`. Selecting a different physical input does not clear that callback. `StudioRack.note` continues invoking it.

Reproduced using a simulated hardware adapter: select internal keyboard, connect it, select `Example Hardware MIDI In`, then play/release the internal keyboard. Two messages still reach the old internal callback even though the selected input is the hardware input. The callback is associated with the previous internal source; this is unwanted mixed input, not proof that any real hardware sent data.

Required fix: explicitly disconnect the previous input dispatch subscription on selection/deselection/mode change, preserve note-release safety, and add regression tests for internal-to-physical and physical-to-internal transitions, unavailable replacement inputs and active notes. Keep sources accurately labelled if multiple inputs ever become an intentional feature.

### Medium: disconnected internal receiver still accepts messages

`DeviceManager.send_to_port` invokes `rack.pedal.receive` whenever the internal pedal name matches, without checking `pedal_id`/connection state. After a mode round trip, the rack reports `pedal_connected: false`, yet selecting the internal output and sending PC24 returns success and increments the receiver count. This was independently reproduced.

Either model the internal receiver as always available and make its status/UI consistent, or require its connection before accepting delivery. Do not report OFFLINE while silently updating its received state.

### Medium: the desktop UI still depends on an installed browser

`src/launcher/desktop_app.py` searches fixed Edge/Chrome locations, launches `--app=<local URL>`, and otherwise opens the default browser. The installer does not bundle an embedded browser engine or install/check WebView2. Python is bundled; the interface runtime is not self-contained.

This may be an acceptable supported-system requirement if documented, but it does not meet the stronger promise that all UI dependencies are handled. Choose an embedded shell/runtime with deliberate offline setup, or explicitly qualify supported installed browsers and provide clear startup failure guidance.

The launcher waits for the browser subprocess to exit before stopping the server. Existing browser sessions can delegate to another process, so subprocess exit need not equal app-window close. This is a source-level lifecycle risk requiring testing, not a behavior reproduced during this review.

### Medium: single-instance behavior is incomplete when the default port is occupied

The launcher checks for PulseStage only on the requested/default port. If another service owns8765 and PulseStage starts on8766, a second launch checks8765 again and can start another engine on8767. There is no actual Windows instance mutex or stored negotiated-port discovery in the inspected launcher. Verify and fix concurrent launch, fallback-port reuse and occupied-port behavior; do not call the current HTTP check a complete single-instance lock.

### Medium: reproducible builds and release claims need tightening

`requirements.txt` contains minimum versions (`>=`), not pinned dependency versions. The dossier's build command installs unpinned packages, and `pulsestage.spec`/`installer.iss` hard-code `D:\Projects\MIDI`. This does not establish reproducible builds from an arbitrary checkout. Keep a pinned build environment/lock and resolve paths from the build files or parameters.

The spec also copies the complete development `config` directory, including `test_user_config.json`, into the distributable. Ship deliberate clean defaults rather than development/user/test configuration files. Inspect all packaged docs/assets for obsolete development-only material.

A successful install/uninstall on this development computer, if accurately recorded, does not establish first launch on a clean Windows machine without existing browsers/runtime components. Verify upgrade/settings retention, offline operation, standard-user launch and final UI behavior there. The dossier's illustrative test names do not match the actual test names; preserve real runner logs rather than presenting a curated list as raw output. The independently rerun count is36.

### Additional source concern: local access checks remain too broad

HTTP/WebSocket checks in `src/api/server.py` use string-prefix origin matching (`startswith` with localhost/127.0.0.1 strings). That is not exact scheme/hostname/port validation, and no Host allowlist is apparent in this code. Review the local security boundary before broad distribution. This was a source inspection, not an external website attack test. Keep the engine on loopback and validate legitimate dynamically chosen ports without accepting arbitrary similarly prefixed origins.

## Do we need loopMIDI?

| Workflow | loopMIDI needed? | Explanation |
| --- | --- | --- |
| Built-in internal practice keyboard and receiver | No | Backend dispatch stays inside PulseStage. Packaged API smoke verified this path. The UI integration defects above still need fixing. |
| PulseStage directly controlling/monitoring USB-MIDI hardware | No | Native WinMM communicates with the MIDI ports exposed by Windows and the device driver. |
| Older DIN MIDI equipment through a USB-MIDI interface | No | The interface/driver supplies the real Windows MIDI port. |
| Inspecting another application's software MIDI stream with MIDI-OX or a DAW | Often useful | A virtual port connects separate Windows applications. loopMIDI is one option; it is an optional diagnostic/routing component. |

loopMIDI's own documentation describes it as a virtual cable between applications, with ports available only while its application is running. Internal practice endpoints do not become Windows MIDI devices and cannot be selected independently by MIDI-OX. Reference: https://www.tobias-erichsen.de/software/loopmidi.html

Do not remove loopMIDI from this development computer simply because it is optional; it remains useful for independent testing. Do not bundle its driver without verifying applicable vendor redistribution terms. This review makes no legal conclusion about a specific redistribution agreement.

## External hardware dependencies, in plain language

1. **MIDI-capable equipment and the correct connection.** USB-MIDI uses a data-capable USB cable. DIN MIDI equipment needs a USB-MIDI interface and appropriate MIDI cables, with OUT connected to IN. TRS MIDI equipment needs its manufacturer's correct adapter type. An ordinary audio-only instrument or footswitch does not automatically provide MIDI.
2. **A working Windows device driver.** Class-compliant USB-MIDI equipment can use Windows' supplied class driver; other equipment may need the manufacturer's driver. Follow the device vendor's supported Windows/version instructions. PulseStage cannot include every manufacturer's driver or make an unsupported device compatible. Microsoft references: https://learn.microsoft.com/en-us/windows-hardware/drivers/audio/usb-audio-class-system-driver--usbaudio-sys- and https://learn.microsoft.com/en-us/windows-hardware/drivers/audio/usb-2-0-audio-drivers
3. **Correct device settings.** Select the actual hardware input/output in PulseStage, match the MIDI channel, confirm documented PC/CC/bank mappings, and enable external MIDI clock on a device that supports it. Port detection alone does not prove command response.
4. **An audio path if sound is expected.** PulseStage sends control messages. The hardware synthesizer/effects unit and its speakers/headphones/audio path produce the sound. An audio interface/ASIO driver, DAW or VST is not inherently required just to send MIDI controls.

The integrated keybed remains a source for the monitor/test path; the current app does not automatically forward incoming notes to the selected hardware output. Do not assume choosing a synth as output turns the test keybed into a general routed hardware piano. That would require an explicitly implemented, safe note-routing feature.

## Recommended acceptance decision

Accept the internal-practice/native-hardware separation and Python packaging approach. Do not approve the full production-complete claim yet. Ask Antigravity to fix the concrete UI/routing findings, resolve/document the browser dependency, supply real clean-machine/desktop lifecycle evidence, rebuild the installer, and publish its new version/hash after fixes. Qualify one actual target musician device before relying on it at a performance. No loopMIDI dependency should be imposed on normal internal practice or direct physical MIDI operation.
