"""
test/unit/test_data_manager.py: DataManager ユニットテスト
- State Save/Load 機能
- JSON 永続化
- エラーハンドリング
"""

import pytest
import asyncio
from pathlib import Path
from test.conftest import InMemoryDataManager


@pytest.mark.unit
class TestDataManager:
    """DataManager ユニットテスト"""
    
    @pytest.fixture
    def dm(self):
        """DataManager インスタンス"""
        return InMemoryDataManager()
    
    @pytest.mark.asyncio
    async def test_save_voice_state(self, dm):
        """Voice State 保存テスト"""
        result = await dm.save_voice_state(
            transcription="テスト音声",
            metadata={"confidence": 0.95}
        )
        assert result is True
        
        # 状態を読み込んで確認
        state = await dm.load_voice_state()
        assert state['data']['transcription'] == "テスト音声"
        assert state['data']['confidence'] == 0.95
    
    @pytest.mark.asyncio
    async def test_save_camera_state(self, dm):
        """Camera State 保存テスト"""
        detections = [
            {"label": "person", "x": 100, "y": 200, "confidence": 0.9}
        ]
        
        result = await dm.save_camera_state(
            detections=detections,
            image_description="テスト画像",
            metadata={"target": "person"}
        )
        assert result is True
        
        # 状態を読み込んで確認
        state = await dm.load_camera_state()
        assert len(state['data']['detections']) == 1
        assert state['data']['image_description'] == "テスト画像"
    
    @pytest.mark.asyncio
    async def test_save_plan_state(self, dm):
        """Plan State 保存テスト"""
        result = await dm.save_plan_state(
            tool="YOLO",
            target="person",
            reasoning="User requested detection"
        )
        assert result is True
        
        # 状態を読み込んで確認
        state = await dm.load_plan_state()
        assert state['data']['tool'] == "YOLO"
        assert state['data']['target'] == "person"
    
    @pytest.mark.asyncio
    async def test_save_execution_state(self, dm):
        """Execution State 保存テスト"""
        commands = [{"axis": "a", "angle": 10}]
        
        result = await dm.save_execution_state(
            speech="実行結果",
            motor_commands=commands,
            status="completed"
        )
        assert result is True
        
        # 状態を読み込んで確認
        state = await dm.load_execution_state()
        assert state['data']['speech'] == "実行結果"
        assert len(state['data']['motor_commands']) == 1
    
    @pytest.mark.asyncio
    async def test_get_summary(self, dm):
        """Summary 取得テスト"""
        # 各ステートを保存
        await dm.save_voice_state("音声")
        await dm.save_plan_state("YOLO", "person", "reason")
        await dm.save_camera_state([], "画像")
        await dm.save_execution_state("応答", [])
        
        # Summary を取得
        summary = await dm.get_summary()
        
        assert 'voice' in summary
        assert 'camera' in summary
        assert 'plan' in summary
        assert 'execution' in summary
    
    @pytest.mark.asyncio
    async def test_clear_all(self, dm):
        """Clear All テスト"""
        # ステートを保存
        await dm.save_voice_state("音声")
        
        # クリア
        result = await dm.clear_all()
        assert result is True
        
        # クリアが反映されたか確認
        summary = await dm.get_summary()
        for stage_name, stage_data in summary.items():
            assert stage_data['status'] == 'idle'
            assert len(stage_data['data']) == 0
    
    @pytest.mark.asyncio
    async def test_timestamp_updated(self, dm):
        """Timestamp が更新されるテスト"""
        # 最初の保存
        state1 = await dm.load_voice_state()
        ts1 = state1.get('timestamp')
        
        # 少し待機
        await asyncio.sleep(0.1)
        
        # 2番目の保存
        await dm.save_voice_state("音声")
        state2 = await dm.load_voice_state()
        ts2 = state2.get('timestamp')
        
        # タイムスタンプが異なることを確認
        assert ts1 != ts2
