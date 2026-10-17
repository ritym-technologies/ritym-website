# PulseStage MIDI: Beginner's Guide for Musicians

Welcome to **PulseStage MIDI**, designed to give touring musicians complete command of their MIDI-equipped effects pedals, synthesizers, and stage gear without the complexity of vintage diagnostic tools.

---

## 1. Quick-Start in 5 Simple Steps

1. **Choose Your Output:**  
   Click the **MIDI Destination** selector and choose your MIDI interface or USB-connected pedal.
2. **Set the MIDI Channel:**  
   Select the channel your pedal is listening on (Channels 1 to 16, typically Channel 1 by default).
3. **Select Your Command:**  
   - Choose **Change Preset (Program Change)** to switch patches.  
   - Choose **Control Parameter (Control Change)** to adjust values like mix, delay time, or bypass.
4. **Enter Your Value:**  
   - For presets: Type the preset number (0–127).  
   - For parameters: Choose the CC number and adjust the slider (0–127).
5. **Press Send:**  
   Click the high-contrast **SEND COMMAND** button (or press `Enter`).

---

## 2. Understanding Preset Numbers: 0–127 vs. 1–128

- **The Technical Rule:** MIDI hardware communicates using numbers starting from `0`. The first patch is technically `0`, and the 128th patch is `127`.
- **The Pedal Screen:** Many pedals (e.g., Boss, Strymon, Line 6) display presets starting at `1`.
- **PulseStage Solution:** Click the toggle in the upper right of the composer:  
  - Switch to **1–128** if your pedal front panel starts at 1.  
  - Switch to **0–127** if your manual uses zero-based numbering.  
  *PulseStage sends the exact correct byte to the wire automatically!*

---

## 3. Synchronizing Tempo (MIDI Clock)

1. Connect your delay or modulation pedal.
2. Select your MIDI Output port.
3. Set your target BPM using the numeric field or tap the **TAP TEMPO** button 4 times in rhythm.
4. Click **START CLOCK**. Your pedal's tempo LED should pulse in lockstep with the on-screen tempo indicator.
5. *Note:* Make sure your pedal's internal settings are set to **MIDI Clock: External** or **MIDI Clock: On**.

---

## 4. Setting Up a "Solo Boost" Action

1. Navigate to the **Performance Actions** panel.
2. Click **+ New Action** and title it "Lead Solo".
3. Add **Step 1**: Target: *Amp Modeler*, Channel 1, Program Change: *25 (Lead Tone)*.
4. Add **Step 2**: Delay: *20 ms*.
5. Add **Step 3**: Target: *Delay Pedal*, Channel 2, CC: *102 (Engage)*, Value: *127*.
6. Save the action. You can now fire it with a single tap or keyboard shortcut during a song!

---

## 5. Stage Safety & Emergency Panic

If a note hangs or an unexpected sound continues during a performance:
- Click the red **PANIC (ALL OFF)** button or press `Escape`.
- PulseStage immediately transmits **All Notes Off (CC 123)** and **All Sound Off (CC 120)** across all active channels and stops any running clock.
