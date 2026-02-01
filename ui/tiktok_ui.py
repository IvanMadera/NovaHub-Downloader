from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QPlainTextEdit, QLineEdit, QFrame, QFileDialog, QProgressBar
)
from PySide6.QtCore import Qt, QThread, Signal, Slot
from PySide6.QtGui import QFont, QPixmap, QImage
import os
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
    progress_updated = Signal(int)  # progreso en porcentaje
    info_updated = Signal(str, str, str, str, str, str, str)  # author, views, date, resolution, duration, size, description
    preview_updated = Signal(object)  # PIL Image
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
            def progress_callback(percent_value):
                self.progress_updated.emit(percent_value)
            
            result = self.downloader.download(
                self.url,
                self.output_path,
                progress_callback=progress_callback
            )
            
            if result.get('success'):
                # Actualizar información del video
                info = result.get('info', {})
                author = info.get('author', 'Desconocido')
                views = self._format_views(info.get('views', 0))
                date = self._format_date(info.get('date', ''))
                resolution = self._format_resolution(
                    info.get('width', 0),
                    info.get('height', 0)
                )
                duration = self._format_duration(info.get('duration', 0))
                size = self._format_filesize(info.get('filesize', 0))
                description = self._truncate_description(info.get('description', ''))
                
                self.info_updated.emit(author, views, date, resolution, duration, size, description)
                
                # Preview image si está disponible
                if 'preview_image' in result:
                    self.preview_updated.emit(result['preview_image'])
                
                self.console_message.emit(
                    f"✓ Descarga exitosa: {result.get('filename', 'video')}",
                    "success"
                )
            else:
                error_msg = result.get('error', 'Error desconocido')
                self.console_message.emit(f"✗ Error: {error_msg}", "error")
        
        except Exception as e:
            self.console_message.emit(f"✗ Error: {str(e)}", "error")
        
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
    
    def _format_date(self, date_str):
        """Formatea la fecha"""
        try:
            if len(date_str) == 8:  # YYYYMMDD
                return f"{date_str[6:8]}/{date_str[4:6]}/{date_str[0:4]}"
            return date_str
        except:
            return "N/A"
    
    def _format_resolution(self, width, height):
        """Formatea la resolución"""
        if width and height:
            return f"{width}x{height}"
        return "N/A"
    
    def _truncate_description(self, description):
        """Trunca la descripción"""
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
            return "0 B"


