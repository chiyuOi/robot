"""
Logger: 構造化ログシステム
- JSON ベースのログ出力
- ステージごとのログ記録
- 監査トレール機能
"""

import logging
import json
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path


class StructuredLogger:
    """構造化ログマネージャー"""
    
    def __init__(
        self,
        name: str,
        log_dir: Optional[Path] = None,
        level: int = logging.INFO
    ):
        """Initialize structured logger
        
        Args:
            name: ロガー名
            log_dir: ログファイルディレクトリ
            level: ログレベル
        """
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)
        self.log_dir = log_dir or Path.cwd() / "logs"
        
        # ログディレクトリ作成
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # ファイルハンドラー設定
        self._setup_file_handler()
        self._setup_console_handler()
    
    def _setup_file_handler(self):
        """ファイルハンドラーをセットアップ"""
        log_file = self.log_dir / f"{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)
    
    def _setup_console_handler(self):
        """コンソールハンドラーをセットアップ"""
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        formatter = logging.Formatter(
            '%(levelname)s: %(message)s'
        )
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
    
    def log_stage(
        self,
        stage: str,
        status: str,
        data: Optional[Dict[str, Any]] = None,
        duration: Optional[float] = None
    ) -> None:
        """ステージログを記録
        
        Args:
            stage: ステージ名 (SENSING, PLANNING, ACTION, etc.)
            status: ステータス (started, completed, error)
            data: ステージデータ
            duration: 実行時間（秒）
        """
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "stage": stage,
            "status": status,
            "data": data or {},
            "duration_ms": int((duration or 0) * 1000)
        }
        
        self.logger.info(json.dumps(log_entry, ensure_ascii=False))
    
    def log_error(
        self,
        stage: str,
        error: Exception,
        context: Optional[Dict[str, Any]] = None
    ) -> None:
        """エラーログを記録
        
        Args:
            stage: エラーが発生したステージ
            error: 例外オブジェクト
            context: エラーコンテキスト
        """
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "stage": stage,
            "status": "error",
            "error_type": type(error).__name__,
            "error_message": str(error),
            "context": context or {}
        }
        
        self.logger.error(json.dumps(log_entry, ensure_ascii=False))
    
    def log_decision(
        self,
        decision_point: str,
        choice: str,
        reason: str,
        context: Optional[Dict[str, Any]] = None
    ) -> None:
        """意思決定ログを記録
        
        Args:
            decision_point: 意思決定のポイント
            choice: 選択内容
            reason: 選択理由
            context: コンテキスト
        """
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "type": "decision",
            "decision_point": decision_point,
            "choice": choice,
            "reason": reason,
            "context": context or {}
        }
        
        self.logger.info(json.dumps(log_entry, ensure_ascii=False))
    
    def log_api_call(
        self,
        api_name: str,
        method: str,
        status: int,
        duration: float,
        response_size: Optional[int] = None
    ) -> None:
        """API呼び出しログを記録
        
        Args:
            api_name: API名 (Groq, Edge TTS, etc.)
            method: HTTPメソッド
            status: ステータスコード
            duration: 処理時間（秒）
            response_size: レスポンスサイズ
        """
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "type": "api_call",
            "api": api_name,
            "method": method,
            "status": status,
            "duration_ms": int(duration * 1000),
            "response_size": response_size
        }
        
        self.logger.info(json.dumps(log_entry, ensure_ascii=False))


# グローバルロガーインスタンス
_global_logger: Optional[StructuredLogger] = None


def get_logger(name: str = "robot_system") -> StructuredLogger:
    """グローバルなStructuredLogger を取得"""
    global _global_logger
    if _global_logger is None:
        _global_logger = StructuredLogger(name)
    return _global_logger
