import asyncio
import json
import sys

class Date:
    def __init__(self, config_path="local.json", *args, **kwargs):
        print("run Date")
        super().__init__(*args, **kwargs)
        self.config_path = config_path

    async def h_reed(self, value):
        config = await asyncio.to_thread(lambda: json.load(open(self.config_path, "r", encoding="utf-8")))
        keep = config.get(value, "error")
        if keep == "error":
            print('\033[31m' + "error:not found", value)
            sys.exit()
        print(keep)
        return keep

    async def s_reed(self, value):
        config = await asyncio.to_thread(lambda: json.load(open(self.config_path, "r", encoding="utf-8")))
        keep = config.get(value, "error")
        if keep == "error":
            print('\033[31m' + "error:not found", value)
        print(keep)
        return keep

    async def save(self, value, content):
        def update():
            with open(self.config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
            config[value] = content
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=4, ensure_ascii=False)
        await asyncio.to_thread(update)

        if await self.s_reed(value) != content:
            print('\033[31m' + "error:could not save", value)
            sys.exit()
        return
