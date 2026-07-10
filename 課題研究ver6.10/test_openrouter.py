#!/usr/bin/env python3
"""Test OpenRouter API with image support"""

import sys
from pathlib import Path
import base64
import cv2
import numpy as np

# Setup paths
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from main.api_client import OpenRouterClient

def test_openrouter_text():
    """Test OpenRouter text API"""
    print("🧪 Testing OpenRouter Text API...")
    try:
        client = OpenRouterClient()
        
        messages = [
            {
                "role": "user",
                "content": "Say 'Hello from OpenRouter!' in Japanese"
            }
        ]
        
        response = client.send_message_with_image(messages)
        print(f"✅ Text API Response: {response}")
        return True
    except Exception as e:
        print(f"❌ Text API Error: {e}")
        return False


def test_openrouter_vision():
    """Test OpenRouter vision API with a test image"""
    print("\n🧪 Testing OpenRouter Vision API...")
    try:
        client = OpenRouterClient()
        
        # Create a simple test image
        img = np.zeros((100, 100, 3), dtype=np.uint8)
        cv2.rectangle(img, (20, 20), (80, 80), (0, 255, 0), -1)  # Green square
        cv2.circle(img, (50, 50), 20, (255, 0, 0), -1)  # Blue circle
        
        # Save and encode
        cv2.imwrite("/tmp/test_image.jpg", img)
        with open("/tmp/test_image.jpg", "rb") as f:
            image_base64 = base64.standard_b64encode(f.read()).decode("utf-8")
        
        # Test vision API
        description = client.describe_image(
            image_base64,
            "Describe what you see in this image in Japanese. What shapes do you see?"
        )
        
        print(f"✅ Vision API Response: {description}")
        return True
    except Exception as e:
        print(f"❌ Vision API Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("OpenRouter API Test Suite")
    print("=" * 60)
    
    text_ok = test_openrouter_text()
    vision_ok = test_openrouter_vision()
    
    print("\n" + "=" * 60)
    print("Test Results:")
    print(f"  Text API: {'✅ PASS' if text_ok else '❌ FAIL'}")
    print(f"  Vision API: {'✅ PASS' if vision_ok else '❌ FAIL'}")
    print("=" * 60)
