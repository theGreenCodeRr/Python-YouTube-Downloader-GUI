import yt_dlp

ydl_opts = {
    'quiet': False, 
    'nocolor': True,
    'nocheckcertificate': True,
    'extractor_args': {'youtube': {'player_client': ['ios']}}
}
with yt_dlp.YoutubeDL(ydl_opts) as ydl:
    try:
        info = ydl.extract_info("https://www.youtube.com/watch?v=X9W25-porY4", download=False)
        print("Success!", info.get('title'))
    except Exception as e:
        print("Failed:", str(e))
