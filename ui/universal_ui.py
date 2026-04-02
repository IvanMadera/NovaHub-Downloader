from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QPlainTextEdit, QLineEdit, QFrame, QFileDialog, QProgressBar
)
from PySide6.QtCore import Qt, QThread, Signal, Slot
from PySide6.QtGui import QFont, QPixmap, QPainter, QPainterPath
import os
import requests
import time
from datetime import datetime
from threading import Lock

from ui.base_ui import PlatformUI
from downloaders.universal import UniversalDownloader

# ===== PALETA =====
BG_MAIN  = "#0E1116"
BG_PANEL = "#151A21"
ACCENT   = "#3B5998"
SUCCESS  = "#9ECE6A"
TEXT_SEC = "#A9B1D6"
ERROR    = "#F7768E"
TEXT_MAIN = "#FFFFFF"
RADIUS   = 14

class UniversalDownloadThread(QThread):
    """Thread de descarga Universal"""
    progress_updated = Signal(int)
    info_updated = Signal(str, str, str, str, str)  # title, date, duration, size, domain
    preview_updated = Signal(bytes)
    console_message = Signal(str, str)
    download_finished = Signal()
    
    def __init__(self, url, output_path, downloader):
        super().__init__()
        self.url = url
        self.output_path = output_path
        self.downloader = downloader
        self.is_running = True
    
    def run(self):
        try:
            self.console_message.emit("➤ Evaluando compatibilidad con el servidor web...", "info")
            info = self.downloader.get_video_info(self.url)
            
            if not info:
                self.console_message.emit("✗ No se pudo obtener información ni soporte multimedia de esta web.", "error")
                return
                
            # Formatear datos
            title = self._truncate_title(info.get('title', 'Desconocido'))
            date = self._format_date(info.get('timestamp', 0))
            duration = self._format_duration(info.get('duration', 0))
            size = self._format_filesize(info.get('filesize', 0))
            domain = info.get('domain', 'URL Externa')
            
            thumbnail_url = info.get('thumbnail')
            
            self.info_updated.emit(title, date, duration, size, domain)
            
            if thumbnail_url:
                try:
                    thumb_response = requests.get(thumbnail_url, timeout=10)
                    if thumb_response.status_code == 200:
                        self.preview_updated.emit(thumb_response.content)
                except:
                    pass
            
            time.sleep(1)
            
            self.console_message.emit("↓ Extrayendo streams y descargando contenido principal...", "info")
            
            def progress_callback(progress_ratio):
                percent = int(progress_ratio * 100)
                self.progress_updated.emit(percent)
            
            success, saved_title = self.downloader.download_audio(
                self.url,
                self.output_path,
                progress_callback=progress_callback
            )
            
            if success:
                self.console_message.emit(f"✔ Descarga exitosa: {saved_title}", "success")
            else:
                self.console_message.emit("✖ La descarga falló", "error")
        
        except Exception as e:
            self.console_message.emit(f"✖ Error de Extractor: {str(e)}", "error")
        
        finally:
            self.download_finished.emit()
            
    def _truncate_title(self, text):
        if not text: return "N/A"
        if len(text) > 80: return text[:77] + "..."
        return text
    
    def _format_date(self, timestamp):
        try:
            if not timestamp or timestamp == 0: return "N/A"
            dt = datetime.fromtimestamp(int(timestamp))
            return dt.strftime("%d/%m/%Y")
        except:
            # yt-dlp might return 'upload_date' in %Y%m%d format
            if isinstance(timestamp, str) and len(timestamp) == 8 and timestamp.isdigit():
                return f"{timestamp[6:]}/{timestamp[4:6]}/{timestamp[:4]}"
            return "N/A"
    
    def _format_duration(self, seconds):
        try:
            if not seconds: return "00:00"
            seconds = int(seconds)
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            secs = seconds % 60
            if hours > 0: return f"{hours:02d}:{minutes:02d}:{secs:02d}"
            return f"{minutes:02d}:{secs:02d}"
        except:
            return "00:00"
    
    def _format_filesize(self, size_bytes):
        try:
            if not size_bytes or size_bytes == 0: return "N/A"
            size_bytes = int(size_bytes)
            if size_bytes >= 1_073_741_824: return f"{size_bytes/1_073_741_824:.2f} GB"
            elif size_bytes >= 1_048_576: return f"{size_bytes/1_048_576:.2f} MB"
            elif size_bytes >= 1_024: return f"{size_bytes/1_024:.2f} KB"
            return f"{size_bytes} B"
        except:
            return "N/A"

