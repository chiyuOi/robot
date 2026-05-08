#!/usr/bin/env python3
"""
Audio Feedback System
Provides audio cues for user feedback at different pipeline stages
"""

import os
import subprocess
import sys
from enum import Enum

class FeedbackType(Enum):
    STARTUP = "beep"
    WAKE_WORD_DETECTED = "ding"
    RECORDING_START = "rec"
    PROCESSING = "thinking"
    RESPONSE_READY = "ready"
    ERROR = "error"
    SUCCESS = "success"

class AudioFeedback:
    """Generate system feedback sounds using text-to-speech"""
    
    def __init__(self, enabled=True, volume=0.5):
        self.enabled = enabled
        self.volume = volume
        self.cache_dir = "/tmp/audio_cache"
        os.makedirs(self.cache_dir, exist_ok=True)
    
    def play_feedback(self, feedback_type: FeedbackType):
        """Play feedback sound"""
        if not self.enabled:
            return
        
        try:
            # Map feedback types to descriptions
            descriptions = {
                FeedbackType.STARTUP: "System ready",
                FeedbackType.WAKE_WORD_DETECTED: "Wake word detected",
                FeedbackType.RECORDING_START: "Recording started",
                FeedbackType.PROCESSING: "Processing",
                FeedbackType.RESPONSE_READY: "Response ready",
                FeedbackType.ERROR: "Error occurred",
                FeedbackType.SUCCESS: "Success",
            }
            
            description = descriptions.get(feedback_type, "Beep")
            
            # Use System sounds on macOS
            if sys.platform == "darwin":
                self._play_macos_sound(feedback_type)
            elif sys.platform == "linux":
                self._play_linux_sound(feedback_type)
            elif sys.platform == "win32":
                self._play_windows_sound(feedback_type)
        except Exception as e:
            print(f"[AudioFeedback] Error: {e}")
    
    def _play_macos_sound(self, feedback_type: FeedbackType):
        """Play sound on macOS"""
        sound_map = {
            FeedbackType.STARTUP: "Glass",
            FeedbackType.WAKE_WORD_DETECTED: "Ping",
            FeedbackType.RECORDING_START: "Pop",
            FeedbackType.PROCESSING: "Submarine",
            FeedbackType.RESPONSE_READY: "Ding",
            FeedbackType.ERROR: "Basso",
            FeedbackType.SUCCESS: "Purr",
        }
        sound = sound_map.get(feedback_type, "Glass")
        os.system(f"afplay /System/Library/Sounds/{sound}.aiff > /dev/null 2>&1 &")
    
    def _play_linux_sound(self, feedback_type: FeedbackType):
        """Play sound on Linux"""
        try:
            import pyaudio
            import numpy as np
            
            # Generate simple beep tones
            frequencies = {
                FeedbackType.STARTUP: 440,
                FeedbackType.WAKE_WORD_DETECTED: 880,
                FeedbackType.RECORDING_START: 660,
                FeedbackType.PROCESSING: 550,
                FeedbackType.RESPONSE_READY: 1000,
                FeedbackType.ERROR: 200,
                FeedbackType.SUCCESS: 700,
            }
            freq = frequencies.get(feedback_type, 440)
            self._generate_tone(freq, 0.3)
        except:
            pass
    
    def _play_windows_sound(self, feedback_type: FeedbackType):
        """Play sound on Windows"""
        try:
            import winsound
            frequency_map = {
                FeedbackType.STARTUP: 1000,
                FeedbackType.WAKE_WORD_DETECTED: 1200,
                FeedbackType.RECORDING_START: 800,
                FeedbackType.PROCESSING: 600,
                FeedbackType.RESPONSE_READY: 1500,
                FeedbackType.ERROR: 200,
                FeedbackType.SUCCESS: 1000,
            }
            duration = 200
            frequency = frequency_map.get(feedback_type, 1000)
            winsound.Beep(frequency, duration)
        except:
            pass
    
    def _generate_tone(self, frequency, duration):
        """Generate a tone using pyaudio"""
        try:
            import pyaudio
            import numpy as np
            
            SAMPLE_RATE = 44100
            frames = int(duration * SAMPLE_RATE)
            t = np.linspace(0, duration, frames)
            wave = np.sin(2 * np.pi * frequency * t) * 0.3
            wave = (wave * 32767).astype(np.int16)
            
            p = pyaudio.PyAudio()
            stream = p.open(format=pyaudio.paInt16, channels=1, 
                          rate=SAMPLE_RATE, output=True)
            stream.write(wave.tobytes())
            stream.close()
            p.terminate()
        except:
            pass
    
    def set_volume(self, volume):
        """Set feedback volume (0.0-1.0)"""
        self.volume = max(0.0, min(1.0, volume))
    
    def toggle(self):
        """Toggle feedback on/off"""
        self.enabled = not self.enabled
        return self.enabled


# Global instance
_feedback_instance = None

def get_feedback():
    """Get or create global feedback instance"""
    global _feedback_instance
    if _feedback_instance is None:
        _feedback_instance = AudioFeedback()
    return _feedback_instance


if __name__ == "__main__":
    fb = AudioFeedback()
    fb.play_feedback(FeedbackType.STARTUP)
    fb.play_feedback(FeedbackType.WAKE_WORD_DETECTED)
    fb.play_feedback(FeedbackType.RECORDING_START)
    fb.play_feedback(FeedbackType.RESPONSE_READY)
