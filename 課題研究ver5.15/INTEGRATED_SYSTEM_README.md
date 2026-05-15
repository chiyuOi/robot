# 統合AI ロボットシステム - 実行ガイド

## システム概要

このシステムは、アルゴリズム図に従う**5段階のパイプライン**で構成されています：

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. 感知 (SENSING)                                               │
│   Pi 5 がウェイクワード → SpeechRecognition STT                 │
│   "ねえロボット！マグカップビで？"                               │
└─────────────────────────────────────────────────────────────────┘
                           ↓ ユーザーテキスト
┌─────────────────────────────────────────────────────────────────┐
│ 2. 計画 (PLANNING) - Groq呼び出し #1                            │
│   ユーザーテキストから適切なツールを選択                          │
│   "USE_TOOL: YOLO, TARGET: blue_mug"                            │
└─────────────────────────────────────────────────────────────────┘
                           ↓ ツール選択
┌─────────────────────────────────────────────────────────────────┐
│ 3. 行動 & 観察 (ACTION & OBSERVATION)                           │
│   ローカルPythonスクリプトが選択したツール（YOLO）を実行          │
│   "Found blue_mug at X:120, Y:450"                              │
│   観測データを返す                                               │
└─────────────────────────────────────────────────────────────────┘
                      ↓ コマンド + 観測結果
┌─────────────────────────────────────────────────────────────────┐
│ 4. 統合 (INTEGRATION) - Groq呼び出し #2                         │
│   観測結果からレスポンスパケットを生成                            │
│   {"speech": "見つけました！左側にあります。",                  │
│    "motor": "point_to(120,450)"}                                │
│   音声テスト + モーターコマンドをまとめる                         │
└─────────────────────────────────────────────────────────────────┘
                    ↓ レスポンスパケット
┌─────────────────────────────────────────────────────────────────┐
│ 5. 実行 (EXECUTION)                                             │
│   ローカルPythonスクリプトが音声 + モーターコマンドを並列実行   │
│   アーム（120, 450）を指す                                       │
│   TTSが音声で応答を読み上げる                                    │
└─────────────────────────────────────────────────────────────────┘
```

## システムの構成要素

### 1. SensingModule（感知モジュール）
- ウェイクワード検出
- ユーザーの音声をテキストに変換
- **パス**: `main/integrated_system.py` - `SensingModule`クラス

### 2. PlanningModule（計画モジュール）
- ユーザー入力を分析
- 最適なツール（YOLO、色追跡、会話など）を選択
- **Groq API呼び出し #1**を使用
- **パス**: `main/integrated_system.py` - `PlanningModule`クラス

### 3. ActionModule（行動モジュール）
- 選択されたツールを実行
- **YOLO**: 物体検出 → 座標取得
- **COLOR_TRACK**: 色追跡
- **MOTION_ONLY**: 動作のみ
- **パス**: `main/integrated_system.py` - `ActionModule`クラス

### 4. IntegrationModule（統合モジュール）
- 観測結果に基づいて応答を生成
- モーターコマンドを作成
- **Groq API呼び出し #2**を使用
- **パス**: `main/integrated_system.py` - `IntegrationModule`クラス

### 5. ExecutionModule（実行モジュール）
- 音声出力とモーターコマンドを並列実行
- **パス**: `main/integrated_system.py` - `ExecutionModule`クラス

## 必要な環境設定

### 1. APIキーの設定
`.env` ファイルに以下を設定してください：

```bash
# Groq API キー（複数設定でローテーション対応）
MY_API_KEY_1=your_groq_api_key_1
MY_API_KEY_2=your_groq_api_key_2  # オプション

# または
GROQ_API_KEY=your_groq_api_key
```

### 2. 必要なPythonパッケージ
```bash
pip install groq ultralytics opencv-python numpy gpiozero python-dotenv
```

### 3. YOLOモデルの配置
```
func/camera/YOLO26n-seg.pt  # セグメンテーションモデル
```

## 実行方法

### シングルパイプライン実行
```bash
python main/integrated_system.py
```

### 連続実行モード
```bash
python main/integrated_system.py --continuous
```

## 使用例

### 例1: 物体検出
```
ユーザー入力: "マグカップを見つけてください"

1. [SENSING] "マグカップを見つけてください" を認識
2. [PLANNING] Groq #1 が "YOLO" ツールを選択、target="マグカップ"
3. [ACTION] YOLO が マグカップを検出 → 座標 (150, 200) を取得
4. [INTEGRATION] Groq #2 が応答生成
   - speech: "マグカップを見つけました。右側にあります。"
   - motor: {"a": 10, "b": -5}
5. [EXECUTION] 音声出力＋モーター制御を並列実行
```

### 例2: 会話のみ
```
ユーザー入力: "こんにちは"

1. [SENSING] "こんにちは" を認識
2. [PLANNING] Groq #1 が "CONVERSATION" ツールを選択
3. [ACTION] 会話準備状態
4. [INTEGRATION] Groq #2 が応答生成
   - speech: "こんにちは！今日はどうしましたか？"
   - motor: []
5. [EXECUTION] 音声出力のみ実行
```

## トラブルシューティング

### APIキーエラー
```
⚠️ API Client Error: .env に MY_API_KEY_1 などのAPIキーが設定されていません。
```
→ `.env` ファイルを確認し、Groq APIキーを設定してください

### カメラが開けない
```
⚠️ Motor control not available
```
→ カメラのアクセス許可を確認してください（特にmacOS）

### YOLOモデルが見つからない
```
⚠️ YOLO model not found at ...
```
→ `func/camera/YOLO26n-seg.pt` が正しく配置されているか確認

### JSONパースエラー
```
⚠️ Failed to parse tool selection
```
→ Groq APIの応答形式を確認し、プロンプトを調整

## パフォーマンス最適化

### 1. モデルの軽量化
- YOLOの推論サイズを調整: `imgsz=320` から `imgsz=256`
- 信頼度閾値を上げる: `conf=0.7`

### 2. 並列処理の最適化
- ExecutionModule で音声とモーター制御を `asyncio.gather()` で並列実行
- 各タスクの完了を待たずに次の処理へ進む

### 3. キャッシング
- 頻繁に使用されるモデルはメモリに保持
- API呼び出しの結果をキャッシュ

## ファイル構成

```
main/
├── integrated_system.py      # 統合システム（メイン）
├── main.py                   # 既存の基本実装
├── brain.py                  # AI決定ロジック
├── ai.py                     # APIクライアントラッパー
└── api_client.py             # APIクライアント

func/
├── camera/
│   ├── camera1.py            # カメラキャプチャ
│   ├── YOLO26n-seg.pt        # YOLOモデル
│   └── yolo-export.py        # YOLO変換
├── motion/
│   └── motor.py              # モーター制御
└── voice-chat/
    ├── speech_controller.py  # 音声制御
    ├── groq-llm.py          # Groq LLM
    ├── groq-whisper-stt.py  # 音声認識
    └── audio_feedback.py    # 音声フィードバック

data/
└── state.py                  # システム状態
```

## 今後の拡張予定

1. **マルチスレッド化**: 複数の観測を並列実行
2. **ローカルモデル統合**: Ollama等のローカルLLMサポート
3. **リアルタイム視覚フィードバック**: カメラストリーミング表示
4. **メモリ管理**: 会話履歴の自動クリーンアップ
5. **エラー回復**: 失敗時の自動リトライ機能

## 参考資料

- Groq API: https://console.groq.com
- YOLO: https://github.com/ultralytics/ultralytics
- asyncio: https://docs.python.org/3/library/asyncio.html
