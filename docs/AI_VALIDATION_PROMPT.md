# PulseStage MIDI: Comprehensive AI Validation & Audit Prompt

> **Instructions for the Auditing AI Agent:**  
> You are acting as an elite Principal Audio Systems Architect, Senior Embedded & Desktop Systems Engineer, and Touring Production Specialist with decades of experience at top-tier musical instrument manufacturers (such as Yamaha, Roland, and Dave Smith Instruments / Sequential).  
> Your task is to perform an exhaustive, independent technical audit and validation of the codebase, architecture, protocols, and user experience of **PulseStage MIDI**, located at `D:\Projects\MIDI\`.
>
> Evaluate the implementation against the stringent requirements below. You must verify actual code, protocol byte encoding, thread scheduling mechanics, timing drift formulas, error handling, and test executions. Do not accept assertions at face value: inspect the files, run the test suites, analyze the timing data, and assess whether this product is truly stage-ready for touring musicians at major international venues.

---

## 1. Project Background and Objective

The project goal was to design and implement an approachable, touring-grade MIDI control station and diagnostic monitor that serves as an easier, modern alternative to technical utilities like MIDI-OX. 

The software operates on Windows 10/11 using native Windows Multimedia subsystem APIs, with architectural abstractions for future macOS and Android ports. It controls compatible effects pedals, synthesizers, and outboard stage gear via 5-pin DIN and USB-MIDI. A future milestone envisions a programmable hardware foot controller companion.

### Core Product Tenets to Verify
1. **Understandable Language over Cryptic Hex:** Plain-language descriptors for all common messages, while keeping raw bytes accessible on demand.
2. **Honesty Regarding Hardware State:** Recognition that standard MIDI is unidirectional (simplex). The UI must never claim an external device has switched patches or adjusted parameters unless verified bidirectional feedback is present.
3. **Stage-Grade Reliability:** Decoupled execution threads, buffer overrun protection (slider rate limiting), zero cumulative clock drift, and non-destructive panic procedures.
4. **Zero Compilation Friction:** Native Windows access without requiring heavy MSVC/C++ SDKs or Rust installations on the musician's laptop.
5. **Privacy & Offline Integrity:** Zero cloud dependencies, subscriptions, or login requirements.

---

## 2. Exhaustive Audit Criteria & Verification Checklist

Review and validate the implementation across the following 8 critical dimensions:

### Domain 1: Architecture & Technology Stack Selection
- [ ] **Stack Justification:** Verify why Python 3.12 + native WinMM (`winmm.dll` via `ctypes`) + FastAPI/WebSocket + standalone frameless app window (`--app`) was chosen over Electron (requires MSVC for `node-gyp`), Rust/Tauri (requires Cargo/Rustc), and C++/WinUI3.
- [ ] **Subsystem Decoupling:** Confirm that UI rendering, API routing, MIDI hardware I/O, action sequencing, and clock generation are strictly separated into dedicated layers (`src/core`, `src/adapters`, `src/engine`, `src/api`, `src/ui`).
- [ ] **Hardware Abstraction Layer (HAL):** Verify that `MidiAdapterBase` provides a clean contract allowing drop-in implementations for `WinMMMidiAdapter` and `VirtualMidiAdapter`, as well as future `CoreMidiAdapter` (macOS) and `AndroidMidiAdapter` (Android).
- [ ] **Inspect File:** `D:\Projects\MIDI\docs\ARCHITECTURE_AND_STACK_DECISION.md`

### Domain 2: Protocol Precision & Binary Encoding/Decoding
- [ ] **Program Change (PC):** Verify that `encode_program_change(ch, prog)` outputs `0xC0 | (ch-1)` and `prog` with strict boundary validation (Channels 1–16, Program 0–127).
- [ ] **Preset Numbering Display Transparency:** Verify that the system transparently toggles between 0-indexed (`0–127`) and 1-indexed (`1–128`) display modes without altering the underlying wire bytes.
- [ ] **Control Change (CC):** Verify `encode_control_change(ch, cc, val)` outputs `0xB0 | (ch-1)`, `cc`, and `val`. Check handling of standard CCs (CC 0 Bank MSB, CC 32 Bank LSB, CC 1 Mod, CC 11 Expr, CC 64 Sustain).
- [ ] **Bank Select:** Verify that Bank Select correctly orders CC 0 (MSB), CC 32 (LSB), followed by Program Change with customizable inter-packet pacing.
- [ ] **Real-Time Messages:** Verify byte encoding and decoding for Clock (`0xF8`), Start (`0xFA`), Continue (`0xFB`), and Stop (`0xFC`).
- [ ] **Inspect Files:** `D:\Projects\MIDI\src\core\codec.py` and `D:\Projects\MIDI\src\core\models.py`

### Domain 3: Timing Engine & Drift Elimination (24 PPQN Clock)
- [ ] **Monotonic Timebase:** Verify that `MidiClock` schedules on an isolated background thread using `time.perf_counter()`.
- [ ] **Windows Multimedia Resolution:** Verify that Windows Multimedia timer granularity is set to 1.0 ms via `timeBeginPeriod(1)` and properly released via `timeEndPeriod(1)`.
- [ ] **Drift Elimination Formula:** Verify that tick target instants are calculated as $t_N = t_0 + N \cdot \Delta t$ rather than relative sleep increments (`time.sleep(interval)`), guaranteeing **zero cumulative drift** over hours of continuous live playback.
- [ ] **Jitter & Telemetry:** Inspect the recorded timing benchmark data in `D:\Projects\MIDI\docs\TIMING_ANALYSIS_REPORT.md` (average jitter must be < 1.5 ms).
- [ ] **Tap Tempo Algorithm:** Verify that `tap_tempo()` implements sliding-window averaging with outlier rejection and timeout.
- [ ] **Inspect Files:** `D:\Projects\MIDI\src\engine\clock.py` and `D:\Projects\MIDI\docs\TIMING_ANALYSIS_REPORT.md`

### Domain 4: Touring Ergonomics & Stage Safety
- [ ] **Buffer Overrun Protection (Rate Limiting):** Verify that the continuous CC slider incorporates a throttle ceiling (25 ms) to prevent saturating 31,250 baud physical serial lines or USB endpoint queues.
- [ ] **Safe Panic Routine:** Verify that the Panic trigger transmits CC 123 (All Notes Off), CC 120 (All Sound Off), and CC 64 (Sustain Off) across channels without spraying unverified SysEx or dangerous reset packets (`0xFF`) that crash pedal firmware.
- [ ] **Emergency Transmission Stop:** Verify that Emergency Stop immediately terminates active clock threads and signals abort tokens to running macros.
- [ ] **Hardware Disconnect Recovery:** Verify that if an active port is unplugged mid-show, the application highlights it as "Disconnected" without crashing, and does not silently redirect traffic to an unintended port or replay stale commands upon reconnection.
- [ ] **Inspect Files:** `D:\Projects\MIDI\src\engine\actions.py`, `D:\Projects\MIDI\src\engine\manager.py`, and `D:\Projects\MIDI\docs\KNOWN_LIMITATIONS.md`

### Domain 5: Primary User Journeys (A through E)
- [ ] **Journey A (Connect & Send):** Verify the 5-step quick send workflow (Output &rarr; Channel &rarr; Command &rarr; Value &rarr; Send) with wire byte preview and honest unverified state banner.
- [ ] **Journey B (Control Parameter):** Verify CC controller selection, value slider, quick Min/Mid/Max presets, and friendly profile naming.
- [ ] **Journey C (Synchronise Tempo):** Verify BPM input, tap tempo, visual beat pulse LED, transport buttons (Start, Continue, Stop), and receiving pedal configuration disclaimers.
- [ ] **Journey D (Troubleshoot Connection):** Verify live diagnostic monitor with TX/RX tags, timestamp, channel, type, hex bytes, pause display (without stopping transmission), clear, smart clock collapsing, and JSON/CSV/Text export.
- [ ] **Journey E (Performance Actions):** Verify multi-step macro execution ("Solo Lead Boost") with explicit target destinations and pacing delays.
- [ ] **Inspect Files:** `D:\Projects\MIDI\src\ui\index.html`, `D:\Projects\MIDI\src\ui\js\app.js`, and `D:\Projects\MIDI\src\ui\css\style.css`

### Domain 6: Configuration Persistence & Atomic Storage
- [ ] **Schema Versioning:** Verify that configuration files declare `"schema_version": 1` and implement migration hooks.
- [ ] **Atomic File Writes:** Verify that `ConfigStore.save()` writes to a temporary file in the target directory and executes an atomic replace (`os.replace`) to prevent file corruption during accidental power loss or laptop battery depletion on stage.
- [ ] **Inspect File:** `D:\Projects\MIDI\src\engine\config_store.py`

### Domain 7: Automated Test Coverage & Verification
- [ ] **Unit Tests:** Execute `python D:\Projects\MIDI\tests\run_tests.py` and verify that all 23 unit tests pass cleanly:
  - `test_action_execution_order`, `test_action_missing_port_safeguard`
  - `test_virtual_adapter_lifecycle`, `test_virtual_disconnect_simulation`
  - `test_bpm_clamping`, `test_clock_execution_and_drift`, `test_tap_tempo_calculation`
  - `test_decode_channel_messages`, `test_decode_realtime`
  - `test_encode_bank_select`, `test_encode_control_change`, `test_encode_program_change`, `test_encode_realtime`
  - `test_action_save_and_delete`, `test_atomic_persistence`, `test_default_config_creation`
  - `test_7bit_boundaries`, `test_action_step_validation`, `test_channel_boundaries`, `test_preset_convention_display`
  - `test_clock_collapsing_filter`, `test_export_formats`, `test_ring_buffer_capacity`
- [ ] **Live Integration Tests:** Execute `python D:\Projects\MIDI\tests\test_e2e.py` and verify all live HTTP and WebSocket endpoints.
- [ ] **Inspect Files in:** `D:\Projects\MIDI\tests\`

### Domain 8: Future Hardware Integration & Platform Roadmap
- [ ] **Hardware Companion Specification:** Verify that the proposed foot controller companion protocol specifies framing (SysEx Universal Non-Realtime / Custom Manufacturer ID `0x00 0x02 0x7E`), device handshake (`0x7E` Inquiry), footswitch assignment (Tap, Hold, Double-Tap), and safe firmware update rollback partitions.
- [ ] **No Decorative Controls:** Verify that no fake or non-functional firmware update buttons exist in the UI prior to physical hardware availability.
- [ ] **Inspect File:** `D:\Projects\MIDI\docs\HARDWARE_INTEGRATION_ROADMAP.md`

---

## 3. Required Output Format for the Validating Agent

Your audit report must be structured as follows:

1. **Executive Verdict:** Overall Assessment (PASS / CONDITIONAL PASS / FAIL) with numerical score (0–100).
2. **Domain-by-Domain Audit Findings:** Explicit verification status (VERIFIED / DEFECT / OBSERVATION) for each of the 8 domains above, citing specific file paths and line ranges.
3. **Stage Readiness Assessment:** Critique from the perspective of a touring keyboardist or guitarist at a major international festival.
4. **Stress & Edge Case Evaluation:** Analysis of system resilience against hardware disconnection, rapid slider dragging, invalid inputs, and timing jitter under CPU load.
5. **Recommendations for Milestone 3 & 4:** Concrete technical recommendations for the physical hardware companion and CoreMIDI / Android ports.
