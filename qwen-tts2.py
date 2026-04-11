from gradio_client import Client
from pydub import AudioSegment
from pydub.playback import play
import time

def play_audio(file_path):
    """
    Play audio file using pydub.

    Args:
        file_path (str): Path to the audio file to play.
    """
    try:
        audio = AudioSegment.from_file(file_path)
        print(f"Playing audio: {file_path}")
        play(audio)
        print("Audio playback completed.")
    except FileNotFoundError:
        print(f"Error: Audio file '{file_path}' not found.")
    except Exception as e:
        print(f"Error playing audio: {e}")

def generate_speech(text, voice, language):
    """
    Generate speech using Qwen3-TTS API.

    Args:
        text (str): Input text to convert to speech.
        voice (str): Selected voice (e.g., "Cherry / 芊悦").
        language (str): Selected language (e.g., "Auto / 自动").
    """
    client = Client("https://qwen-qwen3-tts-demo.ms.show/")
    result = client.predict(
        text=text,
        voice_display=voice,
        language_display=language,
        api_name="/tts_interface"
    )
    return result

def main():
    print("Qwen3-TTS Demo")
    print("----------------")

    # Input text
    text = input("Input Text / 输入文本: ")

    # Select voice
    print("\nSelect Voice / 选择发音人:")
    voices = [
        "Cherry / 芊悦", "Serena / 苏瑶", "Ethan / 晨煦", "Chelsie / 千雪",
        "Momo / 茉兔", "Vivian / 十三", "Moon / 月白", "Maia / 四月",
        "Kai / 凯", "Nofish / 不吃鱼", "Bella / 萌宝", "Jennifer / 詹妮弗",
        "Ryan / 甜茶", "Katerina / 卡捷琳娜", "Aiden / 艾登",
        "Bodega / 西班牙语-博德加", "Alek / 俄语-阿列克", "Dolce / 意大利语-多尔切",
        "Sohee / 韩语-素熙", "Ono Anna / 日语-小野杏", "Lenn / 德语-莱恩",
        "Sonrisa / 西班牙语拉美-索尼莎", "Emilien / 法语-埃米尔安",
        "Andre / 葡萄牙语欧-安德雷", "Radio Gol / 葡萄牙语巴-拉迪奥·戈尔",
        "Eldric Sage / 精品百人-沧明子", "Mia / 精品百人-乖小妹",
        "Mochi / 精品百人-沙小弥", "Bellona / 精品百人-燕铮莺",
        "Vincent / 精品百人-田叔", "Bunny / 精品百人-萌小姬",
        "Neil / 精品百人-阿闻", "Elias / 墨讲师", "Arthur / 精品百人-徐大爷",
        "Nini / 精品百人-邻家妹妹", "Ebona / 精品百人-诡婆婆",
        "Seren / 精品百人-小婉", "Pip / 精品百人-调皮小新",
        "Stella / 精品百人-美少女阿月", "Li / 南京-老李",
        "Marcus / 陕西-秦川", "Roy / 闽南-阿杰", "Peter / 天津-李彼得",
        "Eric / 四川-程川", "Rocky / 粤语-阿强", "Kiki / 粤语-阿清",
        "Sunny / 四川-晴儿", "Jada / 上海-阿珍", "Dylan / 北京-晓东"
    ]
    for i, voice in enumerate(voices, 1):
        print(f"{i}. {voice}")
    voice_choice = int(input("Enter the number of your choice: ")) - 1
    selected_voice = voices[voice_choice]

    # Select language
    print("\nSelect Text Language / 选择文本语言:")
    languages = [
        "Auto / 自动", "English / 英文", "Chinese / 中文",
        "German / 德语", "Italian / 意大利语", "Portuguese / 葡萄牙语",
        "Spanish / 西班牙语", "Japanese / 日语", "Korean / 韩语",
        "French / 法语", "Russian / 俄语"
    ]
    for i, lang in enumerate(languages, 1):
        print(f"{i}. {lang}")
    lang_choice = int(input("Enter the number of your choice: ")) - 1
    selected_language = languages[lang_choice]

    # Generate speech
    print("\nGenerating Speech / 生成语音...")
    start_time = time.time()
    result = generate_speech(text, selected_voice, selected_language)
    generation_time = time.time() - start_time
    print(f"\nGenerated Speech saved as: {result}")
    print(f"Generation Latency: {generation_time:.2f} seconds")
    
    # Play the generated audio
    print("\nPlaying audio...")
    play_start_time = time.time()
    play_audio(result)
    play_time = time.time() - play_start_time
    print(f"Playback Latency: {play_time:.2f} seconds")
    
    # Total latency
    total_time = time.time() - start_time
    print(f"\nTotal Latency: {total_time:.2f} seconds")

if __name__ == "__main__":
    main()