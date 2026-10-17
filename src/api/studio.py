"""Integrated test instruments. Receivers change only on actual MIDI input."""
from collections import deque
import statistics
import sys
import threading
import time
from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

KEYBOARD_PORT = 'PulseStage Keyboard'
PEDAL_PORT = 'PulseStage Pedal Test'
INTERNAL_KEYBOARD_PORT = 'PulseStage Practice Keybed [Internal]'
INTERNAL_PEDAL_PORT = 'PulseStage Reference Pedal [Internal]'


class PedalState:
    def __init__(self):
        self.lock = threading.Lock()
        self.events = deque(maxlen=96)
        self.intervals = deque(maxlen=96)
        self.program = None
        self.msb = self.lsb = 0
        self.cc = {11: 0, 7: 0, 12: 0, 13: 0, 64: 0}
        self.transport = 'STOPPED'
        self.ticks = self.count = 0
        self.last_tick = None
        self.sequence = 0

    def receive(self, data, channel=0, now=None):
        if not data:
            return
        now = time.perf_counter() if now is None else now
        status = data[0]
        ch = (status & 15) + 1 if status < 0xF0 else None
        if ch and channel and ch != channel:
            return
        with self.lock:
            self.count += 1
            self.sequence += 1
            if status == 0xF8:
                if self.last_tick is not None:
                    interval = (now - self.last_tick) * 1000
                    if 0 < interval < 1000:
                        self.intervals.append(interval)
                    else:
                        self.intervals.clear()
                self.last_tick = now
                self.ticks += 1
                return
            if status in (0xFA, 0xFB, 0xFC):
                self.transport = {0xFA: 'RUNNING', 0xFB: 'RUNNING', 0xFC: 'STOPPED'}[status]
                if status == 0xFA:
                    self.ticks = 0
                    self.intervals.clear()
                    self.last_tick = None
            elif status & 0xF0 == 0xC0 and len(data) == 2:
                self.program = data[1]
            elif status & 0xF0 == 0xB0 and len(data) == 3:
                if data[1] in self.cc:
                    self.cc[data[1]] = data[2]
                if data[1] == 0:
                    self.msb = data[2]
                if data[1] == 32:
                    self.lsb = data[2]
            self.events.append({'seq': self.sequence, 'bytes': list(data), 'channel': ch,
                                'time_ms': time.time() * 1000})

    def snapshot(self):
        with self.lock:
            fresh = self.last_tick is not None and time.perf_counter() - self.last_tick < 2
            mean = statistics.mean(self.intervals) if len(self.intervals) >= 24 and fresh else None
            return {'program': self.program, 'bank_msb': self.msb, 'bank_lsb': self.lsb,
                    'cc': dict(self.cc), 'transport': self.transport, 'ticks': self.ticks,
                    'received': self.count, 'sequence': self.sequence,
                    'measured_bpm': round(60000 / (24 * mean), 2) if mean else None,
                    'intervals_ms': list(self.intervals), 'events': list(self.events),
                    'clock_present': fresh}


