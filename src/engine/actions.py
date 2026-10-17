"""
Action Runner Engine: High-Reliability Macro & Preset Sequence Executor.
Features:
- Interruptible step delays via threading.Event.wait()
- Per-packet cancellation checks (including inside Bank Select sub-sequences)
- Strict port validation and truthfulness reporting
- Support for PROGRAM_CHANGE, CONTROL_CHANGE, BANK_SELECT_PC, NOTE_ON, NOTE_OFF, and RAW_HEX
"""
import threading
import time
from typing import Callable, Dict, List, Any, Optional

from ..core.models import SavedAction, ActionStep, CommandType, Direction
from ..core.codec import encode_program_change, encode_control_change, encode_bank_select, decode_message


class ActionRunner:
    def __init__(
        self,
        send_func: Callable[[str, bytes], bool],
        monitor_callback: Optional[Callable[[Any], None]] = None,
    ):
        self._send_func = send_func
        self._monitor_cb = monitor_callback
        self._is_running = False
        self._abort_event = threading.Event()
        self._lock = threading.Lock()

    @property
    def is_running(self) -> bool:
        with self._lock:
            return self._is_running

    def cancel(self) -> None:
        """Interrupts running macros immediately."""
        self._abort_event.set()

    def execute_action(
        self,
        action: SavedAction,
        connected_ports: Dict[str, bool],
    ) -> Dict[str, Any]:
        """
        Executes a saved action sequence with interruptible pacing,
        per-packet cancellation checking, and strict port verification.
        """
        with self._lock:
            if self._is_running:
                return {"success": False, "error": "Another action is currently executing."}
            self._is_running = True
            self._abort_event.clear()

        executed_steps = 0

        try:
            for step in action.steps:
                if self._abort_event.is_set():
                    return {
                        "success": False,
                        "cancelled": True,
                        "error": "Action execution cancelled by user.",
                        "executed_steps": executed_steps,
                    }

                # Verify target port availability
                target = step.target_port_name
                if not target or not connected_ports.get(target, False):
                    return {
                        "success": False,
                        "cancelled": False,
                        "error": f"Target port '{target}' is disconnected or unavailable.",
                        "executed_steps": executed_steps,
                    }

                # Encode step command
                packets: List[bytes] = []
                if step.command_type == CommandType.PROGRAM_CHANGE:
                    packets.append(encode_program_change(step.channel, step.data1))
                elif step.command_type == CommandType.CONTROL_CHANGE:
                    packets.append(encode_control_change(step.channel, step.data1, step.data2))
                elif step.command_type == CommandType.BANK_SELECT_PC:
                    msb = step.data3 if step.data3 is not None else 0
                    packets.extend(encode_bank_select(step.channel, msb, step.data2, step.data1))
                elif step.command_type == CommandType.NOTE_ON:
                    packets.append(bytes([0x90 | (step.channel - 1), step.data1, step.data2]))
                elif step.command_type == CommandType.NOTE_OFF:
                    packets.append(bytes([0x80 | (step.channel - 1), step.data1, 0]))
                elif step.command_type == CommandType.RAW_HEX:
                    if hasattr(step, "raw_hex") and step.raw_hex:
                        try:
                            clean = "".join(step.raw_hex.split())
                            raw_b = bytes.fromhex(clean)
                            if raw_b:
                                packets.append(raw_b)
                        except Exception as e:
                            return {
                                "success": False,
                                "cancelled": False,
                                "error": f"Invalid hex in RAW_HEX step: {e}",
                                "executed_steps": executed_steps,
                            }
                    if not packets:
                        return {
                            "success": False,
                            "cancelled": False,
                            "error": "RAW_HEX action step contains no valid hex payload.",
                            "executed_steps": executed_steps,
                        }

                # Transmit packets with per-packet abort check
                for p_idx, p in enumerate(packets):
                    if self._abort_event.is_set():
                        return {
                            "success": False,
                            "cancelled": True,
                            "error": "Action cancelled during multi-packet sequence." if p_idx > 0 else "Action cancelled before packet send.",
                            "executed_steps": executed_steps,
                        }

                    sent = self._send_func(target, p)
                    if not sent:
                        return {
                            "success": False,
                            "cancelled": False,
                            "error": f"Failed to send packet to '{target}'. Destination dropped.",
                            "executed_steps": executed_steps,
                        }

                    if self._monitor_cb:
                        try:
                            msg = decode_message(p, port_name=target, direction=Direction.TX)
                            self._monitor_cb(msg)
                        except Exception:
                            pass

                executed_steps += 1

                # Interruptible inter-step delay
                if step.delay_ms > 0:
                    cancelled = self._abort_event.wait(timeout=step.delay_ms / 1000.0)
                    if cancelled:
                        return {
                            "success": False,
                            "cancelled": True,
                            "error": "Action execution cancelled during inter-step delay.",
                            "executed_steps": executed_steps,
                        }

            return {
                "success": True,
                "cancelled": False,
                "action_id": action.id,
                "action_name": action.name,
                "executed_steps": executed_steps,
            }

        finally:
            with self._lock:
                self._is_running = False
