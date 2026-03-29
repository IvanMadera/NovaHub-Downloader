import os
from yt_dlp import YoutubeDL
from core.base_downloader import Downloader


class YTDLPLogger:
    def debug(self, msg):
        pass

    def info(self, msg):
        pass

    def warning(self, msg):
        pass

    def error(self, msg):
        pass


def _progress_hook(d, callback=None, title_callback=None):
    status = d.get('status')
    if status == 'downloading':
        percent = d.get('_percent_str', '').strip()
        # Parsear porcentaje a un float 0.0-1.0 si es posible para callback estándar
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


class FacebookDownloader(Downloader):
    """Descargador de contenido de Facebook usando yt-dlp"""
    
    def __init__(self):
        super().__init__("Facebook")

    def get_video_info(self, url: str):
        """Extrae metadata del video de Facebook sin descargar"""
        url = url.strip()
        
        try:
            ydl_opts_info = {
                'quiet': True,
                'no_warnings': True,
                'logger': YTDLPLogger(),
            }

            with YoutubeDL(ydl_opts_info) as ydl:
                info = ydl.extract_info(url, download=False)
                
                title = info.get('title', 'Video de Facebook')
                author = info.get('uploader', 'Usuario de Facebook')
                description = info.get('description', 'Sin descripción')
                duration = info.get('duration', 0)
                thumbnail = info.get('thumbnail')
                view_count = info.get('view_count', 0)
                
                return {
                    'title': title,
                    'author': author,
                    'description': description,
                    'duration': duration,
                    'thumbnail': thumbnail,
                    'view_count': view_count,
                    'download_url': url # En yt-dlp, solo necesitas la URL original para descargar
                }

        except Exception as e:
            print(f"✖ Error obteniendo info de Facebook: {e}")
            return None

    def download_audio(self, url: str, output_path: str, progress_callback=None, title_callback=None):
        """Descarga el video de Facebook usando yt-dlp.
           (Nota: El método se llama download_audio por herencia obligada de Downloader actual,
            pero esto descarga Video MP4).
        """
        try:
            # Primero extraer el título sin descargar
            ydl_opts_info = {
                'quiet': True,
                'no_warnings': True,
                'logger': YTDLPLogger(),
            }

            with YoutubeDL(ydl_opts_info) as ydl:
                info = ydl.extract_info(url, download=False)
                title = info.get('title', 'Video_Facebook')
                import re
                
                # yt-dlp a veces incluye texto de vistas/reacciones en el título de Facebook ej: "X views X reactions"
                # Limpiamos esos patrones comunes
                clean_title = re.sub(r'[\d\,\.]+[KMkm]?\s+(views?|reactions?|likes?)\s*', '', title, flags=re.IGNORECASE)
                
                # Sanear título para archivos
                safe_title = "".join([c for c in clean_title if c.isalpha() or c.isdigit() or c==' ']).rstrip()
                # Colmamos múltiples espacios a uno solo
                safe_title = re.sub(r'\s+', ' ', safe_title).strip()
                
                if not safe_title:
                    import time
                    safe_title = f"FacebookVideo_{int(time.time())}"

            # Notificar título
            if title_callback:
                title_callback(safe_title)

            # Opciones de descarga para generar MP4 directamente 
            # Prioriza buena calidad y audio asegurado (Facebook suele separar audio/video con DASH)
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
            
            # Reintegrar ffmpeg_location si existe para fusionar formatos
            ffmpeg_local_path = os.path.join(os.getcwd(), 'ffmpeg', 'bin')
            if os.path.exists(ffmpeg_local_path):
                ydl_opts['ffmpeg_location'] = ffmpeg_local_path

            with YoutubeDL(ydl_opts) as ydl:
                ydl.extract_info(url, download=True)
                print(f"✓ Descarga exitosa: {safe_title}.mp4")
                return True, safe_title
            
        except Exception as e:
            print(f"✖ Error fatal procesando descarga en Facebook {url}: {e}")
            return False, ''
