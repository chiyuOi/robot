# Groq API Vision モデル設定ガイド

## 現在のエラー

```
404 Client Error: Not Found for url: https://api.groq.com/openai/v1/chat/completions
```

これは以下のいずれかが原因の可能性があります：

1. **モデル名が正確でない**
   - `llama-4-scout-17b-16e-instruct` が存在しない
   - Groq が提供している実際のモデル名を確認が必要

2. **エンドポイントが異なる**
   - Vision API の専用エンドポイントが必要かもしれない
   - `/openai/v1/chat/completions` が正しくない可能性

3. **Vision 機能がまだ利用不可**
   - Groq が Vision をサポートしていない可能性
   - 別の API を使用する必要かもしれない

---

## 確認すべき項目

### 1. Groq API Console で確認

1. [Groq Console](https://console.groq.com) にアクセス
2. **API Keys** セクションで API キーを確認
3. **Documentation** で利用可能なモデル一覧を確認
4. Vision/Image capabilities を探す

### 2. 確認すべき内容

- [ ] 利用可能な Vision モデルの名前
- [ ] Vision モデルのエンドポイント URL
- [ ] 画像送信形式（base64, URL, multipart など）
- [ ] リクエスト形式（OpenAI互換か独自か）

### 3. コマンドラインテスト

```bash
# API キーをエクスポート
export MY_API_KEY_1="gsk_..."

# テスト用 curl コマンド
curl -X POST https://api.groq.com/openai/v1/chat/completions \
  -H "Authorization: Bearer $MY_API_KEY_1" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "llama-4-scout-17b-16e-instruct",
    "messages": [
      {
        "role": "user",
        "content": [
          {
            "type": "text",
            "text": "What do you see in this image?"
          }
        ]
      }
    ]
  }'
```

---

## 実装の修正方法

### Option A: Groq Vision API の正確な情報がある場合

`main/integrated_system.py` の `_generate_image_description` メソッドで以下を修正：

```python
# 正確なモデル名
"model": "groq-vision-model-name-here",

# または Vision 専用エンドポイント
api_url = "https://api.groq.com/openai/v1/vision/completions"  # 例

# 画像形式の変更（必要に応じて）
```

### Option B: 一時的に画像説明をスキップ

以下を実装して、Image Description 機能を無効化：

```python
# _generate_image_description メソッドで
if not self.api_client:
    return "(Image description disabled - Vision API not available)"
```

### Option C: 別の Vision API を使用

- **OpenAI Vision API** - GPT-4V
- **Azure OpenAI Vision** - 日本にリージョンあり
- **Google Vision API** - 無料枠あり
- **Local Ollama** - ollama.ai でローカル実行

---

## 次のステップ

ユーザー側で以下を確認してください：

1. Groq API コンソールにアクセス
2. 利用可能なモデル一覧を確認
3. Vision/Image モデルがあれば、その正確な名前とエンドポイントを教えてください
4. または、Groq API のドキュメントのリンクを共有してください

確認後、コードを修正します。
