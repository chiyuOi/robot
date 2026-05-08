import RPi.GPIO as GPIO
from gpiozero import OutputDevice
import asyncio

class Limiter:
    def __init__(self):
        self.motors_limits = {
            k: [(512//8)*1, (512//8)*7] for k in ["a","b","c","d"]
        }

    async def global_limiter(self, name):
        mn, mx = self.motors_limits[name]
        angle = self.current_step[name]   # ← 子クラスの変数を使う
        if not (mn <= angle <= mx):
            raise ValueError(f"{name} limit over: {angle}")

    async def limiter_warning(self, name):
        zone=8
        mn, mx = self.motors_limits[name]
        angle = self.current_step[name]
        if not (mn+zone <= angle):
            return "small"
        if not (angle <= mx-zone):
            return "big"
        else:
            return "safe"

    async def limit_watch(self, name):
        # 無限監視
        while True:
            await self.global_limiter(name)
            await asyncio.sleep(0.1)

  
class StepperManager(Limiter):
    def __init__(self):
        super().__init__()
        print("run StepperManager")
        self.step_sequence = [
            [1,1,0,0],[0,1,0,0],
            [0,1,1,0],[0,0,1,0],
            [0,0,1,1],[0,0,0,1],
            [1,0,0,1],[1,0,0,0]
         ]
            
        self.angles = {
            "a": 0, "b": 0, "c": 0, "d": 0
            }
        self.motors = {
            "a": [OutputDevice(14), OutputDevice(15), OutputDevice(18), OutputDevice(23)],
            "b": [OutputDevice(26), OutputDevice(19), OutputDevice(13), OutputDevice(6)],
            "c": [OutputDevice(5), OutputDevice(10), OutputDevice(9), OutputDevice(11)],
            "d": [OutputDevice(1), OutputDevice(2), OutputDevice(3), OutputDevice(4)]
        }

        self.current_step = {"a":0, "b":0, "c":0, "d":0}
        self.split = 512
        self.profile_func = self.default_profile
     
    async def step_motor(self, name, steps, direction=1, speed=8):
        steps = abs(steps)
        seq_len = len(self.step_sequence)

        for _ in range(steps):

            future = self.current_step[name] + direction
            mn, mx = self.motors_limits[name]

            if not (mn <= future <= mx):
                raise ValueError(f"{name} physical limit reached")

            self.current_step[name] = future

            idx = self.current_step[name] % seq_len
            self.set_step(name, self.step_sequence[idx])
            await asyncio.sleep(1 / speed)

        self.set_step(name, [0,0,0,0])
 
    async def profile_step_motor(self, name, steps, direction=1, max_speed=8):
        steps = abs(steps)
        seq_len = len(self.step_sequence)

        for i in range(steps):
            speed = self.profile_func(i, steps, max_speed)

            future = self.current_step[name] + direction
            mn, mx = self.motors_limits[name]

            if not (mn <= future <= mx):
                raise ValueError(f"{name} physical limit reached")

            self.current_step[name] = future


            idx = self.current_step[name] % seq_len
            self.set_step(name, self.step_sequence[idx])
            await asyncio.sleep(1 / speed)

        self.set_step(name, [0,0,0,0])
   
    async def lock_motor(self, names):
        if isinstance(names, str):
            names = [names]
        for n in names:
            idx = self.current_step[n] % len(self.step_sequence)
            self.set_step(n, self.step_sequence[idx])
        await asyncio.sleep(0)
        
    def set_step(self, name, pattern):
        for pin, val in zip(self.motors[name], pattern):
            if val:
                pin.on()
            else:
                pin.off()
            
    def default_profile(self, i, steps, max_speed):
        return max_speed

    def update_angle(self, **angles):
        for name, angle in angles.items():
            self.angles[name] = angle
     
    async def move(self, **relative_angles: int):

        tasks = []

        for name, angle in relative_angles.items():

            steps = int(angle * self.split / 360)
            direction = 1 if steps >= 0 else -1

            task = asyncio.create_task(
                self.profile_step_motor(
                    name,
                    abs(steps),
                    direction
                )
            )
            tasks.append(task)

        await asyncio.gather(*tasks)
  
mana = StepperManager()

if __name__=="__main__":
    try:
        await mana.move(a=90, b=90, c=90, d=90)
        await mana.move(a=45, b=45, c=45, d=45)
