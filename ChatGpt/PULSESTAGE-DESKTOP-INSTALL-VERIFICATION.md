# PulseStage 1.1.0 — desktop installation verification

17 October 2026 · Windows x64 · Local verification, not a physical hardware certification.

## Delivered result

PulseStage now opens in a dedicated Windows application window. Python, application packages, Qt WebEngine, the keyboard, reference receiver and local UI assets are included in the installer. Normal operation does not launch Edge/Chrome, require a browser installation, or start a localhost HTTP/WebSocket server. The UI communicates with the MIDI engine through native IPC.

Installer: `D:\Projects\MIDI\dist\PulseStage-Setup-1.1.0-x64.exe` (132,182,528 bytes).

SHA256: `6d97b126af70f70ac956257b688fe6c8ce70aab0f4ed9b325e1dc5a6c6cf7248`.

Installed location: `%LOCALAPPDATA%\Programs\PulseStage`. Open the PulseStage Start Menu shortcut. No terminal or script is needed by the operator. Source scripts remain developer tools in the repository.

## Verified evidence

- 41 automated engine/API tests passed.
- Packaged executable self-check passed using its bundled runtime.
- Packaged and installed renderer/IPC checks passed against the full dark UI.
- Installed check ran with PATH limited to Windows System32 and without PYTHONHOME/PYTHONPATH.
- Keybed note 60 on/off produced two received MIDI events.
- Reference receiver captured program 24 and expression CC11 value 96.
- Footswitch CC64 press/release values 127/0 were received.
- Receiver captured 120 clock ticks in approximately 2.5 seconds and measured 120 BPM; clock stopped afterward.
- Actual mouse interaction with the packaged keyboard produced Note On/Off. Actual clicks on the compact footswitch produced `B0 40 7F` and `B0 40 00`, changing its received ON/OFF readout.
- Setup installed successfully. The official uninstaller removed the application EXE, bundled Python, bundled Qt renderer, the entire install directory and uninstall registry entry. Reinstall succeeded with version 1.1.0 registered.
- Launching a second copy of the source, packaged executable and installed app exited successfully while the primary completed its renderer check. A Windows process lock prevents duplicate engines; the named pipe activates the primary window.
- The uninstall bootstrapper can exit before temporary cleanup finishes. The final verification waits for the entire install directory to disappear before reinstalling. The uninstall log confirms “Removed all? Yes.”
- loopMIDI, its owned virtual MIDI driver packages and MIDI-OX were removed using their official uninstallers. No matching installed-app entries remained. No Windows restart was requested by those uninstallers.
- The loopMIDI uninstaller left a stopped `teVirtualMIDI64` system driver and `oem80.inf` package. After verifying the original INF and Tobias Erichsen publisher, Windows PnPUtil uninstalled and deleted that owned package. The driver service, package and `teVirtualMIDI64.sys` were then absent.

See `install-cycle-report.json`, renderer check JSON and the associated installation/removal logs in this folder. Settings and user presets are preserved; unrelated system Python, browsers and other applications are outside the uninstall scope.

## Code and integration changes

`native_desktop.py` owns the desktop window, packaged resource scheme, Qt WebChannel bridge, native export dialogs, offline Help guide, QLockFile process lock and user-scoped activation named pipe. Windows allows more than one named-pipe server with the same name; listen() alone did not prevent duplicate application instances. The process lock fixes that verified defect. `desktop_engine.py` runs the existing routes directly inside an engine thread through ASGI calls. There is no desktop-mode network control listener.

The existing source HTTP development server is retained as an explicit development entry point. It is not started by the installed desktop application.

Internal practice is the default and needs neither loopMIDI nor MIDI-OX. Keybed -> input monitor and command station -> reference receiver are separate paths. There is no automatic MIDI thru and no audio synthesis.

Fixed mode switching, mode-specific test port names, cleanup of internal input subscriptions when selecting another input, offline receiver transmission checks and router state being shared accidentally across app instances. Shutdown stops clock/actions and releases owned input/output handles. Existing user actions/configuration are preserved.

