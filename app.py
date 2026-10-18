# app.py
import webview
import os
import sys
import requests
from pathlib import Path
from engine import Engine

# --- CONFIG ---
CURRENT_VERSION = "1.1.0"
# IMPORTANT: Replace "TunesDev" and "ConvertFlow" with your actual GitHub username and repo name
VERSION_URL = "https://raw.githubusercontent.com/TunesDev/Multi-Converter-Pro/main/version.txt"
DOWNLOAD_URL = "https://github.com/TunesDev/Multi-Converter-Pro/releases"
# --------------

def get_html_path():
    if getattr(sys, 'frozen', False):
        base_path = Path(sys._MEIPASS)
    else:
        base_path = Path(__file__).parent
    return str(base_path / "index.html")

class API:
    def __init__(self):
        self.engine = Engine()
        self._window = None

    def set_window(self, window):
        self._window = window

    def check_updates(self):
        try:
            response = requests.get(VERSION_URL, timeout=5)
            if response.status_code == 200:
                latest_version = response.text.strip()
                if latest_version != CURRENT_VERSION:
                    return True, latest_version, DOWNLOAD_URL
            return False, CURRENT_VERSION, ""
        except Exception:
            return False, "Error connecting to server", ""

    def convert_files(self, files, target_format):
        def progress_cb(percent):
            if self._window:
                self._window.evaluate_js(f"window.updateProgress({percent})")
        success, msg = self.engine.convert(files, target_format, progress_callback=progress_cb)
        return success, msg

    def open_file_dialog(self):
        if not self._window: return []
        file_types = ('Supported Files (*.jpg;*.jpeg;*.png;*.webp;*.mp4;*.mov;*.mp3;*.wav)', 'All files (*.*)')
        result = self._window.create_file_dialog(webview.FileDialog.OPEN, allow_multiple=True, file_types=file_types)
        return result if result else []

    def open_folder_dialog(self):
        if not self._window: return None
        result = self._window.create_file_dialog(webview.FileDialog.FOLDER)
        if result:
            self.engine.output_dir = result[0]
            return result[0]
        return None

    def open_output_folder(self):
        if os.path.exists(self.engine.output_dir):
            os.startfile(self.engine.output_dir)

    def close_app(self):
        if self._window:
            self._window.destroy()

def bind_drag_drop(window):
    def on_drop(e):
        files = e['dataTransfer']['files']
        if not files: return
        paths = [f.get('pywebviewFullPath') for f in files if f.get('pywebviewFullPath')]
        if paths:
            window.evaluate_js(f"window.processDroppedFiles({paths})")
    window.dom.document.events.drop += on_drop

if __name__ == "__main__":
    api = API()
    html_path = get_html_path()
    
    window = webview.create_window(
        title="ConvertFlow Pro", 
        url=html_path, 
        js_api=api,
        width=1000, 
        height=750,
        background_color="#09090B",
        frameless=True, 
        easy_drag=True 
    )
    api.set_window(window)
    
    try:
        webview.start(bind_drag_drop, window)
    except Exception as e:
        print(f"App closed: {e}")
