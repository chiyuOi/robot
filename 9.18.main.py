import sys
import json
import queue
import threading
import asyncio
import os
import cv2
import pyaudio
import RPi.GPIO as GPIO
from vosk import Model, KaldiRecognizer
from google import genai
from PIL import Image
from groq import Groq

# ==========================================
# 1. モーター制御クラス・モーション定義
# ==========================================
HALF_STEP = [
    [1,0,0,0], [1,1,0,0], [0,1,0,0], [0,1,1,0],
    [0,0,1,0], [0,0,1,1], [0,0,0,1], [1,0,0,1]
]

class StepperMotor:
    def __init__(self, pins, reverse=False):
        self.pins = pins
        self.reverse = reverse
        self.step_index = 0
        
        GPIO.setmode(GPIO.BCM)
        for pin in self.pins:
            GPIO.setup(pin, GPIO.OUT)
            GPIO.output(pin, 0)

    def step(self, direction):
        actual_dir = -direction if self.reverse else direction
        self.step_index = (self.step_index + actual_dir) % 8
        for i in range(4):
            GPIO.output(self.pins[i], HALF_STEP[self.step_index][i])

class Joint:
    def __init__(self, motors):
        self.motors = motors
        self.current_pos = 0

    async def move_to(self, target_pos, speed):
        distance = target_pos - self.current_pos
        direction = 1 if distance > 0 else -1
        delay = 1.0 / speed if speed > 0 else 0.01
        for _ in range(abs(distance)):
            for motor in self.motors:
                motor.step(direction)
            self.current_pos += direction
            await asyncio.sleep(delay)

async def run_sequence(joints, sequence):
    for step_num, step_data in enumerate(sequence):
        print(f"--- 動作ステップ {step_num} ---")
        tasks = [
            joints[0].move_to(target_pos=step_data[0][0], speed=step_data[0][1]),
            joints[1].move_to(target_pos=step_data[1][0], speed=step_data[1][1]),
            joints[2].move_to(target_pos=step_data[2][0], speed=step_data[2][1])
        ]
        await asyncio.gather(*tasks)

# 事前定義モーションテーブル
MOTIONS = {
    "forward": [ [[512, 300], [-512, 300], [512, 200]] ],
    "backward": [ [[-512, 300], [512, 300], [-512, 200]] ],
    "nod": [
        [[0, 300], [-256, 300], [256, 200]],
        [[0, 300], [0, 300], [0, 200]]
    ],
    "look_around": [
        [[256, 300], [0, 300], [256, 200]],
        [[-256, 300], [0, 300], [-256, 200]],
        [[0, 300], [0, 300], [0, 200]]
    ]
}

# ==========================================
# 2. AIクライアント & 視覚解析関数
# ==========================================
groq_client = Groq(api_key=os.environ.get("GROQ_API_KEY", "YOUR_GROQ_API_KEY"))
gemini_client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY", "YOUR_GEMINI_API_KEY"))

def capture_and_analyze_with_gemini(prompt: str) -> str:
    """カメラで撮影しGemini APIで解析"""
    cap = cv2.VideoCapture(0)
    ret, frame = cap.read()
    cap.release()

    if not ret:
        return "カメラからの画像取得に失敗しました。"

    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    pil_img = Image.fromarray(rgb_frame)

    response = gemini_client.models.generate_content(
        model='gemini-2.0-flash',
        contents=[pil_img, prompt]
    )
    return response.text

# Groq Tool Calling 定義
tools = [
    {
        "type": "function",
        "function": {
            "name": "analyze_vision",
            "description": "周囲の状況や目の前の物体・人物の視覚情報が必要な場合にカメラ画像を解析する。",
            "parameters": {
                "type": "object",
                "properties": {
                    "prompt": {
                        "type": "string",
                        "description": "画像に対して確認・分析したいプロンプト"
                    }
                },
                "required": ["prompt"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "execute_motion",
            "description": "ロボットのアーム動作を実行する。",
            "parameters": {
                "type": "object",
                "properties": {
                    "motion_name": {
                        "type": "string",
                        "enum": list(MOTIONS.keys()),
                        "description": "実行するモーション名"
                    }
                },
                "required": ["motion_name"]
            }
        }
    }
]

async def process_user_command(user_text: str, joints):
    """GroqによるルーティングとTool Calling処理"""
    messages = [
        {
            "role": "system",
            "content": (
                "あなたはデスクライト型のコミュニケーションロボットです。"
                "必要に応じて『analyze_vision』で視覚情報を確認し、『execute_motion』でモーションを実行してください。"
                "利用可能なモーション: " + ", ".join(MOTIONS.keys())
            )
        },
        {"role": "user", "content": user_text}
    ]

    try:
        response = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            tools=tools,
            tool_choice="auto"
        )

        response_message = response.choices[0].message
        tool_calls = response_message.tool_calls

        if tool_calls:
            messages.append(response_message)

            for tool_call in tool_calls:
                func_name = tool_call.function.name
                args = json.loads(tool_call.function.arguments)

                if func_name == "analyze_vision":
                    print(f"\n👀 [視覚要求] Prompt: {args['prompt']}")
                    vision_result = capture_and_analyze_with_gemini(args['prompt'])
                    print(f"📷 [Gemini解析結果] {vision_result}")

                    messages.append({
                        "tool_call_id": tool_call.id,
                        "role": "tool",
                        "name": func_name,
                        "content": vision_result
                    })

                elif func_name == "execute_motion":
                    motion_name = args['motion_name']
                    print(f"\n🤖 [モーション実行] {motion_name}")
                    if motion_name in MOTIONS:
                        await run_sequence(joints, MOTIONS[motion_name])

            # Geminiの視覚結果等を含めて最終応答を生成
            second_response = groq_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=messages
            )
            final_text = second_response.choices[0].message.content
            print(f"🤖 [応答] {final_text}")
        else:
            print(f"🤖 [応答] {response_message.content}")

    except Exception as e:
        print(f"エラーが発生しました: {e}")

