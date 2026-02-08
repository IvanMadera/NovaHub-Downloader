from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QPlainTextEdit, QLineEdit, QFrame, QFileDialog, QProgressBar
)
from PySide6.QtCore import Qt, QThread, Signal, Slot
from PySide6.QtGui import QFont, QPixmap, QImage
import os
import requests
from datetime import datetime
from threading import Lock

from ui.base_ui import PlatformUI
from downloaders.tiktok import TikTokDownloader

# ===== PALETA =====
BG_MAIN  = "#0E1116"
BG_PANEL = "#151A21"
ACCENT   = "#3B5998"
SUCCESS  = "#9ECE6A"
TEXT_SEC = "#A9B1D6"
ERROR    = "#F7768E"
RADIUS   = 14


class TikTokDownloadThread(QThread):
    """Thread de descarga para TikTok"""
    progress_updated = Signal(int)  # progreso en porcentaje (0-100)
    info_updated = Signal(str, str, str, str, str, str, str)  # author, views, date, resolution, duration, size, description
    preview_updated = Signal(bytes)  # thumbnail data
    console_message = Signal(str, str)  # message, status
    download_finished = Signal()
    
    def __init__(self, url, output_path, downloader):
        super().__init__()
        self.url = url
        self.output_path = output_path
        self.downloader = downloader
        self.is_running = True
    
    def run(self):
        """Ejecuta la descarga"""
        try:
            # 1. Obtener información del video primero para mostrar en UI
            self.console_message.emit("Obteniendo información del video...", "info")
            info = self.downloader.get_video_info(self.url)
            
            if not info:
                self.console_message.emit("✗ No se pudo obtener información del video", "error")
                return
            
            # Formatear e informar datos
            author = info.get('author', 'Desconocido')
            views = self._format_views(info.get('view_count', 0))
            date = self._format_date(info.get('upload_date', 0))
            resolution = self._format_resolution(
                info.get('width', 0),
                info.get('height', 0)
            )
            duration = self._format_duration(info.get('duration', 0))
            size = self._format_filesize(info.get('filesize', 0))
            description = self._truncate_description(info.get('title', 'Sin descripción'))
            
            self.info_updated.emit(author, views, date, resolution, duration, size, description)
            
            # 2. Obtener miniatura
            thumbnail_url = info.get('thumbnail')
            if thumbnail_url:
                try:
                    thumb_response = requests.get(thumbnail_url, timeout=10)
                    if thumb_response.status_code == 200:
                        self.preview_updated.emit(thumb_response.content)
                except:
                    pass
            
            # 3. Iniciar descarga real
            def progress_callback(progress_ratio):
                # Recibimos un valor de 0.0 a 1.0
                percent = int(progress_ratio * 100)
                self.progress_updated.emit(percent)
            
            success, title = self.downloader.download_audio(
                self.url,
                self.output_path,
                progress_callback=progress_callback
            )
            
            if success:
                self.console_message.emit(
                    f"✔ Descarga exitosa: {title}",
                    "success"
                )
            else:
                self.console_message.emit("✖ La descarga falló", "error")
        
        except Exception as e:
            self.console_message.emit(f"✖ Error: {str(e)}", "error")
        
        finally:
            self.download_finished.emit()
    
    def _format_views(self, views):
        """Formatea las vistas"""
        try:
            views = int(views)
            if views >= 1_000_000:
                return f"{views/1_000_000:.1f}M"
            elif views >= 1_000:
                return f"{views/1_000:.1f}K"
            else:
                return str(views)
        except:
            return "0"
    
    def _format_date(self, timestamp):
        """Formatea la fecha desde Unix timestamp"""
        try:
            if timestamp == 0:
                return "N/A"
            dt = datetime.fromtimestamp(int(timestamp))
            return dt.strftime("%d/%m/%Y")
        except:
            return "N/A"
    
    def _format_resolution(self, width, height):
        """Formatea la resolución"""
        if width and height:
            return f"{width}x{height}"
        return "N/A"
    
    def _truncate_description(self, description):
        """Trunca la descripción"""
        if not description:
            return "N/A"
        if len(description) > 150:
            return description[:147] + "..."
        return description
    
    def _format_duration(self, seconds):
        """Formatea la duración"""
        try:
            seconds = int(seconds)
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            secs = seconds % 60
            if hours > 0:
                return f"{hours:02d}:{minutes:02d}:{secs:02d}"
            else:
                return f"{minutes:02d}:{secs:02d}"
        except:
            return "00:00"
    
    def _format_filesize(self, size_bytes):
        """Formatea el tamaño del archivo"""
        try:
            if not size_bytes:
                return "N/A"
            size_bytes = int(size_bytes)
            if size_bytes >= 1_073_741_824:
                return f"{size_bytes/1_073_741_824:.2f} GB"
            elif size_bytes >= 1_048_576:
                return f"{size_bytes/1_048_576:.2f} MB"
            elif size_bytes >= 1_024:
                return f"{size_bytes/1_024:.2f} KB"
            else:
                return f"{size_bytes} B"
        except:
            return "N/A"


