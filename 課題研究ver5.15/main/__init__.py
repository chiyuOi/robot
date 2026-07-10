"""
Main: 5ステージAIロボットシステムの統合パッケージ
- IntegratedRobotSystem: メインシステム
- Ai: LLM会話管理
- API Clients: Groq API通信
"""

from importlib import import_module

__all__ = [
    # Main system
    'IntegratedRobotSystem',
    
    # Pipeline modules
    'SensingModule',
    'PlanningModule',
    'ActionModule',
    'IntegrationModule',
    'ExecutionModule',
    
    # LLM and API
    'Ai',
    'AutoRotatingAPIClient',
    'GroqVisionClient'
]

_MODULE_MAP = {
    'IntegratedRobotSystem': '.integrated_system',
    'SensingModule': '.integrated_system',
    'PlanningModule': '.integrated_system',
    'ActionModule': '.integrated_system',
    'IntegrationModule': '.integrated_system',
    'ExecutionModule': '.integrated_system',
    'Ai': '.ai',
    'AutoRotatingAPIClient': '.api_client',
    'GroqVisionClient': '.api_client',
}


def __getattr__(name):
    """必要なシンボルだけ遅延インポートする"""
    if name not in _MODULE_MAP:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    module = import_module(_MODULE_MAP[name], __name__)
    return getattr(module, name)
