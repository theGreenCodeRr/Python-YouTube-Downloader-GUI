# 🎥 Self-Hosted YouTube Downloader Web App v2

A modern, fast, and robust self-hosted web application for downloading YouTube videos, built with **Python (FastAPI)**, **yt-dlp**, and a clean HTML/CSS/JS frontend.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.11%2B-blue)
![Docker](https://img.shields.io/badge/docker-ready-blue)

---

## 🌐 Live Demo

You can test the functionality of this application before installing it yourself:
👉 **[Test the Live Demo Here](https://yt.quantumsofts.com/)**

---

## ✨ Features (v2)

* **Modern UI with Thumbnails:** A beautiful, responsive interface featuring Dark Mode support, video thumbnails, and a clean side-by-side layout.
* **Download History:** A built-in "Recent Downloads" panel keeps track of your ongoing and past downloads directly in the browser.
* **Advanced Audio Extraction:** Download videos directly as high-quality audio files (**MP3**, **Lossless WAV**, or **Lossless FLAC**) via server-side FFmpeg processing.
* **Visual Playlist Support:** Paste a YouTube playlist URL to render a clean list of videos. Click any video to instantly queue it up individually, ensuring server stability.
* **Anti-IP Block Support:** Seamlessly supports `cookies.txt` for bypassing YouTube IP blocks (frequent for VPS/Data Center deployments).
* **Automated Cleanup:** Automatically purges temporary video files from the server after they are downloaded to your device, backed by a 24-hour fallback cleanup scheduler.
* **Self-Updating Base:** Automated weekly GitHub Actions rebuild the `yt-dlp` master branch to ensure extractors are always up to date with YouTube API changes.

---

## 🚀 Quick Start (Docker)

The easiest way to run the application is using Docker and Docker Compose.

### 1. Build and Run
Open your terminal in the project directory and run:

```bash
docker compose up --build -d
```

### 2. Access the App
Open your web browser and navigate to the application (default port is `8000`):
```
http://localhost:8000
```

---

## 🛠 Manual Installation (Without Docker)

If you prefer to run it directly on your machine:

### 1. Install Dependencies
Make sure you have Python 3.11+ and `ffmpeg` installed on your system.

```bash
pip install -r requirements.txt
```

### 2. Run the Server
```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

---

## 🍪 Bypassing YouTube Blocks (cookies.txt)

If your deployment server's IP address gets blocked by YouTube (e.g., throwing `KeyError('INNERTUBE_CONTEXT')` or "Failed to extract player response"):
1. Export a `cookies.txt` file from your desktop browser using an extension like *Get cookies.txt*.
2. Place the `cookies.txt` file directly in the root directory of this project.
3. Restart the server/container. The app will automatically detect and use it for all future extractions.

---

## 🔄 CI/CD & Auto-Updates

This repository is configured with two GitHub Actions:
- **Continuous Deployment (`deploy.yml`)**: Pushing to the `main` branch will automatically deploy the latest code to your self-hosted runner.
- **Weekly Auto-Update (`weekly-update.yml`)**: Rebuilds the Docker image every week without cache to pull the absolute latest bleeding-edge version of `yt-dlp` to prevent API breakages.