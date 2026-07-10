import asyncio
import sys
import argparse
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from main.integrated_system import IntegratedRobotSystem
from main.logger import get_logger

class Main:
    def __init__(self, mode="mock", input_method="voice"):
        self.logger = get_logger("robot_main")
        self.mode = mode
        self.input_method = input_method
        self.system = IntegratedRobotSystem(mode=mode, input_method=input_method)

    async def run(self, continuous=False):
        """ロボットシステムを起動"""
        self.logger.log_stage(
            "BOOT",
            "started",
            {"continuous": continuous, "mode": self.mode, "input_method": self.input_method}
        )
        
        try:
            if continuous:
                print("🔄 Running in continuous mode...")
                await self.system.run_continuous()
            else:
                await self.system.run_pipeline()
            
            self.logger.log_stage("BOOT", "completed", {})
        except KeyboardInterrupt:
            print("\n🛑 ユーザーによって停止されました")
        except Exception as e:
            self.logger.log_error("BOOT", e, {"stack_trace": str(e)})
            raise

async def main():
    # 引数解析
    parser = argparse.ArgumentParser(description="Robot AI System - 課題研究ver5.15")
    parser.add_argument("--continuous", action="store_true", help="連続モードで実行")
    parser.add_argument(
        "--mode",
        choices=["mock", "real", "pi"],
        default="mock",
        help="mock=デモ, real/pi=実機Managerを使用"
    )
    parser.add_argument(
        "--input",
        choices=["voice", "keyboard", "auto"],
        default="voice",
        help="入力方式"
    )
    args = parser.parse_args()

    # ASCII アートの表示
    print_startup_banner()

    m = Main(mode=args.mode, input_method=args.input)
    try:
        await m.run(continuous=args.continuous)
    except KeyboardInterrupt:
        print("\n🛑 ユーザーによって停止されました")
    except Exception as e:
        print(f"\n❌ 致命的なエラー: {e}")
        import traceback
        traceback.print_exc()

def print_startup_banner():
    """起動バナーを表示"""
    banner = """
⬜️⬜️⬜️⬜️⬜️⬜️⬜️⬜️⬛️⬜️⬜️⬜️⬜️⬜️⬜️⬜️⬜️⬜️⬜️⬜️⬜️⬜️⬜️⬜️
⬜️⬜️⬜️⬜️⬜️⬜️⬜️⬛️⬛️⬜️⬜️⬜️⬜️⬜️⬜️⬜️⬜️⬜️⬜️⬜️⬜️⬜️⬜️⬜️
⬜️⬜️⬜️⬜️⬜️⬜️⬛️⬜️⬛️⬜️⬜️⬛️⬛️⬜️⬜️⬜️⬜️⬜️⬜️⬜️⬜️⬜️⬜️⬜️
⬜️⬜️⬜️⬜️⬜️⬛️⬜️⬜️⬛️⬜️⬛️⬜️⬛️⬜️⬜️⬜️⬜️⬜️⬜️⬜️⬜️⬜️⬜️⬜️
⬜️⬜️⬜️⬜️⬛️⬛️⬜️⬜️⬛️⬛️⬜️⬜️⬛️⬜️⬜️⬜️⬜️⬜️⬜️⬜️⬜️⬜️⬜️⬜️
⬜️⬛️⬜️⬛️⬜️⬜️⬜️⬜️⬜️⬜️⬜️⬜️⬜️⬜️⬜️⬜️⬜️⬜️⬜️⬜️⬜️⬜️⬜️⬜️
⬜️⬜️⬛️⬛️⬜️⬛️⬜️⬜️⬜️⬜️⬜️⬜️⬛️⬜️⬜️⬛️⬛️⬜️⬜️⬜️⬜️⬜️⬜️⬜️
⬜️⬛️⬛️⬛️⬜️⬜️⬜️⬜️⬜️⬛️⬜️⬜️⬛️⬜️⬜️⬜️⬜️⬜️⬛️⬜️⬜️⬜️⬜️⬜️
⬜️⬜️⬛️⬜️⬜️⬛️⬜️⬛️⬜️⬜️⬜️⬜️⬛️⬜️⬛️⬛️⬛️⬜️⬛️⬛️⬛️⬜️⬜️⬜️
⬜️⬜️⬛️⬜️⬜️️⬜️⬛️⬛️⬜️⬛️⬛️⬜️⬛️⬜️⬜️⬜️⬜️⬜️⬜️⬛️⬜️⬜️⬜️⬜️
⬜️⬜️⬜️⬛️⬜️⬜️️⬜️⬜️⬜️⬜️⬛️⬛️⬜️⬜️⬜️⬜️⬜️⬜️⬜️⬜️⬜️⬜️⬜️⬜️
⬜️⬜️⬜️⬜️⬜️⬜️⬜️⬜️⬜️⬛️⬜️⬛️⬜️⬛️⬜️⬜️⬜️⬜️⬜️⬜️⬜️⬜️⬜️⬜️
⬜️⬜️⬜️⬜️⬛️⬜️⬜️⬜️⬜️⬜️⬜️⬜️⬜️⬜️⬛️⬜️⬜️⬜️⬜️⬜️⬜️⬜️⬜️⬜️
⬜️⬜️⬜️⬜️⬛️⬜️⬜️⬜️⬜️⬜️⬜️⬜️⬛️⬜️⬜️⬜️⬛️⬜️⬜️⬜️⬜️⬜️⬜️⬜️
⬜️⬜️⬜️⬜️⬛️⬜️⬜️⬜️⬜️⬜️⬜️⬜️⬛️⬜️⬜️⬜️⬜️⬛️⬜️⬜️⬜️⬜️⬜️⬜️
⬜️⬜️⬜️⬜️⬛️⬜️⬜️⬜️⬜️⬜️⬜️⬛️⬜️⬜️⬜️⬜️⬜️⬜️⬛️⬜️⬜️⬜️⬜️⬜️
⬜️⬜️⬜️⬜️⬛️⬜️⬜️⬜️⬜️⬛️⬜️⬜️⬛️⬜️⬜️⬜️⬜️⬜️⬜️⬛️⬛️⬜️⬜️⬜️
"""
    print(banner)
    print("   🚀 Robot AI System v5.15 - Starting Up...")
    print("   DI Container: ✅ Ready")
    print("   Structured Logging: ✅ Active")
    print("   Error Handling: ✅ Enhanced\n")

if __name__ == "__main__":
    asyncio.run(main())
