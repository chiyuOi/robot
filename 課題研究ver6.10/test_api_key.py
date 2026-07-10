#!/usr/bin/env python3
"""Test OpenRouter API key and available models"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("OPENROUTER_API_KEY")
print(f"API Key loaded: {api_key[:20]}..." if api_key else "❌ No API key")

if api_key:
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # Test 1: Simple test call
    print("\n1️⃣ Testing simple text completion...")
    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers=headers,
        json={
            "model": "meta-llama/llama-3.2-11b-vision-instruct",
            "messages": [{"role": "user", "content": "Say 'test' in one word"}],
            "max_tokens": 10
        }
    )
    print(f"   Status: {response.status_code}")
    if response.status_code != 200:
        print(f"   Error: {response.text[:200]}")
    else:
        print(f"   ✅ Success: {response.json()['choices'][0]['message']['content']}")
    
    # Test 2: Try a known free model
    print("\n2️⃣ Testing with different model...")
    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers=headers,
        json={
            "model": "openrouter/auto",
            "messages": [{"role": "user", "content": "Hello"}],
            "max_tokens": 10
        }
    )
    print(f"   Status: {response.status_code}")
    if response.status_code != 200:
        print(f"   Error: {response.text[:200]}")
    else:
        print(f"   ✅ Success")
