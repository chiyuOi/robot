from groq import Groq
from openai import OpenAI
from state import State

br_apikey = "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"
system_prompt = """

"""
class Ai:
    def __init__(self, api_key: str, system_prompt: str):
        self.client = OpenAI(api_key=api_key)
        self.system_prompt = system_prompt

    def send(self, message: str) -> str:
        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": message}
            ],
            temperature=0.7
        )
        return response.choices[0].message.content

class Brain:
    def decide(self):
        return self.ai_logic
    @staticmethod
    def ai_logic(self):
        return Ai(api_key=br_apikey,system_prompt=system_prompt).send(message="")