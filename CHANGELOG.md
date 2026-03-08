# Changelog

Todos los cambios notables en este proyecto serán documentados en este archivo.

## [2026.3.7] - 2026-03-07

### ✨ Nueva Funcionalidad: Descargador de Instagram

- **Pestaña Dedicada**: Se integró Instagram al *sidebar* (`✦ Instagram`) con un selector dual para `Video` e `Imagen`.
- **Descarga de Videos y Reels**: Extracción rápida orientada a la URL nativa e integración con el reproductor y barra de progreso de la UI.
- **Descarga de Imágenes y Carruseles**: Función interactiva donde la UI carga dinámicamente una galería en grilla (usando `QScrollArea`) permitiendo al usuario seleccionar o deseleccionar qué fotos de un mismo *post* (carrusel) descargar.
- **Descargas en Máxima Calidad**: Reestructuración del *backend* usando `instaloader` para extraer el puntero `display_url` de máxima calidad y evitar el guardado innecesario de *thumbnails*.

### 🚀 Mejoras de Rendimiento y UI

- **Multihilo Asíncrono para UI**: Las miniaturas de los carruseles masivos ahora son descargadas por un subproceso (`ImageLoaderThread`), previniendo trabas o congelamientos en sistemas Windows.
- **Diseño Homologado**: Se replicaron las reglas estéticas (botones de 100x40px y 120x32px, `hover` con `#6487E5`, color principal `#3B5998`) de la vista de TikTok para mantener uniformidad.

## [2026.2.14] - 2026-02-14

### 🎨 Estandarización de UI (Global)

- **Botones Secundarios Unificados**:
  - Botón "Limpiar consola": Estandarizado a **120x32px**.
  - Botón "Elegir" (Ruta): Estandarizado a **100x40px**.
  - Fuentes: Unificadas a **Segoe UI 10px Normal** (sin negrita) para una apariencia más limpia y consistente.
- **Tipografía**:
  - Títulos de módulos estandarizados a **Segoe UI 20px Bold** con color `TEXT_MAIN` (#FFFFFF).
- **Consistencia Visual**:
  - Homologación de bordes redondeados (8px para elementos de entrada/botones pequeños).
  - Corrección de discrepancias en colores de hover (`#6487E5`) en todos los módulos (TikTok, YouTube, QR).
- **YouTube UI**:
  - Se mantiene el botón de descarga "Gigante" como característica distintiva, pero se alinean los demás controles al estándar global.

## [2026.2.9] - 2026-02-09

### ✨ Nueva Funcionalidad: Generador de Códigos QR

- **Generación de QR**: Soporte para URLs, texto JSON y credenciales WiFi (SSID, contraseña, seguridad).
- **Conversión JSON**: Acepta tanto JSON estricto como objetos JavaScript (sin comillas en claves).
- **Descarga PNG**: Exportación del código QR generado en resolución 720×720 píxeles con diálogo de guardado nativo.
- **Consola de estado**: Mensajes de validación, errores y éxito en tiempo real.

### 🎨 Mejoras Visuales

- **Bordes redondeados**: Aplicación consistente de `border-radius: 14px` en áreas de entrada, consola y visualización del QR.
- **ComboBox refinado**: Corrección de esquinas cortadas en el selector de tipo de contenido.
- **Toggle de contraseña WiFi**: Botón "Mostrar/Ocultar" para verificar la contraseña ingresada.
- **Icono QR en sidebar**: Nuevo icono `⊞` para la sección de generación de códigos QR.

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

## [1.0.0] - 2025-12-07

### ✨ Nueva Funcionalidad: Descargador de YouTube (CLI)

- **Lectura automática de enlaces**: Lee URLs desde `links.txt` (un enlace por línea) en lugar de pedirlas por terminal.
- **Formateo automático de nombres de archivo**:
  - Elimina caracteres especiales, emojis y espacios duplicados.
  - Capitaliza cada palabra y preserva estructura "Artista - Canción".
- **Logger personalizado**: Filtra warnings conocidos de `yt-dlp` (`web_safari`, `SABR`, falta de runtime JS).
- **Barra de progreso mejorada**: Muestra porcentaje, velocidad, ETA y nombre del archivo.
- **Resumen final**: Total procesado con estado de éxito (✅) o error (❌) por archivo.
- **Verificación de dependencias**: Comprueba al inicio si `ffmpeg` está instalado.

### 🔧 Mejoras

- Desactivación de `restrictfilenames` para permitir nombres personalizados.
- Renombramiento de archivos después de la conversión a MP3.
- Manejo mejorado de excepciones con mensajes claros.
- Organización de código con funciones auxiliares bien documentadas.

### 🐛 Correcciones

- Corregido problema de nombres con caracteres especiales que no se formateaban correctamente.
- Solucionado issue donde la ruta no separaba correctamente carpeta/archivo.
- Filtrado de warnings innecesarios que ensuciaban la salida.
- Validación de archivos antes de renombrar para evitar conflictos.
