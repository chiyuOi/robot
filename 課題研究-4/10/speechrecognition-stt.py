import speech_recognition as sr
import threading

recognizer = sr.Recognizer()

def listen_in_background():
    with sr.Microphone() as source:
        while True:
            try:
                audio = recognizer.listen(source)
                text = recognizer.recognize_google(audio)
                print(f"Heard: {text}")
                if text.lower() == "hey bro":
                    print("Transitioning to next program...")
                    break
            except sr.UnknownValueError:
                pass
            except sr.RequestError:
                pass

thread = threading.Thread(target=listen_in_background, daemon=False)
thread.start()
