# PulseStage demo narration

Synthetic American male voice; deliberate pacing.

## 00:00 — The challenge

Before we touch the controls, here's the challenge. A musician needs the right preset, the right settings, and a steady tempo. But when nothing happens, it's hard to tell where the connection failed. Did the computer send the message? Did the device receive it?

## 00:22 — What PulseStage helps us do

PulseStage gives us a way to check those steps. We can send a simple instruction, then watch a test receiver respond. Think of MIDI as a remote control for musical equipment. It carries instructions, rather than the sound itself. Let's try it without any physical instruments.

## 00:45 — First, choose the two connections

Set the input to PulseStage Keyboard, and the output to PulseStage Pedal Test. These are two separate connections. The keyboard sends notes into our monitor. The command station sends settings to the reference pedal. Keyboard notes are not automatically passed through to the pedal.

## 01:06 — Play a key, then release it

Click a piano key, then let go. Pressing it sends a note on instruction. Releasing it sends note off. You don't need to know how to play piano for this check. We are testing the messages. This keyboard does not include its own sound generator.

## 01:26 — Look for the received notes

Open Event monitor. Here we can see the note arrive, followed by its release. R X means received. T X means sent. This is useful when troubleshooting. A sent counter shows that PulseStage transmitted something. The received event gives us separate evidence that it arrived.

## 01:49 — Send the first pedal setting

Back in Control room, choose Control change, then Expression. Set the value to twenty, and click Send command. Now look at the reference pedal. Its Expression display reads twenty. Simply changing the number in the editor does not send anything. We send it deliberately.

## 02:12 — Now change it to one hundred

Let's change that value to one hundred, and send again. The receiver updates its number and knob position. Those four pedal knobs are indicators of settings it received. They are not controls you can turn here. On real equipment, the meaning of each controller depends on that device's MIDI settings.

## 02:35 — What is the metal button?

The metal button below the knobs represents a footswitch, like a button a musician presses with a foot. In this test receiver, controller sixty four turns its ring on or off. Send one hundred twenty seven for on, or zero for off. It is an indicator here, so clicking it won't operate it.

## 02:58 — Change a preset

Next, choose Program change, enter twenty four, and send. The receiver shows preset twenty five. That difference is just numbering. MIDI starts at zero, while this receiver labels presets starting at one. Always check the numbering convention before choosing a musician's preset.

## 03:23 — Check the shared tempo

Set the tempo to one hundred twenty beats per minute, then press Start. The reference receiver shows Running, and measures about one hundred twenty beats per minute from the incoming timing messages. When you're finished, press Stop. A real device must support external MIDI clock, and have that option enabled.

## 03:46 — What if I connect a real instrument?

A compatible physical MIDI device can appear in the connection lists once Windows recognizes it. Connect and power it, click Refresh, then select its port. Some devices need a manufacturer's driver. Older MIDI sockets need a MIDI interface. An ordinary audio cable isn't a MIDI connection. We have not verified physical hardware in this demonstration.

## 04:14 — What needs to be installed?

The keyboard and reference pedal are already inside PulseStage. You don't need to open their older separate applications. But this virtual test still needs loop MIDI installed and running. MIDI OX is optional. The current developer version also needs Python and its packages. A finished Windows installer should include those application dependencies. That installer has not been built yet.

## 04:47 — A simple check before using real gear

That's the basic workflow. Check the connections. Send one small change. Confirm that it arrived. Then test the actual musician's equipment with its documented settings. The written guide beside this video includes the same steps, so you can repeat them at your own pace.