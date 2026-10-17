import time
"""
Robust MIDI 1.0 Binary Codec and Human-Readable Translator
"""
from typing import List, Optional, Tuple
from .models import (
    MidiMessage,
    MessageType,
    Direction,
    PresetNumbering,
    DeviceProfile,
    validate_channel,
    validate_7bit,
)

STATUS_MAP = {
    0x80: MessageType.NOTE_OFF,
    0x90: MessageType.NOTE_ON,
    0xA0: MessageType.POLY_PRESSURE,
    0xB0: MessageType.CONTROL_CHANGE,
    0xC0: MessageType.PROGRAM_CHANGE,
    0xD0: MessageType.CHANNEL_PRESSURE,
    0xE0: MessageType.PITCH_BEND,
}

SYSTEM_MAP = {
    0xF0: MessageType.SYSTEM_EXCLUSIVE,
    0xF1: MessageType.TIME_CODE,
    0xF2: MessageType.SONG_POSITION,
    0xF3: MessageType.SONG_SELECT,
    0xF6: MessageType.TUNE_REQUEST,
    0xF7: MessageType.SYSTEM_EXCLUSIVE,  # EOX
    0xF8: MessageType.CLOCK,
    0xFA: MessageType.START,
    0xFB: MessageType.CONTINUE,
    0xFC: MessageType.STOP,
    0xFE: MessageType.ACTIVE_SENSING,
    0xFF: MessageType.RESET,
}


def encode_program_change(channel: int, program: int) -> bytes:
    validate_channel(channel)
    validate_7bit(program, "Program Change")
    status = 0xC0 | (channel - 1)
    return bytes([status, program])


def encode_control_change(channel: int, controller: int, value: int) -> bytes:
    validate_channel(channel)
    validate_7bit(controller, "Controller Number")
    validate_7bit(value, "Control Value")
    status = 0xB0 | (channel - 1)
    return bytes([status, controller, value])


def encode_bank_select(channel: int, msb: int, lsb: int, program: int) -> List[bytes]:
    validate_channel(channel)
    validate_7bit(msb, "Bank MSB")
    validate_7bit(lsb, "Bank LSB")
    validate_7bit(program, "Program Change")
    # Standard MIDI: CC 0 (MSB), CC 32 (LSB), followed by PC
    msg1 = encode_control_change(channel, 0, msb)
    msg2 = encode_control_change(channel, 32, lsb)
    msg3 = encode_program_change(channel, program)
    return [msg1, msg2, msg3]



def encode_pitch_bend(channel: int, value: int) -> bytes:
    validate_channel(channel)
    if not (0 <= value <= 16383):
        raise ValueError(f"Pitch bend value must be between 0 and 16383, got {value}")
    status = 0xE0 | (channel - 1)
    lsb = value & 0x7F
    msb = (value >> 7) & 0x7F
    return bytes([status, lsb, msb])


def encode_channel_pressure(channel: int, pressure: int) -> bytes:
    validate_channel(channel)
    validate_7bit(pressure, "Channel Pressure")
    status = 0xD0 | (channel - 1)
    return bytes([status, pressure])

def encode_realtime(msg_type: MessageType) -> bytes:
    reverse_map = {
        MessageType.CLOCK: 0xF8,
        MessageType.START: 0xFA,
        MessageType.CONTINUE: 0xFB,
        MessageType.STOP: 0xFC,
        MessageType.ACTIVE_SENSING: 0xFE,
        MessageType.RESET: 0xFF,
    }
    if msg_type not in reverse_map:
        raise ValueError(f"Not a real-time message type: {msg_type}")
    return bytes([reverse_map[msg_type]])


