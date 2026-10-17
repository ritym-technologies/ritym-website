# PulseStage — Guided Demo

Duration: 05:11. Full HD 1920 × 1080, 24 fps, slower American male synthetic narration.

Open **Watch-Demo.html** or **PulseStage-Guided-Demo.mp4**. Enable CC in the HTML player for subtitles. The SRT is available for desktop players.

This is an edited walkthrough using verified still captures of the actual application, with narration and close-ups. It is not a continuous screen recording. It demonstrates local virtual MIDI delivery; it does not claim physical hardware or audio testing.

## Chapters

- **00:00 — The challenge**
- **00:22 — What PulseStage helps us do**
- **00:45 — First, choose the two connections**
- **01:06 — Play a key, then release it**
- **01:26 — Look for the received notes**
- **01:49 — Send the first pedal setting**
- **02:12 — Now change it to one hundred**
- **02:35 — What is the metal button?**
- **02:58 — Change a preset**
- **03:23 — Check the shared tempo**
- **03:46 — What if I connect a real instrument?**
- **04:14 — What needs to be installed?**
- **04:47 — A simple check before using real gear**

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

Source captures and reproducible rendering scripts are in the source subfolder. Narration uses the Benjamin American male preset, generated through Runway at 0.83 speed. It is synthetic narration, not a human recording. No music or synthesized instrument audio is included. Captions are approximately timed from narration segments, rather than word-aligned transcription.


## Physical instruments and dependencies

PulseStage lists MIDI ports exposed by Windows. A compatible powered USB-MIDI instrument, or a MIDI interface for DIN equipment, should become available for selection after Windows recognizes it. Click Refresh, then explicitly choose its input or output as appropriate. Some devices need manufacturer drivers. An audio-only instrument, audio cable, or ordinary sustain pedal is not a MIDI port. Enumeration is not proof of hardware response, and no physical hardware was verified in this demonstration.

The integrated keybed and reference receiver are part of PulseStage's interface and backend. Their current virtual test path still requires loopMIDI installed and running with both named ports. The old standalone keyboard/pedal windows are optional development utilities. MIDI-OX is optional, not a runtime requirement. Direct MIDI hardware operation does not require loopMIDI. Audible notes require a sound generator; PulseStage does not include one.

The current source-based application needs Python, FastAPI, Uvicorn, WebSockets and Pydantic plus transitive dependencies, and a browser. A completed Windows installer was not found in the source review on 17 October 2026. Antigravity must bundle Python and application packages, handle browser/WebView availability, resolve optional virtual-driver licensing and setup, and test on clean Windows. Do not claim all dependencies are already bundled.

References: [Microsoft MIDI-capable USB class driver](https://learn.microsoft.com/en-us/windows-hardware/drivers/audio/usb-2-0-audio-drivers), [loopMIDI port lifetime](https://www.tobias-erichsen.de/software/loopmidi.html).
