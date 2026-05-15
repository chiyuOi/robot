# コミュニケーションロボットの開発　
# 〜拡張現実を使用したロボットアシスタント〜
<img width="528" height="396" alt="image" src="https://github.com/user-attachments/assets/3f92402a-71e8-470b-b3a1-1302de989527" />

# やることリスト
- ❌ファン印刷
- ❌12Vモバイルバッテリー
- ✅リアルタイム画像認識 : *YOLO26n-seg*
- ✅画像デスクリプション生成LLM : *Groq llama-4-scout*
- ✅文字起こし : *Groq Whisper-large-v3-turbo*
- ✅文字読み上げ : *Qwen TTS または Mistral TTS*
- ✅3D外形モデリング
- ❌機能管理（全体のフレームワーク、アルゴリズム）: *Threading　と async*
- ✅モータプログラム生成
- ✅文字読み上げテキスト生成AI
- ✅ボイスチャット
- ✅音楽再生
- ❌(Google検索)
- ❌ローカルでの運用 : *Gemma4, LiteRT-LM*
- ✅画像生成の速度向上
- ✅プロジェクトシステム（画像生成）の作成
- デスクの上に指差して、ライオンの画像生成してって言ったらそこに投影される。
- 解説書投影された後、わからないところ指さして、「ここわからない」って言ったらさらに解説してくれる
  
# ダイアグラム

<img width="586" height="634" alt="image" src="https://github.com/user-attachments/assets/6ed4437a-877b-4bca-850b-7009fecd38ae" />


LLMの使用用途の例：
{コマンド理解}トラッキングの機能があるとする。「トラッキングして」「指追跡して」などいろんな言い方があるから、最終的にトラッキングしてほしいことをロボットが理解するために、LLMに判断させて、動かすべき機能が何かしっかり理解できるようにする。
他の例として。画像認識を使った例だと、「このペンはどこっていうと」LLMがユーザがものを探していると判断する。→周りを物理的に360度回転してスキャンして、画像認識モデルを動かして対象物を認識させる。→ここにあるよって、いう。
LLMの使用はここでは、あくまでユーザのコマンド理解。下のように、自分からプログラムを作る場合もあるが、プログラム生成には時間がかかるので、このように必要な時にだけ使うことで、なるべく自然な交流を目指す。
{モータプログラム出力}まず最初に、インストラクションで、ロボットの説明書のPDFを打ち込む。それによって、例えば、「バイバイして」と言ったら、ロボットハンドが手を振る操作をぶち込んだPDFをもとにプログラムを生成する。


以下に、課題研究ver5.9 のすべてのフォルダとファイルの役割を説明します。

📁 課題研究ver5.9 — ディレクトリ構成と役割
Code
課題研究ver5.9/
├── test.py
├── data/
│   ├── state.py
│   ├── config.json
│   └── local.json
├── main/
│   ├── main.py
│   ├── brain.py
│   ├── ai.py
│   └── api_client.py
└── func/
    ├── camera/
    ├── motion/
    ├── music/
    ├── tools/
    └── voice-chat/
