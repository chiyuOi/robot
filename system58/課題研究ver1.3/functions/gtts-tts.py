from gtts import gTTS
from pydub import AudioSegment
from pydub.playback import play

text = input("Enter text to convert to speech: ")
words = text.split()  # Split the text into words
combined_audio = AudioSegment.silent(duration=0)  # Initialize an empty audio segment

for word in words:
    tts = gTTS(text=word, lang='en')
    tts.save("temp.mp3")
    word_audio = AudioSegment.from_mp3("temp.mp3")
    combined_audio += word_audio  # Append the word audio to the combined audio

# Save the combined audio
combined_audio.export("output.mp3", format="mp3")
print("Audio saved as output.mp3")

# Play the combined audio
play(combined_audio)