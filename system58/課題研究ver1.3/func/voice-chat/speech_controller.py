#!/usr/bin/env python3
"""
Speech Recognition Controller
Controls the transition from speechrecognition-stt.py (wake-word detection) 
to groq-whisper-stt.py (command transcription)
Async subprocess management for optimal parallelization.
"""

import subprocess
import sys
import os
import time
import signal
import tty
import termios
import asyncio

class SpeechController:
    def __init__(self):
        self.running = True
        self.old_settings = termios.tcgetattr(sys.stdin)
        signal.signal(signal.SIGINT, self.handle_shutdown)
        # Clean up signal files on start
        self.cleanup_files()

    def cleanup_files(self):
        """Remove temporary signal and data files."""
        for f in ["/tmp/llm_done.txt", "/tmp/speech_transcription.txt", "/tmp/llm_response.txt", "/tmp/chat_history.json"]:
            if os.path.exists(f):
                os.remove(f)

    def handle_shutdown(self, signum, frame):
        print("\n\n🛑 Shutting down...")
        self.running = False
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, self.old_settings)
        self.cleanup_files()
        sys.exit(0)

    def wait_for_space(self):
        """Waits for the spacebar to be pressed."""
        print("\n▶️ Press SPACE to talk, or Ctrl+C to exit.")
        try:
            tty.setcbreak(sys.stdin.fileno())
            while self.running:
                char = sys.stdin.read(1)
                if char == ' ':
                    break
        finally:
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, self.old_settings)

    async def run_script_async(self, script_name):
        """Run a Python script asynchronously using asyncio."""
        try:
            process = await asyncio.create_subprocess_exec(
                sys.executable,
                script_name,
                cwd=os.path.dirname(os.path.abspath(__file__)),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            if process.returncode != 0:
                print(f"⚠️  {script_name} exited with code {process.returncode}")
            return process.returncode
        except FileNotFoundError:
            print(f"❌ Error: {script_name} not found!")
            return 1
        except Exception as e:
            print(f"❌ Error running {script_name}: {e}")
            return 1

    async def run(self):
        """Main loop: Wait for space -> Transcribe -> Stream LLM & TTS in parallel."""
        print("\n" + "=" * 70)
        print("🚀 AI VOICE ASSISTANT (Press Space to Talk)")
        print("=" * 70)
        
        while self.running:
            # Run blocking I/O in executor thread to avoid blocking event loop
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self.wait_for_space)
            
            if not self.running:
                break

            # --- Step 1: Listen and Transcribe ---
            print("\n--- 🔴 Recording ---")
            await self.run_script_async("groq-whisper-stt.py")

            transcription_path = "/tmp/speech_transcription.txt"
            if not os.path.exists(transcription_path) or os.path.getsize(transcription_path) == 0:
                print("🤫 No speech detected, skipping.")
                continue

            # --- Step 2 & 3: Process LLM and Speak in Parallel (Streaming Mode) ---
            print("\n--- 💬 Processing & Speaking (Streaming + Async) ---")
            cycle_start = time.time()
            
            # Start both scripts concurrently using asyncio.gather
            llm_task = self.run_script_async("groq-llm.py")
            tts_task = self.run_script_async("edge-tts.py")
            
            # Wait for both to complete in parallel
            await asyncio.gather(llm_task, tts_task)
            
            cycle_latency = time.time() - cycle_start
            print(f"⏱️  LLM+TTS Cycle Latency: {cycle_latency:.2f}s")
            
            # Cleanup for the next cycle
            self.cleanup_files()
            
            print("\n✅ Cycle complete.")

if __name__ == "__main__":
    controller = SpeechController()
    try:
        asyncio.run(controller.run())
    except KeyboardInterrupt:
        print("\n\n🛑 Shutting down...")
        controller.cleanup_files()
        sys.exit(0)
