"""
Configuration Persistence Engine with Atomic File Replacement, Durability (fsync),
Pydantic Validation, and Byte-for-Byte Future-Schema Preservation.
"""
import copy
import json
import os
from pathlib import Path
import tempfile
import threading
import time
from typing import Any, Dict, List, Optional

from ..core.models import PreferencesModel, SavedAction, PresetNumbering

CONFIG_SCHEMA_VERSION = 1

DEFAULT_CONFIG: Dict[str, Any] = {
    "schema_version": CONFIG_SCHEMA_VERSION,
    "last_saved_at": 0.0,
    "preferences": {
        "selected_output_name": None,
        "selected_input_name": None,
        "default_channel": 1,
        "preset_convention": PresetNumbering.ZERO_INDEXED.value,
        "clock_bpm": 120.0,
        "show_raw_clock_in_monitor": False,
        "enable_dark_stage_mode": True,
    },
    "actions": [
        {
            "id": "act_solo_boost",
            "name": "Solo Lead Boost",
            "description": "Switch amp modeler to Lead Channel and engage delay",
            "color": "#00F0FF",
            "hotkey": "1",
            "steps": [
                {
                    "id": "s1",
                    "target_port_name": "Virtual Amp Modeler [Out]",
                    "channel": 1,
                    "command_type": "PROGRAM_CHANGE",
                    "data1": 15,
                    "data2": 0,
                    "data3": 0,
                    "delay_ms": 25,
                },
                {
                    "id": "s2",
                    "target_port_name": "Virtual Ambient Delay [Out]",
                    "channel": 1,
                    "command_type": "CONTROL_CHANGE",
                    "data1": 64,
                    "data2": 127,
                    "data3": 0,
                    "delay_ms": 0,
                },
            ],
        },
        {
            "id": "act_clean_ambient",
            "name": "Clean Ambient Wash",
            "description": "Switch to clean chime preset with high reverb mix",
            "color": "#00FFA3",
            "hotkey": "2",
            "steps": [
                {
                    "id": "s1",
                    "target_port_name": "Virtual Amp Modeler [Out]",
                    "channel": 1,
                    "command_type": "PROGRAM_CHANGE",
                    "data1": 2,
                    "data2": 0,
                    "data3": 0,
                    "delay_ms": 20,
                },
                {
                    "id": "s2",
                    "target_port_name": "Virtual Ambient Delay [Out]",
                    "channel": 1,
                    "command_type": "CONTROL_CHANGE",
                    "data1": 11,
                    "data2": 100,
                    "data3": 0,
                    "delay_ms": 0,
                },
            ],
        },
    ],
    "custom_profiles": [],
}


class ConfigStore:
    """
    Manages persistent user preferences and saved actions.
    Guarantees:
    - Atomic writes using tempfile + os.replace.
    - Power-loss durability using os.fsync.
    - Deep copy isolation of default configs.
    - Strict byte-for-byte preservation of unsupported future-schema configuration files.
    """

    def __init__(self, config_path: Path):
        self.config_path = config_path
        self._data: Dict[str, Any] = {}
        self._is_future_schema: bool = False
        self._lock = threading.Lock()
        self.load()

    def load(self) -> Dict[str, Any]:
        with self._lock:
            if not self.config_path.exists():
                self._data = copy.deepcopy(DEFAULT_CONFIG)
                self._is_future_schema = False
                self._save_internal()
                return self._data

            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    loaded = json.load(f)

                schema_ver = loaded.get("schema_version", 0)
                if schema_ver > CONFIG_SCHEMA_VERSION:
                    print(
                        f"Warning: Configuration schema version {schema_ver} is newer than supported {CONFIG_SCHEMA_VERSION}. "
                        "Preserving file byte-for-byte in read-only mode to prevent data loss."
                    )
                    self._is_future_schema = True
                    self._data = copy.deepcopy(loaded)
                    return self._data

                self._is_future_schema = False

                # Validate preferences with Pydantic
                prefs_raw = loaded.get("preferences", {})
                try:
                    valid_prefs = PreferencesModel.model_validate(prefs_raw)
                    loaded["preferences"] = valid_prefs.model_dump()
                except Exception as ve:
                    print(f"Invalid preferences in config: {ve}, restoring default preferences.")
                    loaded["preferences"] = copy.deepcopy(DEFAULT_CONFIG["preferences"])

                self._data = loaded
                return self._data
            except Exception as e:
                print(f"Error loading configuration, falling back to defaults: {e}")
                self._data = copy.deepcopy(DEFAULT_CONFIG)
                self._is_future_schema = False
                return self._data

    def save(self) -> bool:
        with self._lock:
            return self._save_internal()

    def _save_internal(self) -> bool:
        """Atomic write using temporary file replacement to avoid corruption."""
        if self._is_future_schema:
            print(
                f"Cannot overwrite configuration with unsupported schema version {self._data.get('schema_version')}. "
                "Preserving existing on-disk file intact."
            )
            return False

        try:
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            self._data["schema_version"] = CONFIG_SCHEMA_VERSION
            self._data["last_saved_at"] = time.time()

            dir_name = self.config_path.parent
            with tempfile.NamedTemporaryFile("w", dir=dir_name, delete=False, encoding="utf-8") as tf:
                json.dump(self._data, tf, indent=2)
                tf.flush()
                os.fsync(tf.fileno())  # Durability flush to disk
                temp_name = tf.name

            # Atomic replace
            os.replace(temp_name, self.config_path)
            return True
        except Exception as e:
            print(f"Error saving config atomically: {e}")
            return False

    def get_preference(self, key: str, default: Any = None) -> Any:
        with self._lock:
            return self._data.get("preferences", {}).get(key, default)

    def set_preference(self, key: str, value: Any) -> None:
        with self._lock:
            if "preferences" not in self._data:
                self._data["preferences"] = {}
            if key == "clock_bpm":
                try:
                    value = max(40.0, min(300.0, float(value)))
                except (ValueError, TypeError):
                    value = 120.0
            self._data["preferences"][key] = value
            self._save_internal()

    def get_actions(self) -> List[Dict[str, Any]]:
        with self._lock:
            return copy.deepcopy(self._data.get("actions", []))

    def save_action(self, action: SavedAction) -> bool:
        with self._lock:
            if self._is_future_schema:
                return False
            actions = self._data.get("actions", [])
            for i, a in enumerate(actions):
                if a.get("id") == action.id:
                    actions[i] = action.model_dump()
                    return self._save_internal()
            actions.append(action.model_dump())
            self._data["actions"] = actions
            return self._save_internal()

    def delete_action(self, action_id: str) -> bool:
        with self._lock:
            if self._is_future_schema:
                return False
            actions = self._data.get("actions", [])
            initial_len = len(actions)
            self._data["actions"] = [a for a in actions if a.get("id") != action_id]
            if len(self._data["actions"]) < initial_len:
                return self._save_internal()
            return False

    def get_action_by_id(self, action_id: str) -> Optional[SavedAction]:
        with self._lock:
            for a in self._data.get("actions", []):
                if a.get("id") == action_id:
                    return SavedAction.model_validate(a)
            return None