class TikTokUI(PlatformUI):
    
    def __init__(self, parent_widget: QWidget, console_lock: Lock):
        super().__init__(parent_widget, "TikTok")
        self.console_lock = console_lock
        self.downloader = TikTokDownloader()
        self.is_downloading = False
        self.download_thread = None
    
    def build(self):
        """Construye la interfaz de TikTok"""
        # Usar Grid Layout para consistencia con YouTube UI y mejor control
        # Cambio a QVBoxLayout para apilar filas limpiamente
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)
        
        # Título
        title = QLabel("DESCARGA DE CONTENIDO - TIKTOK")
        title.setFont(QFont("Segoe UI", 20, QFont.Bold)) 
        main_layout.addWidget(title)
        
        # ================== CONFIGURATION AREA (URL -> Dest -> Download) ==================
        
        # 1. URL Input (Full Width)
        url_container = QWidget()
        url_layout = QVBoxLayout(url_container)
        url_layout.setContentsMargins(0, 0, 0, 0)
        url_layout.setSpacing(5)
        
        url_label = QLabel("URL del video de TikTok")
        url_layout.addWidget(url_label)
        
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("https://www.tiktok.com/@usuario/video/...")
        self.url_input.setFixedHeight(40)
        self.url_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: {BG_PANEL};
                border: none;
                border-radius: 8px;
                padding: 0 10px;
                color: white;
            }}
        """)
        url_layout.addWidget(self.url_input)
        main_layout.addWidget(url_container)
        
        # 2. Destination Row
        dest_container = QWidget()
        dest_layout = QHBoxLayout(dest_container)
        dest_layout.setContentsMargins(0, 0, 0, 0)
        dest_layout.setSpacing(10)
        
        dest_label = QLabel("Carpeta de destino")
        dest_label.setFixedWidth(110)
        dest_layout.addWidget(dest_label)
        
        self.path = QLineEdit("C:/Descargas")
        self.path.setFixedHeight(40)
        self.path.setReadOnly(True)
        self.path.setStyleSheet(f"""
            QLineEdit {{
                background-color: {BG_PANEL};
                border: none;
                border-radius: 8px;
                padding: 0 10px;
                color: white;
            }}
        """)
        dest_layout.addWidget(self.path, 1)
        
        choose_button = QPushButton("Elegir")
        choose_button.setFixedWidth(90)
        choose_button.setFixedHeight(40)
        choose_button.clicked.connect(self.select_folder)
        dest_layout.addWidget(choose_button)
        
        main_layout.addWidget(dest_container)
        
        # ================== MAIN CONTENT AREA (Split Left/Right) ==================
        content_layout = QHBoxLayout()
        content_layout.setSpacing(20)
        
        # -------- LEFT COLUMN (Info, Console) --------
        left_column = QVBoxLayout()
        left_column.setSpacing(15)
        
        # Video Info (Vertical) - GroupBox style
        info_frame = QFrame()
        info_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {BG_PANEL};
                border-radius: {RADIUS}px;
            }}
        """)
        info_layout = QVBoxLayout(info_frame)
        info_layout.setContentsMargins(15, 15, 15, 15)
        info_layout.setSpacing(10)
        
        # Helper to create info row
        def create_info_row(label_text, value_widget):
            row = QHBoxLayout()
            lbl = QLabel(label_text)
            lbl.setFixedWidth(80) # Fixed width for alignment
            lbl.setStyleSheet(f"color: {TEXT_SEC}; font-weight: bold;")
            row.addWidget(lbl)
            row.addWidget(value_widget)
            return row

        self.author_label = QLabel("N/A")
        info_layout.addLayout(create_info_row("Autor:", self.author_label))
        
        self.date_label = QLabel("N/A")
        info_layout.addLayout(create_info_row("Fecha:", self.date_label))
        
        self.duration_label = QLabel("N/A")
        info_layout.addLayout(create_info_row("Duración:", self.duration_label))
        
        self.size_label = QLabel("N/A")
        info_layout.addLayout(create_info_row("Tamaño:", self.size_label))
        
        # Description acts as a block
        desc_label = QLabel("Descripción:")
        desc_label.setStyleSheet(f"color: {TEXT_SEC}; font-weight: bold;")
        info_layout.addWidget(desc_label)
        
        self.description_label = QLabel("N/A")
        self.description_label.setWordWrap(True)
        self.description_label.setStyleSheet("color: white;")
        # Limit max height for description to avoid pushing too much
        self.description_label.setMaximumHeight(60) 
        info_layout.addWidget(self.description_label)
        
        left_column.addWidget(info_frame)
        
        # Console Header (Outside the frame)
        console_header = QHBoxLayout()
        console_label = QLabel("Resultado de la consola")
        console_header.addWidget(console_label)
        console_header.addStretch()
        
        clear_button = QPushButton("Limpiar consola")
        clear_button.setFixedSize(120, 30)
        clear_button.setFont(QFont("Segoe UI", 9))
        clear_button.clicked.connect(self.clear_console)
        console_header.addWidget(clear_button)
        
        left_column.addLayout(console_header)
        
        # Console Wrapper Frame (for proper border radius)
        console_wrapper = QFrame()
        console_wrapper.setStyleSheet(f"""
            QFrame {{
                background-color: {BG_PANEL};
                border-radius: {RADIUS}px;
            }}
        """)
        console_wrapper_layout = QVBoxLayout(console_wrapper)
        console_wrapper_layout.setContentsMargins(10, 10, 10, 10)
        console_wrapper_layout.setSpacing(0)
        
        self.console = QPlainTextEdit()
        # Takes remaining space but has min height
        self.console.setMinimumHeight(150) 
        self.console.setReadOnly(True)
        self.console.setFrameShape(QFrame.NoFrame)
        self.console.setStyleSheet("background-color: transparent; border: none; color: white;")
        self.console.setPlainText("") 
        console_wrapper_layout.addWidget(self.console)
        
        left_column.addWidget(console_wrapper, 1) # Give it stretch to fill space
        
        content_layout.addLayout(left_column, 6) # 60% width
        
        # -------- RIGHT COLUMN (Large Preview) --------
        preview_container = QWidget()
        preview_layout = QVBoxLayout(preview_container)
        preview_layout.setContentsMargins(0, 0, 0, 0)
        preview_layout.setAlignment(Qt.AlignTop) # Align everything to top
        
        # Title for preview - Centered
        preview_title = QLabel("Vista previa")
        preview_title.setAlignment(Qt.AlignCenter)
        preview_layout.addWidget(preview_title)
        
        self.preview_label = QLabel("Sin vista previa")
        # Reuse size 270x480
        self.preview_label.setFixedSize(270, 480) 
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setStyleSheet(f"background-color: {BG_PANEL}; border-radius: {RADIUS}px; color: {TEXT_SEC};")
        
        # Center the preview label horizontally in the layout
        preview_layout.addWidget(self.preview_label, 0, Qt.AlignHCenter)
        preview_layout.addStretch() # Push up
        
        content_layout.addWidget(preview_container, 4) # 40% width
        
        main_layout.addLayout(content_layout)
        
        # ================== FOOTER (Progress + Download Button) ==================
        
        footer_container = QWidget()
        footer_layout = QHBoxLayout(footer_container)
        footer_layout.setContentsMargins(0, 10, 0, 5)
        footer_layout.setSpacing(15)
        
        progress_label = QLabel("Progreso:")
        progress_label.setFixedWidth(60)
        footer_layout.addWidget(progress_label)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setFixedHeight(8) 
        self.progress_bar.setTextVisible(False)
        footer_layout.addWidget(self.progress_bar, 1) # Stretch factor 1
        
        self.download_button = QPushButton("DESCARGAR")
        self.download_button.setFixedSize(160, 45)
        self.download_button.setFont(QFont("Segoe UI", 10, QFont.Bold))
        self.download_button.setCursor(Qt.PointingHandCursor)
        self.download_button.clicked.connect(self.start_download)
        footer_layout.addWidget(self.download_button)
        
        main_layout.addWidget(footer_container)

        
        # Aplicar estilos
        self.apply_styles()
    
    def apply_styles(self):

        """Aplica estilos QSS"""
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {BG_MAIN};
                color: white;
            }}
            
            QLabel {{
                color: {TEXT_SEC};
            }}
            
            QPlainTextEdit {{
                background-color: transparent;
                border: none;
                padding: 5px;
                color: white;
            }}
            
            QProgressBar {{
                background-color: {BG_PANEL};
                border: none;
                border-radius: 3px;
                color: white;
            }}
            
            QProgressBar::chunk {{
                background-color: {SUCCESS};
                border-radius: 3px;
            }}
            
            QPushButton {{
                background-color: {ACCENT};
                border: none;
                border-radius: 8px;
                color: white;
                text-align: center;
                padding: 5px;
            }}
            
            QPushButton:hover {{
                background-color: #6487E5;
            }}
            
            QPushButton:disabled {{
                background-color: #555;
            }}
            
            QPushButton[secondary="true"] {{
                background-color: #1C2230;
            }}
            
            QPushButton[secondary="true"]:hover {{
                background-color: #252B3A;
            }}
        """)
        
        # Aplicar atributo secondary
        for child in self.findChildren(QPushButton):
            if child.text() in ["Elegir", "Limpiar consola"]:
                child.setProperty("secondary", "true")
    
    def select_folder(self):
        """Abre diálogo para seleccionar carpeta"""
        folder = QFileDialog.getExistingDirectory(self, "Seleccionar carpeta de descarga")
        if folder:
            self.path.setText(folder)
    
    def clear_console(self):
        """Limpia la consola"""
        with self.console_lock:
            self.console.setPlainText("")
    
    @Slot(int)
    def update_progress(self, percent_value):
        """Actualiza la barra de progreso"""
        self.progress_bar.setValue(percent_value)
    
    @Slot(str, str, str, str, str, str, str)
    def update_video_info(self, author, views, date, resolution, duration, size, description):
        """Actualiza la información del video"""
        # Ignoramos views y resolution como pidió el usuario
        self.author_label.setText(author)
        self.date_label.setText(date)
        self.duration_label.setText(duration)
        self.size_label.setText(size)
        self.description_label.setText(description)
    
    @Slot(bytes)
    def set_preview_image(self, image_data):
        """Actualiza la imagen de preview desde datos binarios"""
        try:
            pixmap = QPixmap()
            if pixmap.loadFromData(image_data):
                # Escalar manteniendo aspect ratio para TikTok (retrato)
                scaled_pixmap = pixmap.scaled(
                    270, 480, 
                    Qt.KeepAspectRatio, 
                    Qt.SmoothTransformation
                )
                self.preview_label.setPixmap(scaled_pixmap)
            else:
                self.preview_label.setText("Error al cargar imagen")
        except Exception as e:
            print(f"Error actualizando preview: {e}")


    
    @Slot(str, str)
    def add_to_console(self, message, status="info"):
        """Agrega mensaje a la consola"""
        # Filtro estricto: solo mensaje si es success o error
        if status not in ["success", "error"]:
            return
            
        with self.console_lock:
            # Agregar timestamp o formato si se desea, por ahora simple
            self.console.appendPlainText(message)
    
    def start_download(self):
        """Inicia el proceso de descarga"""
        if self.is_downloading:
            return
            
        self.clear_console()
        
        url = self.url_input.text().strip()
        if not url:
            self.add_to_console("✖ Por favor ingresa una URL válida", "error")
            return
        
        output_path = self.path.text()
        if not output_path or not os.path.exists(output_path) or not os.path.isdir(output_path):
            self.add_to_console("✖ Por favor selecciona una carpeta válida", "error")
            return
        
        self.is_downloading = True
        self.download_button.setEnabled(False)
        self.progress_bar.setValue(0)
        
        # NO enviamos mensaje de "Iniciando descarga..." a la consola
        
        # Crear y conectar el thread
        self.download_thread = TikTokDownloadThread(url, output_path, self.downloader)
        self.download_thread.progress_updated.connect(self.update_progress)
        self.download_thread.info_updated.connect(self.update_video_info)
        self.download_thread.preview_updated.connect(self.set_preview_image)
        self.download_thread.console_message.connect(self.add_to_console)
        self.download_thread.download_finished.connect(self.on_download_finished)
        self.download_thread.start()
    
    @Slot()
    def on_download_finished(self):
        """Maneja cuando termina la descarga"""
        self.is_downloading = False
        self.download_button.setEnabled(True)
        self.progress_bar.setValue(100)
    
    def show(self):
        """Muestra la interfaz"""
        super().show()
    
    def hide(self):
        """Oculta la interfaz"""
        super().hide()
    
    def get_widget(self) -> QWidget:
        """Retorna el widget principal"""
        return self
