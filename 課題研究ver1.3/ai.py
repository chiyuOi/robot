from api_client import AutoRotatingAPIClient

class Ai:
    def __init__(
        self,
        api_client: AutoRotatingAPIClient,
        prompt: str,
        # URLをGroqのオンラインAPIに変更
        api_url: str = "https://api.groq.com/openai/v1/chat/completions",
        # モデル名をGroq上のQwenに変更
        model: str = "qwen-2.5-32b",
        temperature: float = 0.7,
        keep_history: bool = True
    ):
        self.api_client = api_client
        self.prompt = prompt
        self.api_url = api_url
        self.model = model
        self.temperature = temperature
        self.keep_history = keep_history
        self.history = [{"role": "system", "content": self.prompt}]

    def send(self, message: str) -> str:
        if not self.keep_history:
            self.history = [{"role": "system", "content": self.prompt}]

        self.history.append({"role": "user", "content": message})

        payload = {
            "model": self.model,
            "messages": self.history,
            "temperature": self.temperature
        }

        response = self.api_client.post(self.api_url, json=payload)
        data = response.json()

        assistant_message = data["choices"][0]["message"]["content"].strip()

        if self.keep_history:
            self.history.append({"role": "assistant", "content": assistant_message})

        return assistant_message