def decode_message(
    raw_bytes: bytes,
    timestamp_ms: Optional[float] = None,
    port_name: str = "",
    direction: Direction = Direction.RX,
    profile: Optional[DeviceProfile] = None,
    preset_convention: PresetNumbering = PresetNumbering.ZERO_INDEXED,
) -> MidiMessage:
    if not raw_bytes:
        return MidiMessage(
            timestamp_ms=timestamp_ms if timestamp_ms is not None else (time.time() * 1000.0),
            direction=direction,
            port_name=port_name,
            friendly_text="Empty Message",
        )

    b0 = raw_bytes[0]
    raw_list = list(raw_bytes)

    # Realtime / System Messages
    if b0 >= 0xF0:
        msg_type = SYSTEM_MAP.get(b0, MessageType.UNKNOWN)
        d1 = raw_list[1] if len(raw_list) > 1 else None
        d2 = raw_list[2] if len(raw_list) > 2 else None

        msg = MidiMessage(
            timestamp_ms=timestamp_ms if timestamp_ms is not None else (time.time() * 1000.0),
            direction=direction,
            port_name=port_name,
            channel=None,
            message_type=msg_type,
            data1=d1,
            data2=d2,
            raw_bytes=raw_list,
            unverified=False,
        )
        msg.friendly_text = format_friendly_text(msg, profile, preset_convention)
        return msg

    # Channel Voice Messages
    status_nibble = b0 & 0xF0
    channel = (b0 & 0x0F) + 1
    msg_type = STATUS_MAP.get(status_nibble, MessageType.UNKNOWN)

    d1 = raw_list[1] if len(raw_list) > 1 else None
    d2 = raw_list[2] if len(raw_list) > 2 else None

    msg = MidiMessage(
        timestamp_ms=timestamp_ms if timestamp_ms is not None else (time.time() * 1000.0),
        direction=direction,
        port_name=port_name,
        channel=channel,
        message_type=msg_type,
        data1=d1,
        data2=d2,
        raw_bytes=raw_list,
        unverified=(direction == Direction.TX),
    )
    msg.friendly_text = format_friendly_text(msg, profile, preset_convention)
    return msg


def format_friendly_text(
    msg: MidiMessage,
    profile: Optional[DeviceProfile] = None,
    preset_convention: PresetNumbering = PresetNumbering.ZERO_INDEXED,
) -> str:
    mtype = msg.message_type
    ch = f"Ch {msg.channel}: " if msg.channel else ""

    if mtype == MessageType.PROGRAM_CHANGE:
        prog = msg.data1 if msg.data1 is not None else 0
        display_num = prog + 1 if preset_convention == PresetNumbering.ONE_INDEXED else prog
        name = ""
        if profile and prog in profile.pc_map:
            name = f' ("{profile.pc_map[prog]}")'
        return f"{ch}Program Change {prog} -> Preset [{display_num}]{name}"

    elif mtype == MessageType.CONTROL_CHANGE:
        cc = msg.data1 if msg.data1 is not None else 0
        val = msg.data2 if msg.data2 is not None else 0

        # Check friendly CC name from profile or standard MIDI
        cc_name = ""
        if profile and cc in profile.cc_map:
            cc_name = f" ({profile.cc_map[cc]})"
        elif cc == 0:
            cc_name = " (Bank Select MSB)"
        elif cc == 1:
            cc_name = " (Modulation Wheel)"
        elif cc == 7:
            cc_name = " (Channel Volume)"
        elif cc == 10:
            cc_name = " (Pan)"
        elif cc == 11:
            cc_name = " (Expression)"
        elif cc == 32:
            cc_name = " (Bank Select LSB)"
        elif cc == 64:
            state = " [ENGAGED]" if val >= 64 else " [OFF]"
            cc_name = f" (Sustain / Damper{state})"
        elif cc == 120:
            cc_name = " (All Sound Off)"
        elif cc == 121:
            cc_name = " (Reset All Controllers)"
        elif cc == 123:
            cc_name = " (All Notes Off - Panic)"

        return f"{ch}Control Change {cc}{cc_name} = {val}"

    elif mtype == MessageType.NOTE_ON:
        note = msg.data1 or 0
        vel = msg.data2 or 0
        return f"{ch}Note On {note} (Vel {vel})"

    elif mtype == MessageType.NOTE_OFF:
        note = msg.data1 or 0
        return f"{ch}Note Off {note}"

    elif mtype == MessageType.PITCH_BEND:
        lsb = msg.data1 or 0
        msb = msg.data2 or 0
        val = (msb << 7) | lsb
        delta = val - 8192
        return f"{ch}Pitch Bend = {val} ({delta:+d})"

    elif mtype == MessageType.CHANNEL_PRESSURE:
        pressure = msg.data1 or 0
        return f"{ch}Channel Pressure (Aftertouch) = {pressure}"

    elif mtype == MessageType.CLOCK:
        return "Realtime: Timing Clock (24 PPQN)"

    elif mtype == MessageType.START:
        return "Realtime: Start Transport"

    elif mtype == MessageType.CONTINUE:
        return "Realtime: Continue Transport"

    elif mtype == MessageType.STOP:
        return "Realtime: Stop Transport"

    elif mtype == MessageType.ACTIVE_SENSING:
        return "Realtime: Active Sensing"

    elif mtype == MessageType.RESET:
        return "Realtime: System Reset"

    elif mtype == MessageType.SYSTEM_EXCLUSIVE:
        size = len(msg.raw_bytes)
        return f"System Exclusive ({size} bytes)"

    return f"{ch}{mtype.value} [Data: {msg.data1}, {msg.data2}]"
