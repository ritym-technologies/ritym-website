# PulseStage — Guided Demo

Duration: 03:08. Full HD 1920 × 1080, 24 fps, English synthetic narration, on-screen explanations and optional subtitle files.

Open **Watch-Demo.html** or **PulseStage-Guided-Demo.mp4**. Enable CC in the HTML player for subtitles. The SRT is available for desktop players.

This is an edited walkthrough using verified still captures of the actual application, with narration and close-ups. It is not a continuous screen recording. It demonstrates local virtual MIDI delivery; it does not claim physical hardware or audio testing.

## Chapters

- **00:00 — Welcome to the studio**
- **00:15 — Two separate signal paths**
- **00:34 — Play the virtual keyboard**
- **00:52 — See what actually arrived**
- **01:11 — Expression: start low**
- **01:28 — Expression: turn it up**
- **01:46 — The metal footswitch**
- **02:06 — Choose a preset**
- **02:26 — Synchronize the clock**
- **02:45 — Repeat the checks confidently**

## Repeat the demonstration

1. Start loopMIDI. Ensure both **PulseStage Keyboard** and **PulseStage Pedal Test** ports exist. Start PulseStage and select the Control room.
2. Choose **Input: PulseStage Keyboard** and **Output: PulseStage Pedal Test**. Use **Connect receiver** if required. The keybed sends to the Keyboard port; the reference receiver listens on Pedal Test. No automatic MIDI thru connects these paths.
3. Click and release C4 on the integrated keyboard. Open Event monitor and confirm received Note On 60 and Note Off 60. Return to Control room.
4. Choose Control change, channel 1, controller **11 / Expression**. Enter **20**, click **Send command**, and confirm Expression 20 on the reference pedal. Repeat with **100**.
5. Optional: send **CC 7 = 80**, **custom CC 12 = 50**, and **custom CC 13 = 110** to reproduce the other knob positions in the video.
6. Choose **CC 64**, send **127**, and observe the illuminated ring around the metal footswitch. Send **0** to turn it off. The reference knobs and footswitch are read-only received-state indicators. CC64 is a test mapping; real hardware mappings may differ.
7. Choose Program change, enter wire value **24**, and send. The reference receiver's 1–128 display reads **025**. Check display numbering before entering a value.
8. Set clock **120 BPM**, click **Start**, and observe RUNNING plus approximately 120 BPM at the receiver. Click **Stop** after testing.

## If nothing moves

Editing a command does not transmit it: click Send command. RECEIVER ONLINE means the input handle opened; it does not prove data arrived. Check the two distinct port names, reconnect the receiver/keybed, and inspect received events. After restarting loopMIDI, refresh and reopen the ports in PulseStage. Avoid sending an output back into itself.

## MIDI-OX and real equipment

MIDI-OX is a separate MIDI message inspector. It can listen to the relevant loopMIDI port and show note, controller, program and timing messages independently. Opening a port may conflict with other applications depending on the MIDI driver; close competing handles if necessary. This demo does not show a MIDI-OX capture. The keybed has no built-in sound generator. No physical instrument is needed for this software test. Actual pedals require their own MIDI mapping and external-clock settings, and must be tested separately.

## For Antigravity

Include the video, captions and repeatable steps in offline onboarding and the updated user guide. Preserve the distinction between the keyboard input path and command output path. Label receiver knobs and the CC64 footswitch clearly as indicators to prevent users trying to turn or click them. Do not present the software test as physical hardware certification.

Source captures and reproducible rendering scripts are in the source subfolder. Narration was generated locally using the Windows Microsoft Zira voice. No music or synthesized instrument audio is included. Captions are approximately timed from narration segments, rather than word-aligned transcription.
