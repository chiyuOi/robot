import base64
import time
import io
from PIL import Image
from groq import Groq

# 1. Initialize Client
# Best practice: use os.environ.get("GROQ_API_KEY") for security
client = Groq(api_key="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")

def prepare_image(image_path, max_dim=1024, quality=75):
    """Resizes and compresses image to minimize API latency."""
    with Image.open(image_path) as img:
        img.thumbnail((max_dim, max_dim))
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
        buffer = io.BytesIO()
        img.save(buffer, format="JPEG", quality=quality, optimize=True)
        return base64.b64encode(buffer.getvalue()).decode('utf-8')

def run_fast_query(image_path):
    # Prepare image
    b64_data = prepare_image(image_path)
    
    # Start Timer
    start_time = time.perf_counter()
    
    # API Call
    stream = client.chat.completions.create(
        model="meta-llama/llama-4-scout-17b-16e-instruct",
        messages=[{
            "role": "user",
            "content": [
                {"type": "text", "text": "Return ONLY [x,y,gesture]. No text."},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64_data}"}}
            ]
        }],
        temperature=0,
        max_tokens=12,
        stream=True
    )

    # Process Stream
    print("Response: ", end="", flush=True)
    for chunk in stream:
        if chunk.choices[0].delta.content:
            print(chunk.choices[0].delta.content, end="", flush=True)
            
    # Calculate Latency
    end_time = time.perf_counter()
    print(f"\n\nTotal Latency: {end_time - start_time:.4f} seconds")

# Run
if __name__ == "__main__":
    path = "/Users/abdullahattariqalhadi/Desktop/Screenshot 2026-03-09 at 10.32.12.png"
    run_fast_query(path)