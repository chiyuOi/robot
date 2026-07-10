#!/usr/bin/env python3
"""Check OpenRouter available models"""

import requests
import os
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("OPENROUTER_API_KEY")
if not api_key:
    print("❌ No API key found")
    exit(1)

headers = {
    "Authorization": f"Bearer {api_key}",
}

# Get models list
response = requests.get("https://openrouter.ai/api/v1/models", headers=headers)
print(f"Status: {response.status_code}")

if response.status_code == 200:
    models = response.json()
    print(f"\n📊 Available Models: {len(models.get('data', []))} total")
    
    # Filter vision models
    vision_models = []
    for model in models.get('data', []):
        if 'vision' in model.get('name', '').lower() or 'gpt-4' in model.get('id', '').lower():
            vision_models.append({
                'id': model.get('id'),
                'name': model.get('name'),
                'architecture': model.get('architecture', {}).get('modality', 'unknown')
            })
    
    print(f"\n🖼️  Vision Models Available: {len(vision_models)}")
    for m in vision_models[:10]:
        print(f"  - {m['id']}: {m['name']}")
        
    # Show free vision models
    print("\n💰 Free/Affordable Vision Models:")
    free_models = [m for m in models.get('data', []) if m.get('pricing', {}).get('prompt', 0) == 0]
    for m in free_models[:5]:
        print(f"  - {m.get('id')}")
else:
    print(f"Error: {response.text}")