class TikTokUI(PlatformUI):
    
    def __init__(self, parent_widget: QWidget, console_lock: Lock):
        super().__init__(parent_widget, "TikTok")
        self.console_lock = console_lock
        self.downloader = TikTokDownloader()
        self.is_downloading = False
        self.download_thread = None
    
    def build(self):
        """Construye la interfaz de TikTok"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(10)
        
        # Título
        title = QLabel("DESCARGA DE CONTENIDO - TIKTOK")
        title.setFont(QFont("Segoe UI", 22, QFont.Bold))
        main_layout.addWidget(title)
        main_layout.addSpacing(10)
        
        # ================== URL + PREVIEW ==================
        top_layout = QHBoxLayout()
        
        # -------- URL --------
        left_layout = QVBoxLayout()
        url_label = QLabel("URL del video de TikTok")
        left_layout.addWidget(url_label)
        
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("https://www.tiktok.com/@usuario/video/...")
        self.url_input.setFixedHeight(50)
        left_layout.addWidget(self.url_input)
        left_layout.addStretch()
        
        # -------- PREVIEW --------
        preview_frame = QFrame()
        preview_frame.setFixedSize(180, 320)
        preview_layout = QVBoxLayout(preview_frame)
        preview_layout.setContentsMargins(0, 0, 0, 0)
        
        self.preview_label = QLabel("Vista previa")
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setStyleSheet(f"color: {TEXT_SEC};")
        preview_layout.addWidget(self.preview_label)
        
        top_layout.addLayout(left_layout, 1)
        top_layout.addSpacing(16)
        top_layout.addWidget(preview_frame)
        
        main_layout.addLayout(top_layout)
        main_layout.addSpacing(8)
        
        # ================== VIDEO INFO ==================
        info_frame = QFrame()
        info_layout = QGridLayout(info_frame)
        info_layout.setContentsMargins(16, 12, 16, 12)
        info_layout.setSpacing(8)
        
        # Row 0
        info_layout.addWidget(QLabel("Autor:"), 0, 0)
        self.author_label = QLabel("N/A")
        info_layout.addWidget(self.author_label, 0, 1)
        
        info_layout.addWidget(QLabel("Vistas:"), 0, 2)
        self.views_label = QLabel("N/A")
        info_layout.addWidget(self.views_label, 0, 3)
        
        # Row 1
        info_layout.addWidget(QLabel("Fecha:"), 1, 0)
        self.date_label = QLabel("N/A")
        info_layout.addWidget(self.date_label, 1, 1)
        
        info_layout.addWidget(QLabel("Resolución:"), 1, 2)
        self.resolution_label = QLabel("N/A")
        info_layout.addWidget(self.resolution_label, 1, 3)
        
        # Row 2
        info_layout.addWidget(QLabel("Duración:"), 2, 0)
        self.duration_label = QLabel("N/A")
        info_layout.addWidget(self.duration_label, 2, 1)
        
        info_layout.addWidget(QLabel("Tamaño:"), 2, 2)
        self.size_label = QLabel("N/A")
        info_layout.addWidget(self.size_label, 2, 3)
        
        # Row 3 - Description
        info_layout.addWidget(QLabel("Descripción:"), 3, 0)
        self.description_label = QLabel("N/A")
        self.description_label.setWordWrap(True)
        info_layout.addWidget(self.description_label, 3, 1, 1, 3)
        
        main_layout.addWidget(info_frame)
        main_layout.addSpacing(8)
        
        # ================== PROGRESS ==================
        progress_layout = QHBoxLayout()
        progress_label = QLabel("Progreso:")
        progress_layout.addWidget(progress_label)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setFixedHeight(24)
        progress_layout.addWidget(self.progress_bar)
        
        main_layout.addLayout(progress_layout)
        main_layout.addSpacing(8)
        
        # ================== DESTINO + BOTÓN ==================
        dest_layout = QHBoxLayout()
        
        dest_label = QLabel("Destino:")
        dest_layout.addWidget(dest_label)
        
        self.path = QLineEdit("C:/Descargas")
        dest_layout.addWidget(self.path)
        
        choose_button = QPushButton("Elegir")
        choose_button.setMinimumWidth(100)
        choose_button.setFixedHeight(36)
        choose_button.clicked.connect(self.select_folder)
        dest_layout.addWidget(choose_button)
        
        self.download_button = QPushButton("INICIAR DESCARGA")
        self.download_button.setMinimumSize(200, 50)
        self.download_button.setFont(QFont("Segoe UI", 13, QFont.Bold))
        self.download_button.clicked.connect(self.start_download)
        dest_layout.addWidget(self.download_button)
        
        main_layout.addLayout(dest_layout)
        main_layout.addSpacing(10)
        
        # ================== CONSOLE ==================
        console_header = QHBoxLayout()
        console_label = QLabel("Registro de actividad")
        console_header.addWidget(console_label)
        console_header.addStretch()
        
        clear_button = QPushButton("Limpiar consola")
        clear_button.setFixedSize(106, 32)
        clear_button.setFont(QFont("Segoe UI", 12))
        clear_button.clicked.connect(self.clear_console)
        console_header.addWidget(clear_button)
        
        main_layout.addLayout(console_header)
        
        self.console = QPlainTextEdit()
        self.console.setFixedHeight(140)
        self.console.setReadOnly(True)
        self.console.setPlainText("Esperando URL de TikTok...\n")
        main_layout.addWidget(self.console)
        
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
            
            QPlainTextEdit, QLineEdit {{
                background-color: {BG_PANEL};
                border: none;
                border-radius: {RADIUS}px;
                padding: 8px;
                color: white;
            }}
            
            QFrame {{
                background-color: {BG_PANEL};
                border-radius: {RADIUS}px;
            }}
            
            QProgressBar {{
                background-color: {BG_PANEL};
                border: none;
                border-radius: 4px;
                text-align: center;
                color: white;
            }}
            
            QProgressBar::chunk {{
                background-color: {SUCCESS};
                border-radius: 4px;
            }}
            
            QPushButton {{
                background-color: {ACCENT};
                border: none;
                border-radius: 8px;
                color: white;
                padding: 10px;
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
            self.console.setPlainText("Esperando URL de TikTok...\n")
    
    @Slot(int)
    def update_progress(self, percent_value):
        """Actualiza la barra de progreso"""
        self.progress_bar.setValue(percent_value)
    
    @Slot(str, str, str, str, str, str, str)
    def update_video_info(self, author, views, date, resolution, duration, size, description):
        """Actualiza la información del video"""
        self.author_label.setText(author)
        self.views_label.setText(views)
        self.date_label.setText(date)
        self.resolution_label.setText(resolution)
        self.duration_label.setText(duration)
        self.size_label.setText(size)
        self.description_label.setText(description)
    
    @Slot(object)
    def set_preview_image(self, pil_image):
        """Actualiza la imagen de preview"""
        try:
            # Convertir PIL Image a QPixmap
            pil_image = pil_image.convert('RGB')
            data = pil_image.tobytes('raw', 'RGB')
            qimage = QImage(data, pil_image.width, pil_image.height, QImage.Format_RGB888)
            pixmap = QPixmap.fromImage(qimage)
            scaled_pixmap = pixmap.scaled(180, 320, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.preview_label.setPixmap(scaled_pixmap)
        except Exception as e:
            print(f"Error actualizando preview: {e}")
    
    @Slot(str, str)
    def add_to_console(self, message, status="info"):
        """Agrega mensaje a la consola"""
        with self.console_lock:
            self.console.appendPlainText(message)
    
    def start_download(self):
        """Inicia el proceso de descarga"""
        if self.is_downloading:
            self.add_to_console("✗ Ya hay una descarga en progreso", "error")
            return
        
        url = self.url_input.text().strip()
        if not url:
            self.add_to_console("✗ Por favor ingresa una URL válida", "error")
            return
        
        output_path = self.path.text()
        if not output_path or not os.path.exists(output_path) or not os.path.isdir(output_path):
            self.add_to_console("✗ Por favor selecciona una carpeta válida", "error")
            return
        
        self.is_downloading = True
        self.download_button.setEnabled(False)
        self.progress_bar.setValue(0)
        
        with self.console_lock:
            self.console.setPlainText("Iniciando descarga...\n")
        
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