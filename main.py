import os
import time
import asyncio
import uuid
import subprocess
import ssl
from fastapi import FastAPI, HTTPException, BackgroundTasks, Request
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import yt_dlp

# MacOS SSL certificate bypass
try:
    _create_unverified_https_context = ssl._create_unverified_context
except AttributeError:
    pass
else:
    ssl._create_default_https_context = _create_unverified_https_context


app = FastAPI(title="YouTube Video Downloader")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

TEMP_STORAGE_DIR = "/var/www/ytdown"
os.makedirs(TEMP_STORAGE_DIR, exist_ok=True)

# We will store active downloads here for tracking
# { task_id: {"status": "processing" | "completed" | "failed", "filepath": str, "error": str} }
downloads = {}

# Keep track of recent downloads for the UI (capped at 50)
recent_downloads = []

templates = Jinja2Templates(directory="templates")

# Models
class URLRequest(BaseModel):
    url: str

class ProcessRequest(BaseModel):
    url: str
    format_id: str
    title: str = "video"
    thumbnail: str = ""

# Helper functions
def format_bytes(b):
    if b is None: return "0 B"
    if b < 1024: return f"{b} B"
    elif b < 1024**2: return f"{b/1024:.1f} KiB"
    elif b < 1024**3: return f"{b/1024**2:.1f} MiB"
    else: return f"{b/1024**3:.1f} GiB"

def download_video_sync(task_id: str, url: str, format_id: str, output_path: str):
    """
    Synchronous download function meant to be run in a separate thread.
    """
    is_audio_only = format_id.startswith('audio-')
    
    ydl_opts = {
        'merge_output_format': 'mp4',
        'outtmpl': output_path,
        'quiet': True,
        'no_playlist': True,
        'nocheckcertificate': True,
        'no-check-certificate': True,
    }
    
    if is_audio_only:
        audio_codec = format_id.split('-')[1] # mp3, wav, flac
        ydl_opts['format'] = 'bestaudio/best'
        # when extracting audio, yt-dlp will change the extension (e.g. .mp4 -> .mp3)
        # we will handle finding the correct file after download
        ydl_opts['postprocessors'] = [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': audio_codec,
            'preferredquality': '192',
        }]
    else:
        ydl_opts['format'] = f'{format_id}+bestaudio/b'
    
    if os.path.exists("cookies.txt"):
        ydl_opts['cookiefile'] = 'cookies.txt'
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        
        # Audio extraction changes the file extension, so we must search for the final file
        base_path = os.path.splitext(output_path)[0]
        possible_files = [f for f in os.listdir(TEMP_STORAGE_DIR) if f.startswith(os.path.basename(base_path))]
        
        if possible_files:
            # Found the completed file
            actual_path = os.path.join(TEMP_STORAGE_DIR, possible_files[0])
            downloads[task_id]["filepath"] = actual_path
            downloads[task_id]["status"] = "completed"
            
            # Update history status
            for idx, item in enumerate(recent_downloads):
                if item["task_id"] == task_id:
                    recent_downloads[idx]["status"] = "completed"
                    break
        else:
            downloads[task_id]["status"] = "failed"
            downloads[task_id]["error"] = "Output file not found after download."
            for idx, item in enumerate(recent_downloads):
                if item["task_id"] == task_id:
                    recent_downloads[idx]["status"] = "failed"
                    break

    except Exception as e:
        downloads[task_id]["status"] = "failed"
        downloads[task_id]["error"] = str(e)
        for idx, item in enumerate(recent_downloads):
            if item["task_id"] == task_id:
                recent_downloads[idx]["status"] = "failed"
                break


# Background task to clean up old files periodically
async def periodic_cleanup():
    while True:
        try:
            now = time.time()
            for filename in os.listdir(TEMP_STORAGE_DIR):
                filepath = os.path.join(TEMP_STORAGE_DIR, filename)
                if os.path.isfile(filepath):
                    # Delete files older than 24 hours (86400 seconds)
                    if now - os.path.getmtime(filepath) > 86400:
                        os.remove(filepath)
                        print(f"Cleaned up old file: {filepath}")
        except Exception as e:
            print(f"Cleanup error: {e}")
        
        # Run cleanup every hour
        await asyncio.sleep(3600)

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(periodic_cleanup())

