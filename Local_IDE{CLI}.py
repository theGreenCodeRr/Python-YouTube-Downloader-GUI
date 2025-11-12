import tkinter as tk
from tkinter import ttk, messagebox, font, filedialog
import yt_dlp
import threading
import os
import sv_ttk   

class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Video Downloader")
        self.root.minsize(600, 550) 
        
        # --- Main layout frame ---
        main_frame = ttk.Frame(root, padding="15 15 15 15")
        main_frame.pack(expand=True, fill='both')

        # --- 2. URL Entry ---
        url_frame = ttk.Frame(main_frame)
        url_frame.pack(fill='x', pady=5)
        
        url_label = ttk.Label(url_frame, text="Paste Video URL:")
        url_label.pack(side='left', padx=5)
        
        self.url_entry = ttk.Entry(url_frame)
        self.url_entry.pack(side='left', fill='x', expand=True, padx=5)
        
        self.fetch_button = ttk.Button(url_frame, text="Fetch Formats", command=self.start_fetch_thread)
        self.fetch_button.pack(side='left', padx=5)

        # --- 3. Save Location (NEW) ---
        save_frame = ttk.Frame(main_frame)
        save_frame.pack(fill='x', pady=5)
        
        save_label = ttk.Label(save_frame, text="Save To:")
        save_label.pack(side='left', padx=5)
        
        # Use a StringVar to link the path to the Entry
        self.output_path_var = tk.StringVar()
        
        # Set the default path (where the script is)
        default_path = os.path.dirname(os.path.realpath(__file__))
        self.output_path_var.set(default_path)
        
        # The Entry field to show the path
        self.path_entry = ttk.Entry(save_frame, textvariable=self.output_path_var, state="readonly")
        self.path_entry.pack(side='left', fill='x', expand=True, padx=5)
        
        self.browse_button = ttk.Button(save_frame, text="Browse...", command=self.select_save_location)
        self.browse_button.pack(side='left', padx=5)

        # --- 4. Format Listbox ---
        list_label = ttk.Label(main_frame, text="Select a format to download:")
        list_label.pack(fill='x', pady=(10, 5))
        
        list_frame = ttk.Frame(main_frame)
        list_frame.pack(fill='both', expand=True)

        scrollbar = ttk.Scrollbar(list_frame, orient='vertical')
        
        mono_font = font.Font(family="Courier", size=10)
        self.format_listbox = tk.Listbox(list_frame, height=15, yscrollcommand=scrollbar.set, font=mono_font)
        
        scrollbar.config(command=self.format_listbox.yview)
        
        scrollbar.pack(side='right', fill='y')
        self.format_listbox.pack(side='left', fill='both', expand=True)
        
        self.available_formats = []

        # --- 5. Button Frame ---
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(pady=10, fill='x')

        self.download_button = ttk.Button(button_frame, text="Download Selected", command=self.start_download_thread)
        self.download_button.pack(side='left', fill='x', expand=True, padx=(0, 5))
        
        self.open_folder_button = ttk.Button(button_frame, text="Open Folder", command=self.open_download_folder)
        self.open_folder_button.pack(side='left', fill='x', expand=True, padx=(5, 5))
        
        # --- Theme Toggle Button (NEW) ---
        self.dark_mode = tk.BooleanVar(value=True) # Default to dark
        theme_toggle = ttk.Checkbutton(button_frame, text="Dark Mode", variable=self.dark_mode, command=self.toggle_theme, style="Switch.TCheckbutton")
        theme_toggle.pack(side='left', padx=10)


        # --- 6. Progress Bar & Status ---
        progress_frame = ttk.Frame(main_frame)
        progress_frame.pack(fill='x', pady=5)
        
        self.progress_bar = ttk.Progressbar(progress_frame, orient='horizontal', mode='determinate')
        self.progress_bar.pack(fill='x', expand=True)
        
        self.progress_label = ttk.Label(progress_frame, text="", anchor='center')
        self.progress_label.pack(fill='x', expand=True, pady=5)

        # --- 7. Status Bar ---
        self.status_label = ttk.Label(root, text="Status: Ready", relief="sunken", anchor="w", padding="5 2")
        self.status_label.pack(side="bottom", fill="x")

        # Set the initial theme when the app starts
        self.toggle_theme()

    # --- FUNCTION for the "Browse..." button ---
    def select_save_location(self):
        new_path = filedialog.askdirectory(initialdir=self.output_path_var.get())
        if new_path: # Only update if the user selected a folder
            self.output_path_var.set(new_path)

    # --- FUNCTION for the Theme Toggle ---
    def toggle_theme(self):
        if self.dark_mode.get():
            sv_ttk.set_theme("dark")
        else:
            sv_ttk.set_theme("light")

    # --- "Open Folder" function ---
    def open_download_folder(self):
        try:
            path_to_open = self.output_path_var.get()
            os.startfile(path_to_open)
        except FileNotFoundError:
            messagebox.showerror("Error", f"Could not find the folder:\n{path_to_open}")
        except Exception as e:
            messagebox.showerror("Error", f"Could not open folder:\n{e}")

    # --- Helper functions ---
    @staticmethod
    def format_bytes(b):
        if b is None: return "0 B"
        if b < 1024: return f"{b} B"
        elif b < 1024**2: return f"{b/1024:.1f} KiB"
        elif b < 1024**3: return f"{b/1024**2:.1f} MiB"
        else: return f"{b/1024**3:.1f} GiB"

    @staticmethod
    def format_seconds(s):
        if s is None: return "--:--"
        try: m, s = divmod(int(s), 60); h, m = divmod(m, 60); return f"{h:d}:{m:02d}:{s:02d}" if h else f"{m:d}:{s:02d}"
        except Exception: return "--:--"

    def update_status(self, text):
        self.status_label.config(text=f"Status: {text}")

    def clear_progress(self):
        self.progress_label.config(text="")
        self.progress_bar['value'] = 0

    def start_fetch_thread(self):
        self.update_status("Fetching...")
        self.fetch_button.config(state="disabled")
        self.browse_button.config(state="normal")
        self.download_button.config(state="normal")
        self.open_folder_button.config(state="normal")
        self.format_listbox.delete(0, 'end')
        self.available_formats = []
        self.clear_progress()
        
        thread = threading.Thread(target=self.fetch_formats)
        thread.start()

    def fetch_formats(self):
        url = self.url_entry.get()
        if not url:
            messagebox.showerror("Error", "Please paste a URL first.")
            self.update_status("Error: No URL")
            self.fetch_button.config(state="normal")
            return

        ydl_opts = {'quiet': True}
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                
            for f in info.get('formats', []):
                if f.get('vcodec', 'none') != 'none':
                    ext = f.get('ext', '?').ljust(5)
                    res = f.get('resolution', 'audio').ljust(10)
                    filesize_mb = f.get('filesize') or f.get('filesize_approx')
                    
                    if filesize_mb: filesize_str = f"{filesize_mb / (1024*1024):.1f} MB".rjust(10)
                    else: filesize_str = "Unknown MB".rjust(10)

                    desc = f"{res} | {ext} | {filesize_str} | {f.get('format_note', '')}"
                    self.format_listbox.insert('end', desc)
                    self.available_formats.append(f['format_id'])
            
            self.update_status(f"Found {len(self.available_formats)} formats for '{info.get('title', 'video')}'")
        except Exception as e:
            messagebox.showerror("Error", f"Could not fetch formats:\n{e}")
            self.update_status("Error fetching.")
        
        self.fetch_button.config(state="normal")

    # --- Progress Hook ---
    def progress_hook(self, d):
        if d['status'] == 'downloading':
            total_bytes = d.get('total_bytes') or d.get('total_bytes_estimate')
            downloaded_bytes = d.get('downloaded_bytes', 0)
            speed = d.get('speed')
            eta = d.get('eta')
            percent_value = 0.0
            if total_bytes: percent_value = (downloaded_bytes / total_bytes) * 100
            downloaded_str = self.format_bytes(downloaded_bytes)
            total_str = self.format_bytes(total_bytes)
            speed_str = f"{self.format_bytes(speed)}/s" if speed else "..."
            eta_str = self.format_seconds(eta) if eta else "..."
            display_text = f"{percent_value:.1f}%  •  {downloaded_str} / {total_str}  •  {speed_str}  •  ETA: {eta_str}"
            self.root.after(0, self._update_progress_display, percent_value, display_text)
        elif d['status'] == 'finished':
            self.root.after(0, self._update_progress_display, 100, "Download complete, processing file...")
        elif d['status'] == 'error':
             self.root.after(0, self.progress_label.config, text="An error occurred during download.")

    def _update_progress_display(self, percent_value, text):
        self.progress_bar['value'] = percent_value
        self.progress_label.config(text=text)
    # ---------------------------------------------------

    # --- disable/enable buttons ---
    def start_download_thread(self):
        self.update_status("Downloading...")
        self.download_button.config(state="disabled")
        self.open_folder_button.config(state="disabled")
        self.fetch_button.config(state="disabled")
        self.browse_button.config(state="disabled") # Disable browse
        self.clear_progress()
        
        thread = threading.Thread(target=self.download_video)
        thread.start()

    # --- UPDATED to use new path variable ---
    def download_video(self):
        try:
            selected_index = self.format_listbox.curselection()[0]
            format_id = self.available_formats[selected_index]
        except IndexError:
            messagebox.showwarning("Warning", "Please select a format from the list first.")
            self.update_status("Ready")
            # Re-enable buttons
            self.download_button.config(state="normal")
            self.open_folder_button.config(state="normal")
            self.fetch_button.config(state="normal")
            self.browse_button.config(state="normal")
            return

        url = self.url_entry.get()
        
        # --- GET PATH FROM THE NEW VARIABLE ---
        output_path = self.output_path_var.get()
        output_template = os.path.join(output_path, '%(title)s - %(resolution)s.%(ext)s')
        
        ydl_opts = {
            'format': f'{format_id}+bestaudio/b', 
            'progress_hooks': [self.progress_hook],
            'outtmpl': output_template,
            'noplaylist': True,
            'nocolor': True,
        }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            
            self.update_status("Download Complete!")
            self.root.after(0, lambda: self.progress_label.config(text="Download Complete!"))
            messagebox.showinfo("Success", f"Video download finished!\nSaved to: {output_path}")
            
        except Exception as e:
            self.update_status(f"Error: {e}")
            self.root.after(0, lambda: self.progress_label.config(text="Download Failed."))
            messagebox.showerror("Error", f"Download failed:\n{e}")
            
        finally:
            # Re-enable all buttons
            self.download_button.config(state="normal")
            self.open_folder_button.config(state="normal")
            self.fetch_button.config(state="normal")
            self.browse_button.config(state="normal")

# --- Run the App ---
if __name__ == "__main__":
    main_root = tk.Tk()
    
    # App class now handles setting the theme
    app = App(main_root)
    main_root.mainloop()

#https://www.youtube.com/watch?v=8MmkaCjdvLs&list=PLXcxsShHm753dPX7JXvqVCvQNgTUQmwSM&index=1