class AspectRatioLabel(QLabel):
    """Label que mantiene el aspect ratio con bordes redondeados"""
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.setMinimumSize(1, 1)
        self.setScaledContents(False) 
        self.pixmap_original = None
        self.setAlignment(Qt.AlignCenter)
        self.radius = 14

    def setPixmap(self, pixmap):
        self.pixmap_original = pixmap
        self.update_pixmap()

    def resizeEvent(self, event):
        self.update_pixmap()
        super().resizeEvent(event)

    def update_pixmap(self):
        if self.pixmap_original and not self.pixmap_original.isNull():
            scaled = self.pixmap_original.scaled(
                self.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
            rounded = QPixmap(scaled.size())
            rounded.fill(Qt.transparent)
            painter = QPainter(rounded)
            painter.setRenderHint(QPainter.Antialiasing)
            path = QPainterPath()
            path.addRoundedRect(0, 0, scaled.width(), scaled.height(), self.radius, self.radius)
            painter.setClipPath(path)
            painter.drawPixmap(0, 0, scaled)
            painter.end()
            super().setPixmap(rounded)
        else:
            pass

class UniversalUI(PlatformUI):
    
    def __init__(self, parent_widget: QWidget, console_lock: Lock):
        super().__init__(parent_widget, "Universal")
        self.console_lock = console_lock
        self.downloader = UniversalDownloader()
        self.is_downloading = False
        self.download_thread = None
    
    def build(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)
        
        # Título
        title = QLabel("DESCARGA DE CONTENIDO - UNIVERSAL (WEB)")
        title.setFont(QFont("Segoe UI", 20, QFont.Bold)) 
        title.setStyleSheet(f"color: {TEXT_MAIN}; background-color: transparent;")
        main_layout.addWidget(title)
        
        # URL
        url_container = QWidget()
        url_layout = QVBoxLayout(url_container)
        url_layout.setContentsMargins(0, 0, 0, 0)
        url_layout.setSpacing(5)
        
        url_label = QLabel("URL del reproductor en la web")
        url_layout.addWidget(url_label)
        
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("https://vimeo.com/..., https://reddit.com/..., etc.")
        self.url_input.setFixedHeight(40)
        self.url_input.setStyleSheet(f"QLineEdit {{ background-color: {BG_PANEL}; border: none; border-radius: 8px; padding: 0 10px; color: white; }}")
        url_layout.addWidget(self.url_input)
        main_layout.addWidget(url_container)
        
        # Destino
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
        self.path.setStyleSheet(f"QLineEdit {{ background-color: {BG_PANEL}; border: none; border-radius: 8px; padding: 0 10px; color: white; }}")
        dest_layout.addWidget(self.path, 1)
        
        choose_button = QPushButton("Elegir")
        choose_button.setFixedWidth(100)
        choose_button.setFixedHeight(40)
        choose_button.setFont(QFont("Segoe UI", 10))
        choose_button.clicked.connect(self.select_folder)
        dest_layout.addWidget(choose_button)
        main_layout.addWidget(dest_container)
        
        # Split Layout
        content_layout = QHBoxLayout()
        content_layout.setSpacing(20)
        
        # LEFT: Info + Consola
        left_column = QVBoxLayout()
        left_column.setSpacing(15)
        
        info_frame = QFrame()
        info_frame.setStyleSheet(f"QFrame {{ background-color: {BG_PANEL}; border-radius: {RADIUS}px; }}")
        info_layout = QVBoxLayout(info_frame)
        info_layout.setContentsMargins(15, 15, 15, 15)
        info_layout.setSpacing(10)
        
        def create_info_row(label_text, value_widget):
            row = QHBoxLayout()
            lbl = QLabel(label_text)
            lbl.setFixedWidth(80) 
            lbl.setStyleSheet(f"color: {TEXT_SEC}; font-weight: bold;")
            row.addWidget(lbl)
            row.addWidget(value_widget)
            return row

        self.domain_label = QLabel("N/A")
        self.title_label = QLabel("N/A")
        self.title_label.setWordWrap(True)
        self.date_label = QLabel("N/A")
        self.duration_label = QLabel("N/A")
        self.size_label = QLabel("N/A")
        
        info_layout.addLayout(create_info_row("Sitio:", self.domain_label))
        info_layout.addLayout(create_info_row("Media:", self.title_label))
        info_layout.addLayout(create_info_row("Fecha:", self.date_label))
        info_layout.addLayout(create_info_row("Duración:", self.duration_label))
        info_layout.addLayout(create_info_row("Tamaño:", self.size_label))
        
        left_column.addWidget(info_frame)
        
        # HEADER DE CONSOLA
        console_header = QHBoxLayout()
        console_header.addWidget(QLabel("Resultado de la consola"))
        console_header.addStretch()
        clear_button = QPushButton("Limpiar consola")
        clear_button.setFixedSize(120, 32)
        clear_button.setFont(QFont("Segoe UI", 10))
        clear_button.clicked.connect(self.clear_console)
        console_header.addWidget(clear_button)
        left_column.addLayout(console_header)
        
        console_wrapper = QFrame()
        console_wrapper.setStyleSheet(f"QFrame {{ background-color: {BG_PANEL}; border-radius: {RADIUS}px; }}")
        console_wrapper_layout = QVBoxLayout(console_wrapper)
        console_wrapper_layout.setContentsMargins(10, 10, 10, 10)
        
        self.console = QPlainTextEdit()
        self.console.setFont(QFont("Segoe UI", 10))
        self.console.setMinimumHeight(150) 
        self.console.setReadOnly(True)
        self.console.setFrameShape(QFrame.NoFrame)
        self.console.setStyleSheet("background-color: transparent; border: none; color: white;")
        console_wrapper_layout.addWidget(self.console)
        
        left_column.addWidget(console_wrapper, 1)
        content_layout.addLayout(left_column, 6)
        
        # RIGHT: Preview
        preview_container = QWidget()
        preview_layout = QVBoxLayout(preview_container)
        preview_layout.setContentsMargins(0, 0, 0, 0)
        
        preview_title = QLabel("Vista previa web")
        preview_title.setAlignment(Qt.AlignCenter)
        preview_layout.addWidget(preview_title)
        
        self.preview_label = AspectRatioLabel("Sin vista previa")
        self.preview_label.setFixedWidth(270)
        self.preview_label.setStyleSheet(f"background-color: {BG_PANEL}; border-radius: {RADIUS}px; color: {TEXT_SEC};")
        self.preview_label.setSizePolicy(self.preview_label.sizePolicy().horizontalPolicy(), self.preview_label.sizePolicy().verticalPolicy())
        
        preview_layout.addWidget(self.preview_label, 1, Qt.AlignHCenter)
        content_layout.addWidget(preview_container, 4)
        main_layout.addLayout(content_layout)
        
        # FOOTER
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
        footer_layout.addWidget(self.progress_bar, 1)
        
        self.download_button = QPushButton("DESCARGAR")
        self.download_button.setFixedSize(160, 45)
        self.download_button.setFont(QFont("Segoe UI", 10, QFont.Bold))
        self.download_button.setCursor(Qt.PointingHandCursor)
        self.download_button.clicked.connect(self.start_download)
        footer_layout.addWidget(self.download_button)
        
        main_layout.addWidget(footer_container)
        self.apply_styles()
    
    def apply_styles(self):
        self.setStyleSheet(f"""
            QWidget {{ background-color: {BG_MAIN}; color: white; }}
            QLabel {{ color: {TEXT_SEC}; }}
            QPlainTextEdit {{ background-color: transparent; border: none; padding: 5px; color: white; }}
            QProgressBar {{ background-color: {BG_PANEL}; border: none; border-radius: 3px; color: white; }}
            QProgressBar::chunk {{ background-color: {SUCCESS}; border-radius: 3px; }}
            QPushButton {{ background-color: {ACCENT}; border: none; border-radius: 8px; color: white; text-align: center; padding: 5px; }}
            QPushButton:hover {{ background-color: #6487E5; }}
            QPushButton:disabled {{ background-color: #555; }}
            QPushButton[secondary="true"] {{ background-color: #1C2230; }}
            QPushButton[secondary="true"]:hover {{ background-color: #252B3A; }}
            
            QScrollBar:horizontal {{
                border: none; background-color: transparent;
                height: 8px; margin: 0; border-radius: 4px;
            }}
            QScrollBar::handle:horizontal {{
                background-color: #3b4252; min-width: 20px; border-radius: 4px;
            }}
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{ width: 0px; }}
            QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {{ background: none; }}
            QScrollBar:vertical {{
                border: none; background-color: transparent;
                width: 8px; margin: 0; border-radius: 4px;
            }}
            QScrollBar::handle:vertical {{
                background-color: #3b4252; min-height: 20px; border-radius: 4px;
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0px; }}
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{ background: none; }}
        """)
        for child in self.findChildren(QPushButton):
            if child.text() in ["Elegir", "Limpiar consola"]:
                child.setProperty("secondary", "true")
    
    def select_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Seleccionar carpeta de descarga")
        if folder: self.path.setText(folder)
    
    def clear_console(self):
        with self.console_lock: self.console.setPlainText("")
    
    @Slot(int)
    def update_progress(self, percent_value):
        self.progress_bar.setValue(percent_value)
    
    @Slot(str, str, str, str, str)
    def update_video_info(self, title, date, duration, size, domain):
        self.title_label.setText(title)
        self.date_label.setText(date)
        self.duration_label.setText(duration)
        self.size_label.setText(size)
        self.domain_label.setText(domain)
    
    @Slot(bytes)
    def set_preview_image(self, image_data):
        try:
            pixmap = QPixmap()
            if pixmap.loadFromData(image_data):
                self.preview_label.setPixmap(pixmap)
            else:
                self.preview_label.setText("Error al cargar imagen")
        except Exception as e:
            pass

    @Slot(str, str)
    def add_to_console(self, message, status="info"):
        with self.console_lock:
            self.console.appendPlainText(message)
    
    def start_download(self):
        if self.is_downloading: return
        self.clear_console()
        
        # Reiniciar información visual
        self.domain_label.setText("N/A")
        self.title_label.setText("N/A")
        self.date_label.setText("N/A")
        self.duration_label.setText("N/A")
        self.size_label.setText("N/A")
        self.preview_label.setPixmap(QPixmap())
        self.preview_label.setText("Sin vista previa web")
        
        url = self.url_input.text().strip()
        if not url:
            self.add_to_console("✖ Por favor ingresa una URL válida", "error")
            return
        output_path = self.path.text()
        if not output_path or not os.path.exists(output_path):
            self.add_to_console("✖ Por favor selecciona una carpeta válida", "error")
            return
        
        self.is_downloading = True
        self.download_button.setEnabled(False)
        self.progress_bar.setValue(0)
        
        self.download_thread = UniversalDownloadThread(url, output_path, self.downloader)
        self.download_thread.progress_updated.connect(self.update_progress)
        self.download_thread.info_updated.connect(self.update_video_info)
        self.download_thread.preview_updated.connect(self.set_preview_image)
        self.download_thread.console_message.connect(self.add_to_console)
        self.download_thread.download_finished.connect(self.on_download_finished)
        self.download_thread.start()
    
    @Slot()
    def on_download_finished(self):
        self.is_downloading = False
        self.download_button.setEnabled(True)
        self.progress_bar.setValue(100)
    
    def get_widget(self) -> QWidget:
        return self
