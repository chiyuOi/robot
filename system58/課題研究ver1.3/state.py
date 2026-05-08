#state.py
from dataclasses import dataclass

@dataclass
class CameraState:
    c_inf: str | None

@dataclass
class VoiceState:
    v_inf: str | None

@dataclass
class State:
    voice: VoiceState
    camera: CameraState