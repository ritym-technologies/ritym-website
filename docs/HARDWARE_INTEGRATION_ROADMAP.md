# PulseStage MIDI: Hardware Integration and Platform Roadmap

## 1. Programmable MIDI Foot Controller Specification

As part of the future hardware product, PulseStage provides an architectural extension point for our forthcoming programmable hardware foot controller.

### Hardware Device Profile & Architecture
- **Microcontroller Target:** 32-bit ARM Cortex-M4 / ESP32-S3 with native USB-MIDI device support.
- **Physical Interfaces:** 4–8 heavy-duty silent footswitches with dual-color LEDs, 2 TRS expression pedal inputs, 5-pin DIN MIDI In/Out, and USB-C MIDI.
- **Memory:** Onboard non-volatile SPI flash for preset banks, routing tables, and offline configuration.

---

## 2. Private Companion Protocol (Specification Draft)

To maintain absolute transparency, **generic MIDI pedals will not be advertised as supporting this proprietary configuration protocol**. Only our companion hardware implements this specification.

### A. Transport and Framing
- **Framing:** Standard MIDI System Exclusive (SysEx).
- **Manufacturer ID:** 3-byte educational/development ID `0x00 0x02 0x7E`.
- **Command Structure:**
  ```
  0xF0 (SysEx Start)
  0x00 0x02 0x7E (Manufacturer ID)
  0x10 (Device Family: PulseStage Foot Controller)
  0x01 (Device Model)
  <Command Byte>
  <Sub-Command / Payload Length>
  <Payload Bytes (7-bit encoded)>
  <CRC7 Checksum>
  0xF7 (SysEx End)
  ```

### B. Device Handshake & Identity Discovery
- **Handshake Sequence:**
  1. PulseStage sends Universal Non-Realtime SysEx Identity Request:  
     `0xF0 0x7E 0x7F 0x06 0x01 0xF7`
  2. Hardware Controller responds with Identity Reply specifying Family Code, Firmware Version, and Bootloader State:  
     `0xF0 0x7E 0x7F 0x06 0x02 <Family> <Model> <Major> <Minor> <Patch> 0xF7`
  3. PulseStage verifies firmware compatibility against `MINIMUM_SUPPORTED_FIRMWARE = "1.0.0"`.

### C. Footswitch Assignment Configuration Transfer
- Each switch supports three triggers:
  1. **Tap:** Quick press (< 300 ms).
  2. **Hold:** Sustained press (> 500 ms).
  3. **Double-Tap:** Two presses within 250 ms.
- Payloads are transferred in structured chunks with 7-bit ASCII/binary translation and 7-bit CRC validation.

### D. Safe Firmware Update Architecture (Milestone 3)
- Firmware updates will execute via a two-stage bootloader with dual-bank partition rollback.
- **Safety Rule:** No non-functional or decorative update buttons appear in the UI until the physical hardware prototype is connected and verified.

---

## 3. Platform Expansion Roadmap

```
+-------------------------------------------------------------------------------+
|  Milestone 1 & 2 (Now)                                                       |
|  - Windows 10/11 WinMM Native Engine                                         |
|  - Core Codec, Models, Actions, Monitor, and 24 PPQN Clock                   |
|  - Touring-grade Standalone Stage UI                                         |
+-------------------------------------------------------------------------------+
                                        |
+---------------------------------------v---------------------------------------+
|  Milestone 3 (Post-v1)                                                        |
|  - Hardware Foot Controller Companion Protocol Implementation                |
|  - Input-to-Output Routing Engine with Loopback Prevention                    |
|  - Custom User Device Profile Editor                                         |
+-------------------------------------------------------------------------------+
                                        |
+---------------------------------------v---------------------------------------+
|  Milestone 4 (Cross-Platform Expansion)                                      |
|  - macOS Native CoreMIDI Adapter (cffi / pyobjc bridge)                      |
|  - Android USB Host MIDI Adapter (android.media.midi service)                |
|  - Touch-optimized Tablet Stage Mode                                          |
+-------------------------------------------------------------------------------+
```
