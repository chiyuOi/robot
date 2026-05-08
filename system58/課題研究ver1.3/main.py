import asyncio

from commandl_ine import CommandLine, GUI
from brain import Brain
from vision_text_llm import OllamaVisionChat
from motor import StepperManager
from state import State, CameraState, VoiceState
"""
from camera import 
from voice import 
"""


class Main:
    def __init__(self):
        self.stepper = StepperManager()
        self.tr_command = {
            "上": lambda: self.stepper.move(a=5),
            "下": lambda: self.stepper.move(a=-5),
            "右": lambda: self.stepper.move(b=5),
            "左": lambda: self.stepper.move(b=-5),
        }
        self.fps = 5

    async def brain_loop(self):
        print("Brain loop 開始")
        brain = Brain()

        while True:
            await asyncio.sleep(1 / self.fps)
            try:
                result = brain.decide(situation=State)
                print(f"決定事項: {result}")
                if result in self.tr_command:
                    self.tr_command[result]()

            except Exception as e:
                print(f"エラーが発生: {e}")

    @staticmethod
    async def camera_loop():
        print("camera loop")
        while True:
            await asyncio.sleep(0.001)

    @staticmethod
    async def voice_loop():
        print("voice loop")
        while True:
            await asyncio.sleep(0.001)

    @staticmethod
    async def commandline_loop():
        print("commandline loop")
        while True:
            await asyncio.sleep(0.001)
            cli = CommandLine()
            gui = GUI(cli)
            gui.run()
    
    @staticmethod
    async def gemma3_4b_cloud():
        model = "gemma3:4b-cloud"
        chat = OllamaVisionChat(model)
        # Implementation of gemma3_4b_cloud method...


async def main():
    m = Main()
    await asyncio.gather(
        m.brain_loop(),
        m.camera_loop(),
        m.voice_loop(),
        m.commandline_loop(),
        m.gemma3_4b_cloud(),
        return_exceptions=True
    )


if __name__ == "__main__":
    print(
        "\n",
        "⬜️⬜️⬜️⬜️⬜️⬜️⬜️⬛️⬜️⬜️⬜️⬜️⬜️⬜️⬜️⬜️⬜️⬜️⬜️⬜️⬜️⬜️⬜️⬜️\n",
        "⬜️⬜️⬜️⬜️⬜️⬜️⬜️⬛️⬛️⬜️⬜️⬜️⬜️⬜️⬜️⬜️⬜️⬜️⬜️⬜️⬜️⬜️⬜️⬜️\n",
        "⬜️⬜️⬜️⬜️⬜️⬜️⬛️⬜️⬛️⬜️⬜️⬛️⬛️⬜️⬜️⬜️⬜️⬜️⬜️⬜️⬜️⬜️⬜️⬜️\n",
        "⬜️⬜️⬜️⬜️⬜️⬛️⬜️⬜️⬛️⬜️⬛️⬜️⬛️⬜️⬜️⬜️⬜️⬜️⬜️⬜️⬜️⬜️⬜️⬜️\n",
        "⬜️⬜️⬜️⬜️⬛️⬛️⬜️⬜️⬛️⬛️⬜️⬜️⬛️⬜️⬜️⬜️⬜️⬜️⬜️⬜️⬜️⬜️⬜️⬜️\n",
        "⬜️⬛️⬜️⬛️⬜️⬜️⬜️⬜️⬜️⬜️⬜️⬜️⬜️⬜️⬜️⬜️⬜️⬜️⬜️⬜️⬜️⬜️⬜️⬜️\n",
        "⬜️⬜️⬛️⬛️⬜️⬛️⬜️⬜️⬜️⬜️⬜️⬜️⬛️⬜️⬜️⬛️⬛️⬜️⬜️⬜️⬜️⬜️⬜️⬜️\n",
        "⬜️⬛️⬛️⬛️⬜️⬜️⬜️⬜️⬜️⬛️⬜️⬜️⬛️⬜️⬜️⬜️⬜️⬜️⬜️⬛️⬜️⬜️⬜️⬜️\n",
        "⬜️⬜️⬛️⬜️⬜️⬛️⬜️⬛️⬜️⬜️⬜️⬜️⬛️⬜️⬛️⬛️⬛️⬜️⬛️⬛️⬛️⬜️⬜️⬜️\n",
        "⬜️⬜️⬛️⬜️⬜️️⬜️⬛️⬛️⬜️⬛️⬛️⬜️⬛️⬜️⬜️⬜️⬜️⬜️⬜️⬛️⬜️⬜️⬜️⬜️\n",
        "⬜️⬜️⬜️⬛️⬜️⬜️️⬜️⬜️⬜️⬜️⬛️⬛️⬜️⬜️⬜️⬜️⬜️⬜️⬜️⬜️⬜️⬜️⬜️⬜️\n",
        "⬜️⬜️⬜️⬜️⬜️⬜️⬜️⬜️⬜️⬛️⬜️⬛️⬜️⬛️⬜️⬜️⬜️⬜️⬜️⬜️⬜️⬜️⬜️⬜️\n",
        "⬜️⬜️⬜️⬜️⬛️⬜️⬜️⬜️⬜️⬜️⬜️⬜️⬜️⬜️⬛️⬜️⬜️⬜️⬜️⬜️⬜️⬜️⬜️⬜️\n",
        "⬜️⬜️⬜️⬜️⬛️⬜️⬜️⬜️⬜️⬜️⬜️⬜️⬛️⬜️⬜️⬜️⬛️⬜️⬜️⬜️⬜️⬜️⬜️⬜️\n",
        "⬜️⬜️⬜️⬜️⬛️⬜️⬜️⬜️⬜️⬜️⬜️⬜️⬛️⬜️⬜️⬜️⬜️⬛️⬜️⬜️⬜️⬜️⬜️⬜️\n",
        "⬜️⬜️⬜️⬜️⬛️⬜️⬜️⬜️⬜️⬜️⬜️⬛️⬜️⬜️⬜️⬜️⬜️⬜️⬛️⬜️⬜️⬜️⬜️⬜️\n",
        "⬜️⬜️⬜️⬜️⬛️⬜️⬜️⬜️⬜️⬛️⬜️⬜️⬛️⬜️⬜️⬜️⬜️⬜️⬜️⬛️⬜️⬜️⬜️⬜️\n",
        "⬜️⬜️⬜️⬜️⬛️⬜️⬜️⬜️⬜️⬛️⬜️⬜️⬛️⬜️⬜️⬜️⬜️⬜️⬜️⬛️⬛️⬜️⬜️⬜️\n",
        "⬜️⬜️⬜️⬜️⬛️⬜️⬜️⬛️⬜️⬛️⬜️⬜️⬛️⬜️⬜️⬜️⬜️⬜️⬜️⬛️⬜️⬛️⬜️⬜️\n",
        "⬜️⬜️⬜️⬜️⬜️⬛️⬛️⬜️⬜️⬜️⬛️⬛️⬜️⬜️⬜️⬛️⬛️⬛️⬛️⬜️⬛️⬜️⬛️⬜️\n",
        "⬜️⬜️⬜️⬜️⬜️⬜️⬜️⬜️⬜️⬜️⬜️⬜️⬜️⬜️⬜️⬜️⬜️⬜️⬜️⬜️⬜️⬜️⬜️⬜️\n",
    )
    asyncio.run(main())