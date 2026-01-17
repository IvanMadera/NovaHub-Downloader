import os
from yt_dlp import YoutubeDL


class YTDLPLogger:
    def debug(self, msg):
        pass

    def info(self, msg):
        pass

    def warning(self, msg):
        pass

    def error(self, msg):
        pass


def _progress_hook(d, callback=None):
    status = d.get('status')
    if status == 'downloading':
        percent = d.get('_percent_str', '').strip()
        speed = d.get('_speed_str', '').strip()
        eta = d.get('_eta_str', '').strip()
        if callback:
            callback(percent, speed, eta)
    elif status == 'finished':
        if callback:
            callback('100%', '', '')


def download_youtube_audio(url, output_path, progress_callback=None, title_callback=None):
    try:
        # Primero extraer el título sin descargar
        ydl_opts_info = {
            'quiet': True,
            'no_warnings': True,
        }
        
        with YoutubeDL(ydl_opts_info) as ydl:
            info = ydl.extract_info(url, download=False)
            original_title = info.get('title', 'audio')
        
        # Notificar el título de inmediato
        if title_callback:
            title_callback(original_title)
        
        # Ahora descargar
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': os.path.join(output_path, '%(title)s.%(ext)s'),
            'postprocessors': [
                {'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '192'},
                {'key': 'FFmpegMetadata'},
            ],
            'noplaylist': True,
            'ignoreerrors': False,
            'progress_hooks': [lambda d: _progress_hook(d, callback=progress_callback)],
            'logger': YTDLPLogger(),
            'no_warnings': True,
            'quiet': True,
            'overwrites': True,
        }

        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            print(f"✅ Descarga exitosa: {original_title}")
            return True, original_title

    except Exception as e:
        print(f"❌ Error al procesar {url}: {e}")
        return False, None