# ==========================================
# 3. 音声認識 Worker & メイン処理
# ==========================================
FORMAT = pyaudio.paInt16
CHANNELS = 1
CHUNK = 1024

audio_queue = queue.Queue()
command_queue = None
main_loop = None

def audio_callback(in_data, frame_count, time_info, status):
    audio_queue.put(in_data)
    return (None, pyaudio.paContinue)

def speech_recognition_worker(recognizer):
    while True:
        data = audio_queue.get()
        if data is None:
            break
            
        if recognizer.AcceptWaveform(data):
            result_json = recognizer.Result()
            result_dict = json.loads(result_json)
            text = result_dict.get("text", "").replace(" ", "")
            
            if text:
                print(f"\r\033[K[確定] {text}")
                if command_queue is not None and main_loop is not None:
                    main_loop.call_soon_threadsafe(command_queue.put_nowait, text)
        else:
            partial_json = recognizer.PartialResult()
            partial_dict = json.loads(partial_json)
            partial_text = partial_dict.get("partial", "").replace(" ", "")
            if partial_text:
                print(f"\r\033[K (途中) {partial_text}", end="", flush=True)

async def main():
    global command_queue, main_loop
    main_loop = asyncio.get_running_loop()
    command_queue = asyncio.Queue()

    print("Voskの日本語モデルを準備しています...")
    try:
        model = Model(lang="ja")
    except Exception as e:
        print(f"モデルの読み込みに失敗しました: {e}")
        return

    p = pyaudio.PyAudio()
    try:
        RATE = int(p.get_default_input_device_info()['defaultSampleRate'])
    except Exception:
        RATE = 44100

    recognizer = KaldiRecognizer(model, RATE)

    rec_thread = threading.Thread(target=speech_recognition_worker, args=(recognizer,), daemon=True)
    rec_thread.start()

    try:
        stream = p.open(
            format=FORMAT,
            channels=CHANNELS,
            rate=RATE,
            input=True,
            frames_per_buffer=CHUNK,
            stream_callback=audio_callback
        )
    except Exception as e:
        print(f"マイクの初期化に失敗しました: {e}")
        p.terminate()
        return

    try:
        # モーター・ピン設定（既存構成を変更なし）
        pins_m1a = [6, 13, 19, 26]
        pins_m1b = [12, 16, 20, 21]
        pins_m2  = [4, 17, 27, 22]
        pins_m3  = [23, 24, 25, 8]

        m1a = StepperMotor(pins_m1a, reverse=False)
        m1b = StepperMotor(pins_m1b, reverse=True) 
        m2  = StepperMotor(pins_m2, reverse=False)
        m3  = StepperMotor(pins_m3, reverse=False)

        joints = [Joint([m1a, m1b]), Joint([m2]), Joint([m3])]

        print("=" * 45)
        print("🤖 システム起動完了 (Vosk + Groq Tool Calling + Gemini)")
        print("=" * 45)

        stream.start_stream()

        while True:
            command_text = await command_queue.get()

            if "終了" in command_text or "ストップ" in command_text:
                print("\n⏹ 終了コマンドを検知しました。")
                break

            # AIエージェントに判定とモーション実行を委譲
            await process_user_command(command_text, joints)

    finally:
        stream.stop_stream()
        stream.close()
        p.terminate()
        audio_queue.put(None)
        GPIO.cleanup()

if __name__ == "__main__":
    GPIO.setwarnings(False)
    asyncio.run(main())