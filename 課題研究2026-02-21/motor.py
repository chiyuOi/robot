from gpiozero import OutputDevice
import asyncio


class Limiter:
    def __init__(self):
        # 512の1/8〜7/8の範囲。つまり 64 〜 448 が限界値
        self.motors_limits = {
            k: [(512 // 8) * 1, (512 // 8) * 7] for k in ["a", "b", "c", "d"]
        }

    async def global_limiter(self, name):
        mn, mx = self.motors_limits[name]
        angle = self.current_step[name]
        if not (mn <= angle <= mx):
            raise ValueError(f"{name} limit over: {angle}")

    def limiter_warning(self, name):
        zone = 8
        mn, mx = self.motors_limits[name]
        angle = self.current_step[name]
        if not (mn + zone <= angle):
            return "small"
        if not (angle <= mx - zone):
            return "big"
        return "safe"


class StepperManager(Limiter):
    def __init__(self):
        super().__init__()
        print("run StepperManager")
        self.step_sequence = [
            [1, 1, 0, 0], [0, 1, 0, 0],
            [0, 1, 1, 0], [0, 0, 1, 0],
            [0, 0, 1, 1], [0, 0, 0, 1],
            [1, 0, 0, 1], [1, 0, 0, 0]
        ]

        self.angles = {"a": 0, "b": 0, "c": 0, "d": 0}

        self.motors = {
            "a": [OutputDevice(14), OutputDevice(15), OutputDevice(18), OutputDevice(23)],
            "b": [OutputDevice(26), OutputDevice(19), OutputDevice(13), OutputDevice(6)],
            "c": [OutputDevice(5), OutputDevice(10), OutputDevice(9), OutputDevice(11)],
            "d": [OutputDevice(1), OutputDevice(2), OutputDevice(3), OutputDevice(4)]
        }

        # 初期値が0だと limits(64~448) を最初から外れてしまうため、中央値(256)に修正
        self.current_step = {"a": 256, "b": 256, "c": 256, "d": 256}
        self.split = 512
        self.profile_func = self.default_profile
        self._moving_count = 0

    def get_motion_status(self):
        if self._moving_count > 0:
            return 1
        else:
            return 0

    async def move(self, speed=300, **relative_angles: int):
        # ▼ 追加: 動く直前にカウントを増やす
        self._moving_count += 1

        try:
            tasks = []
            for name, angle in relative_angles.items():
                if name not in self.motors:
                    continue
                steps = int(angle * self.split / 360)
                direction = 1 if steps >= 0 else -1
                task = asyncio.create_task(
                    self.profile_step_motor(name, abs(steps), direction, max_speed=speed)
                )
                tasks.append(task)

            status = "success"
            error_msg = None

            if tasks:
                done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_EXCEPTION)
                for task in done:
                    exc = task.exception()
                    if exc:
                        status = "limit_error"
                        error_msg = str(exc)
                        break

                if pending:
                    for task in pending:
                        task.cancel()
                    await asyncio.gather(*pending, return_exceptions=True)

            return {
                "status": status,
                "error": error_msg,
                "angles": self.angles.copy(),
                "current_step": self.current_step.copy()
            }

        finally:
            # ▼ 追加: 動き終わった（またはエラーで止まった）ら確実にカウントを減らす
            self._moving_count -= 1

    async def profile_step_motor(self, name, steps, direction=1, max_speed=300):
        steps = abs(steps)
        seq_len = len(self.step_sequence)

        try:
            for i in range(steps):
                speed = self.profile_func(i, steps, max_speed)
                # ゼロ除算を避けるための安全策
                if speed <= 0:
                    speed = 0.1

                future = self.current_step[name] + direction
                mn, mx = self.motors_limits[name]

                if not (mn <= future <= mx):
                    raise ValueError(f"[{name} モーター] 物理リミットに到達しました (step: {future})")

                self.current_step[name] = future
                idx = self.current_step[name] % seq_len
                self.set_step(name, self.step_sequence[idx])

                # 現在のステップ数に合わせて角度（angles）も同期更新する
                self.angles[name] = (self.current_step[name] - 256) * 360 / self.split

                await asyncio.sleep(1 / speed)

        finally:
            # タスクがキャンセルされたりエラー終了した場合でも必ず通電を切る（発熱防止）
            self.set_step(name, [0, 0, 0, 0])

    def set_step(self, name, pattern):
        for pin, val in zip(self.motors[name], pattern):
            if val:
                pin.on()
            else:
                pin.off()

    def default_profile(self, i, steps, max_speed):
        return max_speed

    async def move(self, speed=300, **relative_angles: int):
        tasks = []
        for name, angle in relative_angles.items():
            if name not in self.motors:
                continue

            steps = int(angle * self.split / 360)
            direction = 1 if steps >= 0 else -1

            task = asyncio.create_task(
                self.profile_step_motor(name, abs(steps), direction, max_speed=speed)
            )
            tasks.append(task)

        if tasks:
            # 全タスクを待機するが、どれか1つでもエラーが起きたら即座に return する
            done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_EXCEPTION)

            # エラーで中断された場合、まだ動いている他のモーターのタスクをキャンセルして停止させる
            if pending:
                for task in pending:
                    task.cancel()
                # キャンセル処理が終わるまで待機
                await asyncio.gather(*pending, return_exceptions=True)

            # 発生したエラーがあれば再送出（mainへ伝える）
            for task in done:
                exc = task.exception()
                if exc:
                    raise exc


async def main():
    mana = StepperManager()
    sender_task = asyncio.crate_task(mana.status_sender_loopp())
    try:
        # speed を引数で指定可能に（数字が大きいほど速い）
        print("90度移動中...")
        await mana.move(speed=500, a=90, b=90, c=90, d=90)

        print("さらに45度移動中...")
        await mana.move(speed=500, a=45, b=45, c=45, d=45)

        # 限界値確認テスト（ここで a=2 などとすると 135度を超えてエラーになるはずです）
        # await mana.move(speed=500, a=2)

        print("完了しました。")

    except ValueError as ve:
        print(f"安全装置が作動しました: {ve}")
    except Exception as e:
        print(f"エラーが発生しました: {e}")
    finally:
        # プログラム終了時に確実に全モーターの通電を切る（二重の安全策）
        for name in mana.motors:
            mana.set_step(name, [0, 0, 0, 0])


if __name__ == "__main__":
    asyncio.run(main())
