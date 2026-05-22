"""
VoiceChatManager: 音声入出力の統合管理
- Groq Whisper STT（音声認識）
- Edge TTS（音声合成）
- 状態管理
"""

import asyncio
import subprocess
import os
import sys
import edge_tts
from typing import Optional
from pathlib import Path


class VoiceChatManager:
    """音声入出力の統合マネージャー"""
    
    def __init__(self):
        """Initialize voice chat manager"""
        self.transcription_file = "/tmp/speech_transcription.txt"
        self.audio_output_file = "/tmp/speech_output.mp3"
        self.script_dir = Path(__file__).parent
    
    async def listen(self, timeout: int = 15) -> str:
        """
        音声入力（Groq Whisper STT）
        
        Args:
            timeout: タイムアウト時間（秒）
        
        Returns:
            認識されたテキスト
        """
        script_path = self.script_dir / "groq-whisper-stt.py"
        
        if not script_path.exists():
            print(f"⚠️  STT スクリプトが見つかりません: {script_path}")
            return ""
        
        try:
            print("🎤 音声認識を開始します...")
            result = subprocess.run(
                ["python3", str(script_path)],
                capture_output=True,
                timeout=timeout
            )
            
            # 認識結果を読み込み
            if os.path.exists(self.transcription_file):
                with open(self.transcription_file, "r", encoding="utf-8") as f:
                    text = f.read().strip()
                
                if text:
                    print(f"✅ 認識完了: {text}")
                    return text
        
        except subprocess.TimeoutExpired:
            print(f"⚠️  STT タイムアウト（{timeout}秒）")
        except Exception as e:
            print(f"⚠️  STT エラー: {e}")
        
        return ""
    
    async def speak(self, text: str, voice: str = 'ja-JP-NanamiNeural') -> None:
        """
        音声出力（Edge TTS）
        
        Args:
            text: 出力するテキスト
            voice: 使用する音声（デフォルト: 日本語）
        """
        try:
            print(f"🔊 音声出力: {text}")
            print("   🎙️  オーディオを生成中...")
            
            # Edge TTS でオーディオを生成
            communicate = edge_tts.Communicate(text, voice)
            await communicate.save(self.audio_output_file)
            
            # プラットフォーム別に再生
            await self._play_audio(self.audio_output_file)
            
            print("   ✅ 再生完了")
        
        except Exception as e:
            print(f"⚠️  TTS エラー: {e}")
    
    async def _play_audio(self, audio_file: str) -> None:
        """プラットフォーム別のオーディオ再生"""
        try:
            if sys.platform == "darwin":
                # macOS
                subprocess.run(['afplay', audio_file], check=False)
            elif sys.platform == "linux":
                # Linux
                subprocess.run(['mpg123', audio_file], check=False)
            elif sys.platform == "win32":
                # Windows
                import winsound
                winsound.PlaySound(audio_file, winsound.SND_FILENAME)
        except Exception as e:
            print(f"⚠️  オーディオ再生エラー: {e}")


__all__ = ['VoiceChatManager']
