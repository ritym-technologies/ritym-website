# PulseStage MIDI: Prioritised Product Backlog

## Milestone 1: Working Vertical Slice (Current Deliverable)

### US-1.1: Device Discovery and Enumeration
- **User Story:** As a musician, I want to see all available MIDI output and input ports so I can connect my gear.
- **Acceptance Criteria:**
  - Enumerate physical, USB, and virtual MIDI ports.
  - Distinguish identically named devices with instance IDs.
  - Detect newly connected or disconnected devices within 2 seconds.
  - Provide a virtual loopback adapter when no physical hardware is plugged in.

### US-1.2: Single-Message Command Sending (PC and CC)
- **User Story:** As a guitarist, I want to send a Program Change or Control Change message to my pedal.
- **Acceptance Criteria:**
  - 5-step quick send workflow: Output -> Channel (1–16) -> Command -> Value (0–127) -> Send.
  - Support both 0-indexed (0–127) and 1-indexed (1–128) preset display conventions.
  - Continuous CC slider with rate limiting (25 ms) and direct numeric input.
  - Clear feedback: "Transmitted to [Port] (Unverified Device State)".

### US-1.3: Real-Time Traffic Monitor
- **User Story:** As a sound technician, I want to inspect outgoing and incoming MIDI messages in plain language.
- **Acceptance Criteria:**
  - Display direction (TX / RX), timestamp, channel, message type, and plain-language summary.
  - Expandable view for raw hex bytes (e.g. `[0xC0, 0x14]`).
  - Pause display toggle without interrupting background transmission.
  - Clear monitor button.

---

## Milestone 2: Useful First Release (Current Deliverable)

### US-2.1: High-Precision MIDI Clock & Transport
- **User Story:** As a performer, I want to send tempo sync (24 PPQN) to my delay and modulation pedals.
- **Acceptance Criteria:**
  - Editable BPM (40–300) and Tap Tempo calculator with 4-tap averaging.
  - Separate Clock generation from Transport controls (Start, Continue, Stop).
  - High-precision monotonic scheduling with zero cumulative drift (< 1.5 ms jitter on Windows).
  - Smart clock filtering in monitor (counter badge rather than 48 lines/sec flood).

### US-2.2: Multi-Command Performance Actions ("Solo / Boost")
- **User Story:** As a stage player, I want to trigger a single button that switches multiple pedals simultaneously.
- **Acceptance Criteria:**
  - Define ordered sequence of commands targeting different ports and channels.
  - Configurable inter-command delay (e.g. 20 ms).
  - Immediate abort if any destination port becomes unavailable.
  - Duplicate, edit, rename, and delete actions.

### US-2.3: Configuration Persistence and Diagnostic Export
- **User Story:** As a user, I want my port selections and custom actions saved between launches.
- **Acceptance Criteria:**
  - Schema-versioned atomic JSON persistence (`schema_version: 1`).
  - Export diagnostic log to JSON, CSV, or formatted text for tech support.

---

## Milestone 3: Hardware Companion & Advanced Routing (Next Phase)

### US-3.1: Foot Controller Protocol & Configuration Editor
- **Acceptance Criteria:**
  - Bidirectional SysEx handshake (`0x7E` Identity Request / Response).
  - Read and write footswitch assignments (Tap, Hold, Double-Tap).
  - Firmware version reading and validation against minimum supported version.

### US-3.2: Safe Input-to-Output Routing & Filtering
- **Acceptance Criteria:**
  - Route messages from Input A to Output B with channel remapping.
  - Loop detection algorithm that drops self-referential message chains.

---

## Milestone 4: Multi-Platform Expansion (Future Roadmap)

### US-4.1: macOS CoreMIDI Integration
- **Acceptance Criteria:**
  - Implement `CoreMidiAdapter` leveraging native CoreMIDI endpoints.
  - Test on macOS 13+ with low-latency dispatch queues.

### US-4.2: Android USB-MIDI Integration
- **Acceptance Criteria:**
  - Implement `AndroidMidiAdapter` using `android.media.midi`.
  - Handle OTG USB hotplugging and Android battery optimization exceptions.
