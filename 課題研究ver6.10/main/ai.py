"""
Ai: LLM Communication Wrapper
会話履歴を管理しながら API 通信を行う
"""

from typing import Optional, List, Dict, Any
from .api_client import AutoRotatingAPIClient


class Ai:
    """LLM（言語モデル）との会話を管理するクラス"""
    
    def __init__(
        self,
        api_client: AutoRotatingAPIClient,
        prompt: str,
        api_url: str,
        model: str,
        temperature: float = 0.7,
        keep_history: bool = True
    ):
        """
        Initialize AI wrapper
        
        Args:
            api_client: API クライアント
            prompt: システムプロンプト
            api_url: API エンドポイント
            model: 使用するモデル
            temperature: 温度パラメータ（0-1）
            keep_history: 会話履歴を保持するか
        """
        self.api_client = api_client
        self.prompt = prompt
        self.api_url = api_url
        self.model = model
        self.temperature = temperature
        self.keep_history = keep_history
        self.conversation_history: List[Dict[str, str]] = []
    
    def send(self, message: str) -> str:
        """
        メッセージを LLM に送信して応答を取得
        
        Args:
            message: ユーザーメッセージ
        
        Returns:
            LLM からの応答
        """
        try:
            # 会話履歴を構築
            messages = []
            
            # システムプロンプトを追加
            if self.prompt:
                messages.append({
                    "role": "system",
                    "content": self.prompt
                })
            
            # 過去の会話履歴を追加
            if self.keep_history:
                messages.extend(self.conversation_history)
            
            # 新しいメッセージを追加
            messages.append({
                "role": "user",
                "content": message
            })
            
            # API に送信
            response = self.api_client.send_request(
                api_url=self.api_url,
                model=self.model,
                messages=messages,
                temperature=self.temperature
            )
            
            # 応答を抽出
            if isinstance(response, dict):
                if 'choices' in response and len(response['choices']) > 0:
                    assistant_message = response['choices'][0]['message']['content']
                else:
                    assistant_message = str(response)
            else:
                assistant_message = str(response)
            
            # 会話履歴に追加
            if self.keep_history:
                self.conversation_history.append({
                    "role": "user",
                    "content": message
                })
                self.conversation_history.append({
                    "role": "assistant",
                    "content": assistant_message
                })
            
            return assistant_message
        
        except Exception as e:
            print(f"⚠️  AI エラー: {e}")
            return f"(エラー: {str(e)[:80]})"
    
    def reset_history(self):
        """会話履歴をリセット"""
        self.conversation_history = []


__all__ = ['Ai']
