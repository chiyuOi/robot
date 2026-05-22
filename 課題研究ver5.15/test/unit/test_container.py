"""
test/unit/test_container.py: DIContainer ユニットテスト
- サービス登録
- サービス取得
- Singleton パターン
"""

import pytest
from main.container import DIContainer
from main.interfaces import IVoiceChat, ICamera


class TestServiceImpl(IVoiceChat):
    """テスト用の実装"""
    
    instance_count = 0
    
    def __init__(self):
        TestServiceImpl.instance_count += 1
        self.id = TestServiceImpl.instance_count
    
    async def listen(self, timeout: int = 15) -> str:
        return "test"
    
    async def speak(self, text: str, voice: str = 'ja-JP-NanamiNeural') -> None:
        pass


@pytest.mark.unit
class TestDIContainer:
    """DIContainer ユニットテスト"""
    
    @pytest.fixture(autouse=True)
    def reset_counter(self):
        """テスト前にカウンターをリセット"""
        TestServiceImpl.instance_count = 0
        yield
        TestServiceImpl.instance_count = 0
    
    def test_register_and_get(self):
        """登録と取得テスト"""
        container = DIContainer()
        container.register('TestService', TestServiceImpl)
        
        service = container.get('TestService')
        assert service is not None
        assert isinstance(service, TestServiceImpl)
    
    def test_singleton_pattern(self):
        """Singleton パターンテスト"""
        container = DIContainer()
        container.register('TestService', TestServiceImpl, singleton=True)
        
        # 最初の取得
        service1 = container.get('TestService')
        id1 = service1.id
        
        # 2番目の取得
        service2 = container.get('TestService')
        id2 = service2.id
        
        # 同じインスタンスが返されることを確認
        assert id1 == id2
        assert service1 is service2
    
    def test_non_singleton_pattern(self):
        """Non-Singleton パターンテスト"""
        container = DIContainer()
        container.register('TestService', TestServiceImpl, singleton=False)
        
        # 最初の取得
        service1 = container.get('TestService')
        id1 = service1.id
        
        # 2番目の取得
        service2 = container.get('TestService')
        id2 = service2.id
        
        # 異なるインスタンスが返されることを確認
        assert id1 != id2
        assert service1 is not service2
    
    def test_unregistered_service(self):
        """未登録サービスの取得テスト"""
        container = DIContainer()
        
        with pytest.raises(ValueError, match="Service not registered"):
            container.get('UnknownService')
    
    def test_register_factory(self):
        """ファクトリー登録テスト"""
        container = DIContainer()
        
        def factory():
            return TestServiceImpl()
        
        container.register_factory('TestService', factory)
        service = container.get('TestService')
        
        assert service is not None
        assert isinstance(service, TestServiceImpl)
    
    def test_factory_singleton(self):
        """ファクトリー Singleton パターンテスト"""
        container = DIContainer()
        
        def factory():
            return TestServiceImpl()
        
        container.register_factory('TestService', factory, singleton=True)
        
        service1 = container.get('TestService')
        id1 = service1.id
        
        service2 = container.get('TestService')
        id2 = service2.id
        
        # 同じインスタンスが返されることを確認
        assert id1 == id2
    
    def test_clear_container(self):
        """コンテナクリアテスト"""
        container = DIContainer()
        container.register('TestService', TestServiceImpl)
        
        # クリア前に取得できることを確認
        service = container.get('TestService')
        assert service is not None
        
        # クリア
        container.clear()
        
        # クリア後は ValueError が発生することを確認
        with pytest.raises(ValueError):
            container.get('TestService')
