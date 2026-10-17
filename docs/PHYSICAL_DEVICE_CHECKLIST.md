# PulseStage MIDI: Physical Device Verification Checklist

Perform this verification with real stage equipment (effects pedals, audio interfaces, hardware synths) before live performance.

| Step | Action | Expected Result | Verified Result | Notes |
| :--- | :--- | :--- | :--- | :--- |
| **1. Output Selection** | Connect USB-MIDI interface; select port in Output dropdown. | Port name appears without errors; status changes to **Connected (Ready)**. | [ ] Pass [ ] Fail [ ] Not Run | Verify correct driver is installed. |
| **2. Program Change** | Set Channel 1, Command "Program Change", Preset 10, click Send. | Receiving pedal displays Preset 10 (or 11 if 1-indexed); Monitor logs TX `0xC0 0x0A`. | [ ] Pass [ ] Fail [ ] Not Run | Check pedal MIDI receive channel. |
| **3. Control Change** | Select CC 64 (or pedal expression CC), drag slider to 127. | Pedal reacts (e.g. bypass LED toggles or parameter shifts); smooth 25ms rate-limited TX stream. | [ ] Pass [ ] Fail [ ] Not Run | Confirm pedal CC mapping table. |
| **4. MIDI Clock Sync** | Set BPM to 120, click Start Clock. | Receiving delay pedal's tempo LED flashes in sync at 120 BPM; Monitor increments clock counter without UI freezing. | [ ] Pass [ ] Fail [ ] Not Run | Ensure pedal is set to External Sync. |
| **5. Transport Controls** | Click Stop Clock, then Continue. | Receiving sequencer/looper pauses and resumes correctly. | [ ] Pass [ ] Fail [ ] Not Run | Stop sends `0xFC`, Continue sends `0xFB`. |
| **6. Disconnect Recovery**| Unplug USB cable while clock is running. | UI marks port as **Disconnected / Missing**; no app crash; error notification displayed. | [ ] Pass [ ] Fail [ ] Not Run | Graceful hardware error handling. |
| **7. Reconnection** | Reconnect USB cable. | Port reappears and re-engages without replaying stale commands. | [ ] Pass [ ] Fail [ ] Not Run | Prevents accidental patch jumps on stage. |
| **8. Multi-Command Action** | Trigger "Solo Boost" macro (PC + CC with 25ms delay). | Both commands execute in exact order; both target devices respond. | [ ] Pass [ ] Fail [ ] Not Run | Verify delay accommodates slow pedals. |
| **9. Panic / Stop All** | Click "Stop All / Panic". | Clock immediately halts; CC 123, CC 120, and CC 64 transmitted. | [ ] Pass [ ] Fail [ ] Not Run | Stage safety test. |
| **10. Persistence** | Close and relaunch application. | Previously saved actions, BPM, and selected port preferences are restored. | [ ] Pass [ ] Fail [ ] Not Run | Schema-versioned configuration test. |
