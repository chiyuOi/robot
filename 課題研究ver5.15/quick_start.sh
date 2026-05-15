#!/bin/bash
# quick_start.sh - 統合AIロボットシステム クイックスタートガイド

echo "=================================="
echo "統合AIロボットシステム クイックスタート"
echo "=================================="
echo ""

# 1. Check Python version
echo "✓ 1. Python バージョン確認..."
python3 --version

# 2. Check dependencies
echo ""
echo "✓ 2. 依存パッケージ確認..."
pip3 show groq ultralytics opencv-python numpy gpiozero python-dotenv | grep "Name:" || echo "⚠️  一部パッケージが未インストール"

# 3. Check .env file
echo ""
echo "✓ 3. 環境設定確認..."
if [ -f ".env" ]; then
    echo "✅ .env ファイルが存在します"
else
    echo "⚠️  .env ファイルが見つかりません（オプション）"
    echo "   Groq API を使用する場合は .env を作成してください"
    echo "   例: echo 'MY_API_KEY_1=your_key' > .env"
fi

# 4. Run tests
echo ""
echo "✓ 4. テストスイート起動オプション："
echo ""
echo "選択してください:"
echo "  1) テストスイート実行（メニュー形式）"
echo "  2) シングルパイプライン実行"
echo "  3) 連続実行モード"
echo "  4) カスタムテスト実行"
echo ""

read -p "選択 (1-4): " choice

case $choice in
  1)
    echo ""
    echo "🚀 テストスイートを起動します..."
    python3 test_integrated_system.py
    ;;
  2)
    echo ""
    echo "🚀 シングルパイプラインを起動します..."
    python3 main/integrated_system.py
    ;;
  3)
    echo ""
    echo "🚀 連続実行モードを起動します..."
    echo "   (Ctrl+C で終了)"
    python3 main/integrated_system.py --continuous
    ;;
  4)
    echo ""
    echo "🚀 カスタムテストオプション:"
    echo "  a) Execution Module テスト"
    echo "  b) Action Module テスト"
    echo "  c) 全モジュール統合テスト"
    echo ""
    read -p "選択 (a-c): " test_choice
    
    case $test_choice in
      a)
        echo "Execution Module テストを実行します..."
        python3 << 'EOF'
import asyncio
from main.integrated_system import ExecutionModule

async def test():
    exec_module = ExecutionModule(stepper_manager=None)
    response = {
        "speech": "テスト実行成功",
        "motor_commands": [{"axis": "a", "angle": 10}],
        "status": "success"
    }
    await exec_module.execute_response(response)

asyncio.run(test())
EOF
        ;;
      b)
        echo "Action Module テストを実行します..."
        python3 << 'EOF'
import asyncio
from main.integrated_system import ActionModule

async def test():
    action = ActionModule()
    config = {"tool": "CONVERSATION", "target": None}
    result = await action.execute(config)
    print(f"Result: {result}")

asyncio.run(test())
EOF
        ;;
      c)
        echo "全モジュール統合テストを実行します..."
        python3 test_integrated_system.py
        ;;
      *)
        echo "無効な選択です"
        ;;
    esac
    ;;
  *)
    echo "無効な選択です"
    ;;
esac

echo ""
echo "✅ クイックスタート完了"
echo ""
echo "詳細は以下のドキュメントを参照してください:"
echo "  - INTEGRATED_SYSTEM_README.md (実行ガイド)"
echo "  - ARCHITECTURE_DETAILED.md (アーキテクチャ詳細)"
echo "  - FIX_LOG.md (修正内容)"
