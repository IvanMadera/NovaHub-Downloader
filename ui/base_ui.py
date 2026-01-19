from abc import ABC, abstractmethod
import customtkinter as ctk


class PlatformUI(ABC):
    """Clase base para interfaces de plataforma"""
    
    def __init__(self, parent_frame: ctk.CTkFrame, platform_name: str):
        self.parent_frame = parent_frame
        self.platform_name = platform_name
        self.main_frame = None
        self.console_lock = None
        
    @abstractmethod
    def build(self):
        """Construir la interfaz de la plataforma"""
        pass
    
    @abstractmethod
    def show(self):
        """Mostrar la interfaz"""
        pass
    
    @abstractmethod
    def hide(self):
        """Ocultar la interfaz"""
        pass
    
    @abstractmethod
    def get_frame(self) -> ctk.CTkFrame:
        """Retornar el frame principal de la plataforma"""
        pass
