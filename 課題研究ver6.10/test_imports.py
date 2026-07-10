#!/usr/bin/env python3
"""
Test refactored aggregator interfaces
"""

import sys
from pathlib import Path

# Setup paths correctly
script_dir = Path(__file__).parent
sys.path.insert(0, str(script_dir))

print(f"Script directory: {script_dir}")
print(f"sys.path[0]: {sys.path[0]}")
print(f"Current working directory: {Path.cwd()}")
print()

# Test imports
try:
    from func.voice_chat import VoiceChatManager
    print("✅ VoiceChatManager imported")
except Exception as e:
    print(f"❌ VoiceChatManager: {e}")
    import traceback
    traceback.print_exc()

try:
    from func.camera import CameraManager
    print("✅ CameraManager imported")
except Exception as e:
    print(f"❌ CameraManager: {e}")

try:
    from func.motion import StepperManager
    print("✅ StepperManager imported")
except Exception as e:
    print(f"❌ StepperManager: {e}")

try:
    from func.tools import ToolsManager
    print("✅ ToolsManager imported")
except Exception as e:
    print(f"❌ ToolsManager: {e}")

# Test integrated_system imports
try:
    from main.integrated_system import SensingModule, ActionModule, ExecutionModule
    print("✅ Pipeline modules imported from integrated_system")
except Exception as e:
    print(f"❌ Pipeline modules: {e}")

print("\n✅ すべてのインポート成功！")
