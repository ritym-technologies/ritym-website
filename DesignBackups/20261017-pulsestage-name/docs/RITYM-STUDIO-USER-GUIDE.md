# RITYM PulseStage — MIDI Studio

Operator guide for the Studio UI revision, 17 October 2026.

## What this application does

PulseStage sends MIDI control instructions and inspects received MIDI. It can change a compatible device's preset, control a parameter and generate MIDI Clock. It does not record audio or contain an audio effects processor. A silent MIDI test can be successful.

The integrated **Keybed** is a virtual MIDI source. The **Reference pedal** is a test receiver with demonstration mappings. It is not a model of a particular manufacturer's pedal and does not process sound.

## Starting the development application

Run `python run_app.py` from the project directory, or use the existing `run_app.bat`. Use native Windows mode, without `--virtual`, for the integrated instruments. The normal local address is `http://127.0.0.1:8765`. If an older engine is running, restart that engine after updating the source; refreshing a browser alone does not reload Python backend changes.

The review preview may run separately at `http://127.0.0.1:18795`. It has an isolated configuration. It is not the final Windows installer. A packaged release should replace these developer instructions with its Start-menu application entry.

## First-time virtual connections

loopMIDI is already installed on this development computer. Keep it running and create these exact ports if absent:

* `PulseStage Keyboard`
* `PulseStage Pedal Test`

In **Control room**, click **Connect keybed**. This opens the integrated keyboard's MIDI output and selects `PulseStage Keyboard` as PulseStage's input.

Click **Connect receiver**. This opens the reference pedal's input and selects `PulseStage Pedal Test` as PulseStage's command output. These buttons intentionally change the displayed connection selections. No connection is silently redirected to a different available device.

The paths are separate:

    Keybed → PulseStage Keyboard → PulseStage input monitor
    Command station → PulseStage Pedal Test → Reference pedal

PulseStage does not automatically forward incoming notes to its selected output. The route strip explicitly says **No automatic thru**.

## Dark Console and Light Console

Dark Console is the initial theme. The top-bar **Light / Dark** button switches themes and remembers the choice in the browser's local storage for that application address. Theme changes affect appearance only; they do not transmit MIDI. Both themes retain readable numeric displays and distinct status labels.

## Control room

**Input source** chooses what PulseStage listens to. It is a MIDI input, not a microphone. **Output destination** chooses where commands created by PulseStage go. The Received counter is RX; Sent is TX. Playing the keybed increases RX in the main application. It does not require the main TX counter to increase.

**Command station:** select the send channel and command type. Drag the value knob vertically, adjust it with arrow keys (Shift for larger steps), or enter the number. Then click **Send command**. The knob edits a value; it does not continuously transmit while being adjusted.

* Control Change: select a controller number and value0–127. Names such as expression or sustain describe common MIDI usage; actual pedal mappings can differ.
* Program Change: select a program and the display convention. In 0–127 mode, value24 sends `C0 18` on channel1. In 1–128 mode, the same wire value is labelled25. Changing convention preserves the wire value.
* Bank + program: explicitly choose MSB, LSB and program. The sequence is CC0, CC32, then Program Change. The bank-to-preset interpretation depends on the receiver.

The recessed display previews bytes. **Sent** means the driver accepted transmission. The reference receiver and Test bench provide separate evidence of arrival. It does not prove an unrelated physical device responded.

**Reference pedal:** display numbering is1–128. Its program display, knob positions, received counters and transport state update only from actual incoming MIDI on its test port. The CC mappings are demonstration mappings: expression11, volume7, parameterA12, parameterB13 and switch64. The footswitch illustration is a read-only indicator of received CC64, not a clickable universal bypass command.

**Master clock:** set BPM and use Start, Continue or Stop. Tap sets tempo from repeated taps. MIDI Clock sends24 ticks per quarter note. The selected output must be correct and the receiver must support/configure external clock. The reference pedal shows a measured BPM only after enough recent ticks; the display returns to dashes when ticks become stale. Clock and transport are separate MIDI concepts, even though the current engine couples stopping clock with its Stop control.

