import os
import re
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


def remove_emojis(text):
    """Elimina todos los emojis del texto"""
    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"  # emoticons
        "\U0001F300-\U0001F5FF"  # symbols & pictographs
        "\U0001F680-\U0001F6FF"  # transport & map symbols
        "\U0001F1E0-\U0001F1FF"  # flags (iOS)
        "\U00002702-\U000027B0"
        "\U000024C2-\U0001F251"
        "\U0001f926-\U0001f937"
        "\U00010000-\U0010ffff"
        "\u2640-\u2642"
        "\u2600-\u2B55"
        "\u200d"
        "\u23cf"
        "\u23e9"
        "\u231a"
        "\ufe0f"  # dingbats
        "\u3030"
        "]+",
        flags=re.UNICODE
    )
    return emoji_pattern.sub(r'', text)


def _progress_hook(d, callback=None, title_callback=None):
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
        # Cuando termina la descarga del video, mostrar "-" en el título
        if title_callback:
            title_callback('-')


class YouTubeDownloader(Downloader):
    """Descargador de contenido de YouTube"""
    
    def __init__(self):
        super().__init__("YouTube")
    
    def download_audio(self, url: str, output_path: str, progress_callback=None, title_callback=None):
        """Descarga audio desde YouTube"""
        try:
            # Primero extraer el título sin descargar
            ydl_opts_info = {
                'quiet': True,
                'no_warnings': True,
                'logger': YTDLPLogger(), # Silenciar errores crudos
            }

            with YoutubeDL(ydl_opts_info) as ydl:
                info = ydl.extract_info(url, download=False)
                original_title = info.get('title', 'audio')
                # Eliminar emojis del título
                original_title = remove_emojis(original_title)

            # Notificar el título de inmediato
            if title_callback:
                title_callback(original_title)

            # Verificar si existe ffmpeg localmente
            ffmpeg_local_path = os.path.join(os.getcwd(), 'ffmpeg', 'bin')
            ffmpeg_location = ffmpeg_local_path if os.path.exists(ffmpeg_local_path) else None

            # Ahora descargar
            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': os.path.join(output_path, f'{original_title}.%(ext)s'),
                'postprocessors': [
                    {'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '320'},
                    {'key': 'FFmpegMetadata'},
                ],
                'ffmpeg_location': ffmpeg_location,
                'noplaylist': True,
                'ignoreerrors': False,
                'progress_hooks': [lambda d: _progress_hook(d, callback=progress_callback, title_callback=title_callback)],
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
            
            # Limpieza de archivos residuales (.webm, .m4a, .part, .ytdl)
            if 'original_title' in locals() and original_title:
                try:
                    # Patrones comunes de archivos temporales o no convertidos
                    extensions_to_clean = ['.webm', '.m4a', '.mp4', '.part', '.ytdl']
                    
                    # Intentar borrar archivos que coincidan exactamente con el nombre base
                    base_filename = os.path.join(output_path, original_title)
                    
                    for ext in extensions_to_clean:
                        file_path = base_filename + ext
                        if os.path.exists(file_path):
                            try:
                                os.remove(file_path)
                                print(f"🧹 Eliminado residuo: {file_path}")
                            except OSError:
                                pass
                                
                    # Búsqueda más agresiva si el nombre fue modificado por yt-dlp
                    # (esto es opcional pero ayuda si yt-dlp saneó el nombre de otra forma)
                except Exception as cleanup_error:
                    print(f"⚠️ Error limpiando residuos: {cleanup_error}")
                    
            return False, ''
