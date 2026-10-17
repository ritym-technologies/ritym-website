"""
Device Connection Lifecycle, Unique Identity, Hot-Plug Detection, and Port Preferences
"""
import sys
import threading
import time
from typing import Callable, Dict, List, Optional, Set
from ..adapters.base import MidiAdapterBase, MidiPortInfo, PortDirection
from ..adapters.virtual_adapter import VirtualMidiAdapter

# Safe conditional import of WinMM adapter (Windows only)
if sys.platform == "win32":
    try:
        from ..adapters.winmm_adapter import WinMMMidiAdapter
    except Exception:
        WinMMMidiAdapter = None
else:
    WinMMMidiAdapter = None


class DeviceManager:
    def __init__(
        self,
        use_virtual: bool = False,
        disconnect_callback: Optional[Callable[[str], None]] = None,
    ):
        self._disconnect_cb = disconnect_callback

        if use_virtual or WinMMMidiAdapter is None:
            self.adapter: MidiAdapterBase = VirtualMidiAdapter()
            self.is_virtual = True
        else:
            self.adapter = WinMMMidiAdapter()
            self.is_virtual = False

        self._internal_rack = None
        self.selected_output_name: Optional[str] = None
        self.selected_output_id: Optional[str] = None
        self.selected_input_name: Optional[str] = None
        self.selected_input_id: Optional[str] = None

        self._hotplug_thread: Optional[threading.Thread] = None
        self._stop_hotplug = threading.Event()
        self._lock = threading.Lock()

        self.start_hotplug_monitor()

    def set_internal_rack(self, rack):
        self._internal_rack = rack

    def get_outputs(self) -> List[MidiPortInfo]:
        with self._lock:
            ports = list(self.adapter.get_output_ports())
            if self._internal_rack and getattr(self._internal_rack, 'transport_mode', None) == 'internal':
                pedal_name = getattr(self._internal_rack, 'pedal_port_name', 'PulseStage Reference Pedal [Internal]')
                ports.append(MidiPortInfo(id="internal_pedal", name=pedal_name, direction=PortDirection.OUTPUT))
            return ports

    def get_inputs(self) -> List[MidiPortInfo]:
        with self._lock:
            ports = list(self.adapter.get_input_ports())
            if self._internal_rack and getattr(self._internal_rack, 'transport_mode', None) == 'internal':
                key_name = getattr(self._internal_rack, 'keyboard_port_name', 'PulseStage Practice Keybed [Internal]')
                ports.append(MidiPortInfo(id="internal_keyboard", name=key_name, direction=PortDirection.INPUT))
            return ports

    def select_output(self, port_name: str) -> bool:
        """Selects and opens output port by name, storing unique port_id."""
        with self._lock:
            if self._internal_rack and getattr(self._internal_rack, 'transport_mode', None) == 'internal':
                if port_name == getattr(self._internal_rack, 'pedal_port_name', None):
                    self.selected_output_name = port_name
                    self.selected_output_id = "internal_pedal"
                    return True

            ports = self.adapter.get_output_ports()
            for p in ports:
                if p.name == port_name:
                    if self.adapter.open_output(p.id):
                        self.selected_output_name = port_name
                        self.selected_output_id = p.id
                        return True
            return False

    def deselect_output(self) -> None:
        """Explicitly closes and deselects the current output port."""
        with self._lock:
            if self.selected_output_id and self.selected_output_id != "internal_pedal":
                self.adapter.close_output(self.selected_output_id)
            self.selected_output_name = None
            self.selected_output_id = None

    def select_input(self, port_name: str, callback) -> bool:
        """Selects and opens input port by name, closing any prior input."""
        with self._lock:
            # Close prior input if different
            if self.selected_input_id and self.selected_input_id != "internal_keyboard":
                self.adapter.close_input(self.selected_input_id)
                self.selected_input_name = None
                self.selected_input_id = None

            if self._internal_rack and getattr(self._internal_rack, 'transport_mode', None) == 'internal':
                if port_name == getattr(self._internal_rack, 'keyboard_port_name', None):
                    self.selected_input_name = port_name
                    self.selected_input_id = "internal_keyboard"
                    self._internal_rack.internal_input_cb = callback
                    return True

            ports = self.adapter.get_input_ports()
            for p in ports:
                if p.name == port_name:
                    if self.adapter.open_input(p.id, callback):
                        self.selected_input_name = port_name
                        self.selected_input_id = p.id
                        return True
            return False

    def deselect_input(self) -> None:
        """Explicitly closes and deselects the current input port."""
        with self._lock:
            if self.selected_input_id and self.selected_input_id != "internal_keyboard":
                self.adapter.close_input(self.selected_input_id)
            if self._internal_rack:
                self._internal_rack.internal_input_cb = None
            self.selected_input_name = None
            self.selected_input_id = None

    def ensure_output_open(self, port_name: str) -> bool:
        """Ensures that an enumerated output port is opened for sending."""
        with self._lock:
            if self._internal_rack and getattr(self._internal_rack, 'transport_mode', None) == 'internal':
                if port_name == getattr(self._internal_rack, 'pedal_port_name', None):
                    return True

            ports = self.adapter.get_output_ports()
            for p in ports:
                if p.name == port_name:
                    return self.adapter.open_output(p.id)
            return False

    def send_to_port(self, port_name: str, data: bytes) -> bool:
        with self._lock:
            if self._internal_rack and getattr(self._internal_rack, 'transport_mode', None) == 'internal':
                if port_name == getattr(self._internal_rack, 'pedal_port_name', None):
                    self._internal_rack.pedal.receive(data, getattr(self._internal_rack, 'pedal_channel', 0))
                    return True

            ports = self.adapter.get_output_ports()
            for p in ports:
                if p.name == port_name:
                    # Dynamically open unselected output destinations for multi-target actions
                    if hasattr(self.adapter, "_open_outputs") and p.id not in self.adapter._open_outputs:
                        self.adapter.open_output(p.id)
                    return self.adapter.send_bytes(p.id, data)
            return False

    def send_to_selected_output(self, data: bytes) -> bool:
        if not self.selected_output_name:
            return False
        return self.send_to_port(self.selected_output_name, data)

    def is_port_connected(self, port_name: str) -> bool:
        with self._lock:
            if self._internal_rack and getattr(self._internal_rack, 'transport_mode', None) == 'internal':
                if port_name in (getattr(self._internal_rack, 'pedal_port_name', None), getattr(self._internal_rack, 'keyboard_port_name', None)):
                    return True
            ports = self.adapter.get_output_ports() + self.adapter.get_input_ports()
            return any(p.name == port_name for p in ports)

    def start_hotplug_monitor(self):
        self._stop_hotplug.clear()
        self._hotplug_thread = threading.Thread(target=self._hotplug_loop, daemon=True)
        self._hotplug_thread.start()

    def stop_hotplug_monitor(self):
        self._stop_hotplug.set()
        if self._hotplug_thread and self._hotplug_thread.is_alive():
            self._hotplug_thread.join(timeout=0.5)

    def _hotplug_loop(self):
        while not self._stop_hotplug.is_set():
            time.sleep(0.5)
            try:
                self.adapter.refresh_ports()
                with self._lock:
                    current_out_names = {p.name for p in self.adapter.get_output_ports()}
                    current_in_names = {p.name for p in self.adapter.get_input_ports()}
                    if self._internal_rack and getattr(self._internal_rack, 'transport_mode', None) == 'internal':
                        current_out_names.add(getattr(self._internal_rack, 'pedal_port_name', ''))
                        current_in_names.add(getattr(self._internal_rack, 'keyboard_port_name', ''))

                    # Check if selected output disappeared
                    if self.selected_output_name and self.selected_output_name not in current_out_names:
                        dropped = self.selected_output_name
                        if self.selected_output_id and self.selected_output_id != "internal_pedal":
                            self.adapter.close_output(self.selected_output_id)
                        self.selected_output_name = None
                        self.selected_output_id = None
                        if self._disconnect_cb:
                            self._disconnect_cb(f"Output port '{dropped}' disconnected.")

                    # Check if selected input disappeared
                    if self.selected_input_name and self.selected_input_name not in current_in_names:
                        dropped_in = self.selected_input_name
                        if self.selected_input_id and self.selected_input_id != "internal_keyboard":
                            self.adapter.close_input(self.selected_input_id)
                        self.selected_input_name = None
                        self.selected_input_id = None
                        if self._disconnect_cb:
                            self._disconnect_cb(f"Input port '{dropped_in}' disconnected.")
            except Exception:
                pass
