"""
Exceptions: カスタム例外クラス定義
- エラーハンドリング体系
- エラー種別の明確化
"""


class RobotException(Exception):
    """ロボットシステム基本例外"""
    
    def __init__(self, message: str, error_code: str = "UNKNOWN"):
        self.message = message
        self.error_code = error_code
        super().__init__(f"[{error_code}] {message}")


class SensingException(RobotException):
    """感知ステージエラー"""
    
    def __init__(self, message: str):
        super().__init__(message, "SENSING_ERROR")


class PlanningException(RobotException):
    """計画ステージエラー"""
    
    def __init__(self, message: str):
        super().__init__(message, "PLANNING_ERROR")


class ActionException(RobotException):
    """行動ステージエラー"""
    
    def __init__(self, message: str):
        super().__init__(message, "ACTION_ERROR")


class IntegrationException(RobotException):
    """統合ステージエラー"""
    
    def __init__(self, message: str):
        super().__init__(message, "INTEGRATION_ERROR")


class ExecutionException(RobotException):
    """実行ステージエラー"""
    
    def __init__(self, message: str):
        super().__init__(message, "EXECUTION_ERROR")


class APIException(RobotException):
    """API通信エラー"""
    
    def __init__(self, message: str, api_name: str = ""):
        super().__init__(f"{api_name}: {message}", "API_ERROR")


class HardwareException(RobotException):
    """ハードウェアエラー"""
    
    def __init__(self, message: str, device: str = ""):
        super().__init__(f"{device}: {message}", "HARDWARE_ERROR")


class ConfigException(RobotException):
    """設定エラー"""
    
    def __init__(self, message: str):
        super().__init__(message, "CONFIG_ERROR")
