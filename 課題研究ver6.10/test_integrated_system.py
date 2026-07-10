#!/usr/bin/env python3
"""
Test Suite for Integrated AI Robot System
Demonstrates each stage of the pipeline with sample data
"""

import asyncio
import json
import sys
from pathlib import Path

# Setup project paths properly
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import the integrated system
from main.integrated_system import (
    SensingModule,
    PlanningModule,
    ActionModule,
    IntegrationModule,
    ExecutionModule,
    IntegratedRobotSystem
)


# ============================================================================
# TEST: SENSING MODULE
# ============================================================================

async def test_sensing():
    """Test the Sensing module with voice or keyboard input"""
    print("\n" + "="*70)
    print("TEST 1: SENSING MODULE - 入力方式選択")
    print("="*70)
    
    sensing = SensingModule()
    
    print("\n📝 入力方式を選択してください:")
    print("1. 🎤 音声入力（マイク）")
    print("2. ⌨️  キーボード入力")
    choice = input("選択 (1-2, デフォルト:2): ").strip() or "2"
    
    input_method = "voice" if choice == "1" else "keyboard"
    
    user_input = await sensing.get_user_input(input_method)
    
    if user_input:
        print(f"\n✅ 入力されたテキスト: {user_input}")
        print(f"✅ Sensing test completed")
    else:
        print(f"\n❌ 入力がありません")


async def test_voice_or_keyboard_pipeline():
    """Test full pipeline with voice or keyboard input"""
    print("\n" + "="*70)
    print("VOICE OR KEYBOARD PIPELINE TEST")
    print("="*70)
    
    system = IntegratedRobotSystem()
    
    # Select input method
    print("\n📍 入力方式を選択してください:")
    print("1. 🎤 音声入力（マイク）")
    print("2. ⌨️  キーボード入力")
    choice = input("選択 (1-2, デフォルト:2): ").strip() or "2"
    
    input_method = "voice" if choice == "1" else "keyboard"
    
    # Get user input
    print(f"\n🚀 {input_method}モードでパイプラインを開始します...")
    user_input = await system.sensing.get_user_input(input_method)
    
    if not user_input:
        print("❌ 入力がありません")
        return
    
    print(f"\n1️⃣ SENSING: User input received")
    print(f"   Input: {user_input}")
    
    # Planning
    print(f"\n2️⃣ PLANNING: Selecting tool...")
    if system.planning:
        tool_config = system.planning.select_tool(user_input)
    else:
        tool_config = {"tool": "YOLO", "target": "object"}
    print(f"   Selected: {tool_config['tool']}")
    print(f"   Target: {tool_config.get('target')}")
    
    # Action
    print(f"\n3️⃣ ACTION: Executing tool...")
    observation = await system.action.execute(tool_config)
    print(f"   Status: {observation.get('status')}")
    
    # Integration
    print(f"\n4️⃣ INTEGRATION: Generating response...")
    if system.integration:
        response = system.integration.generate_response(observation, user_input)
    else:
        response = {
            "speech": "処理完了しました",
            "motor_commands": [],
            "status": "success"
        }
    print(f"   Speech: {response.get('speech')}")
    
    # Execution
    print(f"\n5️⃣ EXECUTION: Running response...")
    await system.execution.execute_response(response)
    
    print("\n✅ Full pipeline test completed successfully!")


# ============================================================================
# TEST: PLANNING MODULE
# ============================================================================