# API Endpoints
@app.post("/api/info")
async def fetch_formats(req: URLRequest):
    ydl_opts = {
        'quiet': True, 
        'nocolor': True,
        'nocheckcertificate': True,
        'extract_flat': 'in_playlist'  # Do not download formats for every video in a playlist
    }
    
    if os.path.exists("cookies.txt"):
        ydl_opts['cookiefile'] = 'cookies.txt'

    try:
        def extract():
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                return ydl.extract_info(req.url, download=False)
        
        info = await asyncio.to_thread(extract)
        
        # Check if it's a playlist
        if info.get('_type') == 'playlist':
            entries = []
            for entry in info.get('entries', []):
                if entry:
                    entries.append({
                        "url": entry.get('url') or entry.get('webpage_url'),
                        "title": entry.get('title', 'Unknown Title'),
                        "duration": entry.get('duration'),
                    })
            return {
                "is_playlist": True,
                "title": info.get('title', 'YouTube Playlist'),
                "entries": entries
            }
        
        # It's a single video
        formats_list = []
        for f in info.get('formats', []):
            if f.get('vcodec', 'none') != 'none':
                filesize = f.get('filesize') or f.get('filesize_approx')
                formats_list.append({
                    "id": f.get('format_id'),
                    "ext": f.get('ext', '?'),
                    "res": f.get('resolution', 'audio'),
                    "note": f.get('format_note', ''),
                    "size_str": format_bytes(filesize),
                })
                
        # Inject Advanced Audio Formats
        formats_list.insert(0, {"id": "audio-mp3", "ext": "mp3", "res": "Audio", "note": "High Quality MP3", "size_str": "Auto"})
        formats_list.insert(1, {"id": "audio-wav", "ext": "wav", "res": "Audio", "note": "Lossless WAV", "size_str": "Auto"})
        formats_list.insert(2, {"id": "audio-flac", "ext": "flac", "res": "Audio", "note": "Lossless FLAC", "size_str": "Auto"})
        
        return {
            "is_playlist": False,
            "title": info.get('title', 'video'),
            "thumbnail": info.get('thumbnail', ''),
            "formats": formats_list
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/process")
async def process_video(req: ProcessRequest, background_tasks: BackgroundTasks):
    task_id = str(uuid.uuid4())
    output_path = os.path.join(TEMP_STORAGE_DIR, f"{task_id}.mp4")
    
    downloads[task_id] = {
        "status": "processing",
        "filepath": output_path,
        "error": None
    }
    
    # Save to history
    recent_downloads.insert(0, {
        "task_id": task_id,
        "title": req.title,
        "thumbnail": req.thumbnail,
        "format": req.format_id,
        "status": "processing",
        "timestamp": time.time()
    })
    # Cap history at 50
    if len(recent_downloads) > 50:
        recent_downloads.pop()
    
    # Spawn background task
    background_tasks.add_task(download_video_sync, task_id, req.url, req.format_id, output_path)
    
    return {"task_id": task_id}

@app.get("/api/recent")
async def get_recent():
    return {"recent": recent_downloads}

@app.get("/api/status/{task_id}")
async def get_status(task_id: str):
    if task_id not in downloads:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return {
        "task_id": task_id,
        "status": downloads[task_id]["status"],
        "error": downloads[task_id]["error"]
    }

def delete_file_after_response(filepath: str, task_id: str):
    """Callback to delete the file after it has been served."""
    try:
        if os.path.exists(filepath):
            os.remove(filepath)
            print(f"Deleted file after stream: {filepath}")
    except Exception as e:
        print(f"Error deleting file {filepath}: {e}")
    finally:
        if task_id in downloads:
            del downloads[task_id]

@app.get("/api/download/{task_id}")
async def download_file(task_id: str, title: str = "video", background_tasks: BackgroundTasks = None):
    if task_id not in downloads:
        raise HTTPException(status_code=404, detail="Task not found")
    
    task_info = downloads[task_id]
    if task_info["status"] != "completed":
        raise HTTPException(status_code=400, detail="Download not completed yet")
    
    filepath = task_info["filepath"]
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="File not found on server")
    
    safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '.', '_', '-')).rstrip()
    filename = f"{safe_title}.mp4"
    
    background_tasks.add_task(delete_file_after_response, filepath, task_id)
    
    return FileResponse(
        path=filepath,
        filename=filename,
        media_type='video/mp4'
    )

# Frontend Serving
@app.get("/")
async def serve_frontend(request: Request):
    return templates.TemplateResponse(request=request, name="index.html", context={"request": request})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
