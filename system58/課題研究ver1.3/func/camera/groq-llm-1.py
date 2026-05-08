import os
from groq import Groq
from dotenv import load_dotenv
import base64
import time
load_dotenv()
client = Groq(api_key=os.environ.get("GROQ_API_KEY"),)
messages=[{"role":"system","content":"Your role is to provide a detailed description for images surrounded by green squares. Respond with  bullet lists of [Object's label]: Their detailed desription with only alphabetical letters. No intro, no conclsions. Keep each of explanation short & precise."}]
def encode_image(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")

while True:
    user_input=input("You:")
    image_path=input("Image Path (Enter to skip):")
    image_path= image_path.replace('"', '').replace("'",'')
    prev_time=time.time()
    if image_path:
        encoded=encode_image(image_path)
        messages.append({"role": "user","content": [{"type": "image_url","image_url": {"url": f"data:image/jpeg;base64,{encoded}"}},
                                                    {"type": "text", "text": user_input}]
        })

    else:
        messages.append({"role":"user","content":user_input})
    
    response = client.chat.completions.create(
        messages=messages,
        model="meta-llama/llama-4-scout-17b-16e-instruct",
        temperature=0.7,
        #More detail
        max_tokens= 512,
        top_p=1.0,
        stop=None,
        stream=False, )
    reply = response.choices[0].message.content
    messages.append({"role":"assistant","content":reply})
    curr_time=time.time()-prev_time
    
    print(f"Model (Latancy:{curr_time:.1f}):{reply}")
    
    
"""
    temperature ・・・Creative word choice 0.7 is the sweet spot for natural human souding output
    max_tokens ・・・A token is roughly ¾ of a word. max_tokens=512 means the reply cuts off at around 380 words, mid-sentence if needed.
    top_p ・・・filter the word list before picking.
    stop ・・・when you want to define when the model stops
    stream ・・・used when you wanna stream your output letter by letter
    
"""