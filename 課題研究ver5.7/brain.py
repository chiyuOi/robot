from groq import Groq

gl_apikey = "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"

control_prompt = """
あなたはロボットを動かすAIシステムです。ハードウェア安全装置、カメラ、ボイスからの命令や状況報告を元にカメラを動かすコマンドを送ってください
コマンド一覧
｛
    "上":カメラが上を向く
    "下":カメラが下を向く
    "右":カメラが右を向く
    "左":カメラが左を向く
    "停止":停止
    "話す":他のAIにスピーカーを使って話すことを許可しこの状態に対応します
    "判断不能": 何もしない
｝
これ以外は送ってはいけません
出力例）左
出力例）話す
"""

chat_prompt = "あなたはロボットの会話AIシステムです。ハードウェア安全装置、カメラ、ボイスからの命令や状況報告を元に会話をしてください"

class Ai:
    def __init__(self, api_key: str, prompt: str):
        self.client = Groq(api_key=api_key)
        self.prompt = prompt
        self.history = [
            {"role": "system", "content": self.prompt}
        ]

    def send(self, message: str) -> str:
        self.history.append({"role": "user", "content": message})

        response = self.client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=self.history,
            temperature=0.7
        )

        assistant_message = response.choices[0].message.content
        self.history.append({"role": "assistant", "content": assistant_message})

        return assistant_message


class Brain:
    def __init__(self):
        self.control_ai = Ai(api_key=gl_apikey, prompt=control_prompt)
        self.chat_ai = Ai(api_key=gl_apikey, prompt=chat_prompt)

    def decide(self, situation: str):
        return self.ai_logic(situation=situation)

    def ai_logic(self, situation: str):
        command = self.control_ai.send(message=situation)
        print(f"run_cmd: {command}")
        if command == "話す":
            speech_text = self.chat_ai.send(message=f"状況: {situation}。これについて人間と話して。")
            return speech_text

        return command

    def test_1_logic(self, situation: str):
        pass


if __name__ == "__main__":
    print("test_brain")
    print("※終了する場合は 'q' を入力してください。")
    brain = Brain()

    while True:
        situation_input = input("\n状況を入力してください")
        if situation_input.lower() in ['q', 'quit', 'exit']:
            print("システムを終了します。")
            break

        if not situation_input.strip():
            continue

        result = brain.decide(situation=situation_input)
        print(f"戻り値: {result}")