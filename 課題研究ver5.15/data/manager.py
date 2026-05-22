"""
DataManager: 中央状態管理システム
- JSON ファイルベースの永続化
- async/await 対応
- 各ステージの入出力を一元管理
"""

import json
import asyncio
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime


class DataManager:
    """中央状態管理マネージャー"""
    
    def __init__(self, data_dir: Optional[Path] = None):
        """Initialize DataManager
        
        Args:
            data_dir: データ保存ディレクトリ（デフォルト: current dir）
        """
        self.data_dir = data_dir or Path(__file__).parent
        self._ensure_data_files()
    
    def _ensure_data_files(self):
        """各ステートファイルが存在することを確認"""
        self.voice_state_file = self.data_dir / "voice_state.json"
        self.camera_state_file = self.data_dir / "camera_state.json"
        self.plan_state_file = self.data_dir / "plan_state.json"
        self.execution_state_file = self.data_dir / "execution_state.json"
        
        # 初期化
        for state_file in [
            self.voice_state_file,
            self.camera_state_file,
            self.plan_state_file,
            self.execution_state_file
        ]:
            if not state_file.exists():
                self._init_state_file(state_file)
    
    def _init_state_file(self, file_path: Path):
        """状態ファイルを初期化"""
        initial_state = {
            "status": "idle",
            "timestamp": datetime.now().isoformat(),
            "data": {}
        }
        with open(file_path, "w") as f:
            json.dump(initial_state, f, indent=2, ensure_ascii=False)
    
    async def _read_state(self, file_path: Path) -> Dict[str, Any]:
        """状態ファイルを読み込み（非同期）"""
        try:
            loop = asyncio.get_event_loop()
            def _read():
                with open(file_path, "r") as f:
                    return json.load(f)
            return await loop.run_in_executor(None, _read)
        except Exception as e:
            print(f"⚠️  Failed to read state: {e}")
            return {"status": "error", "data": {}}
    
    async def _write_state(self, file_path: Path, state: Dict[str, Any]):
        """状態ファイルに書き込み（非同期）"""
        try:
            state["timestamp"] = datetime.now().isoformat()
            loop = asyncio.get_event_loop()
            def _write():
                with open(file_path, "w") as f:
                    json.dump(state, f, indent=2, ensure_ascii=False)
            await loop.run_in_executor(None, _write)
            return True
        except Exception as e:
            print(f"⚠️  Failed to write state: {e}")
            return False
    
    # ============================================================================
    # VOICE STATE
    # ============================================================================
    
    async def save_voice_state(self, transcription: str, metadata: Optional[Dict] = None) -> bool:
        """音声状態を保存
        
        Args:
            transcription: 認識されたテキスト
            metadata: 追加メタデータ
        
        Returns:
            成功したか
        """
        state = {
            "status": "completed",
            "data": {
                "transcription": transcription,
                "input_method": metadata.get("input_method", "voice") if metadata else "voice",
                "confidence": metadata.get("confidence", 0.0) if metadata else 0.0
            }
        }
        return await self._write_state(self.voice_state_file, state)
    
    async def load_voice_state(self) -> Dict[str, Any]:
        """音声状態を読み込み
        
        Returns:
            音声状態
        """
        return await self._read_state(self.voice_state_file)
    
    # ============================================================================
    # CAMERA STATE
    # ============================================================================
    
    async def save_camera_state(
        self,
        detections: list,
        image_description: str,
        metadata: Optional[Dict] = None
    ) -> bool:
        """カメラ状態を保存
        
        Args:
            detections: 検出結果リスト
            image_description: 画像説明
            metadata: 追加メタデータ
        
        Returns:
            成功したか
        """
        state = {
            "status": "completed",
            "data": {
                "detections": detections,
                "image_description": image_description,
                "detection_count": len(detections),
                "target": metadata.get("target", "") if metadata else ""
            }
        }
        return await self._write_state(self.camera_state_file, state)
    
    async def load_camera_state(self) -> Dict[str, Any]:
        """カメラ状態を読み込み
        
        Returns:
            カメラ状態
        """
        return await self._read_state(self.camera_state_file)
    
    # ============================================================================
    # PLAN STATE
    # ============================================================================
    
    async def save_plan_state(self, tool: str, target: str, reasoning: str) -> bool:
        """計画状態を保存
        
        Args:
            tool: 選択されたツール
            target: ターゲット
            reasoning: 理由
        
        Returns:
            成功したか
        """
        state = {
            "status": "completed",
            "data": {
                "tool": tool,
                "target": target,
                "reasoning": reasoning
            }
        }
        return await self._write_state(self.plan_state_file, state)
    
    async def load_plan_state(self) -> Dict[str, Any]:
        """計画状態を読み込み
        
        Returns:
            計画状態
        """
        return await self._read_state(self.plan_state_file)
    
    # ============================================================================
    # EXECUTION STATE
    # ============================================================================
    
    async def save_execution_state(
        self,
        speech: str,
        motor_commands: list,
        status: str = "completed"
    ) -> bool:
        """実行状態を保存
        
        Args:
            speech: 音声出力
            motor_commands: モーターコマンド
            status: ステータス
        
        Returns:
            成功したか
        """
        state = {
            "status": status,
            "data": {
                "speech": speech,
                "motor_commands": motor_commands,
                "motor_count": len(motor_commands)
            }
        }
        return await self._write_state(self.execution_state_file, state)
    
    async def load_execution_state(self) -> Dict[str, Any]:
        """実行状態を読み込み
        
        Returns:
            実行状態
        """
        return await self._read_state(self.execution_state_file)
    
    # ============================================================================
    # UTILITY
    # ============================================================================
    
    async def clear_all(self) -> bool:
        """全ての状態をクリア"""
        try:
            for state_file in [
                self.voice_state_file,
                self.camera_state_file,
                self.plan_state_file,
                self.execution_state_file
            ]:
                self._init_state_file(state_file)
            return True
        except Exception as e:
            print(f"⚠️  Failed to clear all states: {e}")
            return False
    
    async def get_summary(self) -> Dict[str, Any]:
        """全ステートの要約を取得
        
        Returns:
            サマリー
        """
        return {
            "voice": await self.load_voice_state(),
            "camera": await self.load_camera_state(),
            "plan": await self.load_plan_state(),
            "execution": await self.load_execution_state()
        }


# グローバルインスタンス
_data_manager: Optional[DataManager] = None


def get_data_manager(data_dir: Optional[Path] = None) -> DataManager:
    """DataManager シングルトンを取得"""
    global _data_manager
    if _data_manager is None:
        _data_manager = DataManager(data_dir)
    return _data_manager
