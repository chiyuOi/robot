import os
import sys
import json
import threading
import time
from groq import Groq

# --- Configuration ---
TRANSCRIPTION_FILE = "/tmp/speech_transcription.txt"
LLM_RESPONSE_FILE = "/tmp/llm_response.txt"
CHAT_HISTORY_FILE = "/tmp/chat_history.json"
LLM_DONE_SIGNAL = "/tmp/llm_done.txt" # Signal file to indicate completion
MAX_HISTORY_TURNS = 3  # Keep only 3 turns (6 messages) for speed

def main():
    """
    Main function to process transcription, stream LLM response, and manage history.
    """
    # 1. Initialize Groq Client
    try:
        client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
    except Exception as e:
        print(f"❌ Failed to initialize Groq client: {e}")
        sys.exit(1)

    # 2. Read Transcription
    if not os.path.exists(TRANSCRIPTION_FILE):
        print("LLM: Transcription file not found. Exiting.")
        return
    with open(TRANSCRIPTION_FILE, "r") as f:
        user_text = f.read().strip()

    if not user_text:
        print("LLM: No user text to process.")
        return

    # 3. Load Chat History (keep only last 3 turns for speed)
    if os.path.exists(CHAT_HISTORY_FILE):
        with open(CHAT_HISTORY_FILE, "r") as f:
            try:
                chat_history = json.load(f)
                # Keep only last 3 turns (6 messages) for faster processing
                if len(chat_history) > 6:
                    chat_history = chat_history[-6:]
            except json.JSONDecodeError:
                chat_history = []
    else:
        chat_history = []

    # 4. Prepare Messages for API
    system_prompt = "You are a concise voice assistant. Respond in 1-2 sentences maximum. Keep answers brief and natural."
    messages = [{"role": "system", "content": system_prompt}] + chat_history
    messages.append({"role": "user", "content": user_text})
    
    print(f"👤 User: {user_text}\n")

    # 5. Stream LLM Response with Threading for Faster File I/O
    full_response = ""
    file_lock = threading.Lock()  # Thread-safe file writes
    
    def write_chunk_async(chunk_text):
        """Write chunk to file with proper locking."""
        with file_lock:
            try:
                with open(LLM_RESPONSE_FILE, "a") as f:
                    f.write(chunk_text)
                    f.flush()  # Flush immediately for TTS to read
            except Exception as e:
                print(f"⚠️  Error writing chunk: {e}")
    
    try:
        # Stream response from Groq API
        stream = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            temperature=0.3,
            max_tokens=256,
            top_p=0.9,
            stream=True,
        )
        
        # Clear previous response file on first write
        with file_lock:
            with open(LLM_RESPONSE_FILE, "w") as f:
                pass
        
        print("🤖 Assistant: ", end="", flush=True)
        
        # Stream chunks: write to file in background thread, print to console
        for chunk in stream:
            content = chunk.choices[0].delta.content
            if content:
                print(content, end="", flush=True)
                full_response += content
                # Write to file asynchronously for faster streaming
                threading.Thread(target=write_chunk_async, args=(content,), daemon=True).start()
        
        print("\n") # Newline after assistant response

    except Exception as e:
        print(f"\n❌ Error during LLM stream: {e}")
        return
    finally:
        # Wait a brief moment for pending writes to complete
        time.sleep(0.1)
        # Signal that the LLM is done
        with open(LLM_DONE_SIGNAL, "w") as f:
            f.write("done")

    # 6. Update and Save Chat History
    chat_history.append({"role": "user", "content": user_text})
    chat_history.append({"role": "assistant", "content": full_response})
    # Keep history small for speed (max 3 turns = 6 messages)
    if len(chat_history) > 6:
        chat_history = chat_history[-6:]
    
    # Save without formatting indent to reduce I/O overhead
    with file_lock:
        with open(CHAT_HISTORY_FILE, "w") as f:
            json.dump(chat_history, f)

if __name__ == "__main__":
    if not os.environ.get("GROQ_API_KEY"):
        sys.exit("❌ Error: GROQ_API_KEY is not set.")
    main()
