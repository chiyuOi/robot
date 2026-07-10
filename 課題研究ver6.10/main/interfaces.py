"""
Interfaces: 抽象基底クラス定義
- 依存注入パターンの基礎
- 各Managerが実装すべきインターフェース
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List


class IVoiceChat(ABC):
    """音声入出力インターフェース"""
    
    @abstractmethod
    async def listen(self, timeout: int = 15) -> str:
        """音声入力を取得"""
        pass
    
    @abstractmethod
    async def speak(self, text: str, voice: str = 'ja-JP-NanamiNeural') -> None:
        """音声出力を実行"""
        pass


class ICamera(ABC):
    """カメラ・ビジョン処理インターフェース"""
    
    @abstractmethod
    def capture_frame(self) -> Optional[Any]:
        """フレームをキャプチャ"""
        pass
    
    @abstractmethod
    async def detect_objects(self, frame: Any, target: str = '') -> Dict[str, Any]:
        """物体検出を実行"""
        pass
    
    @abstractmethod
    async def describe_image(self, image_path: str, prompt: str = '') -> str:
        """画像を説明"""
        pass
    
    @abstractmethod
    async def capture_and_detect(self, target: str = '') -> Dict[str, Any]:
        """フレームキャプチャと検出を統合実行"""
        pass


class IStepper(ABC):
    """ステッパーモーター制御インターフェース"""
    
    @abstractmethod
    async def move(self, **kwargs) -> str:
        """モーターを動かす"""
        pass


class ITools(ABC):
    """ツール・コマンド実行インターフェース"""
    
    @abstractmethod
    async def parse_command(self, text: str) -> Dict[str, Any]:
        """コマンドを解析"""
        pass
    
    @abstractmethod
    async def execute_command(self, command_str: str) -> Dict[str, Any]:
        """コマンドを実行"""
        pass
