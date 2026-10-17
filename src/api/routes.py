"""
REST API Endpoints for PulseStage MIDI
"""
import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query, Response, UploadFile, File
from pydantic import BaseModel, Field

from ..core.models import (
    CommandType,
    Direction,
    MidiMessage,
    MessageType,
    PresetNumbering,
    SavedAction,
)
from ..core.codec import (
    encode_program_change,
    encode_control_change,
    encode_bank_select,
    encode_pitch_bend,
    encode_channel_pressure,
    decode_message,
)
from ..core.profiles import ProfileRegistry
from ..engine.manager import DeviceManager
from ..engine.clock import MidiClock, TransportState
from ..engine.monitor import MidiMonitor, MonitorFilter
from ..engine.actions import ActionRunner
from ..engine.config_store import ConfigStore

router = APIRouter(prefix="/api")


# Request DTOs with strict boundary validation
class SelectPortRequest(BaseModel):
    port_name: Optional[str] = None
    port_id: Optional[str] = None


class SendProgramChangeRequest(BaseModel):
    channel: int = Field(ge=1, le=16)
    program: int = Field(ge=0, le=127)
    target_port_name: Optional[str] = None
    preset_convention: PresetNumbering = PresetNumbering.ZERO_INDEXED


class SendControlChangeRequest(BaseModel):
    channel: int = Field(ge=1, le=16)
    controller: int = Field(ge=0, le=127)
    value: int = Field(ge=0, le=127)
    target_port_name: Optional[str] = None


class SendBankSelectRequest(BaseModel):
    channel: int = Field(ge=1, le=16)
    msb: int = Field(ge=0, le=127, default=0)
    lsb: int = Field(ge=0, le=127, default=0)
    bank_msb: Optional[int] = Field(ge=0, le=127, default=None)
    bank_lsb: Optional[int] = Field(ge=0, le=127, default=None)
    program: int = Field(ge=0, le=127)
    target_port_name: Optional[str] = None


class SetBpmRequest(BaseModel):
    bpm: float = Field(ge=40.0, le=300.0)



class SendPitchBendRequest(BaseModel):
    channel: int = Field(ge=1, le=16)
    value: int = Field(ge=0, le=16383)
    target_port_name: Optional[str] = None


class SendChannelPressureRequest(BaseModel):
    channel: int = Field(ge=1, le=16)
    pressure: int = Field(ge=0, le=127)
    target_port_name: Optional[str] = None


class SendRawHexRequest(BaseModel):
    hex_string: str
    target_port_name: Optional[str] = None


class PanicRequest(BaseModel):
    channel: Optional[int] = Field(default=None, ge=1, le=16)
    target_port_name: Optional[str] = None


class PreferencesUpdateRequest(BaseModel):
    preferences: Dict[str, Any]