📄 ルートファイル
ファイル	役割
test.py	data/state.py の動作確認用テストスクリプト。State, CameraState, VoiceState を生成して表示するだけのサンドボックス
📁 data/ — データ・状態定義
ファイル	役割
state.py	ロボットの内部状態を定義するデータクラス。CameraState（カメラ情報）、VoiceState（音声情報）、State（両者を統合した全体状態）の3つを持つ
config.json	設定ファイル（現在は空）
local.json	ローカル環境用設定ファイル（現在は空）
📁 main/ — メインロジック・制御系
ファイル	役割
main.py	エントリーポイント。asyncio.gather で brain_loop・camera_loop・voice_loop・commandline_loop・gemma3_4b_cloud を並列実行する。モーターコマンドの変換テーブルも持つ
brain.py	AIによる意思決定の中枢。2つのAIインスタンスを管理：①control_ai（コマンドのみ出力する制御AI）、②chat_ai（会話AIで「話す」コマンド時に起動）。decide() メソッドで状況を受け取りコマンドを返す
ai.py	LLM APIラッパー。システムプロンプト・履歴管理・APIへのメッセージ送信をカプセル化したクラス。keep_history フラグで会話履歴の保持/非保持を切り替え可能
api_client.py	APIキー自動ローテーションクライアント。.env から MY_API_KEY_1, MY_API_KEY_2... を読み込み、429エラー（レート制限）時に自動で次のキーへ切り替える
📁 func/camera/ — カメラ・物体認識
ファイル	役割
camera1.py	学習用サンプル。YOLOモデルをマルチスレッドで推論し、カメラ映像にバウンディングボックス・FPS・座標を表示。コード内に7つのレッスン（FPS計算・Threading等）のコメント解説付き
camera2.py	camera1.py のシンプル版。model.predict(stream=True) を使ったストリーミング推論で物体認識と映像表示を行う
image-seg.py	YOLOモデルで show=True を使い最もシンプルに映像ストリームを表示するだけの最小実装
vision-llm.py	ビジョンLLM。Groq の llama-4-scout モデルに画像を送り、ジェスチャー等を認識するスクリプト（1枚画像に特化）
groq-llm-1.py	インタラクティブな画像チャット。コンソールから画像パスとテキストを入力し、Groqの vision モデルと会話できるCLIツール
yolo-export.py	YOLO26n-seg.pt を NCNN形式 にエクスポートするスクリプト（Raspberry Pi等の軽量デバイス向け変換ツール）
model_ncnn.py	エクスポートされたNCNNモデル（.param / .bin）の動作確認スクリプト
YOLO26n-seg.onnx	YOLOセグメンテーションモデルの ONNXフォーマット（推論用）
YOLO26n-seg.pt	YOLOセグメンテーションモデルの PyTorchフォーマット（エクスポート元）
model.ncnn.bin / model.ncnn.param	YOLOモデルの NCNNフォーマット（軽量デバイス向け）
metadata.yaml	YOLOモデルのメタデータ（クラス名一覧等）
📁 func/motion/ — モーター制御
ファイル	役割
motor.py	ステッピングモータードライバー。Limiter（物理可動範囲チェック）と StepperManager（非同期モーター制御）の2クラス。GPIO制御で最大4軸（a/b/c/d）を並列駆動し、速度・角度指定に対応。単体テスト用の main() / fallback() も内包
📁 func/music/ — 音楽再生
ファイル	役割
music.py	オンライン音楽ストリーミング。yt_dlp でYouTubeから楽曲URLを取得し、vlc でオーディオのみ再生するスクリプト
📁 func/tools/ — ツール・拡張機能
ファイル	役割
commandl_ine.py	CLIとGUIコントローラー。CommandLineクラスは /mode・/status・/exit コマンドを非同期で処理。GUIクラスは tkinter を使ったウィンドウUIでコマンド入力を受け付ける
program_translation.py	自作スクリプト言語インタープリター。print, if, while, end, search, run, sleep トークンをパースして逐次実行する。search でロボットの状態を参照し、run でモーションコマンドを生成できる
📁 func/voice-chat/ — 音声会話システム
ファイル	役割
speech_controller.py	音声会話のオーケストレーター。スペースキー押下 → 音声録音（whisper） → LLM応答とTTSを並列処理するメインループ
groq-whisper-stt.py	音声認識（STT）。マイクで音声を録音し、Groq の Whisper API でテキストに変換。結果を /tmp/speech_transcription.txt に保存
groq-llm.py	LLM応答生成。/tmp/speech_transcription.txt を読み込み、Groq の llama-3.3-70b でストリーミング応答を生成。結果を /tmp/llm_response.txt に書き込み
edge-tts.py	テキスト読み上げ（TTS）。/tmp/llm_response.txt を読み込んで音声合成し、スピーカーから再生する
audio_feedback.py	システム効果音。起動・ウェイクワード検出・録音開始・エラーなど各状態に応じたビープ音をmacOS/Linux/Windows対応で鳴らす
SPEECH_CONTROLLER_README.md	音声制御システムの使い方説明ドキュメント（フロー図・起動手順・カスタマイズ方法）
🔗 システム全体の流れ
Code
[カメラ] camera/ → 物体認識情報
[音声]   voice-chat/ → 音声テキスト変換
          ↓
[状態]   data/state.py → CameraState + VoiceState → State
          ↓
[脳]     main/brain.py → control_ai が状況を判断してコマンド出力
          ↓
[行動]   main/main.py → コマンドをモーター制御に変換
          ↓
[モーター] func/motion/motor.py → ステッピングモーターを動かす
Send message
What would you like to do next?
