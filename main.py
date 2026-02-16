import asyncio
from commandl_ine import CommandLine, GUI
from brain import Brain
from vision-text-llm import OllamaVisionChat

class Main:
    # ... existing methods ...

    @staticmethod
    async def gemma3_4b_cloud():
        model = "gemma3:4b-cloud"
        chat = OllamaVisionChat(model)
        # Implementation of gemma3_4b_cloud method...
