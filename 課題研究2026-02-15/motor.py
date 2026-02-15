from __future__ import annotations
from gpiozero import OutputDevice
import asyncio

# =========================================================
# モータ
# =========================================================
class StepperSystem:
    @staticmethod
    def default_profile(i, steps, max_speed):
        t = i / steps
        acc = 0.4
        ease = 2.0

        if t < acc:
            r = (t / acc) ** ease
        elif t > 1 - acc:
            r = ((1 - t) / acc) ** ease
        else:
            r = 1.0
        return max_speed * max(r, 0.01)

    def __init__(self):
        print("run StepperSystem")
        self.step_sequence = [
            [1,1,0,0],[0,1,0,0],
            [0,1,1,0],[0,0,1,0],
            [0,0,1,1],[0,0,0,1],
            [1,0,0,1],[1,0,0,0]
        ]

        self.motors = {
            "a": [OutputDevice(14), OutputDevice(15), OutputDevice(18), OutputDevice(23)],
            "b": [OutputDevice(26), OutputDevice(19), OutputDevice(13), OutputDevice(6)],
            "c": [OutputDevice(5), OutputDevice(10), OutputDevice(9), OutputDevice(11)]
        }

        self.current_step = {"a":0, "b":0, "c":0}
        self.split = 512
        self.profile_func = self.default_profile

    def set_step(self, name, seq):
        for pin, val in zip(self.motors[name], seq):
            pin.value = val

    async def step_motor(self, name, steps, direction=1, speed=8):
        steps = abs(steps)
        seq_len = len(self.step_sequence)

        for _ in range(steps):
            self.current_step[name] = (self.current_step[name] + direction) % self.split
            idx = self.current_step[name] % seq_len
            self.set_step(name, self.step_sequence[idx])
            await asyncio.sleep(1 / speed)

        self.set_step(name, [0,0,0,0])

    async def step_target(self, name, target, speed=8):
        diff = target - self.current_step[name]
        if diff == 0:
            return
        await self.step_motor(name, abs(diff), 1 if diff > 0 else -1, speed)

    async def profile_step_motor(self, name, steps, direction=1, max_speed=8):
        steps = abs(steps)
        seq_len = len(self.step_sequence)

        for i in range(steps):
            speed = self.profile_func(i, steps, max_speed)
            self.current_step[name] = (self.current_step[name] + direction) % self.split
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

    async def unhold_motor(self, names):
        if isinstance(names, str):
            names = [names]
        for n in names:
            self.set_step(n, [0,0,0,0])
        await asyncio.sleep(0)

# =========================================================
# リミッタ
# =========================================================
class Limiter:
    def __init__(self):
        print("run Limiter")
        self.motors_limits = {
            k: [(512//8)*1, (512//8)*7] for k in ["a","b","c"]
        }

    async def global_limiter(self, name):
        mn, mx = self.motors_limits[name]
        angle = self.current_step[name]
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

    async def safe_motion(self, motion):
        limit_tasks = [
            asyncio.create_task(self.limit_watch("a")),
            asyncio.create_task(self.limit_watch("b")),
            asyncio.create_task(self.limit_watch("c"))
        ]

        try:
            motion_task = asyncio.create_task(motion())
            done, pending = await asyncio.wait(
                limit_tasks + [motion_task],
                return_when=asyncio.FIRST_EXCEPTION
            )

            for t in pending:
                t.cancel()
            return True

        except asyncio.CancelledError:
            return False
            pass

# =========================================================
# モーション
# =========================================================
class Motion:
    async def a_step_motor(self, names, steps, directions, speeds):
        if not isinstance(names, list):
            names, steps, directions, speeds = [names], [steps], [directions], [speeds]

        tasks = []
        for n,s,d,sp in zip(names,steps,directions,speeds):
            tasks.append(self.step_motor(n,s,d,sp))
        await asyncio.gather(*tasks)

    async def test(self, cmd):
        await self.unhold_motor("a")
        await self.step_motor("a", 200, 1, 300)
        await self.step_motor("a", 200, -1, 300)
        await self.lock_motor("a")

    async def tracking(self, cmd):
        x, y = cmd["tip"]

        W, H = 640, 480
        cx = x - W / 2
        cy = H / 2 - y

        dead_zone = 20
        if abs(cx) < dead_zone and abs(cy) < dead_zone:
            return

        gain = 0.5
        base_speed = 300

        target_a = int(self.split / 2 + cx * gain)
        target_b = int(self.split / 2 + cy * gain)

        warn_a = await self.limiter_warning("a")
        warn_b = await self.limiter_warning("b")

        def speed_from_warn(w):
            if w == "safe":
                return base_speed
            else:
                return int(base_speed * 0.3)  # 端はゆっくり

        speed_a = speed_from_warn(warn_a)
        speed_b = speed_from_warn(warn_b)

        await self.a_step_motor(
            names=["a", "b"],
            steps=[
                target_a - self.current_step["a"],
                target_b - self.current_step["b"]
            ],
            directions=[
                1 if target_a > self.current_step["a"] else -1,
                1 if target_b > self.current_step["b"] else -1
            ],
            speeds=[speed_a, speed_b]
        )

    async def idle(self, cmd):
        return