import os
import io
import sys
import speech_recognition as sr
from groq import Groq

# Path for inter-process communication
TRANSCRIPTION_FILE = "/tmp/speech_transcription.txt"

def listen_and_transcribe():
    """Listens for a single phrase, transcribes it, and saves it to a file."""
    # Initialize Groq client
    client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
    
    recognizer = sr.Recognizer()
    microphone = sr.Microphone(sample_rate=16000)
    
    print("✅ Ready to listen!")

    print("\nListening for your command...")
    try:
        with microphone as source:
            # Listen with reduced timeout for faster response (8 seconds max)
            audio_data = recognizer.listen(source, phrase_time_limit=8)
        
        print("🤫 Silence detected, transcribing...")
        
        # Get audio data in WAV format
        wav_bytes = audio_data.get_wav_data()
        audio_file = io.BytesIO(wav_bytes)
        audio_file.name = "audio.wav"
        
        # Transcribe with Groq Whisper API
        transcription = client.audio.transcriptions.create(
            file=("audio.wav", audio_file.read()),
            model="whisper-large-v3"
        )
        
        if transcription.text:
            print(f"💬 Transcription: {transcription.text}")
            # Write the transcription to the file for the LLM to process
            with open(TRANSCRIPTION_FILE, "w") as f:
                f.write(transcription.text)
        else:
            print("🤔 No text transcribed.")
            # Write empty string to signal no input
            with open(TRANSCRIPTION_FILE, "w") as f:
                f.write("")

    except sr.WaitTimeoutError:
        print("👂 No speech detected within the time limit.")
    except sr.UnknownValueError:
        print("🤔 Could not understand audio.")
    except Exception as e:
        print(f"❌ An error occurred during transcription: {e}")

if __name__ == "__main__":
    if not os.environ.get("GROQ_API_KEY"):
        sys.exit("❌ Error: GROQ_API_KEY is not set.")
    
    listen_and_transcribe()
