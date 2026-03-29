# ╫ Nova Hub

**Nova Hub** es una aplicación de escritorio moderna construida con Python y PySide6 diseñada para centralizar la descarga de contenido de múltiples plataformas como YouTube y TikTok. Ofrece una interfaz intuitiva, rápida y estéticamente premium.

## 🎯 Funcionalidades

### 📺 YouTube

- **Descarga de audio**: Extrae el audio en la mejor calidad disponible.
- **Conversión a MP3**: Procesamiento automático a 192 kbps.
- **Gestión de Cola**: Visualización de estado (cola, progreso, éxitos, fallos).
- **Control**: Inicia, detiene y limpia la consola de resultados.

### 📱 TikTok

- **Metadatos en tiempo real**: Visualización de Autor, Fecha, Duración y Descripción antes de descargar.
- **Vista Previa**: Carga de miniatura del video de forma dinámica.
- **Sin Marca de Agua**: Descarga de videos limpios listos para usar.
- **Barra de Progreso**: Seguimiento detallado del estado de descarga.

### 📸 Instagram

- **Múltiples Formatos**: Descarga de Reels, Videos, Fotos y Carruseles (Sidecars).
- **Extracción de Máxima Calidad**: Selección automática de la máxima resolución disponible (`display_url`).
- **Galería Interactiva**: Visualización de miniaturas de carruseles para selección individual antes de descargar.
- **Integración Nativa**: Extracción de URLs vía `instaloader` adaptada para la descarga asíncrona fluida.

### 👥 Facebook

- **Descarga Multipropósito**: Procesa tanto videos públicos como descargas optimizadas unificando audio/video mediante `ffmpeg`.
- **Motor Confiable**: Refactorizado 100% sobre `yt-dlp` logrando velocidades topes y metadatos nativos rápidos.

### 🐦 X (Twitter)

- **Extracción Enriquecida**: Recuperación e interpretación de cuerpo del tweet (descripción), autor, tamaño, duración y fechas.
- **Diseño Resiliente**: Descargas en máxima fidelidad consolidando flujos a .mp4.



### ⊞ Generador de Códigos QR

- **Múltiples formatos**: Soporte para URLs, JSON y credenciales WiFi.
- **Vista previa**: Visualización del código QR generado en tiempo real.
- **Descarga PNG**: Exportación del código QR en 720×720 píxeles con diálogo de guardado.
- **Consola de estado**: Mensajes de validación, errores y éxito.

## 📋 Requisitos

- **Python 3.8+**
- **FFmpeg**: Requerido para la conversión de audio en YouTube.
- **Dependencias**: Listadas en `requirements.txt` (PySide6, requests, yt-dlp, qrcode, Pillow, instaloader).

## 🚀 Instalación y Uso

1. **Clonar el repositorio**:

   ```bash
   git clone https://github.com/IvanMadera/YT-download.git
   cd YT-download
   ```

2. **Instalar dependencias**:

   ```bash
   pip install -r requirements.txt
   ```

3. **Ejecutar la aplicación**:

   ```bash
   python main.py
   ```

## 📁 Estructura del Proyecto

- `main.py`: Punto de entrada de la aplicación.
- `ui/`: Contiene toda la lógica de la interfaz gráfica y vistas.
  - `qr_ui.py`: Vista del generador de códigos QR.
- `downloaders/`: Backend con los scripts de descarga para cada plataforma.
- `core/`: Clases base y abstracciones del sistema.

## ⚠️ Consideraciones Legales

Este proyecto es únicamente para uso educativo y personal. Asegúrate de:

- Respetar los términos de servicio de las plataformas.
- Tener derecho a descargar el contenido.
- Usar las descargas respetando los derechos de autor.

---

**Autor**: [Ivan Madera](https://github.com/IvanMadera)  
**Versión**: 2026.3.15  
**Última actualización**: Marzo 2026
