from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, 
    QFrame, QLabel, QPushButton, QStackedWidget
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from datetime import datetime
from threading import Lock

from ui.youtube_ui import YouTubeUI
from ui.tiktok_ui import TikTokUI

# ===== PALETA =====
BG_MAIN  = "#0E1116"
BG_PANEL = "#151A21"
ACCENT   = "#3B5998"
TEXT_SEC = "#A9B1D6"


class NovaHub(QMainWindow):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("Nova Hub")
        self.resize(1280, 760)
        self.setMinimumSize(1180, 700)

        self.console_lock = Lock()
        self.current_platform = "YouTube"
        
        # Instancias de UIs
        self.platform_uis = {}
        
        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Layout principal
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # ================== SIDEBAR ==================
        sidebar = QFrame()
        sidebar.setFixedWidth(240)
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        sidebar_layout.setSpacing(0)

        # Logo
        logo_label = QLabel("╫ Nova Hub")
        logo_label.setFont(QFont("Segoe UI", 16, QFont.Bold))
        logo_label.setAlignment(Qt.AlignCenter)
        sidebar_layout.addSpacing(24)
        sidebar_layout.addWidget(logo_label)
        sidebar_layout.addSpacing(24)

        # Crear botones dinámicamente
        self.platform_buttons = {}
        platforms_list = ["YouTube", "TikTok"]
        
        for platform_name in platforms_list:
            btn = QPushButton(f"◈  {platform_name}")
            btn.setFixedHeight(38)
            btn.setFont(QFont("Segoe UI", 11))
            btn.clicked.connect(lambda checked, p=platform_name: self.set_platform(p))
            
            # Agregar con márgenes
            sidebar_layout.addSpacing(6)
            container = QWidget()
            container_layout = QHBoxLayout(container)
            container_layout.setContentsMargins(18, 0, 18, 0)
            container_layout.addWidget(btn)
            sidebar_layout.addWidget(container)
            
            self.platform_buttons[platform_name] = btn
        
        sidebar_layout.addStretch()
        
        # ================== FOOTER ==================
        footer_label = QLabel(f"© Copyright {datetime.now().year}")
        footer_label.setFont(QFont("Segoe UI", 10))
        footer_label.setAlignment(Qt.AlignCenter)
        sidebar_layout.addWidget(footer_label)
        sidebar_layout.addSpacing(15)

        # ================== CONTENT AREA ==================
        self.content_widget = QStackedWidget()

        # Construir UIs
        self.platform_uis["YouTube"] = YouTubeUI(self.content_widget, self.console_lock)
        self.platform_uis["YouTube"].build()
        self.content_widget.addWidget(self.platform_uis["YouTube"])
        
        self.platform_uis["TikTok"] = TikTokUI(self.content_widget, self.console_lock)
        self.platform_uis["TikTok"].build()
        self.content_widget.addWidget(self.platform_uis["TikTok"])

        # Agregar al layout principal
        main_layout.addWidget(sidebar)
        main_layout.addWidget(self.content_widget)

        # Aplicar estilos
        self.apply_styles()

        # Mostrar YouTube por defecto
        self.set_platform("YouTube")

    def apply_styles(self):
        """Aplica los estilos QSS a la ventana"""
        self.setStyleSheet(f"""
            QMainWindow {{
                background-color: {BG_MAIN};
            }}
            
            QFrame {{
                background-color: {BG_PANEL};
            }}
            
            QLabel {{
                color: {TEXT_SEC};
            }}
            
            QPushButton {{
                background-color: {BG_PANEL};
                color: {TEXT_SEC};
                border: none;
                border-radius: 8px;
                padding: 10px;
                text-align: left;
            }}
            
            QPushButton:hover {{
                background-color: #1C2230;
            }}
            
            QPushButton[active="true"] {{
                background-color: {ACCENT};
                color: white;
            }}
            
            QStackedWidget {{
                background-color: {BG_MAIN};
            }}
        """)

    def set_platform(self, platform_name: str):
        """Cambia la plataforma activa"""
        # Cambiar plataforma
        self.current_platform = platform_name
        
        # Mostrar nueva plataforma
        if platform_name in self.platform_uis:
            self.content_widget.setCurrentWidget(self.platform_uis[platform_name])

        # Destacar botón
        self.highlight_platform(platform_name)

    def highlight_platform(self, platform_name: str):
        """Destaca el botón de la plataforma activa"""
        for name, btn in self.platform_buttons.items():
            if name == platform_name:
                btn.setProperty("active", "true")
            else:
                btn.setProperty("active", "false")
            btn.style().unpolish(btn)
            btn.style().polish(btn)
