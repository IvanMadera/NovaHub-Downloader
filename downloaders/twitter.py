import os
from yt_dlp import YoutubeDL
from core.base_downloader import Downloader

class YTDLPLogger:
    def debug(self, msg): pass
    def info(self, msg): pass
    def warning(self, msg): pass
    def error(self, msg): pass

def _progress_hook(d, callback=None, title_callback=None):
    status = d.get('status')
    if status == 'downloading':
        percent = d.get('_percent_str', '').strip()
        try:
            percent_val = float(percent.replace('%', '').strip()) / 100.0
        except ValueError:
            percent_val = 0.0
            
        if callback:
            callback(percent_val)
            
    elif status == 'finished':
        if callback:
            callback(1.0)
        if title_callback:
            title_callback('-')

class TwitterDownloader(Downloader):
    """Descargador de contenido de X (Twitter) usando yt-dlp"""
    
    def __init__(self):
        super().__init__("Twitter")

    def get_video_info(self, url: str):
        """Extrae metadata extensa del video de X (Twitter) sin descargar"""
        url = url.strip()
        
        try:
            ydl_opts_info = {
                'quiet': True,
                'no_warnings': True,
                'logger': YTDLPLogger(),
            }

            with YoutubeDL(ydl_opts_info) as ydl:
                info = ydl.extract_info(url, download=False)
                
                title = info.get('title', 'Video de X (Twitter)')
                author = info.get('uploader', 'Usuario de X (Twitter)')
                description = info.get('description', 'Sin descripción')
                duration = info.get('duration', 0)
                thumbnail = info.get('thumbnail')
                view_count = info.get('view_count', 0)
                timestamp = info.get('timestamp', 0)
                filesize = info.get('filesize_approx') or info.get('filesize') or 0
                
                return {
                    'title': title,
                    'author': author,
                    'description': description,
                    'duration': duration,
                    'thumbnail': thumbnail,
                    'view_count': view_count,
                    'timestamp': timestamp,
                    'filesize': filesize,
                    'download_url': url
                }

        except Exception as e:
            print(f"✖ Error obteniendo info de X (Twitter): {e}")
            return None

    def download_audio(self, url: str, output_path: str, progress_callback=None, title_callback=None):
        """Descarga el video de X (Twitter) usando yt-dlp."""
        try:
            ydl_opts_info = {
                'quiet': True,
                'no_warnings': True,
                'logger': YTDLPLogger(),
            }

            with YoutubeDL(ydl_opts_info) as ydl:
                info = ydl.extract_info(url, download=False)
                title = info.get('title', 'Video_X')
                import re
                
                clean_title = re.sub(r'[\d\,\.]+[KMkm]?\s+(views?|reactions?|likes?)\s*', '', title, flags=re.IGNORECASE)
                safe_title = "".join([c for c in clean_title if c.isalpha() or c.isdigit() or c==' ']).rstrip()
                safe_title = re.sub(r'\s+', ' ', safe_title).strip()
                
                if not safe_title:
                    import time
                    safe_title = f"TwitterVideo_{int(time.time())}"

            if title_callback:
                title_callback(safe_title)

            ydl_opts = {
                'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
                'outtmpl': os.path.join(output_path, f'{safe_title}.%(ext)s'),
                'merge_output_format': 'mp4',
                'noplaylist': True,
                'progress_hooks': [lambda d: _progress_hook(d, callback=progress_callback, title_callback=title_callback)],
                'logger': YTDLPLogger(),
                'no_warnings': True,
                'quiet': True,
                'overwrites': True,
            }
            
            ffmpeg_local_path = os.path.join(os.getcwd(), 'ffmpeg', 'bin')
            if os.path.exists(ffmpeg_local_path):
                ydl_opts['ffmpeg_location'] = ffmpeg_local_path

            with YoutubeDL(ydl_opts) as ydl:
                ydl.extract_info(url, download=True)
                print(f"✓ Descarga exitosa: {safe_title}.mp4")
                return True, safe_title
            
        except Exception as e:
            print(f"✖ Error procesando descarga en X (Twitter) {url}: {e}")
            return False, ''
