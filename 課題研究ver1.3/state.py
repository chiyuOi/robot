from dataclasses import dataclass


@dataclass
class CameraState:
    a:123


@dataclass
class VoiceState:
    a:123


@dataclass
class State:
    voice: VoiceState
    camera: CameraState