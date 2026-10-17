# PulseStage Keyboard

A standalone Windows on-screen MIDI piano. It does not modify the main PulseStage application. Requires Python 3 with Tkinter (already available on this computer), and the installed loopMIDI driver for a virtual input.

## Use

1. Keep loopMIDI running with a port named **PulseStage Keyboard**. That port was created during setup. If it disappears, open loopMIDI, enter the name and click `+`.
2. Double-click **Start Keyboard.bat**. The piano automatically connects to that exact port when it is available. Otherwise select it and click Connect.
3. In PulseStage's native Windows mode (without `--virtual`), click Refresh, then choose **PulseStage Keyboard** under **Input Source**. Leave PulseStage's Output Destination empty for the initial monitoring test.
4. Click piano keys or use **A W S E D F T G Y H U J K O L P ;**. A starts at middle C (MIDI note60/C4). White and black keys light up while held. Several typing keys can be held for chords, subject to your computer keyboard's rollover limits. Mouse dragging plays successive notes.
5. Set MIDI channel and velocity (how strongly a note is played). Space toggles sustain; Escape releases notes and sends sustain-off/all-notes-off/all-sound-off. Changing octave/channel, leaving the window or closing it also releases notes. Sustain is a MIDI instruction; the UI highlights physically held keys, not a receiver's sustained sound.
6. The expression slider and Send CC11 button send a controller message for additional input testing.

Routing: **On-screen keyboard output → loopMIDI PulseStage Keyboard → PulseStage input**. The same port appears as an output to the sender and as an input to receivers. It is a software MIDI endpoint, not a physical USB device.

To see messages independently, select PulseStage Keyboard as an input in MIDI-OX. Start with MIDI-OX outputs unselected to avoid echo loops. Windows/driver multi-client availability determines whether receivers can open the same input simultaneously; if busy, close one receiver and test sequentially.

The piano is a MIDI controller, not an audio synthesizer. When using the loopMIDI destination, no sound is expected. You can deliberately select Microsoft GS Wavetable Synth as output to hear notes through Windows audio instead, but those notes will then go to the synth rather than PulseStage's input. MIDI clock generation, audio recording and physical USB-device emulation are outside this keyboard's scope.

If the port is removed, reopen loopMIDI, recreate the port if necessary, Refresh and Connect. The keyboard does not silently switch to another output or replay held notes after reconnection. MIDI sent to a receiver does not prove it responded; receiver/device behavior must be checked separately.

## Tests

`python test_keyboard.py` checks note ownership, overlapping mouse/typing notes, channel-specific release, panic and failures.

`python test_keyboard.py --native` opens only the dedicated PulseStage Keyboard loopMIDI port, sends channel2 note-on/note-off and CC11, captures them through a separate native WinMM input, and writes native-test-results.json. This is a Windows driver loopback test, not physical hardware qualification. Run it with the piano closed and ensure receiver availability first.
