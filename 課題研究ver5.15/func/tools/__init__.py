"""
ToolsManager: コマンド処理・プログラム翻訳を統合管理
"""

import asyncio
import json
from typing import Dict, Any, Optional
from pathlib import Path


class ToolsManager:
    """ツール統合マネージャー"""
    
    def __init__(self):
        """Initialize tools manager"""
        self.script_dir = Path(__file__).parent
    
    async def parse_command(self, text: str) -> Dict[str, Any]:
        """
        ユーザーコマンドをパース
        
        Args:
            text: ユーザー入力
        
        Returns:
            パースされたコマンド
        """
        try:
            # スラッシュコマンドの場合
            if text.startswith("/"):
                parts = text.split()
                command = parts[0]
                args = parts[1:] if len(parts) > 1 else []
                
                return {
                    "type": "command",
                    "command": command,
                    "args": args
                }
            
            # 通常のテキスト入力
            return {
                "type": "text",
                "content": text
            }
        
        except Exception as e:
            print(f"⚠️  コマンドパースエラー: {e}")
            return {
                "type": "error",
                "message": str(e)
            }
    
    async def translate_program(self, code: str) -> str:
        """
        プログラムを翻訳
        
        Args:
            code: 翻訳対象のコード
        
        Returns:
            翻訳されたコード
        """
        try:
            # program_translation.py から翻訳機能を呼び出し
            from . import program_translation
            
            # 非同期実行
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, program_translation.translate, code)
            
            return result
        
        except Exception as e:
            print(f"⚠️  プログラム翻訳エラー: {e}")
            return f"(翻訳失敗: {str(e)[:80]})"
    
    async def execute_command(self, command_str: str) -> Dict[str, Any]:
        """
        コマンドを実行
        
        Args:
            command_str: コマンド文字列
        
        Returns:
            実行結果
        """
        parsed = await self.parse_command(command_str)
        
        if parsed["type"] == "error":
            return parsed
        
        if parsed["type"] == "command":
            cmd = parsed["command"]
            
            # 既知のコマンド
            if cmd == "/mode":
                return {
                    "type": "mode_change",
                    "value": parsed["args"][0] if parsed["args"] else None
                }
            elif cmd == "/status":
                return {
                    "type": "status",
                    "message": "ロボットは正常に動作しています"
                }
            elif cmd == "/exit":
                return {
                    "type": "exit",
                    "message": "終了します"
                }
            else:
                return {
                    "type": "unknown_command",
                    "command": cmd
                }
        
        return {
            "type": "success",
            "message": "コマンド実行完了"
        }


# 内部モジュール（非公開）
from . import commandl_ine
from . import program_translation

__all__ = ['ToolsManager']
