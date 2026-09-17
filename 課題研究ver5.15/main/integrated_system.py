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
from .api_client import AutoRotatingAPIClient, GroqVisionClient
from .ai import Ai
from .container import DIContainer, get_container, setup_di_container
from .exceptions import SensingException, PlanningException, ActionException, IntegrationException, ExecutionException
from .decorators import async_retry
from .logger import get_logger
from func.motion import StepperManager
from func.voice_chat import VoiceChatManager
from func.camera import CameraManager
from func.tools import ToolsManager
from data.state import State, CameraState, VoiceState
from data.manager import get_data_manager
from ultralytics import YOLO
import threading
# STAGE 1: SENSING - Wake Word Detection & Speech Recognition
# ============================================================================

class SensingModule:
    """Detects wake word and captures user speech"""
    
    def __init__(self, container: Optional[DIContainer] = None):
        self.container = container or get_container()
        self.voice_chat = self.container.get('VoiceChat')
        self.data = get_data_manager(Path(__file__).parent.parent / "data")
        self.wake_word = "ねえロボット"
        self.is_recording = False
        self.logger = get_logger()
    
    async def wait_for_wakeword(self):
        """Wait for wake word using speech recognition"""
        print("\n🎤 Waiting for wake word...")
        # Use mock voice chat for demo mode
        voice_chat = self.container.get('VoiceChat')
        user_input = await voice_chat.listen()
        print(f"🎙️ User said: {user_input}")
        
        # Store transcription in DataManager
        await self.data.save_voice_state(user_input, {"input_method": "voice"})
        self.logger.log_stage("SENSING", "completed", {"input": user_input})
        
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
        """Get input from voice using VoiceChatManager"""
        print("\n🎤 音声入力を開始します...")
        print("   マイクに向かってコマンドを話してください...")
        
        try:
            text = await self.voice_chat.listen(timeout=15)
            if text:
                return text
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
        
        # Store in DataManager
        await self.data.save_voice_state(text, {"input_method": "keyboard"})
        
        return text
    
    async def get_user_speech(self) -> str:
        """Get the user's speech transcription"""
        # 既にメモリ内に保存されている
        return await self.voice_chat.listen(timeout=1)


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
- "SYSTEM_REPORT": システム状態を確認し、バグ候補を日本語で報告します

