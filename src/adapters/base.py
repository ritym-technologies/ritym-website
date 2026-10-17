"""
Abstract Base Classes for Platform MIDI Adapters
"""
from abc import ABC, abstractmethod
from enum import Enum
from typing import List, Callable, Optional, Dict, Any
from pydantic import BaseModel, Field


class PortDirection(str, Enum):
    INPUT = "IN"
    OUTPUT = "OUT"


class MidiPortInfo(BaseModel):
    id: str
    name: str
    direction: PortDirection
    is_virtual: bool = False
    is_connected: bool = True
    system_index: int = 0
    manufacturer: str = "Unknown"
    driver_version: str = "1.0"
    is_busy: bool = False
    error_message: Optional[str] = None


MidiInputCallback = Callable[[str, bytes, float], None]


class MidiAdapterBase(ABC):
    """
    Abstract interface guaranteeing cross-platform capability.
    Platform-specific implementations (WinMM, CoreMIDI, Android) inherit from this.
    """

    @abstractmethod
    def refresh_ports(self) -> None:
        """Scan and discover all available ports."""
        pass

    @abstractmethod
    def get_input_ports(self) -> List[MidiPortInfo]:
        """Return list of discovered input ports."""
        pass

    @abstractmethod
    def get_output_ports(self) -> List[MidiPortInfo]:
        """Return list of discovered output ports."""
        pass

    @abstractmethod
    def open_output(self, port_id: str) -> bool:
        """Open a specific output port for sending."""
        pass

    @abstractmethod
    def close_output(self, port_id: str) -> None:
        """Close an output port."""
        pass

    @abstractmethod
    def open_input(self, port_id: str, callback: MidiInputCallback) -> bool:
        """Open an input port and register message callback."""
        pass

    @abstractmethod
    def close_input(self, port_id: str) -> None:
        """Close an input port."""
        pass

    @abstractmethod
    def send_bytes(self, port_id: str, data: bytes) -> bool:
        """Transmit raw bytes to the specified output port."""
        pass

    @abstractmethod
    def close_all(self) -> None:
        """Emergency cleanup of all open handles."""
        pass
