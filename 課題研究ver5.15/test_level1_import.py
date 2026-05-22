#!/usr/bin/env python3
"""
Level 1: Quick Import Test
最速検証 - 各Managerが正しくインポートできるか確認
"""

import sys
from pathlib import Path

# Setup paths
script_dir = Path(__file__).parent
sys.path.insert(0, str(script_dir))

print("="*70)
print("🔍 LEVEL 1: QUICK IMPORT TEST")
print("="*70)

# Test 1: Basic imports
print("\n1️⃣ Testing basic imports...")
try:
    from func.motion import StepperManager
    from func.voice_chat import VoiceChatManager
    from func.camera import CameraManager
    from func.tools import ToolsManager
    print("   ✅ All Manager classes imported successfully")
except Exception as e:
    print(f"   ❌ Import failed: {e}")
    sys.exit(1)

# Test 2: Pipeline module imports
print("\n2️⃣ Testing pipeline module imports...")
try:
    from main import (
        IntegratedRobotSystem,
        SensingModule,
        PlanningModule,
        ActionModule,
        IntegrationModule,
        ExecutionModule,
        Ai,
        AutoRotatingAPIClient,
        GroqVisionClient
    )
    print("   ✅ All main package exports imported successfully")
except Exception as e:
    print(f"   ❌ Import failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 3: Object instantiation (without hardware)
print("\n3️⃣ Testing object instantiation...")
try:
    voice_mgr = VoiceChatManager()
    print("   ✅ VoiceChatManager instantiated")
    
    camera_mgr = CameraManager()
    print("   ✅ CameraManager instantiated")
    
    tools_mgr = ToolsManager()
    print("   ✅ ToolsManager instantiated")
except Exception as e:
    print(f"   ⚠️  Warning during instantiation: {e}")
    print("   (This may be normal if hardware not available)")

# Test 4: Check Manager methods exist
print("\n4️⃣ Checking Manager methods...")
try:
    # VoiceChatManager
    assert hasattr(VoiceChatManager, 'listen'), "VoiceChatManager missing listen()"
    assert hasattr(VoiceChatManager, 'speak'), "VoiceChatManager missing speak()"
    print("   ✅ VoiceChatManager methods OK")
    
    # CameraManager
    assert hasattr(CameraManager, 'capture_frame'), "CameraManager missing capture_frame()"
    assert hasattr(CameraManager, 'detect_objects'), "CameraManager missing detect_objects()"
    assert hasattr(CameraManager, 'describe_image'), "CameraManager missing describe_image()"
    assert hasattr(CameraManager, 'capture_and_detect'), "CameraManager missing capture_and_detect()"
    print("   ✅ CameraManager methods OK")
    
    # ToolsManager
    assert hasattr(ToolsManager, 'parse_command'), "ToolsManager missing parse_command()"
    assert hasattr(ToolsManager, 'execute_command'), "ToolsManager missing execute_command()"
    print("   ✅ ToolsManager methods OK")
except AssertionError as e:
    print(f"   ❌ {e}")
    sys.exit(1)

# Test 5: Test SensingModule with new Manager
print("\n5️⃣ Testing SensingModule with VoiceChatManager...")
try:
    sensing = SensingModule()
    assert hasattr(sensing, 'voice_chat'), "SensingModule missing voice_chat attribute"
    assert isinstance(sensing.voice_chat, VoiceChatManager), "voice_chat is not VoiceChatManager"
    print("   ✅ SensingModule uses VoiceChatManager ✓")
except Exception as e:
    print(f"   ❌ {e}")
    sys.exit(1)

# Test 6: Test ActionModule with new Manager
print("\n6️⃣ Testing ActionModule with CameraManager...")
try:
    action = ActionModule()
    assert hasattr(action, 'camera'), "ActionModule missing camera attribute"
    assert isinstance(action.camera, CameraManager), "camera is not CameraManager"
    print("   ✅ ActionModule uses CameraManager ✓")
except Exception as e:
    print(f"   ❌ {e}")
    sys.exit(1)

# Test 7: Test ExecutionModule with new Manager
print("\n7️⃣ Testing ExecutionModule with VoiceChatManager...")
try:
    execution = ExecutionModule()
    assert hasattr(execution, 'voice_chat'), "ExecutionModule missing voice_chat attribute"
    assert isinstance(execution.voice_chat, VoiceChatManager), "voice_chat is not VoiceChatManager"
    print("   ✅ ExecutionModule uses VoiceChatManager ✓")
except Exception as e:
    print(f"   ❌ {e}")
    sys.exit(1)

print("\n" + "="*70)
print("✅ LEVEL 1 TESTS PASSED - アーキテクチャ検証完了")
print("="*70)
print("""
次のステップ:
- Level 2: 各Managerの単体テスト（オプション）
- Level 3: 5ステージ完全パイプライン実行
""")
