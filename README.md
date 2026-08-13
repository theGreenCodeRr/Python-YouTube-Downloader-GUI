# 🎥 Self-Hosted YouTube Downloader Web App

A modern, fast, and robust self-hosted web application for downloading YouTube videos. Built with **Python (FastAPI)**, **yt-dlp**, and a clean vanilla HTML/CSS/JS frontend.

## ✨ Features

* **Self-Hosted Web GUI:** Access the downloader from any device on your network via a browser.
* **Format Selection:** Fetch a video URL and choose your exact preferred resolution and format.
* **Background Processing:** The server downloads the video asynchronously without blocking the UI, providing real-time status polling.
* **Modern UI:** Clean, responsive interface with a built-in toggle for Dark Mode / Light Mode.
* **Automated Cleanup:** Automatically purges temporary video files from the server after they are downloaded to your device, and includes a 24-hour fallback cleanup scheduler to conserve disk space.
* **CI/CD Ready:** Includes a GitHub Actions workflow to automatically deploy to a self-hosted runner.

---

## 🚀 Quick Start (Docker)

The easiest way to run the application is using Docker and Docker Compose.

### 1. Build and Run
Open your terminal in the project directory and run:

```bash
docker-compose up --build -d
```

### 2. Access the App
Open your web browser and navigate to:
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

## 🔄 Deployment (GitHub Actions)

This repository is configured with a continuous deployment workflow. 
When you push code to the `main` branch, the `.github/workflows/deploy.yml` action will trigger.
Ensure your target server is configured as a `self-hosted` runner in your GitHub repository settings to automatically pull and deploy the latest Docker containers.