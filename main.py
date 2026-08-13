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

TEMP_STORAGE_DIR = "./temp_storage"
os.makedirs(TEMP_STORAGE_DIR, exist_ok=True)

# We will store active downloads here for tracking
# { task_id: {"status": "processing" | "completed" | "failed", "filepath": str, "error": str} }
downloads = {}

templates = Jinja2Templates(directory="templates")

# Models
class URLRequest(BaseModel):
    url: str

class ProcessRequest(BaseModel):
    url: str
    format_id: str

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
    ydl_opts = {
        'format': f'{format_id}+bestaudio/b',
        'merge_output_format': 'mp4',
        'outtmpl': output_path,
        'quiet': True,
        'no_playlist': True,
        'nocheckcertificate': True,
        'no-check-certificate': True,
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        
        # Verify if file actually exists after download (yt-dlp adds extension sometimes if missing)
        # We enforced outtmpl, so it should be exact unless there's a merging issue.
        if os.path.exists(output_path):
            downloads[task_id]["status"] = "completed"
        else:
            # yt-dlp might have appended .mp4 if it wasn't specified, but we did specify it.
            # let's try to find if a file starts with the output_path name
            base_path = os.path.splitext(output_path)[0]
            possible_files = [f for f in os.listdir(TEMP_STORAGE_DIR) if f.startswith(os.path.basename(base_path))]
            if possible_files:
                actual_path = os.path.join(TEMP_STORAGE_DIR, possible_files[0])
                downloads[task_id]["filepath"] = actual_path
                downloads[task_id]["status"] = "completed"
            else:
                downloads[task_id]["status"] = "failed"
                downloads[task_id]["error"] = "Output file not found after download."

    except Exception as e:
        downloads[task_id]["status"] = "failed"
        downloads[task_id]["error"] = str(e)


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
        'nocheckcertificate': True
    }
    try:
        def extract():
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                return ydl.extract_info(req.url, download=False)
        
        # Run in thread pool to not block async loop
        info = await asyncio.to_thread(extract)
        
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
        
        return {
            "title": info.get('title', 'video'),
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
    
    # Spawn background task
    background_tasks.add_task(download_video_sync, task_id, req.url, req.format_id, output_path)
    
    return {"task_id": task_id}

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
