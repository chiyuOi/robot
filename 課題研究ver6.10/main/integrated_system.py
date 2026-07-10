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
import sys
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
from data.manager import get_data_manager


PIPELINE_TOOLS = {"YOLO", "COLOR_TRACK", "MOTION_ONLY", "CONVERSATION"}
GROQ_CHAT_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_TEXT_MODEL = "llama-3.1-8b-instant"


def _extract_json_object(text: str) -> Dict[str, Any]:
    """LLM応答からJSONオブジェクトだけを安全に取り出す。"""
    if not text:
        raise json.JSONDecodeError("empty response", text, 0)

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}")
        if start == -1 or end == -1 or end <= start:
            raise
        return json.loads(text[start:end + 1])


def _normalize_tool_name(tool: Any) -> str:
    normalized = str(tool or "CONVERSATION").strip().upper()
    return normalized if normalized in PIPELINE_TOOLS else "CONVERSATION"


def _fallback_plan(user_input: str, reason: str = "local fallback") -> Dict[str, Any]:
    """Groqが使えない時も止まらない最小限のローカル計画。"""
    text = user_input.lower()
    vision_words = ("どこ", "探", "見つ", "mug", "cup", "カップ", "マグ", "blue", "青", "物")
    motion_words = ("動", "向", "指", "右", "左", "上", "下", "motor", "move")

    if any(word in text for word in vision_words):
        target = "object"
        if "blue" in text or "青" in text:
            target = "blue object"
        if "mug" in text or "マグ" in text:
            target = "mug"
        elif "cup" in text or "カップ" in text:
            target = "cup"
        return {"tool": "YOLO", "target": target, "reasoning": reason}

    if any(word in text for word in motion_words):
        return {"tool": "MOTION_ONLY", "target": "", "reasoning": reason}

    return {"tool": "CONVERSATION", "target": "", "reasoning": reason}
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
    
    async def wait_for_wakeword(self, input_method: str = "voice"):
        """Wake word後のユーザー発話を取得する。"""
        print("\n🎤 STT入力を待機中...")
        user_input = await self.get_user_input(input_method)
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
あなたはコミュニケーションロボットの計画AIです。ユーザーテキストから次に実行するローカルツールを1つだけ選んでください。

利用可能なツール:
- "YOLO": 物体検出を実行。目標の位置座標（X, Y）を取得できます
- "COLOR_TRACK": 特定の色を追跡します
- "MOTION_ONLY": 単純な動作コマンドのみを実行します
- "CONVERSATION": 会話のみで応答します

