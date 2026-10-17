"""
High-Fidelity Virtual MIDI Adapter for Headless Simulation & Automated Testing
"""
import time
from typing import List, Dict, Optional
from .base import MidiAdapterBase, MidiPortInfo, PortDirection, MidiInputCallback


class VirtualMidiAdapter(MidiAdapterBase):
    """
    Simulated adapter simulating real stage devices:
    - Virtual Amp Modeler (Out)
    - Virtual Delay/Reverb Pedal (Out)
    - Virtual Synth (Out)
    - Virtual Master Foot Controller (In)
    """

    def __init__(self, echo_loopback: bool = True):
        self._echo_loopback = echo_loopback
        self._inputs: Dict[str, MidiPortInfo] = {}
        self._outputs: Dict[str, MidiPortInfo] = {}
        self._open_outputs: Dict[str, bool] = {}
        self._open_inputs: Dict[str, MidiInputCallback] = {}
        self.sent_history: List[Dict] = []
        self._simulate_disconnect_id: Optional[str] = None

        self._setup_default_virtual_devices()

    def _setup_default_virtual_devices(self):
        self._outputs = {
            "virt_out_amp": MidiPortInfo(
                id="virt_out_amp",
                name="Virtual Amp Modeler [Out]",
                direction=PortDirection.OUTPUT,
                is_virtual=True,
                manufacturer="VirtualDSP",
                system_index=0,
            ),
            "virt_out_delay": MidiPortInfo(
                id="virt_out_delay",
                name="Virtual Ambient Delay [Out]",
                direction=PortDirection.OUTPUT,
                is_virtual=True,
                manufacturer="VirtualDSP",
                system_index=1,
            ),
            "virt_out_synth": MidiPortInfo(
                id="virt_out_synth",
                name="Virtual Stage Synth [Out]",
                direction=PortDirection.OUTPUT,
                is_virtual=True,
                manufacturer="VirtualDSP",
                system_index=2,
            ),
        }

        self._inputs = {
            "virt_in_ctrl": MidiPortInfo(
                id="virt_in_ctrl",
                name="Virtual Foot Controller [In]",
                direction=PortDirection.INPUT,
                is_virtual=True,
                manufacturer="PulseStage Sim",
                system_index=0,
            )
        }

    def refresh_ports(self) -> None:
        pass

    def get_input_ports(self) -> List[MidiPortInfo]:
        return [
            p for p in self._inputs.values()
            if p.id != self._simulate_disconnect_id
        ]

    def get_output_ports(self) -> List[MidiPortInfo]:
        return [
            p for p in self._outputs.values()
            if p.id != self._simulate_disconnect_id
        ]

    def open_output(self, port_id: str) -> bool:
        if port_id not in self._outputs or port_id == self._simulate_disconnect_id:
            return False
        self._open_outputs[port_id] = True
        return True

    def close_output(self, port_id: str) -> None:
        self._open_outputs.pop(port_id, None)

    def open_input(self, port_id: str, callback: MidiInputCallback) -> bool:
        if port_id not in self._inputs or port_id == self._simulate_disconnect_id:
            return False
        self._open_inputs[port_id] = callback
        return True

    def close_input(self, port_id: str) -> None:
        self._open_inputs.pop(port_id, None)

    def send_bytes(self, port_id: str, data: bytes) -> bool:
        if port_id not in self._open_outputs or port_id == self._simulate_disconnect_id:
            return False

        ts = time.time() * 1000.0
        self.sent_history.append({
            "port_id": port_id,
            "data": list(data),
            "timestamp_ms": ts,
        })

        # Loopback to simulated inputs if enabled
        if self._echo_loopback and "virt_in_ctrl" in self._open_inputs:
            cb = self._open_inputs["virt_in_ctrl"]
            cb("virt_in_ctrl", data, ts)

        return True

    def simulate_incoming(self, port_id: str, data: bytes) -> bool:
        if port_id in self._open_inputs:
            ts = time.time() * 1000.0
            self._open_inputs[port_id](port_id, data, ts)
            return True
        return False

    def simulate_disconnect(self, port_id: str):
        self._simulate_disconnect_id = port_id

    def simulate_reconnect(self):
        self._simulate_disconnect_id = None

    def close_all(self) -> None:
        self._open_outputs.clear()
        self._open_inputs.clear()
