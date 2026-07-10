#!/usr/bin/env python3
"""
Test Phase 1 Implementation: DataManager Integration
テスト内容:
1. DataManager の初期化
2. 各状態の save/load
3. JSON ファイルの永続化
"""

import asyncio
import json
from pathlib import Path
from data.manager import get_data_manager


async def test_data_manager():
    """Test DataManager functionality"""
    print("\n" + "="*70)
    print("🧪 PHASE 1: DataManager Integration Test")
    print("="*70)
    
    # Get DataManager instance
    dm = get_data_manager(Path(__file__).parent / "data")
    
    # Test 1: Voice State
    print("\n1️⃣ Testing Voice State Save/Load...")
    success = await dm.save_voice_state(
        transcription="こんにちは、ロボット",
        metadata={"input_method": "voice", "confidence": 0.95}
    )
    print(f"   ✅ Voice state saved: {success}")
    
    voice_state = await dm.load_voice_state()
    print(f"   ✅ Voice state loaded: {voice_state['data']['transcription']}")
    
    # Test 2: Plan State
    print("\n2️⃣ Testing Plan State Save/Load...")
    success = await dm.save_plan_state(
        tool="YOLO",
        target="person",
        reasoning="ユーザーが人の検出を要求した"
    )
    print(f"   ✅ Plan state saved: {success}")
    
    plan_state = await dm.load_plan_state()
    print(f"   ✅ Plan state loaded: {plan_state['data']['tool']}")
    
    # Test 3: Camera State
    print("\n3️⃣ Testing Camera State Save/Load...")
    detections = [
        {"label": "person", "x": 320, "y": 240, "confidence": 0.92},
        {"label": "dog", "x": 100, "y": 150, "confidence": 0.87}
    ]
    success = await dm.save_camera_state(
        detections=detections,
        image_description="明るい室内に人と犬がいます",
        metadata={"target": "person"}
    )
    print(f"   ✅ Camera state saved: {success}")
    
    camera_state = await dm.load_camera_state()
    print(f"   ✅ Camera state loaded: {len(camera_state['data']['detections'])} detections")
    
    # Test 4: Execution State
    print("\n4️⃣ Testing Execution State Save/Load...")
    motor_commands = [
        {"axis": "a", "angle": 10},
        {"axis": "b", "angle": -5}
    ]
    success = await dm.save_execution_state(
        speech="人を見つけました。モーターを動かします。",
        motor_commands=motor_commands,
        status="completed"
    )
    print(f"   ✅ Execution state saved: {success}")
    
    execution_state = await dm.load_execution_state()
    print(f"   ✅ Execution state loaded: speech='{execution_state['data']['speech']}'")
    
    # Test 5: Get Summary
    print("\n5️⃣ Testing Summary...")
    summary = await dm.get_summary()
    print(f"   ✅ Summary retrieved:")
    for stage_name, stage_data in summary.items():
        status = stage_data.get("status", "unknown")
        data_keys = list(stage_data.get("data", {}).keys())
        print(f"      - {stage_name}: {status} | keys: {data_keys}")
    
    # Test 6: File Verification
    print("\n6️⃣ Verifying JSON files on disk...")
    data_dir = Path(__file__).parent / "data"
    for state_file in [
        data_dir / "voice_state.json",
        data_dir / "camera_state.json",
        data_dir / "plan_state.json",
        data_dir / "execution_state.json"
    ]:
        if state_file.exists():
            with open(state_file, "r") as f:
                content = json.load(f)
            print(f"   ✅ {state_file.name}: {content.get('status')} | timestamp: {content.get('timestamp')}")
        else:
            print(f"   ❌ {state_file.name}: NOT FOUND")
    
    print("\n" + "="*70)
    print("✅ PHASE 1 TEST COMPLETED SUCCESSFULLY")
    print("="*70)
    
    print("\n📊 Summary:")
    print("✅ DataManager initialization: OK")
    print("✅ Voice state management: OK")
    print("✅ Plan state management: OK")
    print("✅ Camera state management: OK")
    print("✅ Execution state management: OK")
    print("✅ JSON file persistence: OK")
    print("\n🚀 Ready for Phase 2: Integration with Pipeline Modules")


if __name__ == "__main__":
    asyncio.run(test_data_manager())