Browser localStorage access for the theme caused severe slowdowns in the embedded custom-scheme renderer. Full-UI checks passed after moving desktop theme persistence to native Windows settings. Desktop mode must not reintroduce localStorage calls. Web development mode retains its independent browser preference. Qt/PySide is pinned to 6.8.3 in this verified build; maintain and qualify renderer updates.

Packaging excludes incompatible ICU DLLs discovered through an unrelated developer tool's PATH; they had shadowed the expected Windows ICU API and prevented the first frozen window from opening. Verify this again whenever changing Qt or the build environment. The lock file and relative-path spec/installer files are included in the repository.

## Footswitch design

The rejected large assembly was replaced with a compact metal pushbutton: 38px surround, 28px cap, a small amber lamp and a short FOOTSWITCH / ON/OFF label. Clicking toggles a CC64 test message to the reference receiver. The lamp and depressed state follow received feedback. The button does not send to another selected hardware destination. OFFLINE means the reference receiver is disconnected.

The four parameter knobs above it remain received-value displays. Edit/send parameter values from the command station. Real hardware may use different mappings from this reference pedal.

## Remaining release qualification

This machine still has other installed software, so the PATH-restricted test is not a clean Windows VM test. A clean-machine installation with browsers and developer tools absent remains necessary before broad distribution. Physical USB/DIN hardware response, manufacturer driver compatibility, long-duration wire timing, high-DPI/accessibility coverage and multiple GPU configurations remain unverified. No claim of professional live-stage timing certification is made.

External MIDI equipment must expose a Windows MIDI port. Class-compliant USB MIDI may use Windows drivers; other devices require the manufacturer's driver. DIN devices need a MIDI interface. Correct port/channel, device-specific PC/CC maps and external clock settings still matter. loopMIDI and MIDI-OX are optional diagnostic tools, not dependencies of direct hardware operation or the internal lab.

The installer is unsigned. Obtain publisher signing and complete clean-machine/hardware qualification before representing it as a broadly qualified production release. The old demo video describes the earlier browser/loopback workflow and needs rerecording for this installation.

## Project preservation

Reviewed source changes were promoted with original hash checks. Replaced source/documents are backed up under `ChatGpt\Backups\before-desktop-1.1.0`. The previous browser-dependent onedir bundle is preserved under `ChatGpt\Backups\browser-build-before-desktop-1.1.0`. The new matching onedir bundle is at `dist\PulseStage`. Historical installers are retained as historical files.

## Windows Installed apps visibility repair — 17 October 2026

The earlier automated registry checks did not establish that the entry appeared in Windows Settings. The user reported it missing, and this was reproduced in both Installed apps and classic Programs and Features. The tool-visible registry had an uninstall key for the correct user SID without hidden/parent flags; normal Windows UI still found no matching app. An app-specific metadata repair in the tool context did not resolve the UI discrepancy.

The same verified Setup.exe was then launched through normal Windows Explorer, using Install for me only and the existing installation directory. PulseStage was closed normally when setup could not close it automatically. Setup completed successfully. Windows Settings changed from 108 to 109 apps and searching PulseStage visibly returned PulseStage version 1.1.0, version 1.1.0, size 423 MB. Its menu exposes an enabled Uninstall option. Screenshot: Desktop-1.1.0-QA/pulsestage-installed-apps-repaired.png.

After this repair, the tool context continued reading the diagnostic DisplayName PulseStage, while Windows displayed the installer's PulseStage version 1.1.0. This is evidence that tool-visible registration alone is insufficient here; the precise registry/context isolation mechanism was not determined. For future installation checks, launch the installer normally through Windows and verify the actual Installed apps UI, rather than relying only on helper-process registry queries. No installer binary or application-code change was needed for this repair. The app remains installed; the Uninstall menu was left open for the user.
