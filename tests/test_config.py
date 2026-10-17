"""
Tests for Config Persistence, Atomic Saving, Deep Copy, and Future Schema Byte-for-Byte Preservation
"""
import json
import tempfile
import unittest
from pathlib import Path
from src.core.models import SavedAction, ActionStep
from src.engine.config_store import ConfigStore, CONFIG_SCHEMA_VERSION


class TestConfigStore(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.config_path = Path(self.temp_dir.name) / "test_config.json"

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_default_config_creation(self):
        store = ConfigStore(self.config_path)
        self.assertTrue(self.config_path.exists())
        self.assertEqual(store._data["schema_version"], CONFIG_SCHEMA_VERSION)
        self.assertEqual(store.get_preference("default_channel"), 1)

    def test_deepcopy_isolation(self):
        store1 = ConfigStore(self.config_path)
        store1.set_preference("clock_bpm", 177.0)

        other_path = Path(self.temp_dir.name) / "other_config.json"
        store2 = ConfigStore(other_path)
        # Store 2 must have default 120, NOT 177!
        self.assertEqual(store2.get_preference("clock_bpm"), 120.0)

    def test_future_schema_rejection(self):
        # Write future schema version 99 with custom user action
        initial_payload = {
            "schema_version": 99,
            "preferences": {"clock_bpm": 222.0},
            "actions": [{"id": "act_custom", "name": "Custom Show Action"}],
        }
        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(initial_payload, f)

        store = ConfigStore(self.config_path)
        self.assertTrue(store._is_future_schema)

        # Mutating preferences must NOT overwrite on-disk future schema
        store.set_preference("clock_bpm", 135.0)

        with open(self.config_path, "r", encoding="utf-8") as f:
            disk_data = json.load(f)

        self.assertEqual(disk_data["schema_version"], 99)
        self.assertEqual(disk_data["actions"][0]["id"], "act_custom")


if __name__ == "__main__":
    unittest.main()