async def test_planning(api_client=None):
    """Test the Planning module with voice or keyboard input"""
    print("\n" + "="*70)
    print("TEST 2: PLANNING MODULE (Tool Selection)")
    print("="*70)
    
    if not api_client:
        print("⚠️  No API client available - skipping planning test")
        return {
            "tool": "YOLO",
            "target": "cup",
            "reasoning": "Demo mode"
        }
    
    planning = PlanningModule(api_client)
    sensing = SensingModule()
    
    # Select input method
    print("\n📍 入力方式を選択してください:")
    print("1. 🎤 音声入力（マイク）")
    print("2. ⌨️  キーボード入力")
    choice = input("選択 (1-2, デフォルト:2): ").strip() or "2"
    input_method = "voice" if choice == "1" else "keyboard"
    
    print(f"\n🚀 {input_method}モードでテストを開始します...")
    print("複数のテスト入力ができます (空白で終了):")
    print()
    
    test_inputs = []
    while True:
        user_input = await sensing.get_user_input(input_method)
        if not user_input:
            break
        test_inputs.append(user_input)
    
    if not test_inputs:
        print("❌ 入力がありません")
        return
    
    for user_input in test_inputs:
        print(f"\n🎯 Input: {user_input}")
        result = planning.select_tool(user_input)
        print(f"✅ Selected tool: {result['tool']}")
        print(f"   Target: {result.get('target', 'N/A')}")


# ============================================================================
# TEST: ACTION MODULE
# ============================================================================

async def test_action():
    """Test the Action module"""
    print("\n" + "="*70)
    print("TEST 3: ACTION & OBSERVATION MODULE")
    print("="*70)
    
    action = ActionModule()
    
    # Test YOLO
    print("\n🎯 Testing YOLO object detection...")
    tool_config = {
        "tool": "YOLO",
        "target": "cup",
        "reasoning": "User wants to find a cup"
    }
    
    result = await action.execute(tool_config)
    print(f"✅ YOLO execution result:")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    
    # Test conversation (no camera needed)
    print("\n💬 Testing conversation mode...")
    tool_config = {
        "tool": "CONVERSATION",
        "target": None
    }
    
    result = await action.execute(tool_config)
    print(f"✅ Conversation mode result:")
    print(json.dumps(result, indent=2, ensure_ascii=False))


# ============================================================================
# TEST: INTEGRATION MODULE
# ============================================================================

async def test_integration(api_client=None):
    """Test the Integration module"""
    print("\n" + "="*70)
    print("TEST 4: INTEGRATION MODULE (Response Generation)")
    print("="*70)
    
    if not api_client:
        print("⚠️  No API client available - showing demo response")
        demo_response = {
            "speech": "見つけました！左から2番目の棚にあります。",
            "motor_commands": [
                {"axis": "a", "angle": 15},
                {"axis": "b", "angle": -10}
            ],
            "status": "success"
        }
        print("✅ Demo response:")
        print(json.dumps(demo_response, indent=2, ensure_ascii=False))
        return
    
    integration = IntegrationModule(api_client)
    
    # Test observation from YOLO
    observation = {
        "status": "success",
        "action": "object_detected",
        "primary": {
            "label": "cup",
            "x": 320,
            "y": 240,
            "confidence": 0.92
        }
    }
    
    user_input = "カップを見つけてください"
    
    print(f"\n📊 Observation: {json.dumps(observation, indent=2, ensure_ascii=False)}")
    print(f"👤 User input: {user_input}")
    
    response = integration.generate_response(observation, user_input)
    print(f"\n✅ Generated response:")
    print(json.dumps(response, indent=2, ensure_ascii=False))


# ============================================================================
# TEST: EXECUTION MODULE
# ============================================================================

async def test_execution():
    """Test the Execution module"""
    print("\n" + "="*70)
    print("TEST 5: EXECUTION MODULE (Parallel Execution)")
    print("="*70)
    
    execution = ExecutionModule(stepper_manager=None)
    
    response = {
        "speech": "見つけました！左側にあります。",
        "motor_commands": [
            {"axis": "a", "angle": 30},
            {"axis": "b", "angle": -15}
        ],
        "status": "success"
    }
    
    print(f"\n📋 Response to execute:")
    print(json.dumps(response, indent=2, ensure_ascii=False))
    
    print("\n⚙️  Executing response...")
    await execution.execute_response(response)
    print("✅ Execution completed")


# ============================================================================
# TEST: FULL PIPELINE
# ============================================================================