def init_routes(
    manager: DeviceManager,
    clock: MidiClock,
    monitor: MidiMonitor,
    action_runner: ActionRunner,
    config_store: ConfigStore,
    profile_registry: ProfileRegistry,
    broadcast_func,
) -> APIRouter:

    @router.get("/status")
    def get_status():
        outputs = manager.get_outputs()
        inputs = manager.get_inputs()
        return {
            "application": "PulseStage MIDI",
            "version": "1.0.0",
            "is_virtual": manager.is_virtual,
            "selected_output": manager.selected_output_name,
            "selected_input": manager.selected_input_name,
            "output_count": len(outputs),
            "input_count": len(inputs),
            "clock": {
                "state": clock.state.value,
                "bpm": clock.bpm,
                "tick_count": clock.tick_count,
            },
            "monitor": {
                "total_recorded": len(monitor.get_messages()),
                "clock_ticks": monitor.clock_tick_counter,
                "tx_count": monitor.tx_counter,
                "rx_count": monitor.rx_counter,
                "is_paused": monitor.is_paused,
            },
        }

    @router.get("/ports")
    def get_ports():
        return {
            "outputs": [p.model_dump() for p in manager.get_outputs()],
            "inputs": [p.model_dump() for p in manager.get_inputs()],
            "selected_output": manager.selected_output_name,
            "selected_input": manager.selected_input_name,
        }

    @router.post("/ports/output/select")
    def select_output(req: SelectPortRequest):
        target_name = req.port_name
        if not target_name and req.port_id:
            for p in manager.get_outputs():
                if p.id == req.port_id:
                    target_name = p.name
                    break

        if not target_name:
            manager.deselect_output()
            config_store.set_preference("selected_output_name", None)
            return {"success": True, "selected_output": None}

        success = manager.select_output(target_name)
        if success:
            config_store.set_preference("selected_output_name", target_name)
            return {"success": True, "selected_output": target_name}
        raise HTTPException(status_code=400, detail=f"Failed to open output port: '{target_name}'. Port may be busy or disconnected.")

    @router.post("/ports/input/select")
    def select_input(req: SelectPortRequest):
        target_name = req.port_name
        if not target_name and req.port_id:
            for p in manager.get_inputs():
                if p.id == req.port_id:
                    target_name = p.name
                    break

        if not target_name:
            manager.deselect_input()
            config_store.set_preference("selected_input_name", None)
            return {"success": True, "selected_input": None}

        def _in_cb(port_id: str, data: bytes, ts: float):
            decoded = decode_message(data, timestamp_ms=ts, port_name=target_name, direction=Direction.RX)
            monitor.record_message(decoded)
            broadcast_func({"type": "midi_message", "message": decoded.model_dump()})

        success = manager.select_input(target_name, _in_cb)
        if success:
            config_store.set_preference("selected_input_name", target_name)
            return {"success": True, "selected_input": target_name}
        raise HTTPException(status_code=400, detail=f"Failed to open input port: '{req.port_name}'.")

    @router.post("/ports/output/deselect")
    def deselect_output_endpoint():
        manager.deselect_output()
        config_store.set_preference("selected_output_name", None)
        return {"success": True, "selected_output": None}

    @router.post("/ports/input/deselect")
    def deselect_input_endpoint():
        manager.deselect_input()
        config_store.set_preference("selected_input_name", None)
        return {"success": True, "selected_input": None}

    @router.post("/send/program-change")
    def send_program_change(req: SendProgramChangeRequest):
        target = req.target_port_name or manager.selected_output_name
        if not target:
            raise HTTPException(status_code=400, detail="No output port selected.")

        if not manager.is_port_connected(target):
            raise HTTPException(status_code=400, detail=f"Destination port '{target}' is disconnected.")

        data = encode_program_change(req.channel, req.program)
        sent = manager.send_to_port(target, data)
        if not sent:
            raise HTTPException(status_code=500, detail=f"Failed to transmit to port '{target}'. Driver rejected packet.")

        msg = decode_message(
            data,
            port_name=target,
            direction=Direction.TX,
            preset_convention=req.preset_convention,
        )
        monitor.record_message(msg)
        broadcast_func({"type": "midi_message", "message": msg.model_dump()})

        return {
            "success": True,
            "destination": target,
            "channel": req.channel,
            "program": req.program,
            "bytes_hex": msg.hex_string,
            "plain_language": msg.friendly_text,
            "unverified_notice": "Transmitted to hardware. Receiving device state unverified (simplex MIDI).",
        }

    @router.post("/send/control-change")
    def send_control_change(req: SendControlChangeRequest):
        target = req.target_port_name or manager.selected_output_name
        if not target:
            raise HTTPException(status_code=400, detail="No output port selected.")

        if not manager.is_port_connected(target):
            raise HTTPException(status_code=400, detail=f"Destination port '{target}' is disconnected.")

        data = encode_control_change(req.channel, req.controller, req.value)
        sent = manager.send_to_port(target, data)
        if not sent:
            raise HTTPException(status_code=500, detail=f"Failed to transmit to port '{target}'. Driver rejected packet.")

        msg = decode_message(data, port_name=target, direction=Direction.TX)
        monitor.record_message(msg)
        broadcast_func({"type": "midi_message", "message": msg.model_dump()})

        return {
            "success": True,
            "destination": target,
            "channel": req.channel,
            "controller": req.controller,
            "value": req.value,
            "bytes_hex": msg.hex_string,
            "plain_language": msg.friendly_text,
        }

    @router.post("/send/bank-select")
    def send_bank_select(req: SendBankSelectRequest):
        target = req.target_port_name or manager.selected_output_name
        if not target:
            raise HTTPException(status_code=400, detail="No output port selected.")

        if not manager.is_port_connected(target):
            raise HTTPException(status_code=400, detail=f"Destination port '{target}' is disconnected.")

        msb = req.bank_msb if req.bank_msb is not None else req.msb
        lsb = req.bank_lsb if req.bank_lsb is not None else req.lsb
        packets = encode_bank_select(req.channel, msb, lsb, req.program)
        for p in packets:
            sent = manager.send_to_port(target, p)
            if not sent:
                raise HTTPException(status_code=500, detail=f"Failed to send bank select packet to '{target}'.")
            msg = decode_message(p, port_name=target, direction=Direction.TX)
            monitor.record_message(msg)
            broadcast_func({"type": "midi_message", "message": msg.model_dump()})

        return {
            "success": True,
            "destination": target,
            "channel": req.channel,
            "bank_msb": req.msb,
            "bank_lsb": req.lsb,
            "program": req.program,
        }


    @router.post("/send/pitch-bend")
    def send_pitch_bend(req: SendPitchBendRequest):
        target = req.target_port_name or manager.selected_output_name
        if not target:
            raise HTTPException(status_code=400, detail="No output port selected.")
        if not manager.is_port_connected(target):
            raise HTTPException(status_code=400, detail=f"Destination port '{target}' is disconnected.")

        data = encode_pitch_bend(req.channel, req.value)
        sent = manager.send_to_port(target, data)
        if not sent:
            raise HTTPException(status_code=500, detail=f"Failed to transmit to port '{target}'. Driver rejected packet.")

        msg = decode_message(data, port_name=target, direction=Direction.TX)
        monitor.record_message(msg)
        broadcast_func({"type": "midi_message", "message": msg.model_dump()})
        return {
            "success": True,
            "destination": target,
            "channel": req.channel,
            "value": req.value,
            "bytes_hex": msg.hex_string,
            "plain_language": msg.friendly_text,
        }

    @router.post("/send/channel-pressure")
    def send_channel_pressure(req: SendChannelPressureRequest):
        target = req.target_port_name or manager.selected_output_name
        if not target:
            raise HTTPException(status_code=400, detail="No output port selected.")
        if not manager.is_port_connected(target):
            raise HTTPException(status_code=400, detail=f"Destination port '{target}' is disconnected.")

        data = encode_channel_pressure(req.channel, req.pressure)
        sent = manager.send_to_port(target, data)
        if not sent:
            raise HTTPException(status_code=500, detail=f"Failed to transmit to port '{target}'. Driver rejected packet.")

        msg = decode_message(data, port_name=target, direction=Direction.TX)
        monitor.record_message(msg)
        broadcast_func({"type": "midi_message", "message": msg.model_dump()})
        return {
            "success": True,
            "destination": target,
            "channel": req.channel,
            "pressure": req.pressure,
            "bytes_hex": msg.hex_string,
            "plain_language": msg.friendly_text,
        }

    @router.post("/send/raw-hex")
    def send_raw_hex(req: SendRawHexRequest):
        target = req.target_port_name or manager.selected_output_name
        if not target:
            raise HTTPException(status_code=400, detail="No output port selected.")
        if not manager.is_port_connected(target):
            raise HTTPException(status_code=400, detail=f"Destination port '{target}' is disconnected.")

        clean = "".join(req.hex_string.split())
        try:
            raw_bytes = bytes.fromhex(clean)
            if len(raw_bytes) == 0:
                raise ValueError("Hex string cannot be empty.")
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid hex string: {e}")

        sent = manager.send_to_port(target, raw_bytes)
        if not sent:
            raise HTTPException(status_code=500, detail=f"Failed to transmit raw bytes to port '{target}'. Driver rejected packet.")

        msg = decode_message(raw_bytes, port_name=target, direction=Direction.TX)
        monitor.record_message(msg)
        broadcast_func({"type": "midi_message", "message": msg.model_dump()})
        return {
            "success": True,
            "destination": target,
            "length": len(raw_bytes),
            "bytes_hex": msg.hex_string,
            "plain_language": msg.friendly_text,
        }

    @router.post("/send/panic")
    def send_panic(req: PanicRequest):
        target = req.target_port_name or manager.selected_output_name
        if not target:
            raise HTTPException(status_code=400, detail="No output port selected for panic transmission.")

        if not manager.is_port_connected(target):
            raise HTTPException(status_code=400, detail=f"Cannot execute Panic: target port '{target}' is disconnected.")

        # Immediately halt clock and actions on panic
        clock.emergency_stop()
        action_runner.cancel()
        broadcast_func({"type": "clock_status", "state": "STOPPED", "bpm": clock.bpm})

        channels = [req.channel] if req.channel else list(range(1, 17))
        delivered_count = 0
        failed_count = 0

        for ch in channels:
            # 1. All Notes Off (CC 123)
            p1 = encode_control_change(ch, 123, 0)
            if manager.send_to_port(target, p1):
                delivered_count += 1
            else:
                failed_count += 1

            # 2. All Sound Off (CC 120)
            p2 = encode_control_change(ch, 120, 0)
            if manager.send_to_port(target, p2):
                delivered_count += 1
            else:
                failed_count += 1

            # 3. Sustain Off (CC 64)
            p3 = encode_control_change(ch, 64, 0)
            if manager.send_to_port(target, p3):
                delivered_count += 1
            else:
                failed_count += 1

        if delivered_count == 0 and failed_count > 0:
            raise HTTPException(status_code=500, detail=f"Panic failed: Port '{target}' rejected transmission.")

        # Record panic in monitor
        panic_msg = MidiMessage(
            port_name=target,
            direction=Direction.TX,
            friendly_text=f"[PANIC] Safe All-Notes-Off (CC 123) and All-Sound-Off (CC 120) sent ({delivered_count} packets delivered).",
        )
        monitor.record_message(panic_msg)
        broadcast_func({"type": "midi_message", "message": panic_msg.model_dump()})

        return {
            "success": True,
            "destination": target,
            "packets_sent": delivered_count,
            "failed_packets": failed_count,
            "message": f"Panic sequence executed: {delivered_count} packets delivered safely. Running clock and macros halted.",
        }

    @router.post("/send/emergency-stop")
    def emergency_stop():
        clock.emergency_stop()
        action_runner.cancel()
        broadcast_func({"type": "clock_status", "state": "STOPPED", "bpm": clock.bpm})
        return {"success": True, "message": "All active clock and action transmissions halted."}

    # MIDI Clock Endpoints
    @router.post("/clock/start")
    def start_clock():
        if not manager.selected_output_name:
            raise HTTPException(status_code=400, detail="Please select an output port for MIDI Clock.")
        if not manager.is_port_connected(manager.selected_output_name):
            raise HTTPException(status_code=400, detail="Selected output port is disconnected.")

        clock.start()
        broadcast_func({"type": "clock_status", "state": "RUNNING", "bpm": clock.bpm})
        return {"success": True, "state": "RUNNING", "bpm": clock.bpm}

    @router.post("/clock/stop")
    def stop_clock():
        clock.stop()
        broadcast_func({"type": "clock_status", "state": "STOPPED", "bpm": clock.bpm})
        return {"success": True, "state": "STOPPED", "bpm": clock.bpm}

    @router.post("/clock/continue")
    def continue_clock():
        if not manager.selected_output_name or not manager.is_port_connected(manager.selected_output_name):
            raise HTTPException(status_code=400, detail="Cannot continue clock: Selected port is disconnected.")
        clock.continue_transport()
        broadcast_func({"type": "clock_status", "state": "RUNNING", "bpm": clock.bpm})
        return {"success": True, "state": "RUNNING", "bpm": clock.bpm}

    @router.post("/clock/bpm")
    def set_bpm(req: SetBpmRequest):
        clock.set_bpm(req.bpm)
        config_store.set_preference("clock_bpm", req.bpm)
        broadcast_func({"type": "clock_status", "state": clock.state.value, "bpm": clock.bpm})
        return {"success": True, "bpm": clock.bpm}

    @router.post("/clock/tap")
    def tap_tempo():
        new_bpm = clock.tap_tempo()
        config_store.set_preference("clock_bpm", new_bpm)
        broadcast_func({"type": "clock_status", "state": clock.state.value, "bpm": clock.bpm})
        return {"success": True, "bpm": new_bpm}

    # Monitor Endpoints
    @router.get("/monitor/messages")
    def get_monitor_messages(
        port: Optional[str] = None,
        channel: Optional[int] = None,
        show_raw_clock: bool = False,
    ):
        flt = MonitorFilter(
            port_name=port,
            channel=channel,
            show_raw_clock=show_raw_clock,
        )
        msgs = monitor.get_messages(flt)
        return {
            "messages": [m.model_dump() for m in msgs[-200:]],
            "clock_tick_counter": monitor.clock_tick_counter,
            "tx_counter": monitor.tx_counter,
            "rx_counter": monitor.rx_counter,
            "is_paused": monitor.is_paused,
        }

    @router.post("/monitor/clear")
    def clear_monitor():
        monitor.clear()
        broadcast_func({"type": "monitor_clear"})
        return {"success": True}

    @router.post("/monitor/pause")
    def toggle_pause():
        monitor.is_paused = not monitor.is_paused
        return {"success": True, "is_paused": monitor.is_paused}

    @router.get("/monitor/export/{fmt}")
    def export_monitor(fmt: str):
        if fmt == "json":
            return Response(content=monitor.export_json(), media_type="application/json")
        elif fmt == "csv":
            return Response(content=monitor.export_csv(), media_type="text/csv")
        elif fmt == "text":
            return Response(content=monitor.export_text(), media_type="text/plain")
        raise HTTPException(status_code=400, detail="Invalid format. Use json, csv, or text.")

    # Actions Endpoints
    @router.get("/actions")
    def get_actions():
        acts = config_store.get_actions()
        return [a.model_dump() if hasattr(a, "model_dump") else a for a in acts]

    @router.post("/actions")
    def save_action(action: SavedAction):
        # Validate steps
        for step in action.steps:
            if step.data1 < 0 or step.data1 > 127:
                raise HTTPException(status_code=422, detail="Step data1 must be 0-127.")
            if step.data2 < 0 or step.data2 > 127:
                raise HTTPException(status_code=422, detail="Step data2 must be 0-127.")
            if step.data3 is not None and (step.data3 < 0 or step.data3 > 127):
                raise HTTPException(status_code=422, detail="Step data3 (Bank MSB) must be 0-127.")

        config_store.save_action(action)
        return {"success": True, "action": action.model_dump()}

    @router.delete("/actions/{action_id}")
    def delete_action(action_id: str):
        deleted = config_store.delete_action(action_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Action not found.")
        return {"success": True}

    @router.post("/actions/{action_id}/execute")
    def execute_action(action_id: str):
        target_action = config_store.get_action_by_id(action_id)
        if not target_action:
            for a in config_store.get_actions():
                a_id = a.id if hasattr(a, "id") else a.get("id")
                if a_id == action_id:
                    target_action = SavedAction.model_validate(a) if isinstance(a, dict) else a
                    break
        if not target_action:
            raise HTTPException(status_code=404, detail="Action not found.")

        # Build connected ports map and ensure output handles are acquired
        connected_map = {}
        for p in manager.get_outputs():
            connected_map[p.name] = True
            manager.ensure_output_open(p.name)

        result = action_runner.execute_action(target_action, connected_map)
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error", "Action execution failed."))

        return result

    # Profiles Endpoints
    @router.get("/profiles")
    def get_profiles():
        profs = profile_registry.list_profiles()
        return [p.model_dump() for p in profs.values()]

    # Config Preferences & Import/Export
    @router.get("/config")
    def get_config():
        return config_store._data

    @router.post("/config/preferences")
    def update_preferences(req: PreferencesUpdateRequest):
        for k, v in req.preferences.items():
            config_store.set_preference(k, v)
        return {"success": True}

    @router.get("/config/export")
    def export_config():
        return Response(content=config_store.export_json(), media_type="application/json")

    @router.post("/config/import")
    def import_config(data: Dict[str, Any]):
        success = config_store.import_json(data)
        if not success:
            raise HTTPException(status_code=400, detail="Invalid configuration format or incompatible schema version.")
        return {"success": True}

    return router
