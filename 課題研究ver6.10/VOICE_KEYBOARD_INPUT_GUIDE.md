# 音声/キーボード入力テスト ガイド

## 新機能概要

`SensingModule` に**音声入力またはキーボード入力を選択できる機能**を追加しました。

### 対応する入力方式

1. **🎤 音声入力（マイク）**
   - Groq Whisper STT を使用
   - 実際のマイク入力を処理
   - マイク対応環境必須

2. **⌨️  キーボード入力**
   - テキスト直接入力
   - テスト・デバッグに最適
   - どこでも実行可能

3. **自動選択（デフォルト）**
   - ユーザーに選択を促す
   - 推奨

---

## 使用方法

### 方法1: テストスイートから実行

```bash
python3 test_integrated_system.py
```

メニューから選択:
```
Select a test to run:
...
9. 🎤 Voice/Keyboard Pipeline Test (入力方式選択可)
0. Exit
```

**選択 9** を入力

```
📍 入力方式を選択してください:
1. 🎤 音声入力（マイク）
2. ⌨️  キーボード入力
選択 (1-2, デフォルト:2): 
```

#### 音声入力を選択（1）

```
選択 (1-2, デフォルト:2): 1
🎤 音声入力を開始します...
   マイクに向かってコマンドを話してください...
```

マイクに向かってコマンドを話します：
```
例: "青いボールを探してください"
例: "赤いカップの位置を教えて"
例: "こんにちは"
```

Groq Whisper STT が音声をテキストに変換：
```
📝 認識されたテキスト: 青いボールを探してください
```

#### キーボード入力を選択（2）

```
選択 (1-2, デフォルト:2): 2
⌨️  キーボード入力:
>>> 
```

テキストを入力：
```
>>> 赤いボールを探してください
📝 入力されたテキスト: 赤いボールを探してください
```

### パイプライン実行

入力方式を選択した後、完全な5段階パイプラインが自動実行されます：

```
1️⃣ SENSING: ユーザー入力を受け取る
   Input: 赤いボールを探してください

2️⃣ PLANNING: Groq #1 でツール選択
   Selected: YOLO
   Target: red_ball

3️⃣ ACTION: 選択ツールを実行
   Status: success

4️⃣ INTEGRATION: Groq #2 で応答生成
   Speech: 赤いボールを見つけました。

5️⃣ EXECUTION: 音声+モーター並列実行
   🔊 Speech: 赤いボールを見つけました。

✅ Full pipeline test completed successfully!
```

---

## コード例

### 直接使用

```python
import asyncio
from main.integrated_system import SensingModule

async def main():
    sensing = SensingModule()
    
    # 入力方式を自動選択（ユーザーに選択させる）
    user_input = await sensing.get_user_input(input_method="auto")
    print(f"入力: {user_input}")
    
    # または明示的に指定
    # user_input = await sensing.get_user_input(input_method="keyboard")
    # user_input = await sensing.get_user_input(input_method="voice")

asyncio.run(main())
```

### 完全なパイプライン

```python
async def main():
    system = IntegratedRobotSystem()
    
    # 1. 入力方式選択
    user_input = await system.sensing.get_user_input("auto")
    
    # 2. ツール選択
    tool_config = system.planning.select_tool(user_input)
    
    # 3. ツール実行
    observation = await system.action.execute(tool_config)
    
    # 4. 応答生成
    response = system.integration.generate_response(observation, user_input)
    
    # 5. 実行
    await system.execution.execute_response(response)
```

---

## 環境要件

### キーボード入力
- ✅ 全環境対応
- 追加要件なし

### 音声入力
- 🎤 マイクデバイス必須
- 🔧 Groq Whisper STT スクリプト（`func/voice-chat/groq-whisper-stt.py`）
- 🔑 Groq API キー（`.env` に設定）

---

## トラブルシューティング

### 問題：音声入力がフォールバックされる

```
⚠️  音声認識エラー: ...
キーボード入力にフォールバック...
```

**原因**:
- STT スクリプトが見つからない
- マイクが接続されていない
- Groq API キーが設定されていない

**解決方法**:
```bash
# 1. キーボード入力を選択
選択 (1-2): 2

# 2. または .env ファイルを確認
cat .env  # MY_API_KEY_1 が設定されているか確認

# 3. STT スクリプトの確認
ls -la func/voice-chat/groq-whisper-stt.py
```

### 問題：キーボード入力が受け付けられない

```
❌ 入力がありません
>>>
```

**解決方法**:
```bash
# テキストを入力してEnterキーを押す
>>> 何か話してください<Enter>
```

---

## サンプルコマンド

テストできるコマンド例：

| コマンド | 期待される動作 |
|---------|--------------|
| "青いボールを探してください" | YOLO物体検出 → "見つけました" |
| "赤いカップは？" | 物体検出 → 位置報告 |
| "右に10度動いて" | モーター制御 → 回転実行 |
| "こんにちは" | 会話 → "こんにちは！" |
| "何が見えますか？" | YOLO推論 → 検出結果報告 |

---

## パフォーマンス

| 項目 | 時間 |
|------|------|
| 音声認識（STT） | 2-5秒 |
| Groq API応答 | 1-2秒 |
| パイプライン全体 | 5-10秒 |

---

## 今後の拡張

- [ ] リアルタイムマイク入力ストリーミング
- [ ] 音声確認ダイアログ ("聞き取りました。確認してもいいですか？")
- [ ] コマンド履歴保存
- [ ] バッチ処理（複数コマンド連続実行）
- [ ] カスタムウェイクワード設定UI

---

## 参考

- [統合システム実行ガイド](INTEGRATED_SYSTEM_README.md)
- [アーキテクチャ詳細](ARCHITECTURE_DETAILED.md)
- [Groq Whisper STT](func/voice-chat/groq-whisper-stt.py)
