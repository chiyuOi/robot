import yt_dlp
import vlc
import time

def play_online_music(search_query):
    # 1. Search and extract the direct audio stream URL
    ydl_opts = {
        'format': 'bestaudio/best',
        'noplaylist': True,
        'quiet': True,
        'default_search': 'ytsearch',
    }

    print(f"Searching for: {search_query}...")
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(f"ytsearch:{search_query}", download=False)['entries'][0]
            url = info['url']
            title = info['title']
            print(f"Streaming: {title}")
        except Exception as e:
            print(f"Could not find music: {e}")
            return

    # 2. Use VLC to play the stream URL
    instance = vlc.Instance('--no-video')
    player = instance.media_player_new()
    media = instance.media_new(url)
    player.set_media(media)

    player.play()

    # Keep the script running while music plays
    print("Playing... Press Ctrl+C to stop.")
    try:
        while True:
            state = player.get_state()
            if state in [vlc.State.Ended, vlc.State.Error]:
                break
            time.sleep(1)
    except KeyboardInterrupt:
        player.stop()
        print("\nStopped.")

if __name__ == "__main__":
    song = input("What song do you want to play? ")
    if song.strip():
        play_online_music(song)