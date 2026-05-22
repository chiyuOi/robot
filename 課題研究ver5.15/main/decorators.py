"""
Decorators: 再利用可能なデコレーター
- リトライロジック
- タイミング測定
- ログ記録
"""

import asyncio
import time
import logging
from functools import wraps
from typing import Callable, Type, Tuple, Any


logger = logging.getLogger(__name__)


def async_retry(
    max_attempts: int = 3,
    backoff_factor: float = 2.0,
    initial_delay: float = 1.0,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
    on_retry: Callable = None
):
    """非同期関数用リトライデコレーター
    
    Args:
        max_attempts: 最大試行回数
        backoff_factor: 指数バックオフの係数
        initial_delay: 初期遅延時間（秒）
        exceptions: リトライ対象の例外タプル
        on_retry: リトライ時に呼ぶコールバック関数
    
    Returns:
        デコレーター関数
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    
                    if attempt == max_attempts - 1:
                        logger.error(
                            f"Function {func.__name__} failed after {max_attempts} attempts: {e}"
                        )
                        raise
                    
                    wait_time = initial_delay * (backoff_factor ** attempt)
                    logger.warning(
                        f"Function {func.__name__} attempt {attempt + 1}/{max_attempts} failed. "
                        f"Retrying in {wait_time:.2f}s... ({type(e).__name__}: {e})"
                    )
                    
                    if on_retry:
                        await on_retry(attempt, e)
                    
                    await asyncio.sleep(wait_time)
            
            if last_exception:
                raise last_exception
        
        return wrapper
    
    return decorator


def sync_retry(
    max_attempts: int = 3,
    backoff_factor: float = 2.0,
    initial_delay: float = 1.0,
    exceptions: Tuple[Type[Exception], ...] = (Exception,)
):
    """同期関数用リトライデコレーター
    
    Args:
        max_attempts: 最大試行回数
        backoff_factor: 指数バックオフの係数
        initial_delay: 初期遅延時間（秒）
        exceptions: リトライ対象の例外タプル
    
    Returns:
        デコレーター関数
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    
                    if attempt == max_attempts - 1:
                        logger.error(
                            f"Function {func.__name__} failed after {max_attempts} attempts: {e}"
                        )
                        raise
                    
                    wait_time = initial_delay * (backoff_factor ** attempt)
                    logger.warning(
                        f"Function {func.__name__} attempt {attempt + 1}/{max_attempts} failed. "
                        f"Retrying in {wait_time:.2f}s..."
                    )
                    
                    time.sleep(wait_time)
            
            if last_exception:
                raise last_exception
        
        return wrapper
    
    return decorator


def async_timing(func: Callable) -> Callable:
    """非同期関数の実行時間を測定するデコレーター
    
    Args:
        func: デコレーターを適用する関数
    
    Returns:
        デコレーター適用済みの関数
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = await func(*args, **kwargs)
            elapsed = time.time() - start_time
            logger.info(f"{func.__name__} completed in {elapsed:.3f}s")
            return result
        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(f"{func.__name__} failed after {elapsed:.3f}s: {e}")
            raise
    
    return wrapper


def sync_timing(func: Callable) -> Callable:
    """同期関数の実行時間を測定するデコレーター
    
    Args:
        func: デコレーターを適用する関数
    
    Returns:
        デコレーター適用済みの関数
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            elapsed = time.time() - start_time
            logger.info(f"{func.__name__} completed in {elapsed:.3f}s")
            return result
        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(f"{func.__name__} failed after {elapsed:.3f}s: {e}")
            raise
    
    return wrapper
