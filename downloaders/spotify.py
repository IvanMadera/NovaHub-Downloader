import os
import requests
import re
import string
from yt_dlp import YoutubeDL
from core.base_downloader import Downloader
from ytmusicapi import YTMusic
from mutagen.id3 import ID3, TIT2, TPE1, TALB, APIC
from mutagen.mp3 import MP3

class SpotifyLogger:
    def debug(self, msg): pass
    def info(self, msg): pass
    def warning(self, msg): pass
    def error(self, msg): pass

def clean_filename(name):
    """Limpia el nombre de la canción para que sea un ID seguro en Windows"""
    valid_chars = f"-_.() {string.ascii_letters}{string.digits}áéíóúÁÉÍÓÚñÑ"
    cleaned = ''.join(c for c in name if c in valid_chars)
    return re.sub(r'\s+', ' ', cleaned).strip()

class SpotifyDownloader(Downloader):
    """
    Descargador de música avanzado (Híbrido)
    Busca metadatos exactos en Spotify y los inyecta en descargas de alta calidad (.mp3) buscando el audio de forma oculta en YouTube Music.
    """
    
    def __init__(self):
        super().__init__("Spotify")
        self.ytm = YTMusic()

    def search_track(self, query):
        """Consulta pura en bases de datos de música (YT Music Studio) que reemplaza Spotify Web bloqueado"""
        try:
            # 1er filtro: Solo buscamos "songs" (pistas de estudio), excluyendo videoclips musicales oficiales
            raw_results = self.ytm.search(query, filter="songs", limit=15)
            clean_results = []
            
            for item in raw_results:
                # Extraer título
                title = item.get('title', 'Unknown')
                
                # Extraer el string de artistas limpios
                artists_list = [a.get('name') for a in item.get('artists', []) if a.get('name')]
                artists = ", ".join(artists_list) if artists_list else "Unknown Artist"
                
                # Extraer álbum o disco
                album = item.get('album', {})
                album_name = album.get('name', 'Single / Unknown Album') if album else 'Single'
                
                # Extraer cover art y FORZAR Resolución Máxima 1080x1080
                thumbnails = item.get('thumbnails', [])
                cover_url = thumbnails[-1]['url'] if thumbnails else None
                if cover_url and '=' in cover_url:
                    cover_url = cover_url.split('=')[0] + "=w1080-h1080-l90-rj"
                
                # Extraer ID inmutable para yt-dlp
                video_id = item.get('videoId')
                if not video_id:
                    continue
                    
                # Duración
                duration_str = item.get('duration', '0:00')
                try:
                    parts = duration_str.split(':')
                    dur_ms = (int(parts[0]) * 60 + int(parts[1])) * 1000
                except:
                    dur_ms = 0

                clean_results.append({
                    'title': title,
                    'artist': artists,
                    'album': album_name,
                    'cover_url': cover_url,
                    'duration_ms': dur_ms,
                    'id': video_id  # Guardamos el ID real ytmusic de la pista original
                })
                
            return clean_results
        except Exception as e:
            print(f"Error en Búsqueda de Música: {e}")
            return []

    def download_audio(self, url, output_path, progress_callback=None, title_callback=None):
        """Override obligatorio de la clase base. En Spotify se usa download_audio_with_tags."""
        return False, "Método obsoleto para Spotify downloader"

    def download_audio_with_tags(self, track_data, output_path, progress_callback=None):
        """
        Descarga el audio y luego le inserta los metadatos de 'track_data' usando Mutagen.
        """
        title = clean_filename(track_data['title'])
        artist = clean_filename(track_data['artist'])
        album = clean_filename(track_data['album'])
        cover_url = track_data.get('cover_url')
        
        # En lugar de usar búsqueda general, le pasamos el id "puro" oficial de música
        # Eso garantiza bajar la pista de estudio, no el videoclip sucio
        direct_url = f"https://music.youtube.com/watch?v={track_data['id']}"
        
        output_filepath = os.path.join(output_path, f"{artist} - {title}.mp3")
        
        # Opciones yt-dlp para sacar en mp3 puro a 192kbps (Buena fidelidad de Spotify)
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': output_filepath.replace('.mp3', '.%(ext)s'),
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'quiet': True,
            'no_warnings': True,
            'logger': SpotifyLogger()
        }
        
        # Progreso custom
        def _hook(d):
            if d['status'] == 'downloading':
                try:
                    p = d.get('_percent_str', '').replace('%','').strip()
                    if progress_callback: progress_callback(float(p)/100.0)
                except:
                    pass
            elif d['status'] == 'finished' and progress_callback:
                progress_callback(1.0)
                
        ydl_opts['progress_hooks'] = [_hook]
        
        ffmpeg_local_path = os.path.join(os.getcwd(), 'ffmpeg', 'bin')
        if os.path.exists(ffmpeg_local_path):
            ydl_opts['ffmpeg_location'] = ffmpeg_local_path

        try:
            with YoutubeDL(ydl_opts) as ydl:
                ydl.extract_info(direct_url, download=True)
                
            # === INYECCIÓN DE ID3 TAGS y COVER ART (MUTAGEN) ===
            if os.path.exists(output_filepath):
                try:
                    audio = MP3(output_filepath, ID3=ID3)
                    
                    if audio.tags is None:
                        audio.add_tags()
                        
                    # Título
                    audio.tags.add(TIT2(encoding=3, text=track_data['title']))
                    # Artista
                    audio.tags.add(TPE1(encoding=3, text=track_data['artist']))
                    # Álbum
                    audio.tags.add(TALB(encoding=3, text=track_data['album']))
                    
                    # Portada (APIC)
                    if cover_url:
                        try:
                            img_response = requests.get(cover_url, timeout=10)
                            if img_response.status_code == 200:
                                audio.tags.add(
                                    APIC(
                                        encoding=3,
                                        mime='image/jpeg',
                                        type=3, # Tipo 3 es Front Cover
                                        desc=u'Cover',
                                        data=img_response.content
                                    )
                                )
                        except Exception as img_e:
                            print(f"Warning cover: {img_e}")
                            
                    # Guardarlo en versión 2.3 explícitamente porque Windows Media Player 
                    # y el Explorador de Windows NO soportan el estándar Id3v2.4 por defecto.
                    audio.save(v2_version=3)
                    return True, f"{artist} - {title}.mp3"
                except Exception as tag_err:
                    print(f"La descarga funcionó pero falló el etiquetado MP3: {tag_err}")
                    return True, f"{artist} - {title}.mp3 (Sin tags)"
            else:
                return False, "No se generó el archivo de salida"
                
        except Exception as e:
            print(f"✖ Error fatal de descarga híbrida ({artist} - {title}): {e}")
            return False, str(e)
