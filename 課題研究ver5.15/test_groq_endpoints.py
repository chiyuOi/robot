#!/usr/bin/env python3
"""Test Groq API endpoints to find vision model support"""

import requests
import os
from pathlib import Path

# Load .env from current directory
env_file = Path(".env")
if env_file.exists():
    with open(env_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                os.environ[key.strip()] = value.strip()

api_key_2 = os.getenv("MY_API_KEY_2")
api_key_1 = os.getenv("MY_API_KEY_1")

print("🔍 Testing Groq API endpoints...\n")
print(f"API Key 1: {api_key_1[:20]}..." if api_key_1 else "❌ No MY_API_KEY_1")
print(f"API Key 2: {api_key_2[:20]}..." if api_key_2 else "❌ No MY_API_KEY_2")
print()

if not api_key_2:
    print("❌ API_KEY_2 not found in .env")
    exit(1)

headers = {
    "Authorization": f"Bearer {api_key_2}",
    "Content-Type": "application/json"
}

# Test 1: Text-only to verify key works
print("1️⃣ Testing text-only endpoint (should work)...")
payload = {
    "model": "llama-3.1-8b-instant",
    "messages": [
        {
            "role": "user",
            "content": "Hello, do you support vision models?"
        }
    ],
    "max_tokens": 100
}

try:
    response = requests.post("https://api.groq.com/openai/v1/chat/completions", json=payload, headers=headers, timeout=5)
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        print(f"   ✅ Text API works! Key is valid.")
        result = response.json()
        print(f"   Response: {result['choices'][0]['message']['content'][:80]}...")
    else:
        print(f"   ❌ Text API failed with status {response.status_code}")
except Exception as e:
    print(f"   ❌ Error: {e}")

# Test 2: Check available models
print("\n2️⃣ Checking available models...")
try:
    response = requests.get("https://api.groq.com/openai/v1/models", headers=headers, timeout=5)
    if response.status_code == 200:
        models = response.json()
        print(f"   ✅ Models endpoint works!")
        if "data" in models:
            all_models = models["data"]
            print(f"   Total models: {len(all_models)}")
            
            # Look for vision models
            vision_models = [m for m in all_models if "llava" in str(m).lower() or "vision" in str(m).lower() or "scout" in str(m).lower()]
            if vision_models:
                print(f"   🦙 Vision-related models found:")
                for m in vision_models[:5]:
                    if isinstance(m, dict):
                        print(f"      - {m.get('id', m)}")
                    else:
                        print(f"      - {m}")
            else:
                print(f"   ❌ No vision-related models found")
                print(f"   First 5 available models:")
                for m in all_models[:5]:
                    if isinstance(m, dict):
                        print(f"      - {m.get('id', m)}")
                    else:
                        print(f"      - {m}")
    else:
        print(f"   ❌ Models endpoint failed: {response.status_code}")
        print(f"   Response: {response.text[:200]}")
except Exception as e:
    print(f"   ❌ Error: {e}")

# Test 3: Try alternative vision endpoints
print("\n3️⃣ Testing alternative endpoints...")
alternative_endpoints = [
    "https://api.groq.com/vision/v1/chat/completions",
    "https://vision-api.groq.com/openai/v1/chat/completions",
    "https://api.groq.com/v1/vision/chat/completions",
]

for url in alternative_endpoints:
    try:
        print(f"\n   Testing: {url}")
        response = requests.head(url, headers=headers, timeout=3)
        print(f"   HEAD Status: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error: {type(e).__name__}")

print("\n✅ Tests completed")
