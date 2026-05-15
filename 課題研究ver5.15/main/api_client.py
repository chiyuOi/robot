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


class OpenRouterClient:
    """OpenRouter API Client with image/vision support"""
    
    def __init__(self):
        load_dotenv()
        self.api_key = os.getenv("OPENROUTER_API_KEY")
        if not self.api_key:
            raise ValueError("OPENROUTER_API_KEY not found in .env")
        
        self.base_url = "https://openrouter.ai/api/v1/chat/completions"
    
    def send_message_with_image(self, messages: list, model: str = "meta-llama/llama-3.2-11b-vision-instruct", max_tokens: int = 500) -> str:
        """Send message with optional image to OpenRouter
        
        Args:
            messages: List of message dicts with role, content (content can have image_url)
            model: Model to use (default: Llama 3.2 11B Vision - lightweight for Pi)
            max_tokens: Max tokens for response
        
        Returns:
            Response text
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com",
            "X-Title": "Robot Vision System"
        }
        
        payload = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": 0.5
        }
        
        response = requests.post(self.base_url, json=payload, headers=headers, timeout=30)
        response.raise_for_status()
        
        result = response.json()
        content = result["choices"][0]["message"]["content"]
        return content if content else "No response generated"
    
    def describe_image(self, image_base64: str, prompt: str = "Describe this image in detail") -> str:
        """Describe an image using OpenRouter's vision model
        
        Args:
            image_base64: Base64 encoded image data (without data URI prefix)
            prompt: Description prompt/request
        
        Returns:
            Image description
        """
        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{image_base64}"
                        }
                    },
                    {
                        "type": "text",
                        "text": prompt
                    }
                ]
            }
        ]
        
        # Use Llama 3.2 Vision - lightweight and good quality for robot
        response = self.send_message_with_image(
            messages,
            model="meta-llama/llama-3.2-11b-vision-instruct",
            max_tokens=300
        )
        return response if response else "Unable to process image"