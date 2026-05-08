import os
import base64
import requests
import json
from pathlib import Path

class OllamaVisionChat:
    def __init__(self, model="ministral-3:3b-cloud", base_url="http://localhost:11434"):
        """
        Initialize Ollama Vision Chat
        
        Args:
            model: The Ollama model to use (default: qwen3-vl:235b-cloud)
            base_url: Ollama API endpoint
        """
        self.model = model
        self.base_url = base_url
        self.api_url = f"{base_url}/api/generate"
        
    def encode_image(self, image_path):
        """Encode image to base64"""
        try:
            with open(image_path, "rb") as image_file:
                return base64.b64encode(image_file.read()).decode('utf-8')
        except Exception as e:
            raise Exception(f"Error reading image: {e}")
    
    def chat(self, prompt, image_path=None, stream=True):
        """
        Send a prompt with optional image to Ollama
        
        Args:
            prompt: Text prompt/question
            image_path: Path to image file (optional)
            stream: Whether to stream the response
        """
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": stream
        }
        
        # Add image if provided
        if image_path:
            if not os.path.exists(image_path):
                raise FileNotFoundError(f"Image not found: {image_path}")
            
            image_base64 = self.encode_image(image_path)
            payload["images"] = [image_base64]
            print(f"📷 Image loaded: {image_path}")
        
        print(f"💬 Prompt: {prompt}\n")
        print("🤖 Response:", end=" ", flush=True)
        
        try:
            response = requests.post(
                self.api_url,
                json=payload,
                stream=stream
            )
            response.raise_for_status()
            
            full_response = ""
            
            if stream:
                for line in response.iter_lines():
                    if line:
                        json_response = json.loads(line)
                        chunk = json_response.get("response", "")
                        print(chunk, end="", flush=True)
                        full_response += chunk
                        
                        if json_response.get("done", False):
                            break
            else:
                json_response = response.json()
                full_response = json_response.get("response", "")
                print(full_response)
            
            print("\n")
            return full_response
            
        except requests.exceptions.RequestException as e:
            print(f"\n❌ Error communicating with Ollama: {e}")
            return None
        except json.JSONDecodeError as e:
            print(f"\n❌ Error parsing response: {e}")
            return None


def interactive_mode():
    """Interactive mode for chatting with vision model"""
    print("=" * 60)
    print("🎨 Ollama Vision Chat - Interactive Mode")
    print("=" * 60)
    print(f"\n🤖 Using model: qwen3-vl:235b-cloud")
    print("\nCommands:")
    print("  /image <path>  - Set image for next query")
    print("  /clear         - Clear current image")
    print("  /quit          - Exit program")
    print("  Just type      - Send text-only query")
    print("=" * 60 + "\n")
    
    chat = OllamaVisionChat(model="qwen3-vl:235b-cloud")
    current_image = None
    
    while True:
        try:
            user_input = input("You: ").strip()
            
            if not user_input:
                continue
            
            # Handle commands
            if user_input.startswith("/"):
                if user_input.lower() == "/quit":
                    print("👋 Goodbye!")
                    break
                    
                elif user_input.lower() == "/clear":
                    current_image = None
                    print("✅ Image cleared\n")
                    continue
                    
                elif user_input.lower().startswith("/image "):
                    image_path = user_input[7:].strip()
                    if os.path.exists(image_path):
                        current_image = image_path
                        print(f"✅ Image set: {image_path}\n")
                    else:
                        print(f"❌ Image not found: {image_path}\n")
                    continue
                    
                else:
                    print("❌ Unknown command\n")
                    continue
            
            # Send query
            chat.chat(user_input, image_path=current_image)
            
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}\n")


def single_query_mode(prompt, image_path=None):
    """Single query mode"""
    chat = OllamaVisionChat(model="qwen3-vl:235b-cloud")
    return chat.chat(prompt, image_path=image_path)


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        # Command-line mode
        if len(sys.argv) == 2:
            # Text-only query
            prompt = sys.argv[1]
            single_query_mode(prompt)
        elif len(sys.argv) == 3:
            # Query with image
            prompt = sys.argv[1]
            image_path = sys.argv[2]
            single_query_mode(prompt, image_path)
        else:
            print("Usage:")
            print("  python ollama_vision.py '<prompt>'")
            print("  python ollama_vision.py '<prompt>' <image_path>")
            print("  python ollama_vision.py  (for interactive mode)")
    else:
        # Interactive mode
        interactive_mode()
