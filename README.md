# 🎥 Python YouTube Downloader

A lightweight, modern desktop app for downloading YouTube videos. Built with Python, `tkinter`, and `yt-dlp`. 

## ✨ Features

* **Zero-Config Setup:** Automatically handles FFmpeg integration in the background for high-quality (1080p+) video/audio merging. No manual downloads required!
* **Resolution Selection:** Fetch a video URL and choose your exact preferred resolution and file size.
* **Modern UI:** Clean, responsive interface with a built-in toggle for Dark Mode / Light Mode.
* **Real-Time Tracking:** Live progress bar showing download speed, file size, and estimated time remaining.
* **Mac-Friendly:** Built-in patch to automatically bypass common macOS Python SSL certificate errors.

---

## 🚀 Quick Start

### 1. Install Dependencies
Open your terminal or command prompt and install the required Python libraries:

```bash
pip install yt-dlp sv-ttk imageio-ffmpeg
```

### 2. Run the App
Navigate to the folder containing the script and run:

```bash
python local_cli.py
```

### 🛠️ Note for Developers
macOS SSL Errors: If you modify the code and encounter [SSL: CERTIFICATE_VERIFY_FAILED] errors on a Mac, ensure the ssl._create_unverified_context lines remain at the top of local_cli.py to bypass local certificate restrictions.

Executable Packaging: Some files in this repository are reserved for future deployment (packaging the app into a standalone .exe or .app for servers). You only need local_cli.py to run the GUI.

### 📄 License
This project is licensed under the MIT License.