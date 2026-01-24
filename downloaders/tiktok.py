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
        """
        Normaliza URLs de TikTok de cualquier formato.
        Maneja: web, mobile, short links, etc.
        """
        url = url.strip()
        
        # Si es una short URL (vm.tiktok.com o vt.tiktok.com), deja que yt-dlp la resuelva
        if 'vm.tiktok.com' in url or 'vt.tiktok.com' in url:
            return url
        
        # Normalizar diferentes dominios a www.tiktok.com
        url = url.replace('m.tiktok.com', 'www.tiktok.com')
        url = url.replace('mobile.tiktok.com', 'www.tiktok.com')
        
        # Eliminar parámetros de query innecesarios pero mantener el path
        parsed_url = urlparse(url)
        clean_url = f"{parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path}"
        
        return clean_url
    
    def get_video_info(self, url: str):
        """Extrae información del video sin descargar"""
        try:
            url_limpia = self._limpiar_url_tiktok(url)
            
            opciones = {
                'quiet': True,
                'no_warnings': True,
                'skip_download': True,
            }
            
            with yt_dlp.YoutubeDL(opciones) as ydl:
                info = ydl.extract_info(url_limpia, download=False)
                
                return {
                    'title': info.get('title', 'Sin título'),
                    'author': info.get('uploader', 'Autor desconocido'),
                    'duration': info.get('duration', 0),
                    'thumbnail': info.get('thumbnail', None),
                    'filesize': info.get('filesize', None),
                }
        except Exception as e:
            return None
    
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
                'progress_hooks': [lambda d: self._progress_hook(d, progress_callback)],
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
                return True, title
        
        except Exception as e:
            print(f"❌ Error al procesar {url}: {e}")
            return False, ''
    
    def _progress_hook(self, d, progress_callback=None):
        """Hook para reporte de progreso"""
        if progress_callback:
            if d['status'] == 'downloading':
                percent = d.get('_percent_str', '0%').strip()
                # Extraer valor numérico del porcentaje
                match = re.search(r'[\d.]+', percent)
                if match:
                    percent_value = float(match.group()) / 100
                else:
                    percent_value = 0
                progress_callback(percent_value)
            elif d['status'] == 'finished':
                progress_callback(1.0)
