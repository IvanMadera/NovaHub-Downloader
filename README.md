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

## 📋 Requisitos

- **Python 3.8+**
- **FFmpeg**: Requerido para la conversión de audio en YouTube.
- **Dependencias**: Listadas en `requirements.txt` (PySide6, requests, yt-dlp).

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
- `downloaders/`: Backend con los scripts de descarga para cada plataforma.
- `core/`: Clases base y abstracciones del sistema.

## ⚠️ Consideraciones Legales

Este proyecto es únicamente para uso educativo y personal. Asegúrate de:
- Respetar los términos de servicio de las plataformas.
- Tener derecho a descargar el contenido.
- Usar las descargas respetando los derechos de autor.

---

**Autor**: [Ivan Madera](https://github.com/IvanMadera)  
**Versión**: 2026.1.31  
**Última actualización**: Febrero 2026
