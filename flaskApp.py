import os
import subprocess
from flask import Flask, request, jsonify, render_template, Response
from flask_cors import CORS
import yt_dlp

# --- Configuration ---
app = Flask(__name__, template_folder='templates')
CORS(app)  # Allow cross-origin requests

# --- Helper Functions ---
def format_bytes(b):
    """Formats bytes into a human-readable string (KiB, MiB, etc.)"""
    if b is None: return "0 B"
    if b < 1024: return f"{b} B"
    elif b < 1024**2: return f"{b/1024:.1f} KiB"
    elif b < 1024**3: return f"{b/1024**2:.1f} MiB"
    else: return f"{b/1024**3:.1f} GiB"

# --- API Endpoints ---

@app.route('/api/fetch_formats', methods=['POST'])
def fetch_formats():
    """
    API endpoint to fetch video formats.
    Expects JSON: {"url": "..."}
    """
    url = request.json.get('url')
    if not url:
        return jsonify({"error": "No URL provided"}), 400

    ydl_opts = {'quiet': True, 'nocolor': True}
    try:
        # Use yt-dlp to extract info without downloading
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
        
        formats_list = []
        for f in info.get('formats', []):
            # We only want video formats (vcodec != 'none')
            if f.get('vcodec', 'none') != 'none':
                filesize = f.get('filesize') or f.get('filesize_approx')
                
                formats_list.append({
                    "id": f.get('format_id'),
                    "ext": f.get('ext', '?'),
                    "res": f.get('resolution', 'audio'),
                    "note": f.get('format_note', ''),
                    "size_str": format_bytes(filesize),
                })
        
        # Send back the title and the list of formats
        return jsonify({
            "title": info.get('title', 'video'),
            "formats": formats_list
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/download')
def download_video():
    """
    This endpoint streams the download directly to the user
    by piping the output of yt-dlp.
    It takes 'url', 'format_id', and 'title' as query parameters.
    """
    url = request.args.get('url')
    format_id = request.args.get('format_id')
    title = request.args.get('title', 'video')
    
    if not url or not format_id:
        return "Missing URL or Format ID", 400

    # Format a clean filename for the user
    safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '.', '_', '-')).rstrip()
    filename = f"{safe_title}.mp4"

    def stream_video():
        """This function will be run as a generator to stream data."""
        # Command to run yt-dlp:
        # -f: format string (video + best audio, merge into mp4)
        # -o -: output to stdout (the pipe)
        command = [
            'yt-dlp',
            '-f', f'{format_id}+bestaudio/b',
            '--merge-output-format', 'mp4',
            '--no-playlist',
            '-o', '-',  # Critical: output to stdout
            url
        ]
        
        # Start the yt-dlp process
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Stream the stdout (the video data) chunk by chunk
        try:
            for chunk in iter(lambda: process.stdout.read(4096), b''):
                yield chunk
        finally:
            # Clean up the process when streaming is done or broken
            process.stdout.close()
            process.stderr.close()
            process.wait()

    # Create the streaming response
    return Response(stream_video(), 
                    mimetype='video/mp4', 
                    headers={
                        "Content-Disposition": f"attachment; filename=\"{filename}\""
                    })

# --- Web Frontend Serving ---

@app.route('/')
def index():
    """
    Serves the main index.html page from the 'templates' folder.
    """
    return render_template('index.html')

# --- Run the App ---
if __name__ == '__main__':
    # Host='0.0.0.0' makes it accessible on network
    app.run(debug=True, host='0.0.0.0', port=5000)