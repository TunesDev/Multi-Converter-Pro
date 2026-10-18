# engine.py
import os
import io
import sys
import subprocess
from pathlib import Path
from PIL import Image
import imageio_ffmpeg

IMG_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tiff", ".ico"}
VID_EXTS = {".mp4", ".mov", ".avi", ".mkv", ".webm", ".gif"}
AUD_EXTS = {".mp3", ".wav", ".aac", ".flac", ".ogg", ".m4a"}

class Engine:
    def __init__(self):
        self.output_dir = str(Path.home() / "Downloads" / "Converted_Files")
        Path(self.output_dir).mkdir(parents=True, exist_ok=True)

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
                try:
                    ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
                except Exception as e:
                    return False, f"Could not find FFmpeg engine: {e}"

                for i, f in enumerate(files):
                    out_name = f['name'] + f".{target_format}"
                    out_path = Path(self.output_dir) / out_name
                    
                    try:
                        # FIXED COMMAND ORDER: Input -> Format specific flags -> Output
                        cmd = [ffmpeg_exe, "-y", "-i", f['path']]
                        
                        if target_format == "mp3":
                            cmd.extend(["-vn", "-acodec", "libmp3lame", str(out_path)])
                        elif target_format == "wav":
                            cmd.extend(["-vn", "-acodec", "pcm_s16le", str(out_path)])
                        else:
                            cmd.append(str(out_path))

                        # Run FFmpeg
                        result = subprocess.run(
                            cmd, 
                            stdout=subprocess.PIPE, 
                            stderr=subprocess.PIPE, 
                            text=True,
                            creationflags=subprocess.CREATE_NO_WINDOW
                        )
                        
                        if out_path.exists(): 
                            success_count += 1
                        else:
                            # Print the actual FFmpeg error to the terminal for debugging
                            print(f"FFmpeg Error for {f['name']}:")
                            print(result.stderr[-500:]) # Print the last 500 chars of the error
                            
                    except Exception as e:
                        print(f"System Error: {e}")
                        
                    send_progress(i + 1, total_files)

            if success_count > 0:
                return True, f"Successfully converted {success_count} files!"
            return False, "Conversion failed. Check the files or try a different format."
            
        except Exception as e:
            return False, str(e)
