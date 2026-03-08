import os
import requests
import instaloader
import time

from core.base_downloader import Downloader

class InstagramDownloader(Downloader):
    """Descargador de contenido de Instagram usando instaloader y requests para la descarga final"""
    
    def __init__(self):
        super().__init__("Instagram")
        # Instanciar instaloader (sin login por ahora)
        self.L = instaloader.Instaloader(
            download_pictures=False,
            download_video_thumbnails=False,
            download_geotags=False,
            download_comments=False,
            save_metadata=False,
            compress_json=False
        )

    def _extract_shortcode(self, url: str) -> str:
        """Extrae el shortcode del video o reel de Instagram"""
        url = url.strip()
        
        # Eliminar query parameters ej. ?igsh=...
        if "?" in url:
            url = url.split("?")[0]
            
        # Remover trailing slash
        if url.endswith("/"):
            url = url[:-1]
            
        # Extraer el último componente de la URL (el shortcode)
        parts = url.split("/")
        if len(parts) > 0:
            shortcode = parts[-1]
            # Validar que no sea nada obvio o vacío
            if shortcode and shortcode not in ("reels", "reel", "p"):
                return shortcode
                
        return None

    def get_video_info(self, url: str):
        """Extrae información del video de Instagram sin descargar"""
        shortcode = self._extract_shortcode(url)
        if not shortcode:
            print("✖ No se pudo extraer el shortcode de la URL")
            return None
            
        try:
            # Obtener el Post instanciado con su metadata
            post = instaloader.Post.from_shortcode(self.L.context, shortcode)
            
            # Verificar si realmente es un video
            if not post.is_video:
                print("✖ El link provisto no corresponde a un video de Instagram")
                return None
            
            author = post.owner_username
            duration = post.video_duration or 0
            thumbnail_url = post.url # En Instaloader la thumbnail del post es el url base
            
            # Formatear la descripción
            description = post.caption or 'Sin descripción'
            
            # Visualizaciones
            view_count = post.video_view_count or 0
            
            # Fecha (UTC -> timestamp)
            upload_date = 0
            if post.date_utc:
                upload_date = int(post.date_utc.timestamp())

            download_url = post.video_url

            return {
                'title': f"{author}_{shortcode}",
                'author': author,
                'duration': duration,
                'thumbnail': thumbnail_url,
                'filesize': 0, # Difícil de saber sin HEAD request
                'view_count': view_count,
                'upload_date': upload_date,
                'width': 0,
                'height': 0,
                'download_url': download_url,
                'shortcode': shortcode
            }

        except Exception as e:
            print(f"✖ Error obteniendo info de Instagram: {e}")
            return None

    def get_images_info(self, url: str):
        """Extrae la información de todas las imágenes de un post o carrusel."""
        shortcode = self._extract_shortcode(url)
        if not shortcode:
            print("✖ No se pudo extraer el shortcode de la URL")
            return None
            
        try:
            post = instaloader.Post.from_shortcode(self.L.context, shortcode)
            author = post.owner_username
            images = []
            
            # Si es un sidecar (carrusel de múltiples fotos/videos)
            if post.typename == 'GraphSidecar':
                for i, node in enumerate(post.get_sidecar_nodes()):
                    if not node.is_video:
                        images.append({
                            'url': node.display_url,
                            'filename': f"{author}_{shortcode}_{i+1}.jpg"
                        })
            else:
                # Si es una sola foto
                if not post.is_video:
                    # Usamos .url que suele apuntar a la mejor calidad
                    images.append({
                        'url': post.url,
                        'filename': f"{author}_{shortcode}.jpg"
                    })
            
            return {
                'author': author,
                'shortcode': shortcode,
                'images': images
            }
            
        except Exception as e:
            print(f"✖ Error obteniendo imágenes de Instagram: {e}")
            return None

    def download_audio(self, url: str, output_path: str, progress_callback=None, title_callback=None):
        """Descarga el video de Instagram.
           (Nota: El método se llama download_audio por herencia obligada de Downloader actual,
            pero esto descarga Video MP4).
        """
        try:
            info = self.get_video_info(url)
            
            if not info or not info.get('download_url'):
                return False, ''

            author = info.get('author', 'instagram_user')
            shortcode = info.get('shortcode', 'video')
            
            # Notificar título
            title = f"{author}_{shortcode}"
            if title_callback:
                title_callback(title)
                
            download_url = info['download_url']
            
            if progress_callback:
                progress_callback(0.1)

            # Descarga real usando requests para poder mostrar el chunk_callback de progreso
            response = requests.get(download_url, stream=True, timeout=30)
            
            if response.status_code != 200:
                print(f"✖ Error al descargar (Requests): Status {response.status_code}")
                return False, ''

            total_size = int(response.headers.get('content-length', 0))
            
            # Nombrar archivo con extensión .mp4
            filename = f"{author}_{shortcode}.mp4"
            filepath = os.path.join(output_path, filename)
            
            downloaded = 0
            chunk_size = 8192
            
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=chunk_size):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        
                        if progress_callback and total_size > 0:
                            progress = downloaded / total_size
                            progress_callback(progress)
                            
            if progress_callback:
                progress_callback(1.0)
                
            print(f"✓ Descarga exitosa: {filename}")
            return True, title
            
        except Exception as e:
            print(f"✖ Error fatal procesando descarga en Instagram {url}: {e}")
            return False, ''
