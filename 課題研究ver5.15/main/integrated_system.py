#!/usr/bin/env python3
"""
Integrated AI Robot System (アルゴリズム統合システム)
5-Stage Pipeline:
1. 感知 (Sensing) - Wake word + Speech Recognition
2. 計画 (Planning) - Groq #1 selects appropriate tool
3. 行動 & 観察 (Action & Observation) - Execute selected tool (YOLO, etc.)
4. 統合 (Integration) - Groq #2 generates response + motor commands
5. 実行 (Execution) - Parallel execution of speech + motor commands
"""

import asyncio
import json
import os
import sys
import cv2
import numpy as np
import time
import base64
from pathlib import Path
from typing import Dict, Any, Optional, List
from dotenv import load_dotenv

# Load environment variables early
load_dotenv()

# Setup project paths properly - add project root, not subdirectories
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import existing modules using full paths
from main.api_client import AutoRotatingAPIClient, OpenRouterClient
from main.ai import Ai
from func.motion.motor import StepperManager
from data.state import State, CameraState, VoiceState
from ultralytics import YOLO
import threading
# STAGE 1: SENSING - Wake Word Detection & Speech Recognition
# ============================================================================

class SensingModule:
    """Detects wake word and captures user speech"""
    
    def __init__(self):
        self.transcription_file = "/tmp/speech_transcription.txt"
        self.wake_word = "ねえロボット"
        self.is_recording = False
    
    async def wait_for_wakeword(self):
        """Wait for wake word using speech recognition"""
        print("\n🎤 Waiting for wake word...")
        # In production, this would use groq-whisper-stt.py
        # For testing, we'll simulate with user input
        user_input = input("🎙️ Say something (or type to simulate): ").strip()
        
        if not user_input:
            return None
        
        # Store transcription
        with open(self.transcription_file, "w") as f:
            f.write(user_input)
        
        return user_input
    
    async def get_user_input(self, input_method: str = "auto") -> str:
        """Get user input via voice or keyboard
        
        Args:
            input_method: "voice", "keyboard", or "auto" (user chooses)
        
        Returns:
            User input text
        """
        if input_method == "auto":
            print("\n📍 入力方式を選択してください:")
            print("1. 🎤 音声入力（マイク）")
            print("2. ⌨️  キーボード入力")
            choice = input("選択 (1-2): ").strip()
            input_method = "voice" if choice == "1" else "keyboard"
        
        if input_method == "voice":
            return await self._get_voice_input()
        else:
            return await self._get_keyboard_input()
    
    async def _get_voice_input(self) -> str:
        """Get input from voice"""
        print("\n🎤 音声入力を開始します...")
        print("   マイクに向かってコマンドを話してください...")
        
        try:
            # Try to use groq-whisper-stt if available
            import subprocess
            import os
            
            # Create a signal file for the STT process
            signal_file = "/tmp/speech_transcription.txt"
            
            # Run speech recognition in a subprocess
            script_path = os.path.join(
                os.path.dirname(__file__),
                "..",
                "func",
                "voice-chat",
                "groq-whisper-stt.py"
            )
            
            if os.path.exists(script_path):
                print("   (Groq Whisper STT を使用中...)")
                # Run the script and wait for it
                result = subprocess.run(
                    ["python3", script_path],
                    capture_output=True,
                    timeout=15
                )
                
                # Read the transcription
                if os.path.exists(signal_file):
                    with open(signal_file, "r") as f:
                        text = f.read().strip()
                    if text:
                        print(f"   📝 認識されたテキスト: {text}")
                        return text
            else:
                print(f"   ⚠️  STT スクリプトが見つかりません: {script_path}")
        
        except Exception as e:
            print(f"   ⚠️  音声認識エラー: {e}")
        
        # Fallback to keyboard input
        print("   キーボード入力にフォールバック...")
        return await self._get_keyboard_input()
    
    async def _get_keyboard_input(self) -> str:
        """Get input from keyboard"""
        print("\n⌨️  キーボード入力:")
        text = input(">>> ").strip()
        
        if not text:
            print("❌ 入力がありません")
            return await self._get_keyboard_input()
        
        print(f"📝 入力されたテキスト: {text}")
        
        # Store in transcription file for consistency
        with open(self.transcription_file, "w") as f:
            f.write(text)
        
        return text
    
    async def get_user_speech(self) -> str:
        """Get the user's speech transcription"""
        if os.path.exists(self.transcription_file):
            with open(self.transcription_file, "r") as f:
                return f.read().strip()
        return ""


