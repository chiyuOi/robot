"""
Data Management Package
- state.py: Data classes
- manager.py: Central state management
"""

from .state import State, CameraState, VoiceState
from .manager import DataManager, get_data_manager

__all__ = ['State', 'CameraState', 'VoiceState', 'DataManager', 'get_data_manager']
