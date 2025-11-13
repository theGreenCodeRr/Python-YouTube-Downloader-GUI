# Python YouTube Downloader GUI

A simple, modern GUI application for downloading YouTube videos with resolution selection and dark mode. Built with Python, `tkinter`, and `yt-dlp`.


## 📋 About The Project

This is a user-friendly desktop app that provides a clean interface for downloading YouTube videos. It uses `yt-dlp` as the backend to fetch video formats and manage the download process, and `tkinter` with the `sv-ttk` theme for the modern user interface.

The app automatically handles merging separate video and audio files (required for 1080p+ videos) as long as **FFmpeg** is present.

## ✨ Features

  * **Fetch Formats:** Paste any YouTube video URL and fetch all available resolutions.
  * **Resolution Selection:** Choose your preferred format from a clean list.
  * **Audio Merging:** Automatically downloads and merges the best audio stream with high-resolution video.
  * **Real-time Progress:** A dynamic progress bar shows percentage, download size, speed, and ETA.
  * **Theme Toggle:** A simple switch to toggle between Dark Mode and Light Mode.
  * **Custom Save Location:** A "Browse..." button lets you choose exactly where to save your file.
  * **Open Folder Button:** Quickly open the download folder directly from the app.

-----

## 🚀 Getting Started

Follow these instructions to get the application running on your local machine.

### 1\. Prerequisites (What you need)

This script has three key dependencies: two Python libraries and one external program.

  * **Python Libraries:**
      * `yt-dlp`: The core downloader that interacts with YouTube.
      * `sv-ttk`: The theme library for the modern dark/light mode GUI.
  * **External Program:**
      * `FFmpeg`: **This is required** for merging video and audio (especially for 1080p and higher).

### 2\. Installation

**A. Install Python Libraries**

Open your terminal or PowerShell and install the two required libraries using `pip`:

```bash
pip install yt-dlp
pip install sv-ttk
```

**B. Install FFmpeg** (optional)

`yt-dlp` needs `ffmpeg.exe` to combine video and audio.

1.  Download FFmpeg from [https://www.gyan.dev/ffmpeg/builds/](https://www.gyan.dev/ffmpeg/builds/) (get the "full" build).
2.  Unzip the file.
3.  Go into the `bin` folder and find `ffmpeg.exe` and `ffprobe.exe`.
4.  **Copy both `ffmpeg.exe` and `ffprobe.exe`** and paste them into the **same folder** as your `YT_downloder.py` script.

### 3\. Running the App

Once all requirements are installed, you can run the application from your terminal:

```bash
python local_cli.py
```
## ignore other files, those are for packaging the app into an executable in server soon 
-----

## 📄 License

This project is licensed under the MIT License.
