import os
import requests
import re
from urllib.parse import urlparse, parse_qs

from core.base_downloader import Downloader


class TikTokDownloader(Downloader):
    """Descargador de contenido de TikTok usando API externa"""
    
    def __init__(self):
        super().__init__("TikTok")
        self.api_url = "https://www.tikwm.com/api/"
    
    def _extract_video_id(self, url: str) -> str:
        """Extrae el ID del video de la URL de TikTok"""
        url = url.strip()
        
        # Patrón para URLs normales
        match = re.search(r'/video/(\d+)', url)
        if match:
            return match.group(1)
        
        # Si es short link, intentar resolverlo
        if 'vm.tiktok.com' in url or 'vt.tiktok.com' in url:
            try:
                response = requests.head(url, allow_redirects=True, timeout=10)
                final_url = response.url
                match = re.search(r'/video/(\d+)', final_url)
                if match:
                    return match.group(1)
            except:
                pass
        
        return None
    
    def get_video_info(self, url: str):
        """Extrae información del video sin descargar"""
        try:
            params = {
                'url': url,
                'hd': 1
            }
            
            response = requests.post(self.api_url, data=params, timeout=15)
            
            if response.status_code != 200:
                print(f"Error API: Status {response.status_code}")
                return None
            
            data = response.json()
            
            if data.get('code') != 0:
                print(f"Error API: {data.get('msg', 'Unknown error')}")
                return None
            
            video_data = data.get('data', {})
            
            # Calcular tamaño estimado (si hay datos)
            filesize = None
            if video_data.get('size'):
                filesize = video_data['size']
            
            return {
                'title': video_data.get('title', 'Sin título'),
                'author': video_data.get('author', {}).get('unique_id', 'Desconocido'),
                'duration': video_data.get('duration', 0),
                'thumbnail': video_data.get('cover', None),
                'filesize': filesize,
                'view_count': video_data.get('play_count', 0),
                'upload_date': video_data.get('create_time', 0),
                'width': video_data.get('width', 0),
                'height': video_data.get('height', 0),
                'download_url': video_data.get('hdplay', video_data.get('play', '')),
            }
            
        except Exception as e:
            print(f"Error obteniendo info: {e}")
            return None
    
    def download_audio(self, url: str, output_path: str, progress_callback=None, title_callback=None):
        """Descarga video desde TikTok"""
        try:
            # Obtener información del video
            info = self.get_video_info(url)
            
            if not info or not info.get('download_url'):
                print("✖ No se pudo obtener la URL de descarga")
                return False, ''
            
            author = info.get('author', 'tiktok_user')
            video_id = self._extract_video_id(url) or 'video'
            
            # Notificar título
            title = f"{author}_{video_id}"
            if title_callback:
                title_callback(title)
            
            # Descargar video
            download_url = info['download_url']
            
            if progress_callback:
                progress_callback(0.1)
            
            response = requests.get(download_url, stream=True, timeout=30)
            
            if response.status_code != 200:
                print(f"✖ Error al descargar: Status {response.status_code}")
                return False, ''
            
            # Obtener tamaño total
            total_size = int(response.headers.get('content-length', 0))
            
            # Guardar archivo
            filename = f"{author}_{video_id}.mp4"
            filepath = os.path.join(output_path, filename)
            
            downloaded = 0
            chunk_size = 8192
            
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=chunk_size):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        
                        # Actualizar progreso
                        if progress_callback and total_size > 0:
                            progress = downloaded / total_size
                            progress_callback(progress)
            
            if progress_callback:
                progress_callback(1.0)
            
            print(f"✓ Descarga exitosa: {filename}")
            return True, title
            
        except Exception as e:
            print(f"✖ Error al procesar {url}: {e}")
            return False, ''