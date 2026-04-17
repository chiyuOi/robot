import os
import io
import threading
from groq import Groq
from collections import deque
import sounddevice as sd
import numpy as np

client = Groq()

class RealtimeSpeechRecognizer:
    def __init__(self, sample_rate=16000, chunk_duration=2):
        """
        Initialize the real-time speech recognizer.
        
        Args:
            sample_rate: Audio sample rate in Hz (default: 16000)
            chunk_duration: Duration of each audio chunk in seconds
        """
        self.sample_rate = sample_rate
        self.chunk_size = int(sample_rate * chunk_duration)
        self.audio_queue = deque(maxlen=self.chunk_size * 2)
        self.is_recording = False
        self.stop_event = threading.Event()
        
    def audio_callback(self, indata, frames, time, status):
        """Callback for audio stream - adds incoming audio to queue."""
        if status:
            print(f"Audio status: {status}")
        # Add audio data to queue (convert to mono if needed)
        self.audio_queue.extend(indata[:, 0].astype(np.float32))
    
    def record_audio_chunks(self):
        """Record audio from microphone and process in chunks."""
        print("🎤 Starting real-time transcription... Press Ctrl+C to stop\n")
        
        try:
            with sd.InputStream(
                channels=1,
                samplerate=self.sample_rate,
                callback=self.audio_callback,
                blocksize=4096,
            ):
                chunk_buffer = []
                
                while not self.stop_event.is_set():
                    # Collect audio data
                    if len(self.audio_queue) >= self.chunk_size:
                        audio_chunk = np.array(
                            [self.audio_queue.popleft() for _ in range(self.chunk_size)]
                        )
                        chunk_buffer.extend(audio_chunk)
                        
                        # Process and transcribe if we have enough data
                        if len(chunk_buffer) >= self.chunk_size:
                            self.transcribe_chunk(np.array(chunk_buffer))
                            chunk_buffer = []
                    else:
                        sd.sleep(100)  # Sleep briefly to avoid busy waiting
                        
        except KeyboardInterrupt:
            print("\n\n✅ Recording stopped by user")
        finally:
            self.stop_event.set()
    
    def transcribe_chunk(self, audio_data):
        """Send audio chunk to Groq Whisper API for transcription."""
        try:
            # Convert float32 audio to PCM16 bytes
            audio_bytes = (audio_data * 32767).astype(np.int16).tobytes()
            
            # Create a file-like object
            audio_file = io.BytesIO(audio_bytes)
            audio_file.name = "audio.wav"
            
            # Send to Groq Whisper API
            transcription = client.audio.transcriptions.create(
                file=("audio.wav", audio_file.read()),
                model="whisper-large-v3-turbo",
                temperature=0,
                response_format="verbose_json",
            )
            
            if transcription.text.strip():  # Only print non-empty transcriptions
                print(f"🔊 Recognized: {transcription.text}")
                
        except Exception as e:
            print(f"❌ Transcription error: {e}")
    
    def start(self):
        """Start the real-time recognition."""
        self.is_recording = True
        self.stop_event.clear()
        self.record_audio_chunks()


class SimpleRealtimeRecognizer:
    """Simpler version - records longer audio chunks before transcribing."""
    
    def __init__(self, sample_rate=16000, record_duration=5):
        """
        Initialize simple recognizer.
        
        Args:
            sample_rate: Audio sample rate in Hz
            record_duration: Duration to record before transcribing
        """
        self.sample_rate = sample_rate
        self.record_duration = record_duration
    
    def record_and_transcribe(self):
        """Record audio and send to Groq for transcription."""
        print(f"🎤 Listening for {self.record_duration} seconds... Press Ctrl+C to stop\n")
        
        try:
            while True:
                print(f"Recording for {self.record_duration} seconds...")
                
                # Record audio
                audio_data = sd.rec(
                    int(self.sample_rate * self.record_duration),
                    samplerate=self.sample_rate,
                    channels=1,
                    dtype=np.float32
                )
                sd.wait()
                
                # Convert and transcribe
                audio_bytes = (audio_data.flatten() * 32767).astype(np.int16).tobytes()
                audio_file = io.BytesIO(audio_bytes)
                audio_file.name = "audio.wav"
                
                print("Sending to Groq Whisper API...")
                transcription = client.audio.transcriptions.create(
                    file=("audio.wav", audio_file.read()),
                    model="whisper-large-v3-turbo",
                    temperature=0,
                    response_format="verbose_json",
                )
                
                if transcription.text.strip():
                    print(f"✅ Recognized: {transcription.text}\n")
                else:
                    print("⚠️  No speech detected\n")
                    
        except KeyboardInterrupt:
            print("\n\n✅ Stopped")


if __name__ == "__main__":
    import sys
    
    print("=" * 60)
    print("🎙️  GROQ REAL-TIME SPEECH RECOGNITION")
    print("=" * 60)
    print("\nChoose mode:")
    print("1. Simple mode (5-second chunks)")
    print("2. Continuous mode (real-time streaming chunks)")
    print("3. File mode (transcribe audio.m4a file)")
    
    choice = input("\nEnter your choice (1-3): ").strip()
    
    if choice == "1":
        recognizer = SimpleRealtimeRecognizer(record_duration=5)
        recognizer.record_and_transcribe()
        
    elif choice == "2":
        recognizer = RealtimeSpeechRecognizer(sample_rate=16000, chunk_duration=2)
        recognizer.start()
        
    elif choice == "3":
        filename = os.path.dirname(__file__) + "/audio.m4a"
        if os.path.exists(filename):
            print(f"🎤 Transcribing {filename}...\n")
            with open(filename, "rb") as file:
                transcription = client.audio.transcriptions.create(
                    file=(filename, file.read()),
                    model="whisper-large-v3-turbo",
                    temperature=0,
                    response_format="verbose_json",
                )
                print(f"✅ Transcription: {transcription.text}")
        else:
            print(f"❌ File not found: {filename}")
    else:
        print("Invalid choice")
