# 統合AIロボットシステム - アーキテクチャ詳細ガイド

## 目次
1. [システム概要](#システム概要)
2. [5段階パイプラインの詳細](#5段階パイプラインの詳細)
3. [各モジュールの実装詳細](#各モジュールの実装詳細)
4. [データフロー](#データフロー)
5. [マルチタスク処理](#マルチタスク処理)
6. [エラーハンドリング](#エラーハンドリング)
7. [パフォーマンス最適化](#パフォーマンス最適化)
8. [拡張ポイント](#拡張ポイント)

---

## システム概要

このシステムは、写真のアルゴリズムに従う**5段階の人工知能パイプライン**です。

```
[ユーザー] 
    ↓
[1. 感知] → 音声認識 → テキスト化
    ↓
[2. 計画] → Groq #1 → ツール選択
    ↓
[3. 行動] → 選択ツール実行 → 観測データ取得
    ↓
[4. 統合] → Groq #2 → 応答生成
    ↓
[5. 実行] → 音声 + モーター並列実行
    ↓
[ユーザー] ← 応答フィードバック
```

### 主な特徴
- **非同期処理**: `asyncio` で複数タスクを並列実行
- **モジュール設計**: 各段階が独立しており、拡張性が高い
- **エラー復旧**: 各段階のエラーをキャッチして継続
- **マルチ言語対応**: プロンプトをカスタマイズ可能
- **リソース効率**: キャッシングと段階的実行

---

## 5段階パイプラインの詳細

### Stage 1: 感知（SENSING）

**目的**: ユーザー入力の認識と音声テキスト化

```python
class SensingModule:
    def __init__(self):
        self.transcription_file = "/tmp/speech_transcription.txt"
    
    async def wait_for_wakeword(self) -> str:
        # ウェイクワード検出
        # 返り値: ユーザーの音声テキスト
```

**実装の流れ**:
1. マイク入力を受け取る
2. ウェイクワード（"ねえロボット"）を検出
3. その後の音声を認識してテキスト化
4. テキストを `/tmp/speech_transcription.txt` に保存

**関連ファイル**:
- `func/voice-chat/groq-whisper-stt.py` - 音声認識エンジン
- `func/voice-chat/speech_controller.py` - 音声制御

**出力例**:
```
"マグカップを探してください"
"右に10度動いてください"
```

---

### Stage 2: 計画（PLANNING）

**目的**: ユーザー入力から最適なツールを選択

```python
class PlanningModule:
    def select_tool(self, user_input: str) -> Dict[str, Any]:
        # Groq API #1 を呼び出し
        # 返り値: {tool, target, reasoning}
```

**実装の流れ**:
1. ユーザーのテキストをGroqへ送信
2. プロンプト: 「利用可能なツール: YOLO, COLOR_TRACK, ...」
3. Groqが最適なツールを選択
4. JSON形式で結果を返す

**利用可能なツール**:

| ツール | 用途 | 返り値 |
|--------|------|--------|
| YOLO | 物体検出 | 座標（X, Y）+ ラベル |
| COLOR_TRACK | 色追跡 | 追跡座標 |
| MOTION_ONLY | 単純な動作 | なし |
| CONVERSATION | 会話のみ | なし |

**Groq プロンプト例**:
```
あなたはロボットの意思決定AIです。
ユーザーの質問に対して、以下のツールから最も適切なものを選択してください。

利用可能なツール:
- "YOLO": 物体検出を実行
- "COLOR_TRACK": 特定の色を追跡します
- "MOTION_ONLY": 単純な動作コマンド
- "CONVERSATION": 会話のみで応答

JSON形式で以下を返してください:
{
    "tool": "YOLO" | "COLOR_TRACK" | "MOTION_ONLY" | "CONVERSATION",
    "target": "検出対象（例：blue_mug）",
    "reasoning": "選択理由"
}
```

**出力例**:
```json
{
    "tool": "YOLO",
    "target": "blue_mug",
    "reasoning": "物体検出が必要な質問のため"
}
```

---

### Stage 3: 行動 & 観察（ACTION & OBSERVATION）

**目的**: 選択されたツールを実行し、観測データを取得

```python
class ActionModule:
    async def execute(self, tool_config: Dict) -> Dict[str, Any]:
        # 選択されたツールを実行
        # 返り値: {status, action, detections, ...}
```

**ツール実装の詳細**:

#### 3.1 YOLO物体検出

```python
async def _execute_yolo(self, config: Dict) -> Dict:
    # 1. カメラからフレーム取得
    cap = cv2.VideoCapture(0)
    ret, frame = cap.read()
    
    # 2. YOLO推論実行
    results = self.yolo_model(frame, imgsz=320, conf=0.5)
    
    # 3. 検出結果を処理
    detections = []
    for result in results:
        for box in result.boxes:
            # 座標、ラベル、信頼度を抽出
            detections.append({
                "label": label,
                "x": cx,
                "y": cy,
                "confidence": conf
            })
    
    # 4. ターゲットに合致する検出を返す
    return {
        "status": "success",
        "action": "object_detected",
        "detections": detections,
        "primary": detections[0]  # 最高信頼度の検出
    }
```

**出力例**:
```json
{
    "status": "success",
    "action": "object_detected",
    "primary": {
        "label": "blue_mug",
        "x": 320,
        "y": 240,
        "confidence": 0.92
    }
}
```

#### 3.2 COLOR_TRACK色追跡

```python
async def _execute_color_track(self, config: Dict) -> Dict:
    # HSV色空間で色追跡
    # 返り値: {status, action, coordinates}
```

#### 3.3 MOTION_ONLY単純動作

```python
# 単に準備状態を返す
return {"action": "motion_ready", "details": "Ready for motion commands"}
```

---

### Stage 4: 統合（INTEGRATION）

**目的**: 観測結果に基づいて応答とモーターコマンドを生成

```python
class IntegrationModule:
    def generate_response(self, observation: Dict, user_input: str) -> Dict:
        # Groq API #2 を呼び出し
        # 返り値: {speech, motor_commands, status}
```

**実装の流れ**:
1. 観測結果をテキストに変換
2. ユーザー入力と観測結果をGroqへ送信
3. 音声応答を生成
4. モーターコマンドを生成

**Groq プロンプト例**:
```
あなたはロボットの統合制御AIです。
観測結果に基づいて、適切な応答とモーターコマンドを生成してください。

ユーザー: マグカップを探してください

観測結果:
{
    "status": "success",
    "action": "object_detected",
    "primary": {
        "label": "blue_mug",
        "x": 320,
        "y": 240,
        "confidence": 0.92
    }
}

JSON形式で以下を返してください:
{
    "speech": "ユーザーへの音声応答",
    "motor_commands": [
        {"axis": "a", "angle": 10},
        {"axis": "b", "angle": -5}
    ],
    "status": "success"
}
```

**出力例**:
```json
{
    "speech": "見つけました！左側にあります。",
    "motor_commands": [
        {"axis": "a", "angle": 15},
        {"axis": "b", "angle": -10}
    ],
    "status": "success"
}
```

**座標変換（例）**:
- 画像座標 (320, 240) から モーター角度 (a=15, b=-10) への変換
- キャリブレーション情報が必要

---

### Stage 5: 実行（EXECUTION）

**目的**: 音声出力とモーターコマンドを並列実行

```python
class ExecutionModule:
    async def execute_response(self, response: Dict) -> None:
        # 音声とモーターを asyncio.gather() で並列実行
```

**実装の流れ**:
```python
async def execute_response(self, response: Dict) -> None:
    tasks = []
    
    # Task 1: 音声出力
    tasks.append(self._play_speech(response["speech"]))
    
    # Task 2: モーター制御
    tasks.append(self._execute_motors(response["motor_commands"]))
    
    # 並列実行
    results = await asyncio.gather(*tasks, return_exceptions=True)
```

**実行タイムライン**:
```
時刻(ms)  | 音声タスク         | モータータスク
0-1000   | [音声再生中....]  | [モーター1動作中....]
         | (TTS処理)       | (ステッパー励磁)
1000+    | [完了]          | [完了]
```

---

## 各モジュールの実装詳細

### SensingModule の詳細

```python
class SensingModule:
    def __init__(self):
        self.transcription_file = "/tmp/speech_transcription.txt"
        self.wake_word = "ねえロボット"
    
    async def wait_for_wakeword(self) -> Optional[str]:
        """ウェイクワード待機"""
        print("🎤 Waiting for wake word...")
        
        # 実装パターン1: ローカル音声認識
        # SpeechRecognition ライブラリを使用
        
        # 実装パターン2: Groq Whisper
        # groq-whisper-stt.py をサブプロセスで実行
        
        # テスト実装: ユーザー入力
        user_input = input("🎙️ Say something: ").strip()
        
        with open(self.transcription_file, "w") as f:
            f.write(user_input)
        
        return user_input
```

### ActionModule の詳細

```python
class ActionModule:
    def __init__(self):
        self.yolo_model = None
        self.lock = threading.Lock()
        self._load_yolo_model()
    
    def _load_yolo_model(self):
        """YOLO モデル読み込み"""
        try:
            model_path = "func/camera/YOLO26n-seg.pt"
            self.yolo_model = YOLO(str(model_path))
            print("✅ YOLO model loaded")
        except Exception as e:
            print(f"⚠️  Failed to load YOLO: {e}")
```

---

## データフロー

### ユースケース1: 物体検出

```
ユーザー: "青いカップを見つけてください"
    ↓
[SENSING] → "青いカップを見つけてください"
    ↓
[PLANNING] → Groq #1
    → "この質問は物体検出が必要"
    → {tool: "YOLO", target: "blue_cup"}
    ↓
[ACTION] → カメラ + YOLO実行
    → 画像処理: 320×640フレーム
    → YOLO推論: 物体検出
    → 結果: {label: "cup", x: 150, y: 200, conf: 0.92}
    ↓
[INTEGRATION] → Groq #2
    → 観測結果を入力
    → "見つけました！左側にあります。"
    → モーターコマンド: {a: 10, b: -5}
    ↓
[EXECUTION] → 並列実行
    → 音声: "見つけました！..."
    → モーター: a軸10度、b軸-5度回転
    ↓
完了 ✓
```

### ユースケース2: 会話のみ

```
ユーザー: "こんにちは"
    ↓
[SENSING] → "こんにちは"
    ↓
[PLANNING] → Groq #1
    → "会話のみが必要"
    → {tool: "CONVERSATION"}
    ↓
[ACTION] → 特に処理なし
    ↓
[INTEGRATION] → Groq #2
    → "こんにちは！今日はどうしましたか？"
    → モーターコマンド: []
    ↓
[EXECUTION] → 音声のみ実行
    ↓
完了 ✓
```

---

## マルチタスク処理

### asyncio を使用した並列実行

```python
# 例1: 複数の非同期タスクを並列実行
tasks = [
    self._play_speech(speech),
    self._execute_motors(commands)
]

results = await asyncio.gather(*tasks, return_exceptions=True)
```

### スレッドセーフな共有リソース

```python
class ActionModule:
    def __init__(self):
        self.lock = threading.Lock()
        self.latest_results = []
    
    def update_results(self, results):
        with self.lock:
            self.latest_results = results
```

---

## エラーハンドリング

### 各段階でのエラー処理

```python
# Stage 2: Planning エラー
try:
    response = self.ai.send(user_input)
    tool_config = json.loads(response)
except json.JSONDecodeError:
    print("⚠️  Failed to parse response")
    tool_config = {"tool": "CONVERSATION"}  # フォールバック

# Stage 3: Action エラー
try:
    results = self.yolo_model(frame, ...)
except Exception as e:
    return {"status": "error", "message": str(e)}

# Stage 4: Integration エラー
try:
    response = self.ai.send(context)
except Exception as e:
    return {
        "speech": "申し訳ありません。エラーが発生しました。",
        "motor_commands": [],
        "status": "error"
    }
```

### リトライロジック

```python
MAX_RETRIES = 3
for attempt in range(MAX_RETRIES):
    try:
        result = await action.execute(config)
        break
    except Exception as e:
        if attempt < MAX_RETRIES - 1:
            await asyncio.sleep(1)  # 1秒待機
            continue
        else:
            raise
```

---

## パフォーマンス最適化

### 1. モデルキャッシング

```python
class ActionModule:
    def __init__(self):
        # メモリにモデルをロード
        self.yolo_model = YOLO("YOLO26n-seg.pt")
        # 再度ロードしない → メモリ効率向上
```

### 2. 推論サイズの最適化

```python
# デフォルト: imgsz=640 (遅い)
# 最適化: imgsz=320 (速い)
results = self.yolo_model(frame, imgsz=320, conf=0.5)
```

### 3. 信頼度閾値の調整

```python
# 信頼度低: conf=0.3 (検出多いが誤検出も多い)
# 信頼度中: conf=0.5 (バランス取れた)
# 信頼度高: conf=0.7 (精度重視)
results = self.yolo_model(frame, conf=0.5)
```

### 4. 非同期処理

```python
# 音声とモーターを同時実行
await asyncio.gather(
    self._play_speech(text),
    self._execute_motors(commands)
)
# 逐次実行より高速
```

---

## 拡張ポイント

### 新しいツールの追加

```python
# ActionModule に新しいツール追加
async def execute(self, tool_config: Dict) -> Dict:
    tool = tool_config.get("tool")
    
    if tool == "YOLO":
        return await self._execute_yolo(tool_config)
    elif tool == "COLOR_TRACK":
        return await self._execute_color_track(tool_config)
    elif tool == "NEW_TOOL":  # 新しいツール
        return await self._execute_new_tool(tool_config)
    
    # 新しいツール実装
    async def _execute_new_tool(self, config):
        # 実装
        pass
```

### 新しいLLMの統合

```python
# Ollama, Claude, GPT などの別LLMを統合
class PlanningModule:
    def __init__(self, api_client):
        self.ai = Ai(
            api_client=api_client,
            # 別のエンドポイント、モデルを指定
            api_url="http://localhost:11434/v1/chat/completions",
            model="llama2",
            temperature=0.5
        )
```

### カスタムプロンプトの実装

```python
CUSTOM_PLANNING_PROMPT = """
カスタマイズされたプロンプト
...
"""

planning = PlanningModule(api_client)
planning.ai.prompt = CUSTOM_PLANNING_PROMPT
```

---

## デバッグとロギング

### ログ出力例

```
2024-01-15 14:30:45 [INFO] Starting integrated system...
2024-01-15 14:30:46 [INFO] STAGE 1: SENSING
2024-01-15 14:30:48 [INFO]   User input: "マグカップを探してください"
2024-01-15 14:30:49 [INFO] STAGE 2: PLANNING
2024-01-15 14:30:50 [DEBUG]   Groq #1 response: {tool: YOLO, target: blue_cup}
2024-01-15 14:30:51 [INFO] STAGE 3: ACTION
2024-01-15 14:30:52 [DEBUG]   YOLO inference time: 234ms
2024-01-15 14:30:52 [DEBUG]   Detected 3 objects
2024-01-15 14:30:53 [INFO] STAGE 4: INTEGRATION
2024-01-15 14:30:54 [DEBUG]   Groq #2 response generated
2024-01-15 14:30:54 [INFO] STAGE 5: EXECUTION
2024-01-15 14:30:55 [DEBUG]   Speech started
2024-01-15 14:30:55 [DEBUG]   Motors started
2024-01-15 14:30:58 [INFO]   Execution completed
```

---

## まとめ

このアーキテクチャは、複雑なAIロボットシステムを5つの明確なステップに分解し、各段階を独立して実装・テスト・拡張できる設計になっています。

**主な利点**:
- ✅ モジュール性：各段階が独立
- ✅ 拡張性：新しいツールやLLMを追加可能
- ✅ テスト性：各段階を個別にテスト可能
- ✅ 効率性：非同期処理で並列実行
- ✅ 堅牢性：エラーハンドリングとフォールバック

**今後の改善案**:
- マルチスレッド化で複数リクエスト同時処理
- キャッシング機構の強化
- リアルタイムビデオフィード表示
- メモリ管理の最適化
- メトリクス収集とモニタリング
