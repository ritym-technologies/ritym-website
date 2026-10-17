"""
Core Domain Models with Strict Validation
"""
from __future__ import annotations
from enum import Enum
from typing import List, Optional, Dict, Any
import time
from pydantic import BaseModel, Field, field_validator

# Type aliases
MidiChannel = int
MidiValue = int


class MessageType(str, Enum):
    NOTE_OFF = "NOTE_OFF"
    NOTE_ON = "NOTE_ON"
    POLY_PRESSURE = "POLY_PRESSURE"
    CONTROL_CHANGE = "CONTROL_CHANGE"
    PROGRAM_CHANGE = "PROGRAM_CHANGE"
    CHANNEL_PRESSURE = "CHANNEL_PRESSURE"
    PITCH_BEND = "PITCH_BEND"
    SYSTEM_EXCLUSIVE = "SYSTEM_EXCLUSIVE"
    TIME_CODE = "TIME_CODE"
    SONG_POSITION = "SONG_POSITION"
    SONG_SELECT = "SONG_SELECT"
    TUNE_REQUEST = "TUNE_REQUEST"
    CLOCK = "CLOCK"
    START = "START"
    CONTINUE = "CONTINUE"
    STOP = "STOP"
    ACTIVE_SENSING = "ACTIVE_SENSING"
    RESET = "RESET"
    UNKNOWN = "UNKNOWN"


class PresetNumbering(str, Enum):
    ZERO_INDEXED = "0-127"
    ONE_INDEXED = "1-128"


class Direction(str, Enum):
    TX = "TX"
    RX = "RX"
    INTERNAL = "INTERNAL"


def validate_channel(v: int) -> int:
    if not (1 <= v <= 16):
        raise ValueError(f"MIDI Channel must be between 1 and 16, got {v}")
    return v


def validate_7bit(v: Optional[int], name: str = "Value") -> Optional[int]:
    if v is None:
        return 0
    if not (0 <= v <= 127):
        raise ValueError(f"MIDI {name} must be between 0 and 127 (7-bit), got {v}")
    return v


class PreferencesModel(BaseModel):
    selected_output_name: Optional[str] = None
    selected_input_name: Optional[str] = None
    default_channel: int = 1
    preset_convention: str = PresetNumbering.ZERO_INDEXED.value
    clock_bpm: float = 120.0
    show_raw_clock_in_monitor: bool = False
    enable_dark_stage_mode: bool = True

    @field_validator("default_channel")
    @classmethod
    def check_ch(cls, v: int) -> int:
        return validate_channel(v)

    @field_validator("clock_bpm")
    @classmethod
    def check_bpm(cls, v: float) -> float:
        return max(40.0, min(300.0, float(v)))


class MidiMessage(BaseModel):
    timestamp_ms: float = Field(default_factory=lambda: time.time() * 1000.0)
    direction: Direction = Direction.TX
    port_name: str = ""
    channel: Optional[int] = None
    message_type: MessageType = MessageType.UNKNOWN
    data1: Optional[int] = None
    data2: Optional[int] = None
    raw_bytes: List[int] = Field(default_factory=list)
    friendly_text: str = ""
    unverified: bool = True

    @field_validator("channel")
    @classmethod
    def check_ch(cls, v: Optional[int]) -> Optional[int]:
        if v is not None:
            return validate_channel(v)
        return None

    @field_validator("data1", "data2")
    @classmethod
    def check_data(cls, v: Optional[int]) -> Optional[int]:
        if v is not None:
            return validate_7bit(v)
        return None

    @property
    def hex_string(self) -> str:
        return " ".join(f"0x{b:02X}" for b in self.raw_bytes)


class CommandType(str, Enum):
    PROGRAM_CHANGE = "PROGRAM_CHANGE"
    CONTROL_CHANGE = "CONTROL_CHANGE"
    BANK_SELECT_PC = "BANK_SELECT_PC"
    NOTE_ON = "NOTE_ON"
    NOTE_OFF = "NOTE_OFF"
    RAW_HEX = "RAW_HEX"


class ActionStep(BaseModel):
    id: str = ""
    target_port_name: str = ""
    channel: int = 1
    command_type: CommandType = CommandType.PROGRAM_CHANGE
    data1: int = 0  # Program or CC number or Note
    data2: int = 0  # CC value or Bank LSB or Velocity
    data3: Optional[int] = 0  # Bank MSB (for BANK_SELECT_PC)
    raw_hex: Optional[str] = None  # Hex string for RAW_HEX
    delay_ms: int = 0  # Pacing delay after executing this step

    @field_validator("channel")
    @classmethod
    def check_ch(cls, v: int) -> int:
        return validate_channel(v)

    @field_validator("data1", "data2", "data3")
    @classmethod
    def check_7bit_fields(cls, v: Optional[int]) -> Optional[int]:
        return validate_7bit(v)

    @field_validator("delay_ms")
    @classmethod
    def check_delay(cls, v: int) -> int:
        if v < 0 or v > 5000:
            raise ValueError(f"Step delay must be between 0 and 5000 ms, got {v}")
        return v

    @field_validator("raw_hex")
    @classmethod
    def check_raw(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v.strip():
            clean = "".join(v.split())
            try:
                b = bytes.fromhex(clean)
                if len(b) == 0:
                    raise ValueError("Raw hex payload must not be empty.")
            except Exception as e:
                raise ValueError(f"Invalid hex string: {e}")
            return v
        return v


class SavedAction(BaseModel):
    id: str
    name: str
    description: str = ""
    color: str = "#00F0FF"
    hotkey: Optional[str] = None
    steps: List[ActionStep] = Field(default_factory=list)
    created_at: float = Field(default_factory=time.time)


class DeviceProfile(BaseModel):
    id: str
    name: str
    manufacturer: str
    description: str = ""
    cc_map: Dict[int, str] = Field(default_factory=dict)
    pc_map: Dict[int, str] = Field(default_factory=dict)
