"""
conftest.py: pytest 設定とフィクスチャー定義
- Mock オブジェクト
- テスト用 DataManager
- 共通フィクスチャー
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
from pathlib import Path
from typing import Dict, Any

# プロジェクトパスを追加
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from main.interfaces import IVoiceChat, ICamera, IStepper, ITools
from main.container import DIContainer
from data.manager import DataManager


# ============================================================================
# Pytest Configuration
# ============================================================================

def pytest_configure(config):
    """pytest 設定"""
    config.addinivalue_line(
        "markers", "unit: Unit test"
    )
    config.addinivalue_line(
        "markers", "integration: Integration test"
    )
    config.addinivalue_line(
        "markers", "async: Async test"
    )


# ============================================================================
# Async Support
# ============================================================================

@pytest.fixture
def event_loop():
    """Event loop フィクスチャー"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# ============================================================================
# Mock Managers
# ============================================================================

class MockVoiceChat(IVoiceChat):
    """VoiceChatManager のモック"""
    
    def __init__(self):
        self.listen_called = False
        self.speak_called = False
    
    async def listen(self, timeout: int = 15) -> str:
        self.listen_called = True
        return "こんにちは"
    
    async def speak(self, text: str, voice: str = 'ja-JP-NanamiNeural') -> None:
        self.speak_called = True


class MockCamera(ICamera):
    """CameraManager のモック"""
    
    def __init__(self):
        self.detect_called = False
        self.describe_called = False
    
    def capture_frame(self):
        return None  # Mock frame
    
    async def detect_objects(self, frame: Any, target: str = '') -> Dict[str, Any]:
        self.detect_called = True
        return {
            "detections": [
                {"label": "person", "x": 320, "y": 240, "confidence": 0.95}
            ]
        }
    
    async def describe_image(self, image_path: str, prompt: str = '') -> str:
        self.describe_called = True
        return "A person is in the image"
    
    async def capture_and_detect(self, target: str = '') -> Dict[str, Any]:
        self.detect_called = True
        return {
            "status": "success",
            "detections": [
                {"label": "person", "x": 320, "y": 240, "confidence": 0.95}
            ],
            "image_description": "A person is in the image"
        }


class MockStepper(IStepper):
    """StepperManager のモック"""
    
    def __init__(self):
        self.move_called = False
        self.last_move_args = {}
    
    async def move(self, **kwargs) -> str:
        self.move_called = True
        self.last_move_args = kwargs
        return "Motor move completed"


class MockTools(ITools):
    """ToolsManager のモック"""
    
    def __init__(self):
        self.parse_called = False
        self.execute_called = False
    
    async def parse_command(self, text: str) -> Dict[str, Any]:
        self.parse_called = True
        return {"command": "test_command", "args": []}
    
    async def execute_command(self, command_str: str) -> Dict[str, Any]:
        self.execute_called = True
        return {"status": "success", "result": "test result"}


# ============================================================================
# Test Data Manager
# ============================================================================

class InMemoryDataManager(DataManager):
    """テスト用 DataManager（メモリベース）"""
    
    def __init__(self):
        """Initialize test data manager with in-memory storage"""
        # 親クラスの初期化をスキップしてメモリベースストレージを使用
        self.data_dir = None
        self._memory = {
            'voice_state': {"status": "idle", "timestamp": None, "data": {}},
            'camera_state': {"status": "idle", "timestamp": None, "data": {}},
            'plan_state': {"status": "idle", "timestamp": None, "data": {}},
            'execution_state': {"status": "idle", "timestamp": None, "data": {}},
        }
        # ファイルパスのみ設定（実際には使用しない）
        self.voice_state_file = Path("voice_state")
        self.camera_state_file = Path("camera_state")
        self.plan_state_file = Path("plan_state")
        self.execution_state_file = Path("execution_state")
    
    async def _read_state(self, file_path):
        """メモリから読み込み"""
        key = file_path.stem if hasattr(file_path, 'stem') else str(file_path)
        return self._memory.get(key, {"status": "idle", "timestamp": None, "data": {}})
    
    async def _write_state(self, file_path, state):
        """メモリに書き込み"""
        from datetime import datetime
        key = file_path.stem if hasattr(file_path, 'stem') else str(file_path)
        state["timestamp"] = datetime.now().isoformat()
        self._memory[key] = state
        return True
    
    async def clear_all(self) -> bool:
        """全ての状態をクリア"""
        try:
            from datetime import datetime
            for key in self._memory.keys():
                self._memory[key] = {
                    "status": "idle",
                    "timestamp": datetime.now().isoformat(),
                    "data": {}
                }
            return True
        except Exception as e:
            print(f"⚠️  Failed to clear all states: {e}")
            return False


# Alias for backwards compatibility
TestDataManager = InMemoryDataManager


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def mock_voice_chat():
    """MockVoiceChat フィクスチャー"""
    return MockVoiceChat()


@pytest.fixture
def mock_camera():
    """MockCamera フィクスチャー"""
    return MockCamera()


@pytest.fixture
def mock_stepper():
    """MockStepper フィクスチャー"""
    return MockStepper()


@pytest.fixture
def mock_tools():
    """MockTools フィクスチャー"""
    return MockTools()


@pytest.fixture
def test_data_manager():
    """InMemoryDataManager フィクスチャー"""
    return InMemoryDataManager()


@pytest.fixture
def di_container(mock_voice_chat, mock_camera, mock_stepper, mock_tools, test_data_manager):
    """設定済みの DIContainer フィクスチャー"""
    container = DIContainer()
    container.register('VoiceChat', lambda: mock_voice_chat, singleton=True)
    container.register('Camera', lambda: mock_camera, singleton=True)
    container.register('Stepper', lambda: mock_stepper, singleton=True)
    container.register('Tools', lambda: mock_tools, singleton=True)
    container.register('DataManager', lambda: test_data_manager, singleton=True)
    return container


@pytest.fixture(autouse=True)
def reset_containers():
    """各テスト間でコンテナをリセット"""
    from main.container import _global_container
    yield
    # テスト後にクリア
    globals()['_global_container'] = None