**Stop all** stops the engine's clock/actions and requests release of the integrated keybed. **Panic** sends the application's sustain-off/all-notes-off/all-sound-off routine to its selected output. Equipment responses vary. Escape invokes Stop all in the new UI; when the action-editor dialog is open, Escape closes that dialog normally.

## Playing the integrated keybed

Click piano keys, or focus the keybed and type **A W S E D F T G Y H U J K O L P ;**. A starts at middle C, MIDI note60/C4. Several typing keys may form chords, subject to computer-keyboard rollover. Use the keybed's own channel and velocity controls; these are independent of Command station's send channel.

Octave controls move the range. Notes are released on focus loss, channel/range change, Release notes and page exit. A backend heartbeat watchdog also releases tracked notes if the browser stops responding. The integrated keybed currently supplies notes and velocity; the separate desktop piano has additional controls such as sustain and expression.

There is no built-in audio synthesizer. To audition sound, the separate desktop keyboard can deliberately target Microsoft's GS Wavetable Synth. That route sends notes to the synth instead of PulseStage's input. Do not change the integrated test route expecting it to provide audio.

## Event monitor

Choose **Event monitor** from the sidebar; it is no longer buried below the controls. Each row includes direction, time, port, channel, message type, bytes and interpretation. Filter by channel and optionally show raw clock. Pause display does not stop capture or MIDI processing. The screen retains at most150 events; backend exports use its own bounded capture history.

**Controller activity** plots the most recent96 CC values. **Clock intervals** plots up to96 intervals measured by the reference receiver. These are MIDI data plots, not audio waveforms. Windows arrival timing is affected by OS/driver scheduling and does not establish physical-wire jitter. Empty displays show an awaiting-data message rather than an invented trace.

Export JSON, CSV or diagnostic text from the capture selector.

## Test bench

Four guided tests distinguish pending, failed and receiver-verified results:

1. **Play a note:** connects/selects the keybed route, then waits for matching Note On and Note Off through the main input.
2. **Change a preset:** sends program24 and requires the exact channel/program bytes at the reference receiver.
3. **Move a parameter:** sends CC11/value96 and requires that event at the receiver.
4. **Follow the clock:** sets120 BPM, requires Start plus at least96 received ticks near120 BPM, then stops. Stop the master clock before beginning this test. Stop all remains available to interrupt it.

Program, parameter and clock tests target only the explicitly selected `PulseStage Pedal Test` port. They do not report a pass merely because a POST/send call returned success. A test times out when matching received evidence is absent. These checks qualify local Windows loopback, not a real pedal.

## Performance actions and MIDI utilities

Actions can be created, edited, duplicated, deleted and run. Each step has an explicit output, MIDI channel and post-step delay. Move steps with the up/down buttons. Program, CC, bank, note and raw-hex step types use the engine's existing models. The editor explains bank field ordering. Missing destinations must be fixed rather than replaced silently. Running an action confirms engine transmission separately from receiver verification.

MIDI utilities provide pitch bend, channel pressure and raw MIDI/SysEx sending to the selected output/send channel. Pitch shows a signed offset around its14-bit center8192. Raw/SysEx commands require documented payloads for the receiving device. A device query is not the same as receiving a response.

## Troubleshooting and MIDI-OX

If RX stays zero, compare the sender's destination and PulseStage's input. They must name the same cable. Ensure native mode, loopMIDI running, the receiver connected, the display unpaused and filters appropriate.

During this development session a newly created second loopMIDI port accepted sends but did not deliver data until loopMIDI was restarted and handles reopened. Restarting the driver/application can invalidate old handles even if the same name reappears. Reconnect the keybed/receiver. For a cached command output, select it, select No output, then deliberately select it again to reopen its handle. Do not assume Refresh alone repairs cached handles. Automatic driver-restart recovery still needs release qualification.

MIDI-OX remains an optional independent diagnostic tool. Select the test cable as its MIDI input, leave outputs unselected initially, and compare bytes with PulseStage. If opening a port is busy, close another receiver and test sequentially. It is not required for normal PulseStage operation and is not an audio engine.

For hardware qualification, connect a real compatible MIDI device/interface and verify its actual response. The current loopback tests do not establish physical compatibility, sustained stage reliability or long-duration timing guarantees.
