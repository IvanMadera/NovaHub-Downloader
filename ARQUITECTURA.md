# Nova Hub - Arquitectura

## Estructura de carpetas

```
YT-download/
├── main.py                          # Punto de entrada
├── requirements.txt                 # Dependencias
├── assets/                          # Imágenes y recursos
│   └── NovaHub_title.png
├── core/                            # Clases base y utilidades
│   ├── __init__.py
│   └── base_downloader.py          # Clase abstracta Downloader
├── downloaders/                     # Implementaciones de descargadores
│   ├── __init__.py
│   ├── youtube.py                  # YouTubeDownloader
│   └── tiktok.py                   # TikTokDownloader (esqueleto)
└── ui/                              # Interfaz gráfica
    ├── __init__.py
    └── main.py                     # Clase NovaHub
```

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
