# Changelog

Todos los cambios notables en este proyecto serán documentados en este archivo.

## [2026.2.8] - 2026-02-08

### 🎨 Mejoras Visuales

- **Iconos en Sidebar**: Implementación de iconos de texto Unicode para las plataformas:
  - YouTube: `▶`
  - TikTok: `♪`
- **Feedback Visual**: Mejora en los logs de consola para TikTok con iconos de estado (`➤`, `ℹ`, `↓`, `✔`, `✖`).

### 🔧 Mejoras Funcionales

- **Logs Detallados**: Habilitación de mensajes informativos en la consola de la UI de TikTok, permitiendo ver el progreso paso a paso (Inicio -> Info -> Descarga -> Resultado).

## [2026.1.31] - 2026-02-07

### ✨ Nueva Interfaz Gráfica (Nova Hub)

- **Migración a GUI**: El proyecto ahora cuenta con una interfaz gráfica moderna construida con **PySide6**.
- **Sidebar Dinámico**: Navegación lateral para cambiar entre plataformas (YouTube, TikTok).
- **Diseño Premium**: Paleta de colores consistente, bordes redondeados, animaciones sutiles y tipografía optimizada.
- **Multi-plataforma**: Soporte unificado para múltiples servicios de descarga bajo el mismo techo.

### 📱 Integración de TikTok

- **Descarga Directa**: Implementación completa de `TikTokDownloader` usando la API de tikwm.
- **Información del Video**: Visualización de metadatos (Autor, Fecha, Duración, Descripción).
- **Vista Previa**: Carga automática de la miniatura del video antes de descargar.
- **Progreso Real**: Barra de progreso vinculada al estado real de la descarga.

### 🔧 Mejoras y Refinamientos

- **Consola Inteligente**:
  - Filtro para mostrar solo éxitos (`✔`) y errores (`✖`).
  - Auto-limpiado de consola al iniciar una nueva descarga.
  - Botón de limpieza manual.
- **Gestión de Carpetas**: Selector de directorios nativo para elegir dónde guardar los archivos.
- **Sidebar Optimizado**: Reducción de tamaños de fuente y ajustes de espaciado para un balance visual profesional.
- **Thread-Safety**: Todas las descargas se ejecutan en hilos secundarios para mantener la fluidez de la UI.

## [Versión Anterior] - 2025-12-07

### ✨ Características Añadidas

- **Lectura automática de enlaces**: Lee URLs desde `links.txt` (un enlace por línea) en lugar de pedirlas por terminal
- **Formateo automático de nombres de archivo**:
  - Elimina caracteres especiales problemáticos
  - Convierte guiones bajos y guiones en espacios
  - Capitaliza cada palabra
  - Elimina emojis
  - Consolida espacios múltiples en espacios únicos
  - Preserva estructura "Artista / Canción" convirtiéndola a "Artista - Canción"

- **Logger personalizado**: Filtra warnings conocidos de `yt-dlp`:
  - Warnings de formatos `web_safari` / `SABR`
  - Warnings sobre falta de runtime JavaScript

- **Barra de progreso mejorada**: Muestra:
  - Porcentaje descargado
  - Velocidad de descarga
  - Tiempo estimado (ETA)
  - Nombre del archivo

- **Resumen final**: Al terminar todas las descargas, muestra:
  - Total de canciones procesadas
  - ✅ Estado de éxito con ruta completa (carpeta/nombre.mp3)
  - ❌ Estado de error para descargas fallidas

- **Verificación de dependencias**: Comprueba al inicio si `ffmpeg` está instalado

### 🔧 Mejoras

- Desactivación de `restrictfilenames` para permitir nombres personalizados
- Renombramiento de archivos después de la conversión a MP3
- Manejo mejorado de excepciones con mensajes claros
- Organización de código con funciones auxiliares bien documentadas

### 🐛 Correcciones

- Corregido problema de nombres con caracteres especiales que no se formateaban correctamente
- Solucionado issue donde la ruta no separaba correctamente carpeta/archivo
- Filtrado de warnings innecesarios que ensuciaban la salida
- Validación de archivos antes de renombrar para evitar conflictos

### 📋 Configuración

**Opciones de `yt-dlp` ajustadas:**

- `format`: `'bestaudio/best'` - Descarga el mejor audio disponible
- `postprocessors`: Convierte a MP3 con calidad 192kbps
- `ignoreerrors`: `False` - Muestra errores en lugar de ocultarlos
- `restrictfilenames`: `False` - Permite nombres personalizados
- `extractor_args`: `youtube:player_client=default` - Evita warnings de extractores

### 📦 Dependencias

- `yt-dlp` >= 2025.11.12
- `ffmpeg` (requerido para conversión a MP3)
- Python 3.6+

### 📝 Estructura del Proyecto

```
YT-download/
├── download.py          # Script principal
├── links.txt            # Archivo con URLs (una por línea)
├── requirements.txt     # Dependencias Python
├── musica/              # Carpeta de salida (se crea automáticamente)
├── README.md            # Documentación
└── CHANGELOG.md         # Este archivo
```

### 🚀 Uso

1. Editar `links.txt` y agregar URLs de YouTube (una por línea)
2. Ejecutar: `python download.py`
3. Los archivos se guardarán formateados en `musica/`

### 🔄 Historial de Versiones

**v1.0.0** - Versión inicial completa con todas las características mencionadas
