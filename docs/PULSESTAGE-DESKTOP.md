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

## Physical equipment

### Reference footswitch

The reference pedal has a metal footswitch illustration with a separate amber lamp and OFF/ON readout. This is received MIDI status, not an editable setting. Click the small metal button to toggle CC64 values 127 and 0 to the reference receiver on the selected channel. The cap depresses and the lamp lights after the receiver reports an ON value. An OFFLINE readout means the reference receiver is disconnected. The test button refuses to send to another selected output. Real devices may map CC64 differently; follow their MIDI implementation charts.

Compatible USB-MIDI hardware uses Windows-exposed MIDI ports; some devices need their manufacturer's driver. DIN equipment needs a USB-MIDI interface/cables. Select the actual port, match channel and documented PC/CC/bank mapping, and enable external MIDI clock if supported. Direct hardware operation does not need loopMIDI or MIDI-OX. An ordinary audio instrument/cable/footswitch is not automatically a MIDI endpoint. Sound requires the instrument's own sound generator and audio path. Physical hardware was not verified in this desktop conversion.

## Development and build

Normal source launch: `python run_app.py` after installing the pinned build environment. Developer tools are not operator prerequisites. For reproducible packaging, install `requirements-build.lock`, run `python -m PyInstaller --clean --noconfirm pulsestage.spec`, then compile `installer.iss` with Inno Setup 6. Build files resolve the checkout directory instead of hard-coding a developer drive. Source-only HTTP development is explicitly separate: `python -m src.launcher.development_server`; it is not started by the desktop product.

`PulseStage.exe --self-check --report result.json` exercises the socket-free application transport with temporary configuration and simulated hardware. It checks internal RX note-on/off and received PC24, and shuts down. It is not a visual renderer, installer or physical-device test.

## Known limits

Actual physical instrument response, a clean Windows VM without any browsers installed, long-duration physical timing, broad accessibility/high-DPI coverage and every supported GPU remain separate qualification work. The architecture does not discover/launch installed browsers or expose a network-control server in desktop mode. The existing video predates this conversion and describes the old loopMIDI-based demo; follow this guide for the new internal default. Do not distribute that video as an exact 1.1 installation walkthrough without updating it.
