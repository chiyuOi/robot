# 🎤 Speech Recognition Controller

A simple orchestrator that manages the transition between two speech recognition programs:

## 🔄 Flow

```
speech_controller.py (Main orchestrator)
         ↓
    [PHASE 1]
    Run: speechrecognition-stt.py
    Task: Listen for "hey bro"
    ✓ Wake-word detected
         ↓
    [TRANSITION]
    Stop: speechrecognition-stt.py
    Start: groq-whisper-stt.py
         ↓
    [PHASE 2]
    Run: groq-whisper-stt.py
    Task: Record and transcribe user command
    ✓ Transcription complete
         ↓
    [DONE]
```

## 🚀 Quick Start

```bash
python speech_controller.py
```

That's it! The controller will automatically:
1. Start the wake-word detector
2. Wait for "hey bro"
3. Switch to Groq transcriber
4. Record and transcribe your command

## 📋 Requirements

Your original files must exist:
- `speechrecognition-stt.py` - Wake-word detector (unchanged)
- `groq-whisper-stt.py` - Groq transcriber (unchanged)

Libraries:
```bash
pip install speech_recognition groq sounddevice numpy
```

## 🎯 How It Works

The controller:
1. **Launches** `speechrecognition-stt.py` as a subprocess
2. **Monitors output** looking for the detection message
3. **Detects signal** when "hey bro" is recognized
4. **Terminates** the detector process
5. **Launches** `groq-whisper-stt.py` to handle the command
6. **Waits** for transcription to complete

## 🛑 Stop

Press `Ctrl+C` to stop the entire system gracefully.

## ⚙️ Key Features

✓ **No file modifications** - Uses your existing files as-is  
✓ **Subprocess management** - Launches/stops programs automatically  
✓ **Signal monitoring** - Detects wake-word from program output  
✓ **Graceful shutdown** - Ctrl+C properly terminates all processes  
✓ **Clear output** - Shows which phase you're in  

## 🔧 Customization

To change the wake word, edit `speechrecognition-stt.py` and modify:
```python
if text.lower() == "hey bro":
```

To change Groq model, edit `groq-whisper-stt.py` in the transcription call:
```python
model="whisper-large-v3-turbo"  # Change this
```
