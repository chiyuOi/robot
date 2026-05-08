from api_client import AutoRotatingAPIClient
from ai import Ai


CONTROL_PROMPT = """
あなたはロボットを動かすAIシステムです。ハードウェア安全装置、カメラ、ボイスからの命令や状況報告を元にカメラを動かすコマンドを送ってください。
コマンド一覧:
"上", "下", "右", "左", "停止", "話す", "判断不能"
※「話す」は、他のAIにスピーカーを使って話すことを許可する状態です。

重要: 出力は上記のコマンドのみとし、理由や余計な言葉は一切出力しないでください。
出力例: 左
出力例: 話す
"""

CHAT_PROMPT = "あなたはロボットの会話AIシステムです。ハードウェア安全装置、カメラ、ボイスからの命令や状況報告を元に人間と自然な会話をしてください。"


class Brain:
    def __init__(self):
        try:
            self.api_client = AutoRotatingAPIClient(env_prefix="MY_API_KEY")

        except ValueError as e:
            print(f"⚠️ 警告: {e}")
            exit(1)

        # ★確実に動くGroqの標準モデルを指定してテストする
        test_url = "https://api.groq.com/openai/v1/chat/completions"
        test_model = "llama-3.1-8b-instant"

        self.control_ai = Ai(
            api_client=self.api_client,
            prompt=CONTROL_PROMPT,
            api_url=test_url,
            model=test_model,
            keep_history=False
        )
        self.chat_ai = Ai(
            api_client=self.api_client,
            prompt=CHAT_PROMPT,
            api_url=test_url,
            model=test_model,
            keep_history=True
        )

    def decide(self, situation: str):
        command = self.control_ai.send(message=situation)
        print(f"[システム内部] run_cmd: {command}")
        if "話す" in command:
            speech_text = self.chat_ai.send(message=f"状況: {situation}。これについて人間と短く話して。")
            return speech_text

        return command


if __name__ == "__main__":
    a1=int(input())
    if a1 == 1:

        from motor import Limiter,StepperManager
        import asyncio

        print("※終了する場合は 'q' ")
        brain = Brain()
        ms=StepperManager()

        tr_command = {
                "上":lambda:ms.move(speed=500,a=32),
                "下":lambda:ms.move(speed=500,a=-32),
                "右":lambda:ms.move(speed=500,b=32),
                "左":lambda:ms.move(speed=500,b=-32),
            }

        async def main():
                await tr_command[result]()

        while True:
            situation_input = input("\n状況を入力してください > ")
            if situation_input.lower() in ['q', 'quit', 'exit']:
                print("システムを終了します。")
                break

            if not situation_input.strip():
                continue

            try:
                result = brain.decide(situation=situation_input)
                print(result)
                asyncio.run(main())

            except Exception as e:
                print(f"エラーが発生: {e}")
    elif a1 == 2:
        brain = Brain()
        while True:
            situation_input = input("\n状況を入力してください > ")
            if situation_input.lower() in ['q', 'quit', 'exit']:
                print("システムを終了します。")
                break

            if not situation_input.strip():
                continue

            try:
                result = brain.decide(situation=situation_input)
                print(result)

            except Exception as e:
                print(f"エラーが発生: {e}")
