"""
DIContainer: 依存注入コンテナ
- サービスの登録と取得
- Singleton パターン対応
"""

from typing import Type, Dict, Any, Optional, Callable


class DIContainer:
    """Dependency Injection Container"""
    
    def __init__(self):
        """Initialize DI container"""
        self._services: Dict[str, Type] = {}
        self._singletons: Dict[str, Any] = {}
        self._factories: Dict[str, Callable] = {}
    
    def register(
        self,
        interface_name: str,
        implementation: Type,
        singleton: bool = False
    ) -> None:
        """サービスを登録
        
        Args:
            interface_name: インターフェース名（唯一識別子）
            implementation: 実装クラス
            singleton: Singleton パターンかどうか
        """
        self._services[interface_name] = {
            'impl': implementation,
            'singleton': singleton
        }
    
    def register_factory(
        self,
        interface_name: str,
        factory: Callable,
        singleton: bool = False
    ) -> None:
        """ファクトリー関数でサービスを登録
        
        Args:
            interface_name: インターフェース名
            factory: インスタンス生成用の関数
            singleton: Singleton パターンかどうか
        """
        self._factories[interface_name] = {
            'factory': factory,
            'singleton': singleton
        }
    
    def get(self, interface_name: str) -> Any:
        """サービスを取得
        
        Args:
            interface_name: インターフェース名
        
        Returns:
            インスタンス
        
        Raises:
            ValueError: サービスが登録されていない場合
        """
        # Singleton チェック
        if interface_name in self._singletons:
            return self._singletons[interface_name]
        
        # ファクトリーから取得
        if interface_name in self._factories:
            factory_info = self._factories[interface_name]
            instance = factory_info['factory']()
            
            if factory_info.get('singleton'):
                self._singletons[interface_name] = instance
            
            return instance
        
        # 登録済みサービスから取得
        if interface_name not in self._services:
            raise ValueError(f"Service not registered: {interface_name}")
        
        service_info = self._services[interface_name]
        impl_class = service_info['impl']
        instance = impl_class()
        
        if service_info.get('singleton'):
            self._singletons[interface_name] = instance
        
        return instance
    
    def clear(self) -> None:
        """登録されたサービスをクリア"""
        self._services.clear()
        self._singletons.clear()
        self._factories.clear()


# グローバルコンテナインスタンス
_global_container: Optional[DIContainer] = None


def get_container() -> DIContainer:
    """グローバルな DIContainer を取得"""
    global _global_container
    if _global_container is None:
        _global_container = DIContainer()
    return _global_container


def setup_di_container(
    voice_chat_impl,
    camera_impl,
    stepper_impl,
    tools_impl,
    data_manager_impl
) -> DIContainer:
    """DIContainer をセットアップ（初期化）
    
    Args:
        voice_chat_impl: VoiceChat実装
        camera_impl: Camera実装
        stepper_impl: Stepper実装
        tools_impl: Tools実装
        data_manager_impl: DataManager実装
    
    Returns:
        セットアップされたコンテナ
    """
    container = get_container()
    
    # すべてのサービスを Singleton として登録
    container.register('VoiceChat', voice_chat_impl, singleton=True)
    container.register('Camera', camera_impl, singleton=True)
    container.register('Stepper', stepper_impl, singleton=True)
    container.register('Tools', tools_impl, singleton=True)
    container.register('DataManager', data_manager_impl, singleton=True)
    
    return container
