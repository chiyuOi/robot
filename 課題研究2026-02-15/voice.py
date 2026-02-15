import speech_recognition as sr
from ollama import Client  # Changed import for clarity and consistency
from gtts import gTTS
import tempfile
import sounddevice as sd
import soundfile as sf
import time
import sys
from pynput import keyboard
import os  # Added for file removal (TTS cleanup)

# --- SETTINGS ---
lang = "ja"
# lang = "en"


language_stt = "ja-JP"
# language_stt = "en-US"

key_held = False
# LLM_MODEL = "gemma3:270m" # Defined model variable
# LLM_MODEL="gpt-oss:120b-cloud"
LLM_MODEL = "deepseek-v3.1:671b-cloud"
# --- CONTEXT/MEMORY SETUP ---
# This list stores the conversation history
# Start with a system message to define the robot's persona (Crucial for memory)
chat_history = [
    {
        "role": "system",
        # Use a strong instruction to keep it concise, helping with speed
        "content": f"You are Alex, a helpful and very concise robot voice assistant. Keep your responses brief and to the point in {lang}-language. Don't use any special letters."
    }
]
MAX_HISTORY_LENGTH = 10  # Total messages (user + assistant) to remember, excluding the system prompt.


# -----Keyboard press ----
def on_press(key):
    global key_held
    try:
        if key.char == 'a' and not key_held:
            key_held = True
    except AttributeError:
        pass


def on_release(key):
    global key_held
    try:
        if key.char == 'a':
            key_held = False
    except AttributeError:
        # Check for Escape key to exit program
        if key == keyboard.Key.esc:
            print("\nExiting program.")
            sys.exit(0)
        pass


listener = keyboard.Listener(on_press=on_press, on_release=on_release)
listener.start()

# --- Initialize Ollama Client ---
# Ollama runs on its own service, connecting via local network interface
try:
    ollama_client = Client('http://127.0.0.1:11434')
except Exception as e:
    print(f"[OLLAMA ERROR] Could not connect to Ollama client: {e}")
    print("Ensure Ollama is running.")
    sys.exit(1)


# --- AI RESPONSE (MODIFIED TO USE HISTORY) ---
def tell(text):
    """Sends text and context to the LLM, updates history, and returns response."""
    global chat_history

    # 1. Add the new user message to the history
    chat_history.append({"role": "user", "content": text})

    # 2. Trim history to prevent it from getting too long and slowing down the LLM
    # We keep the system prompt (index 0) and the last MAX_HISTORY_LENGTH messages.
    if len(chat_history) > MAX_HISTORY_LENGTH + 1:
        chat_history = [chat_history[0]] + chat_history[-(MAX_HISTORY_LENGTH):]

    print(f"[LLM] Sending prompt with {len(chat_history) - 1} turns of history...")

    try:
        # 3. Call the LLM with the full conversation history (the magic happens here)
        response = ollama_client.chat(
            model=LLM_MODEL,
            messages=chat_history  # <--- Pass the entire history list
        )

        ai_text = response["message"]["content"]
        print("AI:", ai_text)

        # 4. Add the AI's response to the history for the next turn
        chat_history.append({"role": "assistant", "content": ai_text})

        return ai_text

    except Exception as e:
        error_message = f"[ERROR] Ollama failed: {type(e).__name__}: {e}"
        print(error_message)
        # Revert the history state by removing the last user message if the call fails
        chat_history.pop()
        return "I'm having trouble connecting to my brain right now."


# --- TTS ---
def say(text):
    """Generates and plays TTS audio."""
    # Note: Using tempfile is fine, but we'll manually ensure cleanup here.
    TTS_FILENAME = "temp_tts.mp3"

    try:
        tts = gTTS(text=text, lang=lang)
        tts.save(TTS_FILENAME)

        # Load and play the audio
        data, samplerate = sf.read(TTS_FILENAME, dtype='float32')
        sd.play(data, samplerate)
        sd.wait()

        # Cleanup
        if os.path.exists(TTS_FILENAME):
            os.remove(TTS_FILENAME)

    except Exception as e:
        print(f"[TTS ERROR] Could not speak response: {e}")


# --- MICROPHONE SETUP (Unchanged) ---
recognizer = sr.Recognizer()
mic_source = sr.Microphone()

with mic_source as source:
    recognizer.adjust_for_ambient_noise(source, duration=5)
    print("Adjusting for ambient noise... Please wait for 5 seconds")

# --- MAIN LOOP ---
TEXT_MAP = {
    "en": {
        "title": "Robot Voice Assistant",
        "action": "ACTION: Press and HOLD 'a' to speak. Press ESC to exit.",
        "greeting": "Hello! I am Raspberry Pi, ready to chat."
    },
    "ja": {
        "title": "ロボット音声アシスタント",
        "action": "操作: 'a' を長押しして話し、ESCで終了します。",
        "greeting": "こんにちは！私はラズパイ、お話する準備ができました。"
    }
}
current_text = TEXT_MAP.get(lang, TEXT_MAP["en"])
spacing = 60
separetor = "="
print(separetor * spacing)
print(f"       {current_text['title']} ({LLM_MODEL})       ")
print(current_text["action"])
print(separetor * spacing)
say(current_text["greeting"] + current_text["action"])
while True:
    try:
        print("\nPress 'a' to start conversation...")

        # Wait for key press
        while not key_held:
            time.sleep(0.05)
            # Check if listener was stopped (ESC press)
            if not listener.running:
                sys.exit(0)

        print("\n[LISTEN MODE] Speak now...")

        with mic_source as source:
            # Added a timeout to prevent infinite blocking if the mic is disconnected
            audio = recognizer.listen(source)
            # add ,timeout=10 if needed

        try:
            # Using Google STT (Requires internet)
            text = recognizer.recognize_google(audio, language=language_stt)
            print("You:", text)

            # --- CONTEXT/MEMORY USAGE HERE ---
            ai_text = tell(text)

            # Use the single-argument say function
            say(ai_text)

        except sr.UnknownValueError:
            print("[STT] Could not understand audio.")

        except sr.RequestError as e:
            print(
                f"[STT ERROR] Could not request results from Google Speech Recognition service; check internet connection. {e}")

    except KeyboardInterrupt:
        print("\nExiting program.")
        sys.exit(0)

    except Exception as e:
        print(f"Unexpected error: {type(e).__name__}: {e}")
        time.sleep(1)