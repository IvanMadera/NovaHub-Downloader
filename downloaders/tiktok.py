import os
import yt_dlp
from urllib.parse import urlparse
import re

from core.base_downloader import Downloader


class TikTokDownloader(Downloader):
    """Descargador de contenido de TikTok"""
    
    def __init__(self):
        super().__init__("TikTok")
    
    def _limpiar_url_tiktok(self, url: str) -> str:
        """Elimina parámetros extra de la URL de TikTok"""
        parsed_url = urlparse(url)
        clean_url = f"{parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path}"
        return clean_url
    
    def download_audio(self, url: str, output_path: str, progress_callback=None, title_callback=None):
        """Descarga video desde TikTok"""
        try:
            # Limpiar URL
            url_limpia = self._limpiar_url_tiktok(url)
            
            # Configurar opciones de descarga
            opciones = {
                'format': 'best',
                'outtmpl': os.path.join(output_path, '%(uploader)s_%(id)s.%(ext)s'),
                'quiet': False,
                'no_warnings': True,
                'progress_hooks': [lambda d: self._progress_hook(d, progress_callback, title_callback)],
            }
            
            # Descargar
            with yt_dlp.YoutubeDL(opciones) as ydl:
                info = ydl.extract_info(url_limpia, download=False)
                title = info.get('uploader', 'TikTok Video')
                
                # Llamar callback de título
                if title_callback:
                    title_callback(title)
                
                # Descargar
                ydl.download([url_limpia])
                print(f"✅ Descarga exitosa: {title}")
                return True, title
        
        except Exception as e:
            print(f"❌ Error al procesar {url}: {e}")
            return False, ''
    
    def _progress_hook(self, d, progress_callback=None, title_callback=None):
        """Hook para reporte de progreso"""
        if progress_callback:
            if d['status'] == 'downloading':
                percent = d.get('_percent_str', '0%')
                speed = d.get('_speed_str', '0B/s')
                eta = d.get('_eta_str', 'unknown')
                progress_callback(percent, speed, eta)
            elif d['status'] == 'finished':
                progress_callback('100%', '', '')
