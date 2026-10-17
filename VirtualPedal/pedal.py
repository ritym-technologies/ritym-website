"""
PulseStage Virtual Effects-Pedal & Tempo Receiver.
A standalone, high-fidelity boutique multi-effects simulator for testing and practicing
MIDI Program Change, Bank Select, Parameter Control Change, and 24 PPQN Realtime Clock.
All animations and values are driven strictly by verified incoming MIDI bytes.
"""

import collections
import math
import os
from pathlib import Path
import subprocess
import sys
import time
import tkinter as tk
from tkinter import ttk, messagebox

# Ensure local imports work
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from midi_receiver import VirtualPedalReceiver, MidiPacket, MidiPortInfo

# Palette
BG_DARK = "#0d1117"
PANEL_BG = "#161b22"
PANEL_BORDER = "#30363d"
ACCENT_CYAN = "#38bdf8"
ACCENT_GREEN = "#10b981"
ACCENT_AMBER = "#f59e0b"
ACCENT_RED = "#ef4444"
TEXT_WHITE = "#f0f6fc"
TEXT_MUTED = "#8b949e"
SCREEN_BG = "#030712"
SCREEN_BORDER = "#1f2937"
SCREEN_TEXT = "#4ade80"

# Preset Names Simulation Map (Bank 0 / Common)
PRESET_NAMES = {
    0: "Clean Acoustic Simulator",
    1: "Warm Vintage Overdrive",
    2: "Tube Screamer Boost",
    3: "British High Gain Lead",
    4: "California Recto Rhythm",
    7: "Classic Rotary Speaker",
    11: "Liquid Analog Chorus",
    16: "Dynamic Stereo Flanger",
    20: "Optical Tremolo (Sync)",
    24: "Cosmic Tape Delay (24)",
    25: "Modulated Ambient Reverb",
    30: "Polyphonic Octave Generator",
    40: "Harmonic Pitch Shifter",
    64: "Studio Plate Reverb",
    100: "Extreme Fuzz & Octave",
    127: "Total Space Void Pad",
}


class RotaryKnob(tk.Canvas):
    """Interactive rotary knob that rotates strictly based on incoming MIDI CC."""
    def __init__(self, parent, label: str, cc_num: int, default_val: int = 0, size: int = 90):
        super().__init__(parent, width=size, height=size + 24, bg=PANEL_BG, highlightthickness=0)
        self.size = size
        self.label = label
        self.cc_num = cc_num
        self.value = default_val
        self.cx = size / 2
        self.cy = size / 2
        self.radius = (size / 2) - 8
        self.draw()

    def set_value(self, val: int):
        self.value = max(0, min(127, val))
        self.draw()

    def draw(self):
        self.delete("all")
        cx, cy, r = self.cx, self.cy, self.radius

        # Outer track
        self.create_arc(
            cx - r, cy - r, cx + r, cy + r,
            start=-45, extent=-270,
            outline="#2d3748", width=6, style="arc"
        )

        # Active fill track (from -225 deg to current val)
        val_frac = self.value / 127.0
        extent_deg = -270 * val_frac
        if abs(extent_deg) > 0:
            self.create_arc(
                cx - r, cy - r, cx + r, cy + r,
                start=-225, extent=extent_deg,
                outline=ACCENT_CYAN, width=6, style="arc"
            )

        # Center knob cap
        cap_r = r - 8
        self.create_oval(
            cx - cap_r, cy - cap_r, cx + cap_r, cy + cap_r,
            fill="#1f2937", outline="#374151", width=2
        )

        # Indicator pointer needle
        angle_deg = 225 - (270 * val_frac)
        angle_rad = math.radians(angle_deg)
        nx = cx + (cap_r - 4) * math.cos(angle_rad)
        ny = cy - (cap_r - 4) * math.sin(angle_rad)
        self.create_line(cx, cy, nx, ny, fill=ACCENT_CYAN, width=3, capstyle="round")

        # Value text in center
        self.create_text(cx, cy, text=str(self.value), fill=TEXT_WHITE, font=("Segoe UI", 10, "bold"))

        # Label text below
        self.create_text(
            cx, self.size + 10,
            text=f"{self.label}\n[CC {self.cc_num}]",
            fill=TEXT_MUTED, font=("Segoe UI", 8), justify="center"
        )


class VirtualPedalApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("PulseStage Stomp — Virtual Pedal & Tempo Receiver")
        self.root.geometry("1100x850")
        self.root.minsize(980, 750)
        self.root.configure(bg=BG_DARK)

        self.receiver = VirtualPedalReceiver(default_port_name="PulseStage Pedal Test")
        self.ports = []

        # Configuration & State
        self.listen_channel = tk.IntVar(value=1)  # 1-16 or 0 for OMNI
        self.display_convention = tk.StringVar(value="1-128")  # "1-128" or "0-127"
        self.current_program = 0
        self.bank_msb = None
        self.bank_lsb = None
        self.is_engaged = True  # Footswitch bypass state

        # Clock Telemetry
        self.clock_ticks = 0
        self.transport_running = False
        self.last_clock_time = 0.0
        self.clock_intervals = collections.deque(maxlen=24)  # 24 ticks = 1 quarter note
        self.measured_bpm = 0.0
        self.beat_count = 0

        # UI Elements
        self.knobs = {}
        self.build_ui()

        # Refresh and auto-connect
        self.refresh_ports()

        # Polling loop for thread-safe UI updates
        self.root.after(20, self.poll_midi)
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def refresh_ports(self):
        self.ports = self.receiver.list_ports()
        self.port_combo["values"] = [repr(p) for p in self.ports]
        if self.ports:
            # Prefer 'PulseStage Pedal Test', else 'PulseStage Keyboard', else first
            match_idx = 0
            for i, p in enumerate(self.ports):
                if "pedal" in p.name.lower():
                    match_idx = i
                    break
                elif "keyboard" in p.name.lower():
                    match_idx = i

            self.port_combo.current(match_idx)
            self.connect_port()
        else:
            self.lbl_status.config(
                text="No MIDI In ports found. Open loopMIDI to create 'PulseStage Pedal Test'.",
                fg=ACCENT_AMBER
            )

    def connect_port(self):
        idx = self.port_combo.current()
        if idx >= 0 and idx < len(self.ports):
            selected = self.ports[idx]
            success = self.receiver.open(selected)
            if success:
                self.lbl_status.config(
                    text=f"CONNECTED: Listening on '{selected.name}' via {self.receiver.driver_type}",
                    fg=ACCENT_GREEN
                )
                self.log_event("SYSTEM", f"Connected to input '{selected.name}'")
            else:
                self.lbl_status.config(
                    text=f"Failed to open port '{selected.name}'",
                    fg=ACCENT_RED
                )

    def open_loopmidi(self):
        path = Path(r"C:\Program Files (x86)\Tobias Erichsen\loopMIDI\loopMIDI.exe")
        if path.exists():
            subprocess.Popen([str(path)])
        else:
            messagebox.showinfo("loopMIDI", "Install loopMIDI, create port 'PulseStage Pedal Test', then Refresh.")

    def build_ui(self):
        # 1. Header Frame
        header = tk.Frame(self.root, bg=BG_DARK, padx=20, pady=10)
        header.pack(fill="x")

        title_frame = tk.Frame(header, bg=BG_DARK)
        title_frame.pack(side="left")
        tk.Label(
            title_frame, text="PULSESTAGE STOMP",
            font=("Segoe UI", 18, "bold"), fg=TEXT_WHITE, bg=BG_DARK
        ).pack(side="left")
        tk.Label(
            title_frame, text="  VIRTUAL HARDWARE RECEIVER & TEMPO LAB",
            font=("Segoe UI", 9, "bold"), fg=ACCENT_CYAN, bg=BG_DARK
        ).pack(side="left", pady=(5, 0))

        # Channel & Numbering selectors on top right
        ctrl_frame = tk.Frame(header, bg=BG_DARK)
        ctrl_frame.pack(side="right")

        tk.Label(ctrl_frame, text="Listen Ch:", font=("Segoe UI", 9), fg=TEXT_MUTED, bg=BG_DARK).pack(side="left", padx=4)
        ch_combo = ttk.Combobox(
            ctrl_frame, textvariable=self.listen_channel,
            values=[0] + list(range(1, 17)), width=4, state="readonly"
        )
        ch_combo.pack(side="left", padx=4)
        ch_combo.bind("<<ComboboxSelected>>", self.on_channel_change)

        tk.Label(ctrl_frame, text="Preset Num:", font=("Segoe UI", 9), fg=TEXT_MUTED, bg=BG_DARK).pack(side="left", padx=(12, 4))
        btn_num = tk.Button(
            ctrl_frame, textvariable=self.display_convention,
            command=self.toggle_display_convention,
            font=("Segoe UI", 9, "bold"), bg=PANEL_BG, fg=TEXT_WHITE,
            activebackground=PANEL_BORDER, activeforeground=TEXT_WHITE,
            relief="flat", bd=1, padx=8, pady=3, cursor="hand2"
        )
        btn_num.pack(side="left", padx=4)

        btn_panic = tk.Button(
            ctrl_frame, text="RESET PEDAL", command=self.reset_pedal,
            font=("Segoe UI", 9, "bold"), bg="#7f1d1d", fg="#fecaca",
            activebackground=ACCENT_RED, activeforeground=TEXT_WHITE,
            relief="flat", bd=0, padx=10, pady=4, cursor="hand2"
        )
        btn_panic.pack(side="left", padx=(12, 0))

        # 1B. Port Connection Bar
        port_bar = tk.Frame(self.root, bg=PANEL_BG, padx=20, pady=8)
        port_bar.pack(fill="x", padx=20, pady=(0, 6))

        tk.Label(port_bar, text="RECEIVE MIDI FROM:", font=("Segoe UI", 9, "bold"), fg=TEXT_MUTED, bg=PANEL_BG).pack(side="left", padx=(0, 10))
        self.port_combo = ttk.Combobox(port_bar, state="readonly", width=38)
        self.port_combo.pack(side="left", padx=(0, 8))
        self.port_combo.bind("<<ComboboxSelected>>", lambda e: self.connect_port())

        tk.Button(
            port_bar, text="Connect", command=self.connect_port,
            font=("Segoe UI", 9, "bold"), bg=ACCENT_CYAN, fg=BG_DARK,
            activebackground="#7dd3fc", relief="flat", padx=10, pady=2, cursor="hand2"
        ).pack(side="left", padx=4)

        tk.Button(
            port_bar, text="Refresh", command=self.refresh_ports,
            font=("Segoe UI", 9), bg="#2d3748", fg=TEXT_WHITE,
            activebackground="#4a5568", relief="flat", padx=8, pady=2, cursor="hand2"
        ).pack(side="left", padx=4)

        tk.Button(
            port_bar, text="Open loopMIDI", command=self.open_loopmidi,
            font=("Segoe UI", 9), bg="#2d3748", fg=TEXT_WHITE,
            activebackground="#4a5568", relief="flat", padx=8, pady=2, cursor="hand2"
        ).pack(side="left", padx=8)

        # Status subtitle
        self.lbl_status = tk.Label(
            self.root, text="Initializing MIDI port...",
            font=("Segoe UI", 9), fg=TEXT_MUTED, bg=BG_DARK, anchor="w", padx=20
        )
        self.lbl_status.pack(fill="x")

        # 2. Main Hardware Chassis
        chassis = tk.Frame(self.root, bg=PANEL_BG, bd=2, relief="groove", padx=16, pady=16)
        chassis.pack(fill="x", padx=20, pady=(6, 10))

        # --- A. Pedal Screen (Liquid Crystal / LED Display) ---
        screen_frame = tk.Frame(chassis, bg=SCREEN_BG, bd=3, relief="sunken", padx=16, pady=12)
        screen_frame.pack(fill="x")

        # Top row of screen: Bank & Preset Number
        screen_top = tk.Frame(screen_frame, bg=SCREEN_BG)
        screen_top.pack(fill="x")

        self.lbl_preset_num = tk.Label(
            screen_top, text="PRESET 001",
            font=("Consolas", 24, "bold"), fg=SCREEN_TEXT, bg=SCREEN_BG
        )
        self.lbl_preset_num.pack(side="left")

        self.lbl_raw_bytes = tk.Label(
            screen_top, text="RAW: -- --",
            font=("Consolas", 11, "bold"), fg="#93c5fd", bg="#1e293b", padx=8, pady=3
        )
        self.lbl_raw_bytes.pack(side="right")

        self.lbl_bank_info = tk.Label(
            screen_top, text="BANK: MSB -- | LSB --",
            font=("Consolas", 11), fg=ACCENT_AMBER, bg=SCREEN_BG, padx=12
        )
        self.lbl_bank_info.pack(side="right")

        # Middle row of screen: Preset Name
        self.lbl_preset_name = tk.Label(
            screen_frame, text="Clean Acoustic Simulator",
            font=("Segoe UI", 14), fg="#e2e8f0", bg=SCREEN_BG, anchor="w"
        )
        self.lbl_preset_name.pack(fill="x", pady=(4, 0))

        # Bottom row of screen: Wire details & instruction
        self.lbl_wire_detail = tk.Label(
            screen_frame,
            text="Wire Value: PC 0 (0x00) | Driven strictly by incoming MIDI bytes",
            font=("Segoe UI", 9), fg="#64748b", bg=SCREEN_BG, anchor="w"
        )
        self.lbl_wire_detail.pack(fill="x", pady=(4, 0))

        # --- B. Middle Controls: Footswitch & Tempo LED & Knobs ---
        mid_row = tk.Frame(chassis, bg=PANEL_BG, pady=14)
        mid_row.pack(fill="x")

        # Left Column: Footswitch & Beat Tempo Box
        left_box = tk.Frame(mid_row, bg=PANEL_BG, padx=10)
        left_box.pack(side="left", fill="y", padx=(0, 20))

        # Stomp Footswitch
        fs_frame = tk.LabelFrame(left_box, text="STOMPBOX BYPASS (CC 64)", font=("Segoe UI", 8, "bold"),
                                 fg=TEXT_MUTED, bg=PANEL_BG, padx=10, pady=8)
        fs_frame.pack(fill="x", pady=(0, 10))

        self.btn_footswitch = tk.Button(
            fs_frame, text="ENGAGED", command=self.toggle_footswitch,
            font=("Segoe UI", 11, "bold"), bg=ACCENT_GREEN, fg=BG_DARK,
            activebackground="#34d399", activeforeground=BG_DARK,
            relief="raised", bd=3, padx=16, pady=8, cursor="hand2"
        )
        self.btn_footswitch.pack()
        tk.Label(fs_frame, text="Value >= 64: Engaged\nValue < 64: Bypassed",
                 font=("Segoe UI", 7), fg=TEXT_MUTED, bg=PANEL_BG, justify="center").pack(pady=(4, 0))

        # Tempo & Beat Light Frame
        tempo_frame = tk.LabelFrame(left_box, text="TEMPO & BEAT RECEIVER (24 PPQN)",
                                    font=("Segoe UI", 8, "bold"), fg=TEXT_MUTED, bg=PANEL_BG, padx=10, pady=8)
        tempo_frame.pack(fill="x")

        t_row = tk.Frame(tempo_frame, bg=PANEL_BG)
        t_row.pack(fill="x")

        # Glowing beat light canvas
        self.cv_beat = tk.Canvas(t_row, width=32, height=32, bg=PANEL_BG, highlightthickness=0)
        self.cv_beat.pack(side="left", padx=4)
        self.beat_light_id = self.cv_beat.create_oval(4, 4, 28, 28, fill="#374151", outline="#4b5563", width=2)

        self.lbl_bpm = tk.Label(
            t_row, text="--.- BPM",
            font=("Consolas", 14, "bold"), fg=TEXT_WHITE, bg=PANEL_BG
        )
        self.lbl_bpm.pack(side="left", padx=8)

        self.lbl_transport = tk.Label(
            tempo_frame, text="TRANSPORT: STOPPED",
            font=("Segoe UI", 8, "bold"), fg=ACCENT_RED, bg=PANEL_BG
        )
        self.lbl_transport.pack(anchor="w", pady=(4, 0))

        self.lbl_ticks = tk.Label(
            tempo_frame, text="Ticks: 0 | Beats: 0",
            font=("Segoe UI", 8), fg=TEXT_MUTED, bg=PANEL_BG
        )
        self.lbl_ticks.pack(anchor="w")

        # Right Area: 4 Rotary Knobs
        knobs_frame = tk.LabelFrame(
            mid_row, text="TEST DEMO PARAMETERS (Drive strictly from PulseStage CC)",
            font=("Segoe UI", 8, "bold"), fg=ACCENT_CYAN, bg=PANEL_BG, padx=16, pady=8
        )
        knobs_frame.pack(side="left", fill="both", expand=True)

        k_grid = tk.Frame(knobs_frame, bg=PANEL_BG)
        k_grid.pack(expand=True)

        self.knobs[11] = RotaryKnob(k_grid, "Expression / Time", 11, default_val=64)
        self.knobs[11].grid(row=0, column=0, padx=12, pady=6)

        self.knobs[7] = RotaryKnob(k_grid, "Master Volume", 7, default_val=100)
        self.knobs[7].grid(row=0, column=1, padx=12, pady=6)

        self.knobs[12] = RotaryKnob(k_grid, "Param / Feedback", 12, default_val=40)
        self.knobs[12].grid(row=0, column=2, padx=12, pady=6)

        self.knobs[13] = RotaryKnob(k_grid, "Tone / Filter", 13, default_val=80)
        self.knobs[13].grid(row=0, column=3, padx=12, pady=6)

        # 3. Bottom Telemetry & Raw MIDI Inspection
        log_frame = tk.LabelFrame(
            self.root, text="INCOMING MIDI TELEMETRY & WIRE INSPECTOR (Hardware Evidence)",
            font=("Segoe UI", 9, "bold"), fg=TEXT_MUTED, bg=BG_DARK, padx=14, pady=8
        )
        log_frame.pack(fill="both", expand=True, padx=20, pady=(0, 14))

        # Table / Treeview
        columns = ("time", "delta", "ch", "type", "hex", "desc")
        self.tree = ttk.Treeview(log_frame, columns=columns, show="headings", height=8)
        self.tree.heading("time", text="Time (ms)")
        self.tree.heading("delta", text="Delta")
        self.tree.heading("ch", text="Ch")
        self.tree.heading("type", text="Message Type")
        self.tree.heading("hex", text="Raw Hex")
        self.tree.heading("desc", text="Decoded Behavior / Parameter")

        self.tree.column("time", width=85, anchor="center")
        self.tree.column("delta", width=70, anchor="center")
        self.tree.column("ch", width=45, anchor="center")
        self.tree.column("type", width=140, anchor="w")
        self.tree.column("hex", width=110, anchor="center")
        self.tree.column("desc", width=420, anchor="w")

        scrollbar = ttk.Scrollbar(log_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Telemetry footer actions
        bot_bar = tk.Frame(log_frame, bg=BG_DARK, pady=4)
        bot_bar.pack(fill="x", side="bottom")

        tk.Button(
            bot_bar, text="Clear Log", command=self.clear_log,
            font=("Segoe UI", 8), bg=PANEL_BG, fg=TEXT_MUTED, relief="flat", padx=8, pady=2
        ).pack(side="left")

        self.lbl_clock_info = tk.Label(
            bot_bar, text="Timing measured via Windows WinMM driver callback arrival times. Software telemetry; does not certify physical pedal hardware sync.",
            font=("Segoe UI", 8), fg=TEXT_MUTED, bg=BG_DARK
        )
        self.lbl_clock_info.pack(side="right")

    def toggle_display_convention(self):
        if self.display_convention.get() == "1-128":
            self.display_convention.set("0-127")
        else:
            self.display_convention.set("1-128")
        self.update_preset_display()

    def on_channel_change(self, event=None):
        ch = self.listen_channel.get()
        text = f"Ch {ch}" if ch > 0 else "OMNI (All Channels)"
        self.log_event("FILTER", f"Pedal listening filter changed to {text}")

    def reset_pedal(self):
        self.current_program = 0
        self.bank_msb = None
        self.bank_lsb = None
        self.clock_ticks = 0
        self.transport_running = False
        self.measured_bpm = 0.0
        self.beat_count = 0
        self.clock_intervals.clear()
        for k in self.knobs.values():
            k.set_value(64)
        self.update_preset_display()
        self.lbl_transport.config(text="TRANSPORT: STOPPED", fg=ACCENT_RED)
        self.lbl_bpm.config(text="--.- BPM")
        self.lbl_ticks.config(text="Ticks: 0 | Beats: 0")
        self.flash_beat_light(False)
        self.log_event("RESET", "Pedal parameters and clock reset to defaults.")

    def toggle_footswitch(self):
        self.is_engaged = not self.is_engaged
        self.update_footswitch_ui()
        self.log_event("LOCAL", f"Footswitch manually toggled to {'ENGAGED' if self.is_engaged else 'BYPASS'}")

    def update_footswitch_ui(self):
        if self.is_engaged:
            self.btn_footswitch.config(text="ENGAGED", bg=ACCENT_GREEN, activebackground="#34d399")
        else:
            self.btn_footswitch.config(text="BYPASS", bg="#374151", activebackground="#4b5563")

    def update_preset_display(self, raw_hex: str = ""):
        conv = self.display_convention.get()
        disp_num = (self.current_program + 1) if conv == "1-128" else self.current_program
        self.lbl_preset_num.config(text=f"PRESET {disp_num:03d}")

        name = PRESET_NAMES.get(self.current_program, f"User Patch {disp_num}")
        self.lbl_preset_name.config(text=name)

        if raw_hex:
            self.lbl_raw_bytes.config(text=f"RAW: {raw_hex}")

        msb_str = str(self.bank_msb) if self.bank_msb is not None else "--"
        lsb_str = str(self.bank_lsb) if self.bank_lsb is not None else "--"
        self.lbl_bank_info.config(text=f"BANK: MSB {msb_str} | LSB {lsb_str}")

        self.lbl_wire_detail.config(
            text=f"Wire Payload: Program {self.current_program} (0x{self.current_program:02X}) | Mode: {conv}"
        )

    def flash_beat_light(self, on: bool):
        color = ACCENT_AMBER if on else "#374151"
        self.cv_beat.itemconfig(self.beat_light_id, fill=color)

    def log_event(self, source: str, desc: str, raw_hex: str = "", ch: str = "-", delta: str = "-"):
        t_ms = f"{time.time() * 1000.0 % 100000:.1f}"
        item = self.tree.insert("", 0, values=(t_ms, delta, ch, source, raw_hex, desc))
        children = self.tree.get_children()
        if len(children) > 200:
            for c in children[200:]:
                self.tree.delete(c)

    def clear_log(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

    def poll_midi(self):
        """Processes incoming packets strictly from the MIDI queue."""
        packets = self.receiver.get_packets(max_count=100)
        current_time = time.perf_counter()

        for pkt in packets:
            self.process_packet(pkt, current_time)

        self.root.after(15, self.poll_midi)

    def process_packet(self, pkt: MidiPacket, current_time: float):
        raw = pkt.raw_bytes
        if not raw:
            return

        status = raw[0]
        hex_str = pkt.hex_str

        # 1. Realtime System Messages
        if status == 0xF8:  # Timing Clock (24 PPQN)
            self.clock_ticks += 1
            if self.last_clock_time > 0:
                delta = current_time - self.last_clock_time
                self.clock_intervals.append(delta)
                if len(self.clock_intervals) >= 12:
                    avg_interval = sum(self.clock_intervals) / len(self.clock_intervals)
                    if avg_interval > 0:
                        calc_bpm = 60.0 / (24.0 * avg_interval)
                        if 30 <= calc_bpm <= 350:
                            self.measured_bpm = calc_bpm
                            self.lbl_bpm.config(text=f"{self.measured_bpm:.1f} BPM")

            self.last_clock_time = current_time

            # Beat light: every 24 ticks (quarter note beat)
            if self.clock_ticks % 24 == 1:
                self.beat_count += 1
                self.flash_beat_light(True)
                self.root.after(60, lambda: self.flash_beat_light(False))

            self.lbl_ticks.config(text=f"Ticks: {self.clock_ticks:,} | Beats: {self.beat_count}")
            return

        elif status == 0xFA:  # Start
            self.transport_running = True
            self.lbl_transport.config(text="TRANSPORT: RUNNING (Start)", fg=ACCENT_GREEN)
            self.log_event("REALTIME", "Transport Start [0xFA]", hex_str)
            return

        elif status == 0xFB:  # Continue
            self.transport_running = True
            self.lbl_transport.config(text="TRANSPORT: RUNNING (Continue)", fg=ACCENT_GREEN)
            self.log_event("REALTIME", "Transport Continue [0xFB]", hex_str)
            return

        elif status == 0xFC:  # Stop
            self.transport_running = False
            self.lbl_transport.config(text="TRANSPORT: STOPPED [0xFC]", fg=ACCENT_RED)
            self.flash_beat_light(False)
            self.log_event("REALTIME", "Transport Stop [0xFC]", hex_str)
            return

        # 2. Channel Voice Messages
        ch = pkt.channel
        listen_ch = self.listen_channel.get()

        if listen_ch != 0 and ch != listen_ch:
            self.log_event(
                "IGNORED",
                f"Channel {ch} message ignored (Pedal set to Ch {listen_ch})",
                hex_str, ch=f"Ch {ch}"
            )
            return

        nibble = pkt.command_nibble
        d1 = pkt.data1
        d2 = pkt.data2

        if nibble == 0xC0:  # Program Change
            prog = d1 if d1 is not None else 0
            self.current_program = prog
            self.update_preset_display(raw_hex=hex_str)
            conv = self.display_convention.get()
            disp_num = (prog + 1) if conv == "1-128" else prog
            name = PRESET_NAMES.get(prog, f"Preset {disp_num}")
            self.log_event(
                "PROGRAM CHANGE",
                f"Switched to Preset {disp_num} ('{name}') [Raw PC: {prog}]",
                hex_str, ch=f"Ch {ch}"
            )

        elif nibble == 0xB0:  # Control Change
            cc = d1 if d1 is not None else 0
            val = d2 if d2 is not None else 0

            # Bank Select MSB (CC 0)
            if cc == 0:
                self.bank_msb = val
                self.update_preset_display()
                self.log_event("BANK SELECT", f"Bank MSB (CC 0) set to {val}", hex_str, ch=f"Ch {ch}")

            # Bank Select LSB (CC 32)
            elif cc == 32:
                self.bank_lsb = val
                self.update_preset_display()
                self.log_event("BANK SELECT", f"Bank LSB (CC 32) set to {val}", hex_str, ch=f"Ch {ch}")

            # Bypass Footswitch (CC 64 or CC 102)
            elif cc in (64, 102):
                self.is_engaged = (val >= 64)
                self.update_footswitch_ui()
                state_str = "ENGAGED" if self.is_engaged else "BYPASS"
                self.log_event("STOMP BYPASS", f"Footswitch set to {state_str} (val {val})", hex_str, ch=f"Ch {ch}")

            # Knobs mapped
            elif cc in self.knobs:
                self.knobs[cc].set_value(val)
                label = self.knobs[cc].label
                self.log_event("PARAM CONTROL", f"{label} [CC {cc}] -> {val}", hex_str, ch=f"Ch {ch}")

            else:
                self.log_event("UNMAPPED CC", f"Controller {cc} = {val}", hex_str, ch=f"Ch {ch}")

        elif nibble == 0x90:  # Note On
            note = d1 or 0
            vel = d2 or 0
            self.log_event("NOTE ON", f"Note {note} Velocity {vel}", hex_str, ch=f"Ch {ch}")

        elif nibble == 0x80:  # Note Off
            note = d1 or 0
            self.log_event("NOTE OFF", f"Note {note}", hex_str, ch=f"Ch {ch}")

        else:
            self.log_event("MIDI", f"Status 0x{status:02X} Data: {d1}, {d2}", hex_str, ch=f"Ch {ch}")

    def on_close(self):
        self.receiver.stop()
        self.root.destroy()


def main():
    root = tk.Tk()
    app = VirtualPedalApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
