from abc import ABC, abstractmethod


class Downloader(ABC):
    """Clase base para todos los descargadores de contenido"""
    
    def __init__(self, platform_name: str):
        self.platform_name = platform_name
    
    @abstractmethod
    def download_audio(self, url: str, output_path: str, progress_callback=None, title_callback=None):
        """
        Descarga audio desde la plataforma
        
        Args:
            url: URL del contenido
            output_path: Ruta donde guardar el archivo
            progress_callback: Función para reportar progreso (percent, speed, eta)
            title_callback: Función para reportar el título
        
        Returns:
            (success: bool, title: str)
        """
        pass