class StudioRack:
    def __init__(self, enabled=True, adapter=None, transport_mode=None):
        self.enabled = enabled and sys.platform == 'win32'
        self.adapter = adapter
        if transport_mode is None:
            self.transport_mode = 'loopmidi' if adapter is not None else 'internal'
        else:
            self.transport_mode = transport_mode
        self.internal_input_cb = None
        self.io_lock = threading.RLock()
        self.keyboard_id = self.pedal_id = None
        self.keyboard_port_name = INTERNAL_KEYBOARD_PORT if transport_mode == 'internal' else KEYBOARD_PORT
        self.pedal_port_name = INTERNAL_PEDAL_PORT if transport_mode == 'internal' else PEDAL_PORT
        self.pedal_channel = 0
        self.notes = set()
        self.pedal = PedalState()
        self.last_heartbeat = time.monotonic()
        self.stop_event = threading.Event()
        self.worker = None

    def detect_loopmidi(self) -> bool:
        if not self.enabled and self.adapter is None:
            return False
        try:
            adapter = self.get_adapter()
            out_names = {p.name for p in adapter.get_output_ports()}
            in_names = {p.name for p in adapter.get_input_ports()}
            return KEYBOARD_PORT in out_names and PEDAL_PORT in in_names
        except Exception:
            return False

    def set_mode(self, mode: str):
        if mode not in ('internal', 'loopmidi'):
            raise ValueError(f"Unknown transport mode: {mode}")
        with self.io_lock:
            self.release_notes()
            if self.keyboard_id and self.adapter and self.transport_mode == 'loopmidi':
                self.adapter.close_output(self.keyboard_id)
            if self.pedal_id and self.adapter and self.transport_mode == 'loopmidi':
                self.adapter.close_input(self.pedal_id)
            self.keyboard_id = None
            self.pedal_id = None
            self.transport_mode = mode
            self.keyboard_port_name = INTERNAL_KEYBOARD_PORT if mode == 'internal' else KEYBOARD_PORT
            self.pedal_port_name = INTERNAL_PEDAL_PORT if mode == 'internal' else PEDAL_PORT
        return self.state()

    def get_adapter(self):
        if not self.enabled and self.adapter is None:
            raise RuntimeError('Integrated instruments require native Windows mode, without --virtual.')
        if self.adapter is None:
            from ..adapters.winmm_adapter import WinMMMidiAdapter
            self.adapter = WinMMMidiAdapter()
        self.adapter.refresh_ports()
        return self.adapter

    def connect(self, instrument):
        with self.io_lock:
            if not self.enabled and self.adapter is None:
                raise RuntimeError('Integrated instruments require native Windows mode, without --virtual.')

            if self.transport_mode == 'internal':
                if instrument == 'keyboard':
                    self.keyboard_id = 'internal_keyboard'
                    self.keyboard_port_name = INTERNAL_KEYBOARD_PORT
                    self.last_heartbeat = time.monotonic()
                    if self.worker is None:
                        self.worker = threading.Thread(target=self.watchdog, daemon=True)
                        self.worker.start()
                else:
                    self.pedal_id = 'internal_pedal'
                    self.pedal_port_name = INTERNAL_PEDAL_PORT
                    self.pedal = PedalState()
                return self.state()

            # loopMIDI transport mode
            adapter = self.get_adapter()
            if instrument == 'keyboard':
                ports = [p for p in adapter.get_output_ports() if p.name == KEYBOARD_PORT]
                if len(ports) != 1:
                    raise RuntimeError(f'Create exactly one \u201c{KEYBOARD_PORT}\u201d port in loopMIDI and keep it running, or switch to Internal Practice transport.')
                if self.keyboard_id:
                    self.release_notes()
                    adapter.close_output(self.keyboard_id)
                self.keyboard_id = None
                if not adapter.open_output(ports[0].id):
                    raise RuntimeError('Keyboard output could not be opened. Check loopMIDI and other MIDI clients.')
                self.keyboard_id = ports[0].id
                self.keyboard_port_name = KEYBOARD_PORT
                self.last_heartbeat = time.monotonic()
                if self.worker is None:
                    self.worker = threading.Thread(target=self.watchdog, daemon=True)
                    self.worker.start()
            else:
                ports = [p for p in adapter.get_input_ports() if p.name == PEDAL_PORT]
                if len(ports) != 1:
                    raise RuntimeError(f'Create exactly one \u201c{PEDAL_PORT}\u201d port in loopMIDI and keep it running, or switch to Internal Practice transport.')
                if self.pedal_id:
                    adapter.close_input(self.pedal_id)
                self.pedal_id = None
                self.pedal = PedalState()
                if not adapter.open_input(ports[0].id, lambda pid, data, ts: self.pedal.receive(data, self.pedal_channel)):
                    raise RuntimeError('Pedal input is busy or unavailable. Close its standalone receiver and retry.')
                self.pedal_id = ports[0].id
                self.pedal_port_name = PEDAL_PORT
        return self.state()

    def note(self, note, channel, velocity, on):
        with self.io_lock:
            if not self.keyboard_id:
                raise RuntimeError('Connect the keybed first.')
            target = (channel, note)
            if on and target in self.notes:
                return
            if not on and target not in self.notes:
                return

            packet = bytes([(0x90 if on else 0x80) + channel - 1, note, velocity if on else 0])

            if self.transport_mode == 'internal':
                if self.internal_input_cb:
                    self.internal_input_cb("internal_keyboard", packet, time.time() * 1000)
                if on:
                    self.notes.add(target)
                else:
                    self.notes.discard(target)
                self.last_heartbeat = time.monotonic()
                return

            if not self.adapter.send_bytes(self.keyboard_id, packet):
                raise RuntimeError('The keyboard driver rejected the note. Reconnect the keybed.')
            if on:
                self.notes.add(target)
            else:
                self.notes.discard(target)
            self.last_heartbeat = time.monotonic()

    def release_notes(self):
        with self.io_lock:
            failed = False
            if self.keyboard_id:
                channels = {channel for channel, note in self.notes}
                if self.transport_mode == 'internal':
                    if self.internal_input_cb:
                        for ch, note in list(self.notes):
                            self.internal_input_cb("internal_keyboard", bytes([0x80 + ch - 1, note, 0]), time.time() * 1000)
                        for channel in channels:
                            self.internal_input_cb("internal_keyboard", bytes([0xB0 + channel - 1, 64, 0]), time.time() * 1000)
                            self.internal_input_cb("internal_keyboard", bytes([0xB0 + channel - 1, 123, 0]), time.time() * 1000)
                    self.notes.clear()
                    return

                for ch, note in list(self.notes):
                    failed |= not self.adapter.send_bytes(self.keyboard_id, bytes([0x80 + ch - 1, note, 0]))
                for channel in channels:
                    failed |= not self.adapter.send_bytes(self.keyboard_id, bytes([0xB0 + channel - 1, 64, 0]))
                    failed |= not self.adapter.send_bytes(self.keyboard_id, bytes([0xB0 + channel - 1, 123, 0]))
            self.notes.clear()
            if failed:
                raise RuntimeError('Some note releases were rejected by the driver. Reconnect the keybed.')

    def watchdog(self):
        while not self.stop_event.wait(1):
            with self.io_lock:
                if self.notes and time.monotonic() - self.last_heartbeat > 5:
                    try:
                        self.release_notes()
                    except RuntimeError:
                        pass

    def state(self):
        return {
            'keyboard_connected': bool(self.keyboard_id),
            'keyboard_port': self.keyboard_port_name,
            'pedal_connected': bool(self.pedal_id),
            'pedal_port': self.pedal_port_name,
            'pedal_channel': self.pedal_channel,
            'held_notes': len(self.notes),
            'pedal': self.pedal.snapshot(),
            'native_enabled': self.enabled,
            'transport_mode': self.transport_mode,
            'loopmidi_detected': self.detect_loopmidi()
        }

    def close(self):
        self.stop_event.set()
        if self.worker:
            self.worker.join(timeout=1.5)
        with self.io_lock:
            try:
                self.release_notes()
            except RuntimeError:
                pass
            if self.adapter:
                self.adapter.close_all()
            self.keyboard_id = self.pedal_id = None


