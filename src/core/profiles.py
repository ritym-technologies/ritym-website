"""
Curated Device Profiles with Verified Parameter Mappings from Manufacturer Manuals
"""
from typing import Dict, Optional
from .models import DeviceProfile


STANDARD_MIDI_PROFILE = DeviceProfile(
    id="general_midi",
    name="General MIDI 1.0 / Generic Pedal",
    manufacturer="Standard",
    description="Universal standard MIDI controllers and switches",
    cc_map={
        0: "Bank Select MSB",
        1: "Modulation",
        7: "Master Volume",
        10: "Pan",
        11: "Expression Controller",
        32: "Bank Select LSB",
        64: "Sustain / Damper Switch",
        120: "All Sound Off",
        121: "Reset All Controllers",
        123: "All Notes Off",
    },
    pc_map={},
)

STRYMON_TIMELINE_PROFILE = DeviceProfile(
    id="strymon_timeline",
    name="Strymon TimeLine Delay",
    manufacturer="Strymon",
    description="Dedicated delay processor",
    cc_map={
        11: "Expression Pedal",
        93: "Tap Tempo",
        97: "Infinite Repeats / Hold",
        102: "Bypass / Engage Toggle",
    },
    pc_map={
        0: "Bank 00A",
        1: "Bank 00B",
        2: "Bank 01A",
        3: "Bank 01B",
    },
)

STRYMON_BIGSKY_PROFILE = DeviceProfile(
    id="strymon_bigsky",
    name="Strymon BigSky Reverb",
    manufacturer="Strymon",
    description="Dedicated reverberator (Manual Rev D)",
    cc_map={
        100: "Expression Pedal (BigSky Manual p.23)",
        97: "Freeze / Infinite Reverb",
        102: "Bypass / Engage Toggle",
    },
    pc_map={
        0: "Preset 00A",
        1: "Preset 00B",
        2: "Preset 00C (BigSky Manual p.23)",
    },
)

LINE6_HELIX_PROFILE = DeviceProfile(
    id="line6_helix",
    name="Line 6 Helix / HX Stomp",
    manufacturer="Line 6",
    description="Amp modeler and multi-effects",
    cc_map={
        49: "Footswitch 1 Emulation",
        50: "Footswitch 2 Emulation",
        51: "Footswitch 3 Emulation",
        52: "Footswitch 4 Emulation",
        53: "Footswitch 5 Emulation",
        59: "Tap Tempo",
        68: "Tuner Screen Toggle",
        71: "Snapshot Select (0=1, 1=2, 2=3)",
    },
    pc_map={
        0: "Preset 01A",
        1: "Preset 01B",
        2: "Preset 01C",
        3: "Preset 01D",
    },
)

BOSS_500_PROFILE = DeviceProfile(
    id="boss_500",
    name="Boss 500 Series (DD-500, RV-500, MD-500)",
    manufacturer="Boss / Roland",
    description="Advanced digital processing pedals",
    cc_map={
        16: "CTL 1 Switch",
        17: "CTL 2 Switch",
        27: "Effect Bypass / On",
        28: "Tap Tempo",
        82: "Roll / Hold Effect",
    },
    pc_map={},
)

EVENTIDE_H9_PROFILE = DeviceProfile(
    id="eventide_h9",
    name="Eventide H9 / H90 Harmonizer",
    manufacturer="Eventide",
    description="Multi-effects processor",
    cc_map={
        1: "Ribbon Controller",
        11: "Expression",
        80: "Tap Tempo",
        81: "HotSwitch Toggle",
    },
    pc_map={},
)


class ProfileRegistry:
    def __init__(self):
        self._profiles: Dict[str, DeviceProfile] = {
            STANDARD_MIDI_PROFILE.id: STANDARD_MIDI_PROFILE,
            STRYMON_TIMELINE_PROFILE.id: STRYMON_TIMELINE_PROFILE,
            STRYMON_BIGSKY_PROFILE.id: STRYMON_BIGSKY_PROFILE,
            LINE6_HELIX_PROFILE.id: LINE6_HELIX_PROFILE,
            BOSS_500_PROFILE.id: BOSS_500_PROFILE,
            EVENTIDE_H9_PROFILE.id: EVENTIDE_H9_PROFILE,
        }

    def list_profiles(self) -> Dict[str, DeviceProfile]:
        return self._profiles.copy()

    def get_profile(self, profile_id: str) -> Optional[DeviceProfile]:
        return self._profiles.get(profile_id)

    def register_profile(self, profile: DeviceProfile):
        self._profiles[profile.id] = profile


def get_default_profile() -> DeviceProfile:
    return STANDARD_MIDI_PROFILE
