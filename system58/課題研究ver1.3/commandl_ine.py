import tkinter as tk
import asyncio
class CommandLine:
    def __init__(self):
        print("run CommandLine")
        self.current_mode = "auto"
        self.command_list = {
            "/mode": self.change_mode,
            "/status": self.status,
            "/exit": self.exit_cli,
        }

        self.mode_list = ["program", "auto","test"]

    @staticmethod
    async def r_line():
        return await asyncio.to_thread(input, "enter your line: ")

    async def change_mode(self):
        print(f"Select mode:{self.mode_list}")
        new_mode = await self.r_line()
        if new_mode in self.mode_list:
            self.current_mode = new_mode
            print(f'\033[32mMode changed to: {self.current_mode}\033[0m')
        else:
            print('\033[31mInvalid mode.\033[0m')

    async def status(self):
        print(f"Current Mode: {self.current_mode}")

    async def exit_cli(self):
        print("bye")
        raise SystemExit

    async def c_line(self):
        try:
            cmd = await self.r_line()
            func = self.command_list.get(str(cmd))
            if func:
                await func()
            else:
                print('\033[31m' + "unknown command", '\033[0m')
        except Exception as e:
            print("command error:", e)

    async def cli_loop(self):
        while True:
            await self.c_line()

class GUI:
    def __init__(self, cli):
        self.cli = cli
        self.root = tk.Tk()
        self.root.title("CommandLine")

        self.output = tk.Text(self.root, height=10, width=40)
        self.output.pack()

        self.entry = tk.Entry(self.root, width=40)
        self.entry.pack()

        self.entry.bind("<Return>", self.handle_input)

    def log(self, text):
        self.output.insert(tk.END, text + "\n")
        self.output.see(tk.END)

    def handle_input(self, event=None):
        cmd = self.entry.get()
        self.entry.delete(0, tk.END)

        if cmd.startswith("/mode"):
            parts = cmd.split()
            if len(parts) == 2:
                result = asyncio.run(self.cli.change_mode(parts[1]))
                self.log(result)
            else:
                self.log("Usage: /mode <program|auto|test>")

        elif cmd == "/status":
            result = asyncio.run(self.cli.status())
            self.log(result)

        else:
            self.log("unknown command")

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    cli = CommandLine()
    gui = GUI(cli)
    gui.run()
