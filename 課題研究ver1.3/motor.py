from gpiozero import OutputDevice
import asyncio

class Limiter:
    def __init__(self):
        # 1回転 512ステップ想定。物理限界: 64〜448ステップ (中心256)
        self.limits = {k: [64, 448] for k in ["a", "b", "c", "d"]}

    def check_limit(self, name, next_step):
        mn, mx = self.limits[name]
        if not (mn <= next_step <= mx):
            raise ValueError(f"【惨劇】{name}が限界値 {next_step} に到達しました。")

class StepperManager(Limiter):
    def __init__(self):
        super().__init__()
        # 28BYJ-48 等の 1-2相励磁用シーケンス
        self.step_sequence = [
            [1, 1, 0, 0], [0, 1, 0, 0], [0, 1, 1, 0], [0, 0, 1, 0],
            [0, 0, 1, 1], [0, 0, 0, 1], [1, 0, 0, 1], [1, 0, 0, 0]
        ]
        
        # モーター定義 (ピンアサインはそのまま)
        self.motors = {
            "a": [OutputDevice(6), OutputDevice(13), OutputDevice(19), OutputDevice(26)],
            "b": [OutputDevice(12), OutputDevice(16), OutputDevice(20), OutputDevice(21)],
            "c": [OutputDevice(5), OutputDevice(10), OutputDevice(9), OutputDevice(11)],
            "d": [OutputDevice(1), OutputDevice(2), OutputDevice(3), OutputDevice(4)]
        }

        # --- 演算用パラメータ ---
        self.split = 512          # 1回転のステップ数 (ギア比に合わせて要調整)
        self.origin_step = 256    # 0度の基準位置
        self.current_step = {k: 256 for k in self.motors}
        self.angles = {k: 0.0 for k in self.motors}
        self._moving_count = 0

    def get_motion_status(self):
        return 1 if self._moving_count > 0 else 0

    async def move(self, speed=300, **relative_angles: float):
        """相対角度で指定 (例: a=90)"""
        self._moving_count += 1
        tasks = []
        try:
            for name, angle in relative_angles.items():
                if name not in self.motors: continue
                
                # 度数からステップ数へ変換 (四捨五入)
                steps_to_move = round(angle / (360.0 / self.split))
                if steps_to_move == 0: continue
                
                direction = 1 if steps_to_move > 0 else -1
                tasks.append(asyncio.create_task(
                    self._run_motor(name, abs(steps_to_move), direction, speed)
                ))

            if tasks:
                done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_EXCEPTION)
                for t in done:
                    if t.exception():
                        for p in pending: p.cancel()
                        raise t.exception()
            return {"status": "success", "angles": self.angles.copy()}
        finally:
            self._moving_count -= 1

    async def _run_motor(self, name, steps, direction, speed):
        seq_len = len(self.step_sequence)
        try:
            for _ in range(steps):
                next_pos = self.current_step[name] + direction
                
                # リミットチェック (Limiterクラス)
                self.check_limit(name, next_pos)

                # 状態更新
                self.current_step[name] = next_pos
                # 正確な絶対角度を再計算
                self.angles[name] = (self.current_step[name] - self.origin_step) * (360.0 / self.split)
                
                # ハードウェア出力
                pattern = self.step_sequence[self.current_step[name] % seq_len]
                self._set_pins(name, pattern)
                
                await asyncio.sleep(1 / speed)
        finally:
            self._set_pins(name, [0, 0, 0, 0]) # 停止時は通電オフ

    def _set_pins(self, name, pattern):
        for pin, val in zip(self.motors[name], pattern):
            pin.on() if val else pin.off()

async def main():
    mana = StepperManager()
    try:
        print("運命の歯車を回します...")
        # 90度回転
        await mana.move(speed=400, a=90, b=-45)
        print(f"現在の角度: {mana.angles}")
        
        # さらに45度回転 (累積される)
        await mana.move(speed=400, a=45)
        print(f"最終角度: {mana.angles}")

    except Exception as e:
        print(f"エラー発生: {e}")

if __name__ == "__main__":
    asyncio.run(main())
