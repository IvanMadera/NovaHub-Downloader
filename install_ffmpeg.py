import os
import sys
import requests
import zipfile
import io

def install_ffmpeg():
    print("⬇️  Iniciando descarga de FFmpeg (aprox. 25MB)...")
    print("    Si tarda un poco es normal, por favor espera.")
    
    # URL directa a la versión "essentials" (más ligera) y específica para Windows 64-bit
    # Usando el release 'latest' de gyan.dev que es el mirror oficial recomendado
    url = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
    
    try:
        # Descargar con stream para no cargar todo en memoria
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        print("📦 Extrayendo archivos...")
        
        # Usar io.BytesIO para manejar el zip en memoria
        with zipfile.ZipFile(io.BytesIO(response.content)) as z:
            # Buscar los archivos ejecutables dentro de la estructura del zip
            ffmpeg_data = None
            ffprobe_data = None
            
            for file_info in z.infolist():
                if file_info.filename.endswith("bin/ffmpeg.exe"):
                    ffmpeg_data = z.read(file_info)
                elif file_info.filename.endswith("bin/ffprobe.exe"):
                    ffprobe_data = z.read(file_info)
            
            if not ffmpeg_data or not ffprobe_data:
                print("❌ No se encontraron ffmpeg.exe o ffprobe.exe en el ZIP descargado.")
                return

            # Definir carpeta de destino: ./ffmpeg/bin/
            base_dir = os.getcwd()
            dest_dir = os.path.join(base_dir, "ffmpeg", "bin")
            
            if not os.path.exists(dest_dir):
                os.makedirs(dest_dir)
                print(f"📁 Carpeta creada: {dest_dir}")
            
            # Escribir los archivos
            ffmpeg_path = os.path.join(dest_dir, "ffmpeg.exe")
            with open(ffmpeg_path, "wb") as f:
                f.write(ffmpeg_data)
                
            ffprobe_path = os.path.join(dest_dir, "ffprobe.exe")
            with open(ffprobe_path, "wb") as f:
                f.write(ffprobe_data)
                
        print("-" * 50)
        print(f"✅ ¡INSTALACIÓN COMPLETADA!")
        print(f"    Archivos guardados en: {dest_dir}")
        print("🚀 Ahora reinicia tu aplicación (main.py) y el error debería haber desaparecido.")
        print("-" * 50)
        
    except Exception as e:
        print(f"❌ Ocurrió un error: {e}")

if __name__ == "__main__":
    install_ffmpeg()