# ============================================================================
# STAGE 2: PLANNING - Tool Selection via Groq #1
# ============================================================================

class PlanningModule:
    """Uses Groq API to decide which tool to use"""
    
    PLANNING_PROMPT = """
あなたはロボットの意思決定AIです。ユーザーの質問に対して、以下のツールから最も適切なものを選択してください。

利用可能なツール:
- "YOLO": 物体検出を実行。目標の位置座標（X, Y）を取得できます
- "COLOR_TRACK": 特定の色を追跡します
- "MOTION_ONLY": 単純な動作コマンドのみを実行します
- "CONVERSATION": 会話のみで応答します

重要: 以下の形式で**有効なJSON（コメントなし）**のみを返してください。他の言葉は一切出力しないでください:
{"tool": "YOLO", "target": "検出対象", "reasoning": "理由"}
"""
    
    def __init__(self, api_client: AutoRotatingAPIClient):
        self.ai = Ai(
            api_client=api_client,
            prompt=self.PLANNING_PROMPT,
            api_url="https://api.groq.com/openai/v1/chat/completions",
            model="llama-3.1-8b-instant",  # Updated to supported model
            temperature=0.5,
            keep_history=False
        )
    
    def select_tool(self, user_input: str) -> Dict[str, Any]:
        """Select appropriate tool based on user input"""
        print(f"\n🧠 Planning (Groq #1): Analyzing user request...")
        print(f"   User said: {user_input}")
        
        try:
            response = self.ai.send(user_input)
            print(f"   Response: {response}")
            
            # Parse JSON response
            tool_config = json.loads(response)
            print(f"   Selected tool: {tool_config['tool']}")
            return tool_config
        except json.JSONDecodeError:
            print(f"⚠️  Failed to parse tool selection, defaulting to CONVERSATION")
            return {
                "tool": "CONVERSATION",
                "target": None,
                "reasoning": "Failed to parse response"
            }


# ============================================================================
# STAGE 3: ACTION & OBSERVATION - Execute Selected Tool
# ============================================================================

