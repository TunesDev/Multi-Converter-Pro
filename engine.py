# engine.py
import os
import io
import subprocess
from pathlib import Path
from PIL import Image
import imageio_ffmpeg
import ffmpeg

IMG_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tiff", ".ico"}
VID_EXTS = {".mp4", ".mov", ".avi", ".mkv", ".webm", ".gif"}
AUD_EXTS = {".mp3", ".wav", ".aac", ".flac", ".ogg", ".m4a"}

class Engine:
    def __init__(self):
        self.output_dir = str(Path.home() / "Downloads" / "Converted_Files")
        Path(self.output_dir).mkdir(parents=True, exist_ok=True)
        
        # Add FFmpeg to PATH for the ffmpeg-python wrapper
        ffmpeg_dir = os.path.dirname(imageio_ffmpeg.get_ffmpeg_exe())
        os.environ["PATH"] += os.pathsep + ffmpeg_dir

    def convert(self, files, target_format, progress_callback=None):
        target_format = target_format.lower()
        total_files = len(files)
        success_count = 0

        def send_progress(current, total):
            if progress_callback:
                percent = int((current / total) * 100)
                progress_callback(percent)

        try:
            if target_format == "pdf":
                images = []
                for f in files:
                    img = Image.open(f['path'])
                    if img.mode != "RGB": img = img.convert("RGB")
                    buf = io.BytesIO()
                    img.save(buf, format="JPEG")
                    buf.seek(0)
                    images.append(Image.open(buf))
                if images:
                    out_name = files[0]['name'] + ".pdf"
                    out_path = Path(self.output_dir) / out_name
                    images[0].save(out_path, save_all=True, append_images=images[1:], resolution=100.0)
                    success_count = total_files
                    send_progress(total_files, total_files)

            elif target_format in ["png", "jpg", "webp"]:
                for i, f in enumerate(files):
                    img = Image.open(f['path'])
                    if target_format == "jpg" and img.mode in ("RGBA", "P"): img = img.convert("RGB")
                    out_name = f['name'] + f".{target_format}"
                    out_path = Path(self.output_dir) / out_name
                    if target_format == "jpg": img.save(out_path, "JPEG", quality=95)
                    else: img.save(out_path, target_format.upper())
                    success_count += 1
                    send_progress(i + 1, total_files)

            elif target_format in ["mp4", "mp3", "wav"]:
                ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
                for i, f in enumerate(files):
                    out_name = f['name'] + f".{target_format}"
                    out_path = Path(self.output_dir) / out_name
                    
                    try:
                        # We use direct subprocess instead of ffmpeg-python to ensure NO CMD WINDOW
                        cmd = [ffmpeg_exe, "-y", "-i", f['path'], str(out_path)]
                        if target_format == "mp3":
                            cmd.insert(3, "-vn")
                            cmd.extend(["-acodec", "libmp3lame"])
                        elif target_format == "wav":
                            cmd.insert(3, "-vn")
                            cmd.extend(["-acodec", "pcm_s16le"])

                        # THE MAGIC FLAG: This hides the CMD window
                        subprocess.run(
                            cmd, 
                            stdout=subprocess.DEVNULL, 
                            stderr=subprocess.DEVNULL, 
                            creationflags=subprocess.CREATE_NO_WINDOW
                        )
                        
                        if out_path.exists(): 
                            success_count += 1
                    except Exception as e:
                        print(f"FFmpeg error: {e}")
                        
                    send_progress(i + 1, total_files)

            if success_count > 0:
                return True, f"Successfully converted {success_count} files!"
            return False, "Conversion failed."
            
        except Exception as e:
            return False, str(e)
