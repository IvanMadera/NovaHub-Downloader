from abc import ABCMeta, abstractmethod
from PySide6.QtWidgets import QWidget
from PySide6.QtCore import QMetaObject


class ABCQtMeta(type(QWidget), ABCMeta):
    """Metaclase combinada para resolver conflicto entre ABC y QWidget"""
    pass


class PlatformUI(QWidget, metaclass=ABCQtMeta):
    """Clase base para interfaces de plataforma"""
    
    def __init__(self, parent_widget: QWidget, platform_name: str):
        super().__init__(parent_widget)
        self.platform_name = platform_name
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
    def get_widget(self) -> QWidget:
        """Retornar el widget principal de la plataforma"""
        pass
