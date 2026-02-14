# Nova Hub - Arquitectura

## Estructura de carpetas

```
YT-download/
├── main.py                          # Punto de entrada (Lanza NovaHub)
├── requirements.txt                 # Dependencias (PySide6, requests, etc.)
├── core/                            # Clases base y utilidades
│   ├── __init__.py
│   └── base_downloader.py          # Clase abstracta Downloader (Base para YT/TikTok)
├── downloaders/                     # Lógica de descarga (Backend)
│   ├── __init__.py
│   ├── youtube.py                  # YouTubeDownloader (yt-dlp)
│   └── tiktok.py                   # TikTokDownloader (API tikwm)
└── ui/                              # Interfaz gráfica (Frontend)
    ├── __init__.py
    ├── main.py                     # Ventana principal NovaHub y Sidebar
    ├── base_ui.py                  # Clase base PlatformUI para las vistas
    ├── youtube_ui.py               # Vista específica de YouTube
    ├── tiktok_ui.py                # Vista específica de TikTok
    └── qr_ui.py                    # Vista del generador de códigos QR
```

## Arquitectura de la UI

El proyecto utiliza un patrón de **Vistas Intercambiables** gestionadas por un `QStackedWidget` en `ui/main.py`:

1.  **NovaHub (ui/main.py)**: Administra el Sidebar, el Footer y el contenedor principal.
2.  **PlatformUI (ui/base_ui.py)**: Clase base que define el contrato para cualquier plataforma nueva (método `build()`).
3.  **QRUI (ui/qr_ui.py)**: Módulo independiente para generación de códigos QR (no hereda de PlatformUI al no ser un descargador).
4.  **Hilos de Descarga**: Tanto YouTube como TikTok ejecutan sus descargas en hilos separados (`QThread`) para evitar que la interfaz se congele.
5.  **Comunicación**: Se utilizan `Signals` y `Slots` de PySide6 para actualizar la UI (progreso, consola, metadatos) desde los hilos de descarga.

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