重要: 有効なJSONのみを返してください。他の言葉は出力しないでください:
{"tool": "YOLO", "target": "blue_mug", "reasoning": "ユーザーが青いマグの場所を聞いたため"}
"""
    
    def __init__(self, api_client: AutoRotatingAPIClient, container: Optional[DIContainer] = None):
        self.container = container or get_container()
        self.ai = Ai(
            api_client=api_client,
            prompt=self.PLANNING_PROMPT,
            api_url=GROQ_CHAT_URL,
            model=GROQ_TEXT_MODEL,
            temperature=0.2,
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
            tool_config = _extract_json_object(response)
            tool_config["tool"] = _normalize_tool_name(tool_config.get("tool"))
            tool_config.setdefault("target", "")
            tool_config.setdefault("reasoning", "")
            print(f"   Selected tool: {tool_config['tool']}")
            
            # Store in DataManager
            await self.data.save_plan_state(
                tool=tool_config.get("tool", "CONVERSATION"),
                target=tool_config.get("target", ""),
                reasoning=tool_config.get("reasoning", "")
            )
            
            self.logger.log_decision("PLANNING", tool_config.get("tool", "CONVERSATION"), tool_config.get("reasoning", ""))
            
            return tool_config
        except Exception as e:
            print(f"⚠️  Planning failed, using local fallback: {e}")
            default_config = _fallback_plan(user_input, f"Groq planning fallback: {e}")
            await self.data.save_plan_state(
                tool=default_config["tool"],
                target=default_config.get("target", ""),
                reasoning=default_config.get("reasoning", "")
            )
            self.logger.log_error("PLANNING", e, {"fallback": default_config})
            return default_config


# ============================================================================
# STAGE 3: ACTION & OBSERVATION - Execute Selected Tool
# ============================================================================

class ActionModule:
    """Executes the selected tool and returns observations"""
    
    def __init__(self, api_client: Optional[AutoRotatingAPIClient] = None, container: Optional[DIContainer] = None):
        self.container = container or get_container()
        self.camera = self.container.get('Camera')
        self.tools = self.container.get('Tools')
        self.api_client = api_client
        self.data = get_data_manager(Path(__file__).parent.parent / "data")
        self.logger = get_logger()
    
    async def execute(self, tool_config: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the selected tool"""
        tool = _normalize_tool_name(tool_config.get("tool", "CONVERSATION"))
        
        if tool == "YOLO":
            return await self._execute_yolo(tool_config)
        elif tool == "COLOR_TRACK":
            return await self._execute_color_track(tool_config)
        elif tool == "MOTION_ONLY":
            return await self._execute_motion_only(tool_config)
        else:
            return {
                "status": "success",
                "action": "conversation_ready",
                "details": "Ready for conversation"
            }
    
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
        return {
            "status": "success",
            "action": "color_tracked",
            "coordinates": [320, 240]
        }

    async def _execute_motion_only(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare a motion-only observation packet."""
        command = config.get("target") or config.get("command") or ""
        parsed = await self.tools.parse_command(command) if command else {"type": "motion_text", "content": ""}
        return {
            "status": "success",
            "action": "motion_ready",
            "command": command,
            "parsed_command": parsed,
            "details": "Ready for motor command generation"
        }


# ============================================================================
# STAGE 4: INTEGRATION - Response Generation via Groq #2
# ============================================================================

class IntegrationModule:
    """Uses Groq API to generate response and motor commands based on observations"""
    
    INTEGRATION_PROMPT = """
あなたはコミュニケーションロボットの統合AIです。ユーザー要求、選択ツール、観測結果からレスポンスパケットを生成してください。

重要: 有効なJSONのみを返してください。他の言葉は出力しないでください:
{"speech": "見つけました。左側にあります。", "motor_commands": [{"axis": "a", "angle": 10}], "status": "success"}

軸の説明:
- "a", "b", "c", "d": 各ステッパーモーター軸
- angle: 相対角度（度数）（正=時計回り、負=反時計回り）
- 物体座標がある場合、画像中心からのずれを小さな角度に変換してよい
"""
    
    def __init__(self, api_client: AutoRotatingAPIClient, container: Optional[DIContainer] = None):
        self.container = container or get_container()
        self.ai = Ai(
            api_client=api_client,
            prompt=self.INTEGRATION_PROMPT,
            api_url=GROQ_CHAT_URL,
            model=GROQ_TEXT_MODEL,
            temperature=0.4,
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
            result = _extract_json_object(response)
            result = self._normalize_response(result)
            
            # Save execution state
            await self.data.save_execution_state(
                speech=result.get("speech", ""),
                motor_commands=result.get("motor_commands", []),
                status="completed"
            )
            
            self.logger.log_stage("INTEGRATION", "completed", {"response_length": len(result.get("speech", ""))})
            
            return result
        except Exception as e:
            print(f"⚠️  Integration failed, using local fallback: {e}")
            error_response = self._build_fallback_response(observation, user_input, str(e))
            
            # Save error state
            await self.data.save_execution_state(
                speech=error_response["speech"],
                motor_commands=error_response.get("motor_commands", []),
                status=error_response.get("status", "fallback")
            )
            
            self.logger.log_error("INTEGRATION", e, {"fallback": error_response})
            return error_response

    def _normalize_response(self, result: Dict[str, Any]) -> Dict[str, Any]:
        speech = str(result.get("speech") or "処理しました。")
        commands = result.get("motor_commands") or result.get("motor") or []
        if isinstance(commands, dict):
            commands = [commands]

        normalized_commands = []
        for cmd in commands:
            if not isinstance(cmd, dict):
                continue
            axis = str(cmd.get("axis", "")).lower()
            if axis not in {"a", "b", "c", "d"}:
                continue
            try:
                angle = float(cmd.get("angle", 0))
            except (TypeError, ValueError):
                continue
            if angle:
                normalized_commands.append({"axis": axis, "angle": angle})

        return {
            "speech": speech,
            "motor_commands": normalized_commands,
            "status": result.get("status", "success")
        }

    def _build_fallback_response(self, observation: Dict[str, Any], user_input: str, reason: str) -> Dict[str, Any]:
        primary = observation.get("primary") or {}
        if observation.get("action") == "object_detected" and primary:
            label = primary.get("label", "対象")
            x = int(primary.get("x", 320))
            y = int(primary.get("y", 240))
            motor_commands = self._point_to_coordinates(x, y)
            return {
                "speech": f"{label}を見つけました。座標はX{x}、Y{y}です。",
                "motor_commands": motor_commands,
                "status": "fallback",
                "reason": reason
            }

        if observation.get("action") == "no_object_found":
            return {
                "speech": "見つけられませんでした。少し向きを変えてもう一度探します。",
                "motor_commands": [{"axis": "a", "angle": 10}],
                "status": "fallback",
                "reason": reason
            }

        return {
            "speech": "了解しました。",
            "motor_commands": [],
            "status": "fallback",
            "reason": reason
        }

    def _point_to_coordinates(self, x: int, y: int) -> List[Dict[str, Any]]:
        center_x, center_y = 320, 240
        commands = []
        horizontal_angle = max(-25, min(25, round((x - center_x) / 16)))
        vertical_angle = max(-20, min(20, round((center_y - y) / 16)))
        if horizontal_angle:
            commands.append({"axis": "a", "angle": horizontal_angle})
        if vertical_angle:
            commands.append({"axis": "b", "angle": vertical_angle})
        return commands


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
    """Main integrated system orchestrating the flowchart's 5 stages."""

    def __init__(self, mode: str = "mock", input_method: str = "voice"):
        self.mode = mode
        self.input_method = input_method
        if (mode or "mock").lower() in {"mock", "demo", "test"}:
            self.api_client = None
        else:
            try:
                self.api_client = AutoRotatingAPIClient(env_prefix="MY_API_KEY")
            except ValueError as e:
                print(f"⚠️  API Client Error: {e}")
                print("⚠️  Groqなしのローカルフォールバックで継続します")
                self.api_client = None

        self._setup_pipeline_services(mode)
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

    def _setup_pipeline_services(self, mode: str) -> None:
        """Register local/Pi managers or test doubles for the pipeline."""
        normalized_mode = (mode or "mock").lower()

        if normalized_mode in {"real", "hardware", "pi"}:
            from func.voice_chat import VoiceChatManager
            from func.camera import CameraManager
            from func.motion import StepperManager
            from func.tools import ToolsManager
            from data.manager import DataManager

            setup_di_container(
                VoiceChatManager,
                CameraManager,
                StepperManager,
                ToolsManager,
                DataManager
            )
            print("🔧 Pipeline services: real hardware/local managers")
            return

        from test.conftest import MockVoiceChat, MockCamera, MockStepper, MockTools, InMemoryDataManager

        setup_di_container(
            MockVoiceChat,
            MockCamera,
            MockStepper,
            MockTools,
            InMemoryDataManager
        )
        print("🔧 Pipeline services: mock demo managers")
    
    async def run_pipeline(self, user_input: Optional[str] = None) -> Dict[str, Any]:
        """Run the complete 5-stage pipeline"""
        print("\n" + "="*70)
        print("🤖 INTEGRATED AI ROBOT SYSTEM")
        print("="*70)
        print("Pipeline: Sensing → Planning → Action → Integration → Execution")
        print("="*70)
        
        try:
            # STAGE 1: SENSING
            print("\n📍 STAGE 1: SENSING")
            if user_input:
                user_speech = user_input
                await self.sensing.data.save_voice_state(
                    user_speech,
                    {"input_method": "direct"}
                )
            else:
                user_speech = await self.sensing.wait_for_wakeword(self.input_method)
            if not user_speech:
                print("❌ No speech detected")
                return {"status": "no_input"}
            
            # STAGE 2: PLANNING
            print("\n📍 STAGE 2: PLANNING")
            if self.planning:
                try:
                    tool_config = await self.planning.select_tool(user_speech)
                except PlanningException as e:
                    print(f"❌ Planning failed: {e}")
                    self.logger.log_error("PLANNING", e, {})
                    return {"status": "planning_error", "error": str(e)}
            else:
                print("⚠️  Planning module not available, using local fallback")
                tool_config = _fallback_plan(user_speech, "Groq client not configured")
                await self.action.data.save_plan_state(
                    tool=tool_config["tool"],
                    target=tool_config.get("target", ""),
                    reasoning=tool_config.get("reasoning", "")
                )
            
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
                return {"status": "action_error", "error": str(e), "tool_config": tool_config}
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
                    return {"status": "integration_error", "error": str(e), "observation": observation}
            else:
                print("⚠️  Integration module not available")
                response = IntegrationModule.__new__(IntegrationModule)._build_fallback_response(
                    observation,
                    user_speech,
                    "Groq client not configured"
                )
                await self.execution.data.save_execution_state(
                    response["speech"],
                    response.get("motor_commands", []),
                    response.get("status", "fallback")
                )
            
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
                return {"status": "execution_error", "error": str(e), "response": response}
            
            sys.stdout.flush()
            print("\n✅ Pipeline execution completed successfully!")
            self.logger.log_stage("PIPELINE", "completed", {})
            return {
                "status": "success",
                "user_input": user_speech,
                "tool_config": tool_config,
                "observation": observation,
                "response": response
            }
        
        except Exception as e:
            import sys
            print(f"\n❌ Error in pipeline: {e}")
            import traceback
            traceback.print_exc()
            self.logger.log_error("PIPELINE", e, {})
            sys.stdout.flush()
            return {"status": "error", "error": str(e)}
    
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
