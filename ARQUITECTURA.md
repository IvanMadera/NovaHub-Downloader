# Nova Hub - Arquitectura

## Estructura de carpetas

```
YT-download/
├── main.py                          # Punto de entrada (Lanza NovaHub)
├── requirements.txt                 # Dependencias (PySide6, requests, etc.)
├── core/                            # Clases base y utilidades
│   ├── __init__.py
│   └── base_downloader.py          # Clase abstracta Downloader (Base para todos los módulos)
├── downloaders/                     # Lógica de descarga (Backend)
│   ├── __init__.py
│   ├── youtube.py                  # YouTubeDownloader (yt-dlp)
│   ├── tiktok.py                   # TikTokDownloader (API tikwm)
│   ├── facebook.py                 # FacebookDownloader (yt-dlp)
│   ├── twitter.py                  # TwitterDownloader (yt-dlp)
│   ├── instagram.py                # InstagramDownloader (instaloader)
│   ├── spotify.py                  # SpotifyDownloader (spotipy + mutagen)
│   └── universal.py                # UniversalDownloader (yt-dlp genérico)
└── ui/                              # Interfaz gráfica (Frontend)
    ├── __init__.py
    ├── main.py                     # Ventana principal NovaHub y Sidebar
    ├── base_ui.py                  # Clase base PlatformUI para las vistas
    ├── youtube_ui.py               # Vista específica de YouTube
    ├── tiktok_ui.py                # Vista específica de TikTok
    ├── facebook_ui.py              # Vista específica de Facebook
    ├── twitter_ui.py               # Vista específica de X/Twitter
    ├── instagram_ui.py             # Vista específica de Instagram
    ├── spotify_ui.py               # Vista específica de Spotify (búsqueda + cola)
    ├── universal_ui.py             # Vista Universal (motor yt-dlp genérico)
    └── qr_ui.py                    # Vista del generador de códigos QR
```

## Arquitectura de la UI

El proyecto utiliza un patrón de **Vistas Intercambiables** gestionadas por un `QStackedWidget` en `ui/main.py`:

1. **NovaHub (ui/main.py)**: Administra el Sidebar, el Footer y el contenedor principal. Los botones del sidebar se generan dinámicamente desde el diccionario `PLATFORMS`.
2. **PlatformUI (ui/base_ui.py)**: Clase base que define el contrato para cualquier plataforma nueva (método `build()`).
3. **QRUI (ui/qr_ui.py)**: Módulo para generación de códigos QR. Comparte el mismo design language pero con layout y lógica propios.
4. **Design Language Unificado**: Todas las vistas comparten la misma paleta (`BG_MAIN=#0E1116`, `BG_PANEL=#151A21`, `ACCENT=#3B5998`, `RADIUS=14px`) y los mismos estándares de tipografía (`Segoe UI`), scrollbars y botones.
5. **Hilos de Descarga**: Todos los módulos ejecutan descargas en hilos separados (`QThread`) con `threading.Lock` para escritura thread-safe en la consola.
6. **Comunicación**: Se utilizan `Signals` y `Slots` de PySide6 para actualizar la UI (progreso, consola, metadatos, vista previa) desde los hilos de descarga.

## Cómo agregar una nueva plataforma

1. Crear archivo en `downloaders/nueva_plataforma.py`:
```python
from core.base_downloader import Downloader

class NuevaPlataformaDownloader(Downloader):
    def __init__(self):
        super().__init__("Nueva Plataforma")
    
    def download_audio(self, url, output_path, progress_callback=None, title_callback=None):
        # Implementar lógica
        pass
```

2. Agregar en `ui/main.py` en el diccionario PLATFORMS:
```python
from downloaders.nueva_plataforma import NuevaPlataformaDownloader

PLATFORMS = {
    "YouTube": YouTubeDownloader(),
    "TikTok": TikTokDownloader(),
    "Nueva Plataforma": NuevaPlataformaDownloader(),
}
```

¡Listo! Los botones del sidebar se crearán automáticamente.

## Cómo funciona

- Todos los descargadores heredan de `Downloader` (clase base abstracta)
- La UI no está acoplada a ninguna plataforma específica
- Los botones del sidebar se generan dinámicamente desde el diccionario PLATFORMS
- El mismo código maneja cualquier plataforma
