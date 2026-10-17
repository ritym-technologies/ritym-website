"""PulseStage Keyboard — local on-screen piano for Windows MIDI inputs."""
import tkinter as tk
from tkinter import ttk, messagebox
import subprocess
from pathlib import Path
from midi_backend import MidiOutput, KeyboardSession

BG = '#10151e'
PANEL = '#1b2330'
TEXT = '#ecf2f8'
MUTED = '#9aacc2'
ACCENT = '#36e0c4'
NAMES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
KEYS = ['a', 'w', 's', 'e', 'd', 'f', 't', 'g', 'y', 'h', 'u', 'j', 'k', 'o', 'l', 'p', 'semicolon']


def note_name(note):
    return f'{NAMES[note % 12]}{note // 12 - 1}'


class KeyboardApp:
    def __init__(self, root):
        self.root = root
        self.midi = MidiOutput()
        self.session = KeyboardSession(self.transmit)
        self.ports = []
        self.channel = tk.IntVar(value=1)
        self.velocity = tk.IntVar(value=100)
        self.expression = tk.IntVar(value=127)
        self.sustain = tk.BooleanVar(value=False)
        self.shift = 0
        self.mouse_down = False
        self.space_down = False
        self.release_jobs = {}
        self.messages = 0
        self.key_rects = {}
        self.key_bounds = []
        self.status = tk.StringVar(value='Choose a MIDI output and connect.')
        self.route_mode_text = tk.StringVar(value='Select a port to see routing instructions.')
        self.detail = tk.StringVar(value='Ready to play • MIDI only; no built-in sound')
        self.range_text = tk.StringVar()
        root.title('PulseStage Keyboard — Virtual MIDI Piano')
        root.geometry('1180x740')
        root.minsize(960, 700)
        root.configure(bg=BG)
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('TCombobox', fieldbackground=PANEL, background=PANEL,
                        foreground=TEXT, arrowcolor=ACCENT, padding=7)
        style.map('TCombobox', fieldbackground=[('readonly', PANEL)],
                  foreground=[('readonly', TEXT)])
        style.configure('TSpinbox', fieldbackground=PANEL, foreground=TEXT, padding=6)
        self.build()
        root.bind('<KeyPress>', self.key_press)
        root.bind('<KeyRelease>', self.key_release)
        root.bind('<FocusOut>', lambda event: root.after_idle(self.check_focus))
        root.bind_all('<ButtonRelease-1>', self.mouse_release, add='+')
        root.protocol('WM_DELETE_WINDOW', self.close)
        self.refresh()
        matches = [p for p in self.ports if p.name == 'PulseStage Keyboard']
        if len(matches) == 1:
            self.port_box.current(self.ports.index(matches[0]))
            self.connect()
        root.after(1500, self.watch_port)

    def label(self, parent, text, size=11, color=TEXT, **kwargs):
        return tk.Label(parent, text=text, bg=parent['bg'], fg=color,
                        font=('Segoe UI', size), **kwargs)

    def button(self, parent, text, command, accent=False):
        return tk.Button(parent, text=text, command=command,
                         bg=ACCENT if accent else '#293649', fg=BG if accent else TEXT,
                         activebackground='#78ebd8', activeforeground=BG,
                         relief='flat', bd=0, padx=16, pady=9, cursor='hand2',
                         font=('Segoe UI', 10, 'bold'))

    def show_routing_help(self):
        msg = (
            "HOW TO USE THIS KEYBOARD:\n\n"
            "1. TO TEST WITH PULSESTAGE (Control Mode):\n"
            "   • Virtual Keyboard: SEND MIDI TO -> 'PulseStage Keyboard'\n"
            "   • In PulseStage: Refresh -> set Input Source to 'PulseStage Keyboard'\n"
            "   • Result: Keys pressed increment PulseStage RX counter and show Note events in monitor!\n"
            "     (This is a silent digital control test. MIDI carries instructions, not audio sound).\n\n"
            "2. TO HEAR AUDIBLE PIANO SOUND (Sound Mode):\n"
            "   • Virtual Keyboard: SEND MIDI TO -> 'Microsoft GS Wavetable Synth'\n"
            "   • Result: You will hear actual acoustic piano sound through your PC speakers.\n"
            "     (Note: Because Windows Synth outputs audio to speakers, PulseStage monitor RX will stay 0).\n\n"
            "NOTE: PulseStage does not automatically duplicate input to output unless explicitly configured."
        )
        messagebox.showinfo("PulseStage Keyboard Routing Guide", msg)

    def build(self):
        top = tk.Frame(self.root, bg=BG)
        top.pack(fill='x', padx=28, pady=(21, 10))
        self.label(top, 'PulseStage Keyboard', 25).pack(side='left')
        self.label(top, 'VIRTUAL MIDI PIANO', 10, ACCENT).pack(side='left', padx=20, pady=(10, 0))
        self.button(top, 'Routing Help', self.show_routing_help).pack(side='right', padx=(10, 0))
        self.button(top, 'ALL NOTES OFF  ·  Esc', self.panic).pack(side='right')

        route = tk.Frame(self.root, bg=PANEL, padx=18, pady=14)
        route.pack(fill='x', padx=28)
        self.label(route, 'SEND MIDI TO', 9, MUTED).grid(row=0, column=0, sticky='w')
        self.port_box = ttk.Combobox(route, state='readonly', width=35)
        self.port_box.grid(row=1, column=0, padx=(0, 10), pady=(7, 0), sticky='ew')
        self.port_box.bind('<<ComboboxSelected>>', lambda event: self.connect())
        self.button(route, 'Refresh', self.refresh).grid(row=1, column=1, padx=5, pady=(7, 0))
        self.button(route, 'Connect', self.connect, True).grid(row=1, column=2, padx=5, pady=(7, 0))
        self.button(route, 'Open loopMIDI', self.open_loop).grid(row=1, column=3, padx=5, pady=(7, 0))
        route.columnconfigure(0, weight=1)

        # Clear routing guidance banner for non-musician owner & beginners
        self.route_banner = tk.Label(self.root, textvariable=self.route_mode_text, bg='#182333', fg='#38bdf8',
                                     font=('Segoe UI', 9, 'bold'), padx=14, pady=6, wraplength=1100, justify='left',
                                     bd=1, relief='solid')
        self.route_banner.pack(fill='x', padx=28, pady=(8, 4))

        tk.Label(self.root, textvariable=self.status, bg=BG, fg=ACCENT,
                 anchor='w', font=('Segoe UI', 10)).pack(fill='x', padx=30, pady=(4, 8))

        controls = tk.Frame(self.root, bg=BG)
        controls.pack(fill='x', padx=28)
        self.label(controls, 'Channel', 10, MUTED).pack(side='left', padx=(0, 8))
        self.channel_box = ttk.Combobox(controls, state='readonly', values=list(range(1, 17)),
                                       textvariable=self.channel, width=3)
        self.channel_box.pack(side='left')
        self.channel_box.bind('<<ComboboxSelected>>', lambda event: self.panic())
        self.label(controls, 'Velocity', 10, MUTED).pack(side='left', padx=(20, 4))
        self.scale(controls, self.velocity, 1, 127, 140).pack(side='left')
        self.sustain_button = self.button(controls, 'Sustain OFF  ·  Space', self.toggle_sustain)
        self.sustain_button.pack(side='left', padx=15)
        self.button(controls, '− Octave', lambda: self.octave(-12)).pack(side='right')
        self.button(controls, '+ Octave', lambda: self.octave(12)).pack(side='right', padx=8)

        rail = tk.Frame(self.root, bg=BG)
        rail.pack(fill='x', padx=30, pady=(11, 7))
        tk.Label(rail, textvariable=self.range_text, bg=BG, fg=MUTED,
                 font=('Segoe UI', 10)).pack(side='left')
        self.label(rail, 'Click keys or type A W S E D F T G Y H U J K O L P ;', 10, MUTED).pack(side='right')

        self.canvas = tk.Canvas(self.root, bg='#080c12', highlightthickness=0, height=245, takefocus=True)
        self.canvas.pack(fill='both', expand=True, padx=28)
        self.canvas.bind('<Configure>', lambda event: self.draw())
        self.canvas.bind('<ButtonPress-1>', self.mouse_press)
        self.canvas.bind('<B1-Motion>', self.mouse_move)

        footer = tk.Frame(self.root, bg=BG)
        footer.pack(fill='x', padx=28, pady=(12, 4))
        self.label(footer, 'Expression · CC11', 10, MUTED).pack(side='left')
        self.scale(footer, self.expression, 0, 127, 180).pack(side='left', padx=10)
        self.button(footer, 'Send CC11', self.send_expression).pack(side='left')
        tk.Label(footer, textvariable=self.detail, bg=BG, fg=TEXT,
                 font=('Consolas', 10), anchor='e').pack(side='right')
        self.label(self.root, 'In PulseStage: Refresh → Input Source → PulseStage Keyboard. Keep loopMIDI running.',
                   10, MUTED).pack(pady=(4, 14))
        self.update_range()

    def scale(self, parent, variable, low, high, length):
        return tk.Scale(parent, from_=low, to=high, variable=variable, orient='horizontal',
                        length=length, bg=BG, fg=TEXT, troughcolor=PANEL, highlightthickness=0,
                        activebackground=ACCENT, sliderrelief='flat', font=('Segoe UI', 9))

    def update_range(self):
        self.range_text.set(f'{note_name(48 + self.shift)} – {note_name(84 + self.shift)}   ·   Typing A = {note_name(60 + self.shift)}')

    def refresh(self):
        if self.midi.handle:
            try:
                self.panic(quiet=True)
                self.midi.close()
            except Exception as error:
                self.status.set(f'Could not release previous output: {error}')
                return
        self.ports = self.midi.ports()
        self.port_box['values'] = [f'{p.name}  [port {p.index}]' for p in self.ports]
        self.port_box.set('')
        matches = [i for i, p in enumerate(self.ports) if p.name == 'PulseStage Keyboard']
        if len(matches) == 1:
            self.port_box.current(matches[0])
        self.status.set('Select a port and Connect. Use PulseStage Keyboard for the virtual input.')
        self.route_mode_text.set('Select a port and click Connect to view routing guidance.')

    def connect(self):
        index = self.port_box.current()
        if index < 0:
            self.status.set('Create PulseStage Keyboard in loopMIDI, then Refresh and Connect.')
            self.route_mode_text.set('No port selected.')
            return
        try:
            if self.midi.handle:
                self.panic(quiet=True)
            self.midi.open(self.ports[index])
            port_name = self.midi.port.name
            self.status.set(f'Connected to {port_name} — ready to send notes')
            self.canvas.focus_set()

            # Beginner guidance distinguishing Sound vs Control
            lower_name = port_name.lower()
            if 'wavetable' in lower_name or 'synth' in lower_name:
                self.route_mode_text.set('🔊 SOUND AUDITION MODE: Notes play through Windows Synthesizer (audible piano). PulseStage RX stays 0 unless PulseStage listens to this synth.')
            elif 'keyboard' in lower_name or 'loop' in lower_name or 'test' in lower_name:
                self.route_mode_text.set('🎯 PULSESTAGE CONTROL MODE: Notes sent to virtual cable. In PulseStage, set INPUT SOURCE to \'' + port_name + '\' to see RX count rise. (Silent digital control; MIDI is instructions, not audio).')
            else:
                self.route_mode_text.set(f'Transmitting MIDI data to {port_name}. (Silent loopback unless an audio synthesizer is attached).')
        except Exception as error:
            self.status.set(f'Connection failed: {error}')
            self.route_mode_text.set(f'Error connecting to port: {error}')

    def transmit(self, packet):
        self.midi.send(packet)
        self.messages += 1
        self.detail.set(f'TX {self.messages}   ' + ' '.join(f'{value:02X}' for value in packet))

    def attempt(self, callback):
        try:
            callback()
        except Exception as error:
            self.status.set(f'MIDI error: {error}')
        self.paint()

    def press(self, source, note):
        self.attempt(lambda: self.session.press(source, note, self.channel.get(), self.velocity.get()))

    def release(self, source):
        self.attempt(lambda: self.session.release(source))

    def panic(self, quiet=False):
        self.mouse_down = False
        self.space_down = False
        for job in self.release_jobs.values():
            self.root.after_cancel(job)
        self.release_jobs.clear()
        try:
            if self.midi.handle:
                self.session.panic()
            else:
                self.session.held.clear()
            if not quiet:
                self.status.set('All notes released; sustain off.')
        except Exception as error:
            self.status.set(f'Note cleanup failed: {error}')
        self.sustain.set(False)
        self.sustain_button.configure(text='Sustain OFF  ·  Space', bg='#293649')
        self.paint()

    def toggle_sustain(self):
        desired = not self.sustain.get()
        try:
            self.transmit(bytes([0xB0 + self.channel.get() - 1, 64, 127 if desired else 0]))
            self.sustain.set(desired)
            self.sustain_button.configure(text=f'Sustain {"ON" if desired else "OFF"}  ·  Space',
                                           bg='#226254' if desired else '#293649')
            self.canvas.focus_set()
        except Exception as error:
            self.status.set(str(error))

    def send_expression(self):
        self.attempt(lambda: self.transmit(bytes([0xB0 + self.channel.get() - 1, 11, self.expression.get()])))

    def octave(self, delta):
        self.panic(quiet=True)
        self.shift = max(-24, min(24, self.shift + delta))
        self.update_range()
        self.draw()
        self.canvas.focus_set()

    def key_press(self, event):
        key = event.keysym.lower()
        if key == 'escape':
            self.panic()
            return 'break'
        if isinstance(event.widget, (ttk.Combobox, tk.Entry, tk.Spinbox, tk.Scale)):
            return
        if key in self.release_jobs:
            self.root.after_cancel(self.release_jobs.pop(key))
        if key == 'space':
            # Ignore repeat while held; release is handled like other typing keys.
            if not self.space_down:
                self.toggle_sustain()
                self.space_down = True
            return 'break'
        if key in KEYS:
            self.press('key:' + key, 60 + self.shift + KEYS.index(key))
            return 'break'

    def key_release(self, event):
        key = event.keysym.lower()
        if key not in KEYS and key != 'space':
            return
        if key in self.release_jobs:
            self.root.after_cancel(self.release_jobs[key])
        self.release_jobs[key] = self.root.after(12, lambda: self.finish_release(key))

    def finish_release(self, key):
        self.release_jobs.pop(key, None)
        if key == 'space':
            self.space_down = False
        else:
            self.release('key:' + key)

    def check_focus(self):
        if self.root.focus_displayof() is None:
            self.panic(quiet=True)

    def draw(self):
        self.canvas.delete('all')
        self.key_rects.clear()
        self.key_bounds = []
        low, high = 48 + self.shift, 84 + self.shift
        whites = [n for n in range(low, high + 1) if n % 12 not in (1, 3, 6, 8, 10)]
        width = max(self.canvas.winfo_width(), 500) / len(whites)
        height = max(self.canvas.winfo_height(), 200)
        typing = {60 + self.shift + i: (';' if key == 'semicolon' else key.upper()) for i, key in enumerate(KEYS)}
        for i, note in enumerate(whites):
            x = i * width
            self.key_rects[note] = self.canvas.create_rectangle(x + 1, 1, x + width - 1, height - 2,
                                        fill='#f3f0e7', outline='#a9b3be', width=1)
            self.key_bounds.append((note, x, 0, x + width, height))
            if note in typing:
                self.canvas.create_text(x + width / 2, height - 48, text=typing[note], fill='#6b798b', font=('Segoe UI', 11, 'bold'))
            self.canvas.create_text(x + width / 2, height - 24, text=note_name(note), fill='#283344', font=('Segoe UI', 10))
        for note in range(low, high + 1):
            if note % 12 not in (1, 3, 6, 8, 10):
                continue
            left = sum(n < note for n in whites) * width - width * .31
            right, bottom = left + width * .62, height * .62
            self.key_rects[note] = self.canvas.create_rectangle(left, 0, right, bottom,
                                        fill='#17202b', outline='#05080e', width=2)
            self.key_bounds.append((note, left, 0, right, bottom))
            self.canvas.create_line(left + 3, bottom - 7, right - 3, bottom - 7, fill='#344354', width=3)
            if note in typing:
                self.canvas.create_text((left + right) / 2, bottom - 25, text=typing[note], fill='#a5b4c8', font=('Segoe UI', 10))
        self.paint()

    def paint(self):
        active = {note for note, channel in self.session.held.values()}
        for note, rectangle in self.key_rects.items():
            self.canvas.itemconfigure(rectangle, fill=ACCENT if note in active else
                                      '#17202b' if note % 12 in (1, 3, 6, 8, 10) else '#f3f0e7')

    def hit(self, event):
        for note, x1, y1, x2, y2 in reversed(self.key_bounds):
            if x1 <= event.x < x2 and y1 <= event.y < y2:
                return note

    def mouse_press(self, event):
        self.canvas.focus_set()
        self.mouse_down = True
        self.mouse_move(event)

    def mouse_move(self, event):
        if self.mouse_down:
            note = self.hit(event)
            if note is None:
                self.release('mouse')
            else:
                self.press('mouse', note)

    def mouse_release(self, event):
        if self.mouse_down:
            self.mouse_down = False
            self.release('mouse')

    def watch_port(self):
        if self.midi.port:
            try:
                if self.midi.port not in self.midi.ports():
                    self.panic(quiet=True)
                    self.midi.close()
                    self.status.set('MIDI port disconnected. Reopen loopMIDI, then Refresh and Connect.')
                    self.route_mode_text.set('Port disconnected.')
            except Exception as error:
                self.status.set(f'Output disconnected: {error}')
        self.root.after(1500, self.watch_port)

    def open_loop(self):
        path = Path(r'C:\Program Files (x86)\Tobias Erichsen\loopMIDI\loopMIDI.exe')
        if path.exists():
            subprocess.Popen([str(path)])
        else:
            messagebox.showinfo('loopMIDI', 'Install loopMIDI, create PulseStage Keyboard, then Refresh.')

    def close(self):
        self.panic(quiet=True)
        try:
            self.midi.close()
        finally:
            self.root.destroy()


if __name__ == '__main__':
    root = tk.Tk()
    KeyboardApp(root)
    root.mainloop()
