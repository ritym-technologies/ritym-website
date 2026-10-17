"""
High-Throughput Diagnostic MIDI Monitor with Smart Dual-Ring Clock Isolation
Features:
- Dual-ring architecture: raw clocks are captured in a dedicated ring buffer,
  guaranteeing that 24 PPQN clock ticks NEVER evict meaningful PC, CC, Note, or SysEx diagnostic events.
- Telemetry counters for TX, RX, and Clock ticks.
- JSON, CSV, and text diagnostic export.
"""
import collections
import csv
import io
import json
import threading
import time
from typing import List, Optional, Dict, Any
from ..core.models import MidiMessage, MessageType, Direction


class MonitorFilter:
    def __init__(
        self,
        port_name: Optional[str] = None,
        channel: Optional[int] = None,
        direction: Optional[Direction] = None,
        message_type: Optional[MessageType] = None,
        show_raw_clock: bool = False,
    ):
        self.port_name = port_name
        self.channel = channel
        self.direction = direction
        self.message_type = message_type
        self.show_raw_clock = show_raw_clock

    def matches(self, msg: MidiMessage) -> bool:
        if msg.message_type == MessageType.CLOCK and not self.show_raw_clock:
            return False

        if self.port_name and msg.port_name != self.port_name:
            return False

        if self.channel is not None and msg.channel != self.channel:
            return False

        if self.direction and msg.direction != self.direction:
            return False

        if self.message_type and msg.message_type != self.message_type:
            return False

        return True


class MidiMonitor:
    def __init__(self, capacity: int = 1000):
        self.capacity = capacity
        # Primary diagnostic ring buffer (PC, CC, Notes, SysEx, Transport)
        self._buffer: collections.deque[MidiMessage] = collections.deque(maxlen=capacity)
        # Dedicated clock tick ring buffer (prevents clock eviction)
        self._clock_buffer: collections.deque[MidiMessage] = collections.deque(maxlen=capacity)
        self._lock = threading.Lock()
        self.is_paused: bool = False

        # Live telemetry aggregators
        self.clock_tick_counter: int = 0
        self.tx_counter: int = 0
        self.rx_counter: int = 0
        self.last_clock_timestamp: float = 0.0

    def record_message(self, msg: MidiMessage) -> None:
        with self._lock:
            # Update telemetry counters
            if msg.message_type == MessageType.CLOCK:
                self.clock_tick_counter += 1
                self.last_clock_timestamp = msg.timestamp_ms
                # Record to dedicated clock buffer; NEVER evicts primary diagnostic history!
                self._clock_buffer.append(msg)
                return
            elif msg.direction == Direction.TX:
                self.tx_counter += 1
            elif msg.direction == Direction.RX:
                self.rx_counter += 1

            # Append to primary diagnostic ring buffer
            self._buffer.append(msg)

    def get_messages(self, filter_obj: Optional[MonitorFilter] = None) -> List[MidiMessage]:
        with self._lock:
            diag_snapshot = list(self._buffer)
            clock_snapshot = list(self._clock_buffer)

        if not filter_obj or not filter_obj.show_raw_clock:
            # Default view: pure diagnostic events, 100% immune to clock eviction
            if not filter_obj:
                return diag_snapshot
            return [m for m in diag_snapshot if filter_obj.matches(m)]

        # If raw clock explicitly requested, combine both buffers sorted by timestamp
        combined = diag_snapshot + clock_snapshot
        combined.sort(key=lambda m: m.timestamp_ms)
        return [m for m in combined if filter_obj.matches(m)]

    def clear(self) -> None:
        with self._lock:
            self._buffer.clear()
            self._clock_buffer.clear()
            self.clock_tick_counter = 0
            self.tx_counter = 0
            self.rx_counter = 0

    def export_json(self) -> str:
        with self._lock:
            msgs = list(self._buffer)
        data = {
            "application": "PulseStage MIDI",
            "exported_at": time.time(),
            "total_messages": len(msgs),
            "clock_ticks_recorded": self.clock_tick_counter,
            "messages": [m.model_dump() for m in msgs],
        }
        return json.dumps(data, indent=2)

    def export_csv(self) -> str:
        with self._lock:
            msgs = list(self._buffer)

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["Timestamp_ms", "Direction", "Port", "Channel", "Type", "Data1", "Data2", "Hex", "Description"])

        for m in msgs:
            writer.writerow([
                f"{m.timestamp_ms:.2f}",
                m.direction.value,
                m.port_name,
                m.channel or "-",
                m.message_type.value,
                m.data1 if m.data1 is not None else "-",
                m.data2 if m.data2 is not None else "-",
                m.hex_string,
                m.friendly_text,
            ])

        return output.getvalue()

    def export_text(self) -> str:
        with self._lock:
            msgs = list(self._buffer)

        lines = [
            "=" * 78,
            " PULSESTAGE MIDI - DIAGNOSTIC TRAFFIC CAPTURE",
            f" Exported: {time.strftime('%Y-%m-%d %H:%M:%S')}",
            f" Total Events: {len(msgs)} | Clock Ticks: {self.clock_tick_counter}",
            "=" * 78,
            f"{'TIME (ms)':<12} | {'DIR':<4} | {'PORT':<20} | {'CH':<4} | {'HEX':<14} | DESCRIPTION",
            "-" * 78,
        ]

        for m in msgs:
            ch_str = str(m.channel) if m.channel else "-"
            lines.append(
                f"{m.timestamp_ms:<12.1f} | {m.direction.value:<4} | {m.port_name[:20]:<20} | {ch_str:<4} | {m.hex_string:<14} | {m.friendly_text}"
            )

        return "\n".join(lines)