async def test_full_pipeline():
    """Test the complete pipeline with voice or keyboard input"""
    print("\n" + "="*70)
    print("FULL PIPELINE TEST")
    print("="*70)
    
    system = IntegratedRobotSystem()
    
    # Select input method
    print("\n📍 入力方式を選択してください:")
    print("1. 🎤 音声入力（マイク）")
    print("2. ⌨️  キーボード入力")
    choice = input("選択 (1-2, デフォルト:2): ").strip() or "2"
    input_method = "voice" if choice == "1" else "keyboard"
    
    # Get user input
    print(f"\n🚀 Starting full pipeline test ({input_method}モード)...")
    user_input = await system.sensing.get_user_input(input_method)
    
    if not user_input:
        print("❌ 入力がありません")
        return
    
    print("\n1️⃣ SENSING: User input received")
    print(f"   Input: {user_input}")
    
    print("\n2️⃣ PLANNING: Selecting tool...")
    if system.planning:
        tool_config = system.planning.select_tool(user_input)
    else:
        tool_config = {"tool": "YOLO", "target": "unknown"}
    print(f"   Selected: {tool_config['tool']}")
    print(f"   Target: {tool_config.get('target')}")
    
    print("\n3️⃣ ACTION: Executing tool...")
    observation = await system.action.execute(tool_config)
    print(f"   Status: {observation.get('status')}")
    if observation.get('primary'):
        print(f"   Result: Found '{observation['primary'].get('label')}' at ({observation['primary']['x']}, {observation['primary']['y']})")
    
    print("\n4️⃣ INTEGRATION: Generating response...")
    if system.integration:
        response = system.integration.generate_response(observation, user_input)
    else:
        response = {
            "speech": "処理完了しました。",
            "motor_commands": [],
            "status": "success"
        }
    print(f"   Speech: {response.get('speech', 'N/A')}")
    print(f"   Motor commands: {response.get('motor_commands', [])}")
    
    print("\n5️⃣ EXECUTION: Running response...")
    await system.execution.execute_response(response)
    
    print("\n✅ Full pipeline test completed successfully!")


# ============================================================================
# MENU & MAIN ENTRY POINT
# ============================================================================

def print_menu():
    """Print test menu"""
    print("\n" + "="*70)
    print("INTEGRATED AI ROBOT SYSTEM - TEST SUITE")
    print("="*70)
    print("\nSelect a test to run:")
    print("1. Sensing Module (Wake word detection)")
    print("2. Planning Module (Tool selection)")
    print("3. Action Module (Object detection)")
    print("4. Integration Module (Response generation)")
    print("5. Execution Module (Parallel execution)")
    print("6. Full Pipeline Test")
    print("7. Run all tests")
    print("8. Run system in interactive mode")
    print("9. 🎤 Voice/Keyboard Pipeline Test (入力方式選択可)")
    print("0. Exit")
    print("="*70)


async def main():
    """Main test runner"""
    
    # Try to load API client
    api_client = None
    try:
        from main.api_client import AutoRotatingAPIClient
        api_client = AutoRotatingAPIClient(env_prefix="MY_API_KEY")
        print("✅ API Client initialized")
    except Exception as e:
        print(f"⚠️  API Client not available: {e}")
        print("   Tests will run in demo mode")
    
    while True:
        print_menu()
        choice = input("\nEnter choice (0-8): ").strip()
        
        try:
            if choice == "1":
                await test_sensing()
            elif choice == "2":
                await test_planning(api_client)
            elif choice == "3":
                await test_action()
            elif choice == "4":
                await test_integration(api_client)
            elif choice == "5":
                await test_execution()
            elif choice == "6":
                await test_full_pipeline()
            elif choice == "7":
                print("\n🔄 Running all tests...")
                await test_sensing()
                await test_planning(api_client)
                await test_action()
                await test_integration(api_client)
                await test_execution()
                await test_full_pipeline()
                print("\n✅ All tests completed!")
            elif choice == "8":
                print("\n🤖 Starting system in interactive mode...")
                system = IntegratedRobotSystem()
                await system.run_continuous()
            elif choice == "9":
                await test_voice_or_keyboard_pipeline()
            elif choice == "0":
                print("\n👋 Exiting test suite")
                break
            else:
                print("❌ Invalid choice. Please try again.")
        
        except KeyboardInterrupt:
            print("\n\n⚠️  Test interrupted by user")
        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 Test suite terminated")
