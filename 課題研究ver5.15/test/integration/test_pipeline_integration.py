"""
test/integration/test_pipeline_integration.py
- Mock を使用したパイプライン統合テスト
- ステージ間のデータフロー確認
"""

import pytest
from test.conftest import MockVoiceChat, MockCamera, MockStepper, MockTools, TestDataManager
from main.integrated_system import ActionModule


@pytest.mark.integration
@pytest.mark.asyncio
class TestPipelineIntegration:
    """パイプライン統合テスト"""
    
    @pytest.mark.asyncio
    async def test_stage1_sensing_writes_to_data(self, test_data_manager):
        """STAGE 1: Sensing が DataManager に書き込む"""
        # 音声入力を保存
        await test_data_manager.save_voice_state(
            transcription="こんにちは",
            metadata={"input_method": "voice"}
        )
        
        # DataManager から読み込んで確認
        state = await test_data_manager.load_voice_state()
        assert state['data']['transcription'] == "こんにちは"
    
    @pytest.mark.asyncio
    async def test_stage2_planning_writes_to_data(self, test_data_manager):
        """STAGE 2: Planning が DataManager に書き込む"""
        await test_data_manager.save_plan_state(
            tool="YOLO",
            target="person",
            reasoning="User requested detection"
        )
        
        state = await test_data_manager.load_plan_state()
        assert state['data']['tool'] == "YOLO"
        assert state['data']['target'] == "person"
    
    @pytest.mark.asyncio
    async def test_stage3_action_writes_to_data(self, test_data_manager, mock_camera):
        """STAGE 3: Action が DataManager に書き込む"""
        # MockCamera で検出を実行
        result = await mock_camera.capture_and_detect(target="person")
        
        # DataManager に保存
        await test_data_manager.save_camera_state(
            detections=result['detections'],
            image_description=result['image_description'],
            metadata={"target": "person"}
        )
        
        # 確認
        state = await test_data_manager.load_camera_state()
        assert len(state['data']['detections']) > 0
        assert state['data']['image_description'] == "A person is in the image"
    
    @pytest.mark.asyncio
    async def test_stage5_execution_reads_from_data(self, test_data_manager, mock_voice_chat, mock_stepper):
        """STAGE 5: Execution が DataManager から読み込む"""
        # 実行状態を保存
        await test_data_manager.save_execution_state(
            speech="テスト応答",
            motor_commands=[{"axis": "a", "angle": 10}]
        )
        
        # 実行状態を読み込み
        state = await test_data_manager.load_execution_state()
        speech = state['data']['speech']
        commands = state['data']['motor_commands']
        
        # 検証
        assert speech == "テスト応答"
        assert len(commands) > 0
    
    @pytest.mark.asyncio
    async def test_mock_managers_integration(self, mock_voice_chat, mock_camera, mock_stepper, mock_tools):
        """Mock Manager 統合テスト"""
        # STAGE 1: 音声入力
        text = await mock_voice_chat.listen()
        assert text == "こんにちは"
        assert mock_voice_chat.listen_called
        
        # STAGE 3: 物体検出
        result = await mock_camera.capture_and_detect(target="person")
        assert result['status'] == "success"
        assert len(result['detections']) > 0
        
        # STAGE 5: 音声出力
        await mock_voice_chat.speak("応答")
        assert mock_voice_chat.speak_called
        
        # STAGE 5: モーター制御
        response = await mock_stepper.move(a=10, b=-5)
        assert mock_stepper.move_called
        assert mock_stepper.last_move_args == {'a': 10, 'b': -5}
    
    @pytest.mark.asyncio
    async def test_full_pipeline_data_flow(self, test_data_manager, di_container):
        """完全なパイプラインデータフロー"""
        # STAGE 1: 音声入力
        await test_data_manager.save_voice_state("ロボットよ、前に進め")
        
        # STAGE 2: 計画
        await test_data_manager.save_plan_state("MOTION_ONLY", "", "Motion command requested")
        
        # STAGE 3: 行動
        await test_data_manager.save_camera_state([], "No objects detected")
        
        # STAGE 4: 統合
        await test_data_manager.save_execution_state(
            "モーターを動かします",
            [{"axis": "c", "angle": 45}]
        )
        
        # 全ステート取得
        summary = await test_data_manager.get_summary()
        
        # 全てのステージが正常に遷移していることを確認
        assert summary['voice']['status'] == 'completed'
        assert summary['plan']['status'] == 'completed'
        assert summary['camera']['status'] == 'completed'
        assert summary['execution']['status'] == 'completed'

    @pytest.mark.asyncio
    async def test_stage3_system_report_finds_bugs_in_japanese(self, test_data_manager, di_container):
        """STAGE 3: SYSTEM_REPORT がバグ候補を日本語で返す"""
        await test_data_manager.save_voice_state("system report find bugs", {"input_method": "keyboard"})
        await test_data_manager.save_plan_state("SYSTEM_REPORT", "bugs", "report requested")
        await test_data_manager.save_camera_state([], "No objects detected")
        await test_data_manager.save_execution_state("実行失敗", [], status="error")

        action = ActionModule(container=di_container)
        action.data = test_data_manager

        result = await action.execute({"tool": "SYSTEM_REPORT"})

        assert result["action"] == "system_report_generated"
        assert result["language"] == "ja"
        assert "日本語" in result["report_text"]
        assert any(bug["stage"] == "execution" for bug in result["bugs"])
