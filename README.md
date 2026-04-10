
# やることリスト
- ✅リアルタイム画像認識
- ✅画像デスクリプション生成LLM
- ✅文字起こし
- ✅文字読み上げ
- ❌3D外形モデリング
- ❌機能管理（全体のフレームワーク、アルゴリズム）
- ❌モータプログラム生成・文字読み上げテキスト生成AI
- ❌拡張機能（音楽再生、Google検索）
- ❌ローカルでの運用
- 

# AI System Architecture

## Overview
This system utilizes four AI components working together:

<img width="459" height="505" alt="image" src="https://github.com/user-attachments/assets/d304036f-8e21-48ce-9c9c-2f8948a83663" />

<img width="459" height="505" alt="image" src="スクリーンショット 2026-03-16 10.25.59.PNG" />



## AI Components

### 1. Gemini 2.0 Flash
**Capabilities:**
- Image processing
- Live streaming analysis
- Text generation and understanding

### 2. Text Humanization AI
**Model:** qwen3-vl:235b-instruct-cloud
**Purpose:** 
- Converts AI-generated text into natural, human-like speech
- Improves conversational flow and readability

### 3. Motor Command AI
**Model:** qwen3-vl:235b-instruct-cloud

**Purpose:**
- Processes natural language instructions
- Generates motor control commands
- Handles robotics coordination

### 4. [Fourth AI Component]
*To be specified*

## System Integration
These AI components work collaboratively to process multimodal inputs (image, video, text) and generate both natural language responses and motor control outputs.

## P.S. Possible changes
- Possible transition all LLM library from Ollama to Groq,
- Image recognition: Gemini 2.0 Flash (Google AI studio) → llama-4-scout (Groq)
- Motor command and Text Humanization- qwen-instruct(ollama) → Unknown (Groq)
- Speech-To-Text library; SpeechRecognition Library → whisper-large-v3-turbo (Groq)
  
  **System Overview Draft**
  
  - Wake-word and command text input: Whisper-lage-v3-turbo→
Image Recognition LLM(Input: Image, Transcribed Text | Output: XY axis & object description, Response Text to Transcribed Text) →  Qwen3-32b(Humanization, Motor command) →　Humanized text: gTTS,  Motor Command Text- Move motors


