# Llama-4-Scout 画像説明機能 セットアップガイド

## 概要

YOLO による物体検出に加えて、**Llama-4-Scout-17B** (Groq API) を使用して画像全体の詳細な説明を生成するシステムが追加されました。

### 🎯 実行フロー

```
ユーザー入力
    ↓
┌─────────────────────────────────┐
│  フレームキャプチャ             │
└─────────┬───────────────────────┘
          │
    ┌─────┴─────┐
    │           │
[YOLO推論]  [Llama-4-Scout]
    │           │
    └─────┬─────┘
        (並列実行)
          │
    物体検出結果 + 画像説明
          │
[Integration Module]
          │
    最終応答 & モーター制御
```

---

## 🔧 セットアップ手順

### ステップ1: 既存の Groq API キーを使用

既に `.env` ファイルに `MY_API_KEY_1` (Groq API キー) が設定されていれば OK です。

```bash
# 確認
cat .env | grep MY_API_KEY_1
```

### ステップ2: requests ライブラリをインストール

```bash
pip install requests
```

### ステップ3: 動作確認

完了！これだけです。既存の Groq API キーで Llama-4-Scout が使用できます。

---

## 📝 使用方法

### テスト実行

```bash
# テストスイート起動
python3 test_integrated_system.py

# メニューから:
# "3" → Action Module Test
```

### 出力例

```
🎯 Testing YOLO object detection...

🎯 Action (YOLO Execution): Detecting objects...
🦙 Llama-4-Scout (Groq): Generating image description...
   Found: cup at (240, 180)
   ✅ Description generated
   📸 Image Description: The image shows a kitchen workspace with a white ceramic cup placed on a wooden desk, surrounded by various office supplies...

✅ YOLO execution result:
{
  "status": "success",
  "action": "object_detected",
  "primary": {
    "label": "cup",
    "x": 240,
    "y": 180,
    "confidence": 0.92
  },
  "image_description": "The image shows a kitchen workspace..."
}
```

---

## 🤖 モデルの詳細

| パラメータ | 値 |
|-----------|-----|
| **モデル名** | llama-4-scout-17b-16e-instruct |
| **提供元** | Groq API |
| **型** | マルチモーダル（テキスト + 画像） |
| **入力** | Base64 画像 + テキストプロンプト |
| **出力** | 画像説明（日本語対応） |
| **推論時間** | 1-3秒（Groq クラウド） |
| **API 呼び出し** | POST `/openai/v1/chat/completions` |

---

## 💡 カスタマイズ

### プロンプト変更

[main/integrated_system.py](main/integrated_system.py#L344-L354) で変更可能：

```python
# 現在の設定
if user_target:
    prompt = f"This image is being analyzed by a robot. Please describe what you see, particularly focusing on finding: {user_target}. Provide a detailed description in Japanese."
else:
    prompt = "This image is being analyzed by a robot. Please describe what you see in detail. Respond in Japanese."

# 例：日本語でのカスタマイズ
prompt = f"このロボット画像から{user_target}を見つけるのに役立つ詳細な説明をしてください。"
```

### モデルパラメータ調整

```python
payload = {
    "max_tokens": 200,      # ← 出力長（小さい=高速、大きい=詳細）
    "temperature": 0.5      # ← 創造性（0=確定的、1=創造的）
}
```

---

## ⚠️ トラブルシューティング

### 問題: `MY_API_KEY_1 not set`

**解決法:**
```bash
# .env ファイルを確認
cat .env

# なければ追加（Groq ダッシュボードから取得）
echo "MY_API_KEY_1=gsk_..." >> .env
```

### 問題: `requests not installed`

**解決法:**
```bash
pip install requests
```

### 問題: API エラー (401 Unauthorized)

**解決法:**
1. Groq ダッシュボードで API キーを確認
2. キーが有効か確認（失効していないか）
3. .env ファイルに正しく設定されているか確認

### 問題: タイムアウト（遅い応答）

**解決法:**
1. ネット接続確認
2. Groq API の状態確認
3. `timeout=10` を `timeout=20` に増やす

---

## 📊 パフォーマンス

| ステップ | 時間 |
|--------|------|
| フレームキャプチャ | 0.1-0.5秒 |
| YOLO推論 | 0.5-1秒 |
| Llama-4-Scout | 1-2秒 |
| **合計（並列）** | **1.5-3秒** |

---

## 🎯 実装例

### 完全なパイプライン

```python
import asyncio
from main.integrated_system import IntegratedRobotSystem

async def main():
    system = IntegratedRobotSystem()
    
    # ユーザー入力
    user_input = "赤いボール探してください"
    
    # Planning: ツール選択
    tool_config = system.planning.select_tool(user_input)
    
    # Action: YOLO + Llama-4-Scout (並列実行)
    observation = await system.action.execute(tool_config)
    # {
    #     "primary": {...},                    ← YOLO 結果
    #     "image_description": "The image..." ← Llama-4-Scout 結果
    # }
    
    # Integration: 応答生成
    response = system.integration.generate_response(observation, user_input)
    
    # Execution: 音声 + モーター
    await system.execution.execute_response(response)

asyncio.run(main())
```

---

## 📚 参考リンク

- [Groq API ドキュメント](https://console.groq.com/docs)
- [Llama-4-Scout モデル](https://huggingface.co/meta-llama/Llama-4-Scout-17B-16e-instruct)
- [Groq API Console](https://console.groq.com)

---

## 🔐 セキュリティ注意

⚠️ **API キーを Git に コミットしないこと**

```bash
# .gitignore に追加
echo ".env" >> .gitignore

# 既にコミット済みの場合
git rm --cached .env
git commit -m "Remove .env from tracking"
```

---

## ✅ チェックリスト

- [x] Groq API キー設定済み
- [x] requests ライブラリインストール済み
- [ ] テスト実行完了
- [ ] Llama-4-Scout で画像説明生成確認

---

## 次のステップ

- [ ] ラズパイでテスト実行
- [ ] 複数画像のバッチ処理
- [ ] 結果のキャッシング機構追加
- [ ] エラーハンドリング強化
