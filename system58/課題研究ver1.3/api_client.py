import os
import time
import threading
import requests
from dotenv import load_dotenv

class AutoRotatingAPIClient:
    """
    複数APIキーの自動ローテーションとリトライ機能を内包したAPIクライアント
    """
    def __init__(self, env_prefix: str = "MY_API_KEY", auth_type: str = "Bearer"):
        load_dotenv()
        self._keys = self.load_numbered_keys(env_prefix)
        self._auth_type = auth_type

        if not self._keys:
            raise ValueError(f".env に {env_prefix}_1 などのAPIキーが設定されていません。")

        self._current_index = 0
        self._lock = threading.Lock()

    def load_numbered_keys(self, prefix: str) -> list:
        keys = []
        index = 1
        while True:
            key = os.getenv(f"{prefix}_{index}")
            if not key:
                break
            keys.append(key)
            index += 1
        return keys

    def _rotate_key(self, failed_key: str):
        with self._lock:
            current_key = self._keys[self._current_index]
            if current_key == failed_key:
                old_idx = self._current_index
                self._current_index = (self._current_index + 1) % len(self._keys)
                print(f"🔄 [API Client] 制限エラー(429)を検知。キーを切り替えました (Key_{old_idx + 1} -> Key_{self._current_index + 1})")

    def _get_current_key(self) -> str:
        with self._lock:
            return self._keys[self._current_index]

    def request(self, method: str, url: str, **kwargs) -> requests.Response:
        max_retries = len(self._keys)
        kwargs.setdefault("timeout", 10.0)

        for attempt in range(max_retries):
            current_key = self._get_current_key()
            headers = dict(kwargs.get("headers", {}))
            headers["Authorization"] = f"{self._auth_type} {current_key}".strip()
            headers["Content-Type"] = "application/json"
            kwargs["headers"] = headers

            try:
                response = requests.request(method, url, **kwargs)

                if response.status_code == 429:
                    self._rotate_key(current_key)
                    time.sleep(1)
                    continue

                response.raise_for_status()
                return response

            except requests.exceptions.RequestException as e:
                if getattr(e.response, "status_code", None) == 429:
                    self._rotate_key(current_key)
                    time.sleep(1)
                    continue
                raise e

        raise RuntimeError(f"🚨 すべてのAPIキー({max_retries}個)が利用制限に達しました。")

    def post(self, url: str, **kwargs):
        return self.request("POST", url, **kwargs)