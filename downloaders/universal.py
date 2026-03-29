import os
from yt_dlp import YoutubeDL
from core.base_downloader import Downloader

class UniversalLogger:
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

class UniversalDownloader(Downloader):
    """Descargador de contenido Universal para cualquier sitio web usando yt-dlp"""
    
    def __init__(self):
        super().__init__("Universal")

    def get_video_info(self, url: str):
        """Extrae metadata extensa del video sin descargar, usando fallbacks seguros"""
        url = url.strip()
        
        try:
            ydl_opts_info = {
                'quiet': True,
                'no_warnings': True,
                'logger': UniversalLogger(),
            }

            with YoutubeDL(ydl_opts_info) as ydl:
                info = ydl.extract_info(url, download=False)
                
                title = info.get('title', 'Video Universal')
                author = info.get('uploader') or info.get('creator') or info.get('channel') or 'Desconocido'
                description = info.get('description', 'Sin descripción proporcionada por la web')
                duration = info.get('duration', 0)
                thumbnail = info.get('thumbnail')
                view_count = info.get('view_count', 0)
                timestamp = info.get('timestamp') or info.get('upload_date') or 0 # upload_date comes as YYYYMMDD
                filesize = info.get('filesize_approx') or info.get('filesize') or 0
                
                # Extract URL domain to show
                from urllib.parse import urlparse
                domain = urlparse(url).netloc
                
                return {
                    'title': title,
                    'author': author,
                    'description': description,
                    'duration': duration,
                    'thumbnail': thumbnail,
                    'view_count': view_count,
                    'timestamp': timestamp,
                    'filesize': filesize,
                    'domain': domain,
                    'download_url': url
                }

        except Exception as e:
            print(f"✖ Error obteniendo info Universal: {e}")
            return None

    def download_audio(self, url: str, output_path: str, progress_callback=None, title_callback=None):
        """Descarga el video universal usando yt-dlp al formato más estable y compatible."""
        try:
            ydl_opts_info = {
                'quiet': True,
                'no_warnings': True,
                'logger': UniversalLogger(),
            }

            with YoutubeDL(ydl_opts_info) as ydl:
                info = ydl.extract_info(url, download=False)
                title = info.get('title', 'Video_Universal')
                import re
                
                # Sanear título simple
                safe_title = "".join([c for c in title if c.isalpha() or c.isdigit() or c==' ' or c=='-' or c=='_']).rstrip()
                safe_title = re.sub(r'\s+', ' ', safe_title).strip()
                
                if not safe_title or len(safe_title) < 2:
                    import time
                    from urllib.parse import urlparse
                    domain = urlparse(url).netloc.replace('www.', '')
                    safe_title = f"{domain}_video_{int(time.time())}"

            if title_callback:
                title_callback(safe_title)

            # Para universal usamos mp4 de preferencia
            ydl_opts = {
                'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
                'outtmpl': os.path.join(output_path, f'{safe_title}.%(ext)s'),
                'merge_output_format': 'mp4',
                'noplaylist': True,
                'progress_hooks': [lambda d: _progress_hook(d, callback=progress_callback, title_callback=title_callback)],
                'logger': UniversalLogger(),
                'no_warnings': True,
                'quiet': True,
                'overwrites': True,
            }
            
            ffmpeg_local_path = os.path.join(os.getcwd(), 'ffmpeg', 'bin')
            if os.path.exists(ffmpeg_local_path):
                ydl_opts['ffmpeg_location'] = ffmpeg_local_path

            with YoutubeDL(ydl_opts) as ydl:
                ydl.extract_info(url, download=True)
                print(f"✓ Descarga Universal exitosa: {safe_title}")
                return True, safe_title
            
        except Exception as e:
            print(f"✖ Error procesando descarga Universal en {url}: {e}")
            return False, ''