class NoteRequest(BaseModel):
    note: int = Field(ge=0, le=127)
    channel: int = Field(default=1, ge=1, le=16)
    velocity: int = Field(default=100, ge=1, le=127)
    on: bool


class PedalChannel(BaseModel):
    channel: int = Field(ge=0, le=16)


class TransportModeRequest(BaseModel):
    mode: str = Field(pattern='^(internal|loopmidi)$')


def studio_routes(rack):
    router = APIRouter(prefix='/api/studio')

    def run(function):
        try:
            return function()
        except (RuntimeError, OSError) as error:
            raise HTTPException(status_code=409, detail=str(error)) from error

    @router.get('/state')
    def state():
        return rack.state()

    @router.post('/mode')
    def set_mode(request: TransportModeRequest):
        return run(lambda: rack.set_mode(request.mode))

    @router.post('/connect/{instrument}')
    def connect(instrument: str):
        if instrument not in ('keyboard', 'pedal'):
            raise HTTPException(404, 'Unknown instrument')
        return run(lambda: rack.connect(instrument))

    @router.post('/note')
    def note(request: NoteRequest):
        run(lambda: rack.note(request.note, request.channel, request.velocity, request.on))
        return {'sent': True}

    @router.post('/release')
    def release():
        run(rack.release_notes)
        return {'released': True}

    @router.post('/heartbeat')
    def heartbeat():
        rack.last_heartbeat = time.monotonic()
        return {'alive': True}

    @router.post('/pedal-channel')
    def channel(request: PedalChannel):
        rack.pedal_channel = request.channel
        rack.pedal = PedalState()
        return rack.state()

    return router