class ActionModule:
    """Executes the selected tool and returns observations"""
    
    def __init__(self, api_client: Optional[AutoRotatingAPIClient] = None):
        self.yolo_model = None
        self.camera = None
        self.lock = threading.Lock()
        self.latest_results = []
        self.api_client = api_client
        self._load_yolo_model()
    
    def _load_yolo_model(self):
        """Load YOLO model for object detection"""
        try:
            # Try to load the model from the camera folder
            model_path = Path(__file__).parent.parent / "func" / "camera" / "YOLO26n-seg.pt"
            if model_path.exists():
                self.yolo_model = YOLO(str(model_path))
                print("✅ YOLO model loaded successfully")
            else:
                print(f"⚠️  YOLO model not found at {model_path}")
        except Exception as e:
            print(f"⚠️  Failed to load YOLO model: {e}")
    
    async def execute(self, tool_config: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the selected tool"""
        tool = tool_config.get("tool", "CONVERSATION")
        
        if tool == "YOLO":
            return await self._execute_yolo(tool_config)
        elif tool == "COLOR_TRACK":
            return await self._execute_color_track(tool_config)
        elif tool == "MOTION_ONLY":
            return {"action": "motion_ready", "details": "Ready for motion commands"}
        else:
            return {"action": "conversation_ready", "details": "Ready for conversation"}
    
    async def _execute_yolo(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Execute YOLO object detection + Llama-4-Scout image description in parallel"""
        print("\n🎯 Action (YOLO Execution): Detecting objects...")
        
        if self.yolo_model is None:
            return {"status": "error", "message": "YOLO model not loaded"}
        
        try:
            # Open camera
            cap = cv2.VideoCapture(0)
            if not cap.isOpened():
                return {"status": "error", "message": "Cannot open camera"}
            
            # Capture a frame
            ret, frame = cap.read()
            cap.release()
            
            if not ret:
                return {"status": "error", "message": "Failed to capture frame"}
            
            # Save frame temporarily for Llama-4-Scout
            temp_image_path = "/tmp/captured_frame.jpg"
            cv2.imwrite(temp_image_path, frame)
            
            # Run YOLO inference and Llama-4-Scout in parallel
            yolo_task = asyncio.create_task(self._run_yolo_inference(frame, config))
            llama_task = asyncio.create_task(self._generate_image_description(temp_image_path, config))
            
            yolo_results = await yolo_task
            image_description = await llama_task
            
            # Extract detection results
            detections = []
            target = config.get("target", "").lower()
            
            for result in yolo_results:
                for box in result.boxes:
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    cx = int((x1 + x2) / 2)
                    cy = int((y1 + y2) / 2)
                    cls = int(box.cls[0])
                    label = result.names[cls].lower()
                    conf = float(box.conf[0])
                    
                    # If target is specified, filter for matching objects
                    if target and target in label:
                        detections.append({
                            "label": label,
                            "x": cx,
                            "y": cy,
                            "confidence": conf,
                            "bbox": [x1, y1, x2, y2]
                        })
                    elif not target:
                        # Return all detections if no specific target
                        detections.append({
                            "label": label,
                            "x": cx,
                            "y": cy,
                            "confidence": conf,
                            "bbox": [x1, y1, x2, y2]
                        })
            
            # Sort by confidence and take top detection
            detections.sort(key=lambda x: x["confidence"], reverse=True)
            
            if detections:
                top_detection = detections[0]
                print(f"   Found: {top_detection['label']} at ({top_detection['x']}, {top_detection['y']})")
                print(f"   📸 Image Description: {image_description}")
                return {
                    "status": "success",
                    "action": "object_detected",
                    "detections": detections,
                    "primary": top_detection,
                    "image_description": image_description
                }
            else:
                print(f"   No objects detected for target: {target}")
                print(f"   📸 Image Description: {image_description}")
                return {
                    "status": "success",
                    "action": "no_object_found",
                    "detections": [],
                    "image_description": image_description
                }
        
        except Exception as e:
            print(f"⚠️  Error in YOLO execution: {e}")
            return {"status": "error", "message": str(e)}
    
    async def _run_yolo_inference(self, frame: np.ndarray, config: Dict[str, Any]):
        """Run YOLO inference in async context"""
        return self.yolo_model(frame, imgsz=320, conf=0.5, verbose=False)
    
    async def _generate_image_description(self, image_path: str, config: Dict[str, Any]) -> str:
        """Generate image description using OpenRouter's vision model"""
        try:
            print("🖼️  OpenRouter (Nemotron): Generating image description with vision...")
            
            # Initialize OpenRouter client
            openrouter = OpenRouterClient()
            
            # Read and encode image as base64
            with open(image_path, "rb") as img_file:
                image_data = base64.standard_b64encode(img_file.read()).decode("utf-8")
            
            # Generate description based on user context
            user_target = config.get("target", "")
            if user_target:
                prompt = f"This image is being analyzed by a robot. Please describe what you see, particularly focusing on finding: {user_target}. Provide a detailed description in Japanese."
            else:
                prompt = "This image is being analyzed by a robot. Please describe what you see in detail in Japanese."
            
            # Call OpenRouter with image
            description = openrouter.describe_image(image_data, prompt)
            
            print(f"   ✅ Description generated via OpenRouter Vision")
            return description
            
        except Exception as e:
            print(f"⚠️  OpenRouter error: {e}")
            return f"(Description generation skipped: {str(e)[:80]})"
    
    async def _execute_color_track(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Execute color tracking"""
        print("\n🎨 Action (Color Track): Tracking color...")
        # Implementation placeholder
        return {
            "status": "success",
            "action": "color_tracked",
            "coordinates": [320, 240]
        }


# ============================================================================
# STAGE 4: INTEGRATION - Response Generation via Groq #2
# ============================================================================

class IntegrationModule:
    """Uses Groq API to generate response and motor commands based on observations"""
    
    INTEGRATION_PROMPT = """
あなたはロボットの統合制御AIです。観測結果に基づいて、適切な応答とモーターコマンドを生成してください。

重要: 以下の形式で**有効なJSON（コメントなし）**のみを返してください。他の言葉は一切出力しないでください:
{"speech": "音声応答", "motor_commands": [{"axis": "a", "angle": 10}], "status": "success"}

軸の説明:
- "a", "b", "c", "d": 各ステッパーモーター軸
- angle: 相対角度（度数）（正=時計回り、負=反時計回り）
"""
    
    def __init__(self, api_client: AutoRotatingAPIClient):
        self.ai = Ai(
            api_client=api_client,
            prompt=self.INTEGRATION_PROMPT,
            api_url="https://api.groq.com/openai/v1/chat/completions",
            model="llama-3.1-8b-instant",  # Updated to supported model
            temperature=0.7,
            keep_history=False
        )
    
    def generate_response(self, observation: Dict[str, Any], user_input: str) -> Dict[str, Any]:
        """Generate response and motor commands based on observations"""
        print(f"\n🔄 Integration (Groq #2): Generating response...")
        
        # Extract image description if available
        image_description = observation.get("image_description", "")
        
        # Format the context for Groq
        context = f"""
ユーザー: {user_input}

観測結果:
{json.dumps({k: v for k, v in observation.items() if k != "image_description"}, indent=2, ensure_ascii=False)}

画像描写:
{image_description}

このデータに基づいて、適切な音声応答とモーターコマンドを生成してください。
"""
        
        try:
            response = self.ai.send(context)
            print(f"   Response: {response}")
            
            # Parse JSON response
            result = json.loads(response)
            return result
        except json.JSONDecodeError as e:
            print(f"⚠️  Failed to parse response: {e}")
            return {
                "speech": "申し訳ありません。応答を生成できませんでした。",
                "motor_commands": [],
                "status": "error"
            }


# ============================================================================
# STAGE 5: EXECUTION - Parallel Speech & Motor Control
# ============================================================================

class ExecutionModule:
    """Executes speech output and motor commands in parallel"""
    
    def __init__(self, stepper_manager: Optional[StepperManager] = None):
        self.stepper = stepper_manager
    
    async def execute_response(self, response: Dict[str, Any]) -> None:
        """Execute speech and motor commands in parallel"""
        print(f"\n⚙️ Execution: Running response...")
        
        tasks = []
        
        # Task 1: Play speech
        if response.get("speech"):
            tasks.append(self._play_speech(response["speech"]))
        
        # Task 2: Execute motor commands
        if response.get("motor_commands") and self.stepper:
            tasks.append(self._execute_motors(response["motor_commands"]))
        
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    print(f"⚠️  Task {i} failed: {result}")
    
    async def _play_speech(self, text: str) -> None:
        """Play speech output using Edge TTS"""
        try:
            import edge_tts
            import subprocess
            import sys
            
            # Use Japanese voice by default for this robot
            voice = 'ja-JP-NanamiNeural'
            audio_file = "/tmp/speech_output.mp3"
            
            print(f"   🔊 Speech: {text}")
            print("   🎙️  Generating audio...")
            
            # Generate audio with edge_tts
            communicate = edge_tts.Communicate(text, voice)
            await communicate.save(audio_file)
            
            # Play audio based on platform
            if sys.platform == "darwin":  # macOS
                subprocess.run(['afplay', audio_file], check=False)
            elif sys.platform == "linux":  # Linux (Raspberry Pi)
                subprocess.run(['mpg123', audio_file], check=False)
            elif sys.platform == "win32":  # Windows
                subprocess.run(['powershell', '-c', f'Add-Type –AssemblyName System.Speech; (New-Object System.Speech.Synthesis.SpeechSynthesizer).Speak(\"{text}\")'], check=False)
            
            # Clean up
            if sys.platform != "win32":
                try:
                    import os
                    os.remove(audio_file)
                except:
                    pass
        except ImportError:
            print(f"   🔊 Speech (text only): {text}")
            print("   ⚠️  Edge TTS not available - text output only")
        except Exception as e:
            print(f"   🔊 Speech (text only): {text}")
            print(f"   ⚠️  TTS Error: {e}")
    
    async def _execute_motors(self, commands: List[Dict[str, Any]]) -> None:
        """Execute motor commands"""
        if not self.stepper:
            print("   ⚠️  Stepper manager not available")
            return
        
        try:
            motor_kwargs = {}
            for cmd in commands:
                axis = cmd.get("axis")
                angle = cmd.get("angle")
                if axis and angle:
                    motor_kwargs[axis] = angle
                    print(f"   ⚙️  Motor {axis}: {angle}°")
            
            if motor_kwargs:
                result = await self.stepper.move(**motor_kwargs)
                print(f"   ✅ Motor execution: {result}")
        except Exception as e:
            print(f"   ⚠️  Motor execution error: {e}")


# ============================================================================
# MAIN INTEGRATED SYSTEM
# ============================================================================

class IntegratedRobotSystem:
    """Main integrated system orchestrating all 5 stages"""
    
    def __init__(self):
        try:
            self.api_client = AutoRotatingAPIClient(env_prefix="MY_API_KEY")
        except ValueError as e:
            print(f"⚠️  API Client Error: {e}")
            print("⚠️  Continuing in demonstration mode")
            self.api_client = None
        
        self.sensing = SensingModule()
        self.planning = PlanningModule(self.api_client) if self.api_client else None
        self.action = ActionModule(self.api_client)
        self.integration = IntegrationModule(self.api_client) if self.api_client else None
        
        # Initialize motor control (optional)
        try:
            self.stepper = StepperManager()
        except Exception as e:
            print(f"⚠️  Motor control not available: {e}")
            self.stepper = None
        
        self.execution = ExecutionModule(self.stepper)
    
    async def run_pipeline(self) -> None:
        """Run the complete 5-stage pipeline"""
        print("\n" + "="*70)
        print("🤖 INTEGRATED AI ROBOT SYSTEM")
        print("="*70)
        print("Pipeline: Sensing → Planning → Action → Integration → Execution")
        print("="*70)
        
        try:
            # STAGE 1: SENSING
            print("\n📍 STAGE 1: SENSING")
            user_speech = await self.sensing.wait_for_wakeword()
            if not user_speech:
                print("❌ No speech detected")
                return
            
            # STAGE 2: PLANNING
            print("\n📍 STAGE 2: PLANNING")
            if self.planning:
                tool_config = self.planning.select_tool(user_speech)
            else:
                print("⚠️  Planning module not available, using default CONVERSATION")
                tool_config = {"tool": "CONVERSATION", "target": None}
            
            # STAGE 3: ACTION & OBSERVATION
            print("\n📍 STAGE 3: ACTION & OBSERVATION")
            observation = await self.action.execute(tool_config)
            
            # STAGE 4: INTEGRATION
            print("\n📍 STAGE 4: INTEGRATION")
            if self.integration:
                response = self.integration.generate_response(observation, user_speech)
            else:
                print("⚠️  Integration module not available")
                response = {
                    "speech": f"You said: {user_speech}",
                    "motor_commands": [],
                    "status": "demo"
                }
            
            # STAGE 5: EXECUTION
            print("\n📍 STAGE 5: EXECUTION")
            await self.execution.execute_response(response)
            
            print("\n✅ Pipeline execution completed successfully!")
        
        except Exception as e:
            print(f"\n❌ Error in pipeline: {e}")
            import traceback
            traceback.print_exc()
    
    async def run_continuous(self) -> None:
        """Run the system in continuous mode"""
        print("\n" + "="*70)
        print("🤖 CONTINUOUS AI ROBOT SYSTEM")
        print("Press Ctrl+C to exit")
        print("="*70)
        
        try:
            while True:
                await self.run_pipeline()
                print("\nReady for next command...")
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            print("\n\n🛑 System shutdown initiated by user")
        except Exception as e:
            print(f"\n❌ Fatal error: {e}")


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

async def main():
    system = IntegratedRobotSystem()
    
    # Run single pipeline or continuous mode
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--continuous":
        await system.run_continuous()
    else:
        await system.run_pipeline()


if __name__ == "__main__":
    asyncio.run(main())
