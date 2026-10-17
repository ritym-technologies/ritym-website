# PulseStage MIDI: Architecture and Stack Decision

## 1. Stack Evaluation and Technology Comparison

Before finalizing the implementation stack, four competing approaches were evaluated against touring reliability, system prerequisites, audio/timing precision, and platform portability.

| Architecture Option | Windows MIDI API Coverage | Clock Scheduling Precision | Dependencies / Build Tools | Packaging & Installation | Score (1-10) | Final Decision |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Option A: Pure C++ / WinUI 3 (MSVC)** | Full WinMM & Windows.Devices.Midi | Sub-millisecond via `timeSetEvent` / multimedia timer | Requires Visual Studio, Windows SDK, MSVC C++ compiler (~15 GB) | Native MSIX / EXE | 6 / 10 | **Rejected:** Machine lacks MSVC/C++ compiler toolchain (`cl.exe`). High maintenance barrier. |
| **Option B: Node.js / Electron + node-midi** | Node native addon to RtMidi | V8 event loop jitter; requires multimedia timers via C++ | Requires Python, Visual C++ build tools for `node-gyp` native addon compilation | Electron packaging (~150MB bundle) | 5 / 10 | **Rejected:** `node-gyp` fails without native C++ compiler on host. Significant memory footprint. |
| **Option C: Rust + Tauri + midir** | Native Windows WinMM | Excellent RT thread capability | Requires Rust toolchain (`rustc`, `cargo`), MSVC build tools | Small native binary | 5 / 10 | **Rejected:** Cargo/Rust is not installed on host machine. |
| **Option D: Python Core Engine + Native WinMM (ctypes) + FastAPI / WebSocket + Touring Stage Web App (Edge/Chrome App Mode)** | Complete direct access to `winmm.dll` via `ctypes` without compiler | Sub-millisecond precision with `time.perf_counter()` + `timeBeginPeriod(1)` on a dedicated OS worker thread | Zero C++ compiler needed. Uses pre-installed Python 3.12, FastAPI, Uvicorn, WebSockets. | Single double-click `.bat` launcher; standalone frameless app window via Edge/Chrome | **9.5 / 10** | **SELECTED** |

### Why Option D Was Selected

1. **Deterministic, Zero-Compile Windows Multimedia Access:**  
   Windows provides `winmm.dll` as a core system library on every Windows machine since Windows 95. Python's `ctypes` interacts directly with `midiOutOpen`, `midiOutShortMsg`, `midiInOpen`, and `midiInStart` with zero compiler requirements and sub-millisecond execution overhead.
2. **Decoupled Timing Thread:**  
   The MIDI Clock generator executes on an isolated native OS daemon thread. Python sets the Windows Multimedia Timer resolution to 1 ms (`timeBeginPeriod(1)`) and computes intervals using monotonic `time.perf_counter()`. Cumulative drift is eliminated by scheduling tick $N$ at $t_N = t_0 + N \cdot \Delta t$.
3. **Decoupled UI & Native Presentation:**  
   The UI runs in a dedicated application window via Microsoft Edge or Google Chrome `--app` mode, delivering hardware-accelerated 60/120 FPS rendering, zero-lag CSS animations, and instant responsive feedback without bloating memory.
4. **Cross-Platform Abstraction:**  
   The adapter layer (`MidiAdapterBase`) cleanly separates platform drivers from core message encoding, scheduling, and state persistence. macOS (CoreMIDI) and Android (`android.media.midi`) adapters can be dropped in without changing the core engine.

---

## 2. Architectural Subsystem Separation

```
+-------------------------------------------------------------------------------+
|                       Presentation Layer (Stage UI)                          |
|  - High-Contrast Stage Theme  - 5-Step Send Workflow  - Live Parameter Slider |
|  - Pulsing Clock Visualizer   - Diagnostic Monitor    - Saved Action Trigger  |
+---------------------------------------+---------------------------------------+
                                        | WebSocket (Bi-directional) & REST
+---------------------------------------v---------------------------------------+
|                       Application Core / API Service                          |
|  - WebSocket Event Broadcaster (TX/RX/Status)   - Schema-Versioned Config     |
|  - Action Sequence Orchestrator                 - Diagnostic Export Formatter |
+---------------------------------------+---------------------------------------+
            |                           |                           |
+-----------v-----------+   +-----------v-----------+   +-----------v-----------+
|      MIDI Clock       |   |   Diagnostic Monitor  |   |    Action Engine      |
| - 24 PPQN Generator   |   | - Bounded Ring Buffer |   | - Multi-step Macros   |
| - Drift Compensator   |   | - Smart Clock Filter  |   | - Inter-step Pacing   |
| - Transport Controls  |   | - Hex & Text Decoders |   | - Safety Cancellation |
+-----------+-----------+   +-----------+-----------+   +-----------+-----------+
            |                           |                           |
+-----------v---------------------------v---------------------------v-----------+
|                          MIDI Adapter Layer (HAL)                             |
|  +------------------------------+   +--------------------------------------+  |
|  |   Windows WinMM Adapter      |   |       Virtual / Test Adapter         |  |
|  | - winmm.dll via ctypes       |   | - Headless Simulation Engine         |  |
|  | - Real-time In/Out Callbacks |   | - Automated Test Harness             |  |
|  +------------------------------+   +--------------------------------------+  |
+-------------------------------------------------------------------------------+
```

---

## 3. Reliability and Fault-Tolerance Safeguards

1. **Buffer Overrun Protection (Rate Limiting):**  
   Continuous slider adjustments throttle Control Change updates to a configurable minimum interval (25 ms) to prevent saturating physical MIDI 31,250 baud serial buffers or USB endpoint queues.
2. **Safe Panic Implementation:**  
   Sends CC 123 (All Notes Off) followed by CC 120 (All Sound Off) and CC 64 (Sustain Off = 0). Does not transmit arbitrary raw reset bytes (`0xFF`) or undefined SysEx dumps that could crash external pedal firmware.
3. **Emergency Transmission Halt:**  
   Immediately terminates the MIDI Clock thread and signals cancellation to any active multi-command action sequence.
4. **Device Disconnection Recovery:**  
   Port polling detects disconnected hardware within 1.5 seconds. If a target port drops, running actions fail gracefully with an explicit UI notification; reconnecting restores readiness without replaying stale commands.