重要: 以下の形式で**有効なJSON（コメントなし）**のみを返してください。他の言葉は一切出力しないでください:
{"tool": "YOLO", "target": "検出対象", "reasoning": "理由"}
"""
    
    def __init__(self, api_client: AutoRotatingAPIClient, container: Optional[DIContainer] = None):
        self.container = container or get_container()
        self.ai = Ai(
            api_client=api_client,
            prompt=self.PLANNING_PROMPT,
            api_url="https://api.groq.com/openai/v1/chat/completions",
            model="llama-3.1-8b-instant",  # Updated to supported model
            temperature=0.5,
            keep_history=False
        )
        self.data = get_data_manager(Path(__file__).parent.parent / "data")
        self.logger = get_logger()
    
    @async_retry(max_attempts=3, initial_delay=1.0, exceptions=(Exception,))
    async def select_tool(self, user_input: str) -> Dict[str, Any]:
        """Select appropriate tool based on user input"""
        print(f"\n🧠 Planning (Groq #1): Analyzing user request...")
        print(f"   User said: {user_input}")
        
        try:
            response = self.ai.send(user_input)
            print(f"   Response: {response}")
            
            # Parse JSON response
            tool_config = json.loads(response)
            print(f"   Selected tool: {tool_config['tool']}")
            
            # Store in DataManager
            await self.data.save_plan_state(
                tool=tool_config.get("tool", "CONVERSATION"),
                target=tool_config.get("target", ""),
                reasoning=tool_config.get("reasoning", "")
            )
            
            self.logger.log_decision("PLANNING", tool_config.get("tool", "CONVERSATION"), tool_config.get("reasoning", ""))
            
            return tool_config
        except json.JSONDecodeError as e:
            print(f"⚠️  Failed to parse tool selection, defaulting to CONVERSATION")
            default_config = {
                "tool": "CONVERSATION",
                "target": None,
                "reasoning": "Failed to parse response"
            }
            await self.data.save_plan_state(
                tool="CONVERSATION",
                target="",
                reasoning="Failed to parse response"
            )
            self.logger.log_error("PLANNING", e, {"response": str(response)})
            raise PlanningException(f"Failed to parse planning response: {e}")


# ============================================================================
# STAGE 3: ACTION & OBSERVATION - Execute Selected Tool
# ============================================================================

class ActionModule:
    """Executes the selected tool and returns observations"""
    
    def __init__(self, api_client: Optional[AutoRotatingAPIClient] = None, container: Optional[DIContainer] = None):
        self.container = container or get_container()
        self.camera = self.container.get('Camera')
        self.api_client = api_client
        self.data = get_data_manager(Path(__file__).parent.parent / "data")
        self.logger = get_logger()
    
    async def execute(self, tool_config: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the selected tool"""
        tool = tool_config.get("tool", "CONVERSATION")
        
        if tool == "YOLO":
            return await self._execute_yolo(tool_config)
        elif tool == "COLOR_TRACK":
            return await self._execute_color_track(tool_config)
        elif tool == "SYSTEM_REPORT":
            return await self._execute_system_report()
        elif tool == "MOTION_ONLY":
            return {"action": "motion_ready", "details": "Ready for motion commands"}
        else:
            return {"action": "conversation_ready", "details": "Ready for conversation"}
    
    @async_retry(max_attempts=3, initial_delay=1.0, exceptions=(Exception,))
    async def _execute_yolo(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Execute YOLO object detection + Llama-4-Scout image description using CameraManager"""
        print("\n🎯 Action (YOLO Execution): Detecting objects...")
        
        target = config.get("target", "")
        
        try:
            # CameraManager を使用して統合実行
            results = await self.camera.capture_and_detect(target)
            
            if results["status"] == "error":
                self.logger.log_error("ACTION", Exception("YOLO error"), {"target": target})
                raise ActionException(f"YOLO execution failed: {results.get('error')}")
            
            # 検出結果を形式化
            detections = results.get("detections", [])
            image_description = results.get("image_description", "")
            
            # Save to DataManager
            await self.data.save_camera_state(
                detections=detections,
                image_description=image_description,
                metadata={"target": target}
            )
            
            if detections:
                top_detection = detections[0]
                print(f"   Found: {top_detection['label']} at ({top_detection['x']}, {top_detection['y']})")
                print(f"   📸 Image Description: {image_description}")
                
                self.logger.log_stage("ACTION", "completed", {"detections": len(detections), "target": target})
                
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
                
                self.logger.log_stage("ACTION", "completed", {"detections": 0, "target": target})
                
                return {
                    "status": "success",
                    "action": "no_object_found",
                    "detections": [],
                    "image_description": image_description
                }
        except Exception as e:
            self.logger.log_error("ACTION", e, {"target": target})
            raise ActionException(f"Action execution failed: {e}")

    
    async def _execute_color_track(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Execute color tracking"""
        print("\n🎨 Action (Color Track): Tracking color...")
        # Implementation placeholder
        return {
            "status": "success",
            "action": "color_tracked",
            "coordinates": [320, 240]
        }

    async def _execute_system_report(self) -> Dict[str, Any]:
        """Generate system bug report in Japanese"""
        summary = await self.data.get_summary()
        stage_labels = {
            "voice": "感知",
            "camera": "行動",
            "plan": "計画",
            "execution": "実行"
        }

        bugs = []
        for stage_key, stage_label in stage_labels.items():
            status = summary.get(stage_key, {}).get("status", "unknown")
            if status in {"error", "failed"}:
                bugs.append({
                    "stage": stage_key,
                    "severity": "high",
                    "message": f"{stage_label}ステージでエラー状態を検出しました（status={status}）。"
                })
            elif status == "idle":
                bugs.append({
                    "stage": stage_key,
                    "severity": "medium",
                    "message": f"{stage_label}ステージのデータが未実行です（status=idle）。"
                })

        if bugs:
            report_text = "システムレポート（日本語）: バグ候補を検出しました。 " + " ".join(
                f"{idx + 1}. {bug['message']}" for idx, bug in enumerate(bugs)
            )
        else:
            report_text = "システムレポート（日本語）: 現時点で明確なバグは検出されませんでした。"

        return {
            "status": "success",
            "action": "system_report_generated",
            "language": "ja",
            "bugs": bugs,
            "report_text": report_text,
            "summary": summary
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

system_report_generated の観測結果を受け取った場合は、必ず日本語で簡潔にバグ報告してください。

軸の説明:
- "a", "b", "c", "d": 各ステッパーモーター軸
- angle: 相対角度（度数）（正=時計回り、負=反時計回り）
"""
    
    def __init__(self, api_client: AutoRotatingAPIClient, container: Optional[DIContainer] = None):
        self.container = container or get_container()
        self.ai = Ai(
            api_client=api_client,
            prompt=self.INTEGRATION_PROMPT,
            api_url="https://api.groq.com/openai/v1/chat/completions",
            model="llama-3.1-8b-instant",  # Updated to supported model
            temperature=0.7,
            keep_history=False
        )
        self.data = get_data_manager(Path(__file__).parent.parent / "data")
        self.logger = get_logger()
    
    @async_retry(max_attempts=3, initial_delay=1.0, exceptions=(Exception,))
    async def generate_response(self, observation: Dict[str, Any], user_input: str) -> Dict[str, Any]:
        """Generate response and motor commands based on observations"""
        print(f"\n🔄 Integration (Groq #2): Generating response...")
        
        try:
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
            
            response = self.ai.send(context)
            print(f"   Response: {response}")
            
            # Parse JSON response
            result = json.loads(response)
            
            # Save execution state
            await self.data.save_execution_state(
                speech=result.get("speech", ""),
                motor_commands=result.get("motor_commands", []),
                status="completed"
            )
            
            self.logger.log_stage("INTEGRATION", "completed", {"response_length": len(result.get("speech", ""))})
            
            return result
        except json.JSONDecodeError as e:
            print(f"⚠️  Failed to parse response: {e}")
            error_response = {
                "speech": "申し訳ありません。応答を生成できませんでした。",
                "motor_commands": [],
                "status": "error"
            }
            
            # Save error state
            await self.data.save_execution_state(
                speech=error_response["speech"],
                motor_commands=[],
                status="error"
            )
            
            self.logger.log_error("INTEGRATION", e, {"response": str(response)})
            raise IntegrationException(f"Failed to parse integration response: {e}")


# ============================================================================
# STAGE 5: EXECUTION - Parallel Speech & Motor Control
# ============================================================================

class ExecutionModule:
    """Executes speech output and motor commands in parallel"""
    
    def __init__(self, stepper_manager: Optional[StepperManager] = None, container: Optional[DIContainer] = None):
        self.container = container or get_container()
        self.stepper = stepper_manager or self.container.get('Stepper')
        self.voice_chat = self.container.get('VoiceChat')
        self.data = get_data_manager(Path(__file__).parent.parent / "data")
        self.logger = get_logger()
    
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
            try:
                results = await asyncio.gather(*tasks, return_exceptions=True)
                for i, result in enumerate(results):
                    if isinstance(result, Exception):
                        print(f"⚠️  Task {i} failed: {result}")
                        self.logger.log_error("EXECUTION", result, {"task_index": i})
                
                self.logger.log_stage("EXECUTION", "completed", {"tasks": len(tasks)})
            except Exception as e:
                self.logger.log_error("EXECUTION", e, {"task_count": len(tasks)})
                raise ExecutionException(f"Execution failed: {e}")
    
    async def _play_speech(self, text: str) -> None:
        """Play speech output using VoiceChatManager (Edge TTS)"""
        try:
            # Use Japanese voice by default for this robot
            voice = 'ja-JP-NanamiNeural'
            await self.voice_chat.speak(text, voice)
            print("   ✅ Speech playback complete")
        except Exception as e:
            print(f"   ⚠️  Speech playback error: {e}")
            raise ExecutionException(f"Speech execution failed: {e}")
    
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
            raise ExecutionException(f"Motor execution failed: {e}")


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
        
        # Import mock classes
        from test.conftest import MockVoiceChat, MockCamera, MockStepper, MockTools, InMemoryDataManager
    
        # Use mock implementations for demo mode
        voice_impl = MockVoiceChat
        camera_impl = MockCamera
        stepper_impl = MockStepper
        tools_impl = MockTools
        dm_impl = InMemoryDataManager
    
        # Setup DIContainer with all services
        setup_di_container(voice_impl, camera_impl, stepper_impl, tools_impl, dm_impl)
        self.container = get_container()
        
        self.sensing = SensingModule(self.container)
        self.planning = PlanningModule(self.api_client, self.container) if self.api_client else None
        self.action = ActionModule(self.api_client, self.container)
        self.integration = IntegrationModule(self.api_client, self.container) if self.api_client else None
        
        # Get stepper manager (may be None)
        try:
            self.stepper = self.container.get('Stepper')
        except:
            print(f"⚠️  Motor control not available")
            self.stepper = None
        
        self.execution = ExecutionModule(self.stepper, self.container)
        self.logger = get_logger()
    
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
                try:
                    tool_config = await self.planning.select_tool(user_speech)
                except PlanningException as e:
                    print(f"❌ Planning failed: {e}")
                    self.logger.log_error("PLANNING", e, {})
                    return
            else:
                print("⚠️  Planning module not available, using default CONVERSATION")
                if "system report" in user_speech.lower():
                    tool_config = {"tool": "SYSTEM_REPORT", "target": "bugs"}
                else:
                    tool_config = {"tool": "CONVERSATION", "target": None}
            
            # STAGE 3: ACTION & OBSERVATION
            print("\n📍 STAGE 3: ACTION & OBSERVATION")
            print("   ⏳ Executing action...")
            import sys
            sys.stdout.flush()
            
            try:
                observation = await self.action.execute(tool_config)
                print(f"   ✅ Action completed. Got observation: {list(observation.keys())}")
            except ActionException as e:
                print(f"❌ Action failed: {e}")
                self.logger.log_error("ACTION", e, {})
                return
            sys.stdout.flush()
            
            # STAGE 4: INTEGRATION
            print("\n📍 STAGE 4: INTEGRATION")
            print(f"   ⏳ Generating response from observation...")
            sys.stdout.flush()
            
            if self.integration:
                try:
                    response = await self.integration.generate_response(observation, user_speech)
                    print(f"   ✅ Response generated: {list(response.keys())}")
                except IntegrationException as e:
                    print(f"❌ Integration failed: {e}")
                    self.logger.log_error("INTEGRATION", e, {})
                    return
            else:
                print("⚠️  Integration module not available")
                if observation.get("action") == "system_report_generated":
                    response = {
                        "speech": observation.get("report_text", "システムレポートを生成しました。"),
                        "motor_commands": [],
                        "status": "success"
                    }
                else:
                    response = {
                        "speech": f"You said: {user_speech}",
                        "motor_commands": [],
                        "status": "demo"
                    }
            
            sys.stdout.flush()
            
            # STAGE 5: EXECUTION
            print("\n📍 STAGE 5: EXECUTION")
            print(f"   ⏳ Executing speech and motor commands...")
            sys.stdout.flush()
            
            try:
                await self.execution.execute_response(response)
                print(f"   ✅ Execution completed")
            except ExecutionException as e:
                print(f"❌ Execution failed: {e}")
                self.logger.log_error("EXECUTION", e, {})
                return
            
            sys.stdout.flush()
            print("\n✅ Pipeline execution completed successfully!")
            self.logger.log_stage("PIPELINE", "completed", {})
        
        except Exception as e:
            import sys
            print(f"\n❌ Error in pipeline: {e}")
            import traceback
            traceback.print_exc()
            self.logger.log_error("PIPELINE", e, {})
            sys.stdout.flush()
    
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
