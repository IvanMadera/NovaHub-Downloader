from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QPlainTextEdit, QLineEdit, QFrame, QFileDialog, QProgressBar, QStackedWidget
)
from PySide6.QtCore import Qt, QThread, Signal, Slot
from PySide6.QtGui import QFont, QPixmap
import os
import requests
import time
from datetime import datetime
from threading import Lock

from ui.base_ui import PlatformUI
from downloaders.instagram import InstagramDownloader

# ===== PALETA REUTILIZADA =====
BG_MAIN  = "#0E1116"
BG_PANEL = "#151A21"
ACCENT   = "#3B5998"
SUCCESS  = "#9ECE6A"
TEXT_SEC = "#A9B1D6"
ERROR    = "#F7768E"
TEXT_MAIN = "#FFFFFF"
RADIUS   = 14

class InstagramDownloadThread(QThread):
    """Thread de descarga para Videos de Instagram"""
    progress_updated = Signal(int)
    info_updated = Signal(str, str, str, str, str, str, str) # author, views, date, resolution, duration, size, description
    preview_updated = Signal(bytes)
    console_message = Signal(str, str)
    download_finished = Signal()
    
    def __init__(self, url, output_path, downloader):
        super().__init__()
        self.url = url
        self.output_path = output_path
        self.downloader = downloader
    
    def run(self):
        try:
            self.console_message.emit("➤ Iniciando proceso...", "info")
            self.console_message.emit("ℹ Obteniendo información de Instagram...", "info")
            info = self.downloader.get_video_info(self.url)
            
            if not info:
                self.console_message.emit("✗ No se pudo obtener información del video", "error")
                return
            
            author = info.get('author', 'N/A')
            views = self._format_views(info.get('view_count', 0))
            date = self._format_date(info.get('upload_date', 0))
            resolution = "N/A"
            duration = self._format_duration(info.get('duration', 0))
            size = "N/A" # No lo sabemos con instaloader de antemano de forma rapida
            description = info.get('description', 'Sin descripción')
            if len(description) > 100: description = description[:97] + "..."
            
            self.info_updated.emit(author, views, date, resolution, duration, size, description)
            
            # Obtener thumbnail
            thumbnail_url = info.get('thumbnail')
            if thumbnail_url:
                try:
                    thumb_response = requests.get(thumbnail_url, timeout=10)
                    if thumb_response.status_code == 200:
                        self.preview_updated.emit(thumb_response.content)
                except:
                    pass
            
            time.sleep(1)
            self.console_message.emit("↓ Descargando video...", "info")
            
            def progress_callback(progress_ratio):
                percent = int(progress_ratio * 100)
                self.progress_updated.emit(percent)
                
            success, title = self.downloader.download_audio(
                self.url,
                self.output_path,
                progress_callback=progress_callback
            )
            
            if success:
                self.console_message.emit(f"✔ Descarga exitosa: {title}", "success")
            else:
                self.console_message.emit("✖ La descarga falló", "error")
                
        except Exception as e:
            self.console_message.emit(f"✖ Error: {str(e)}", "error")
        finally:
            self.download_finished.emit()

    def _format_views(self, views):
        try:
            v = int(views)
            if v >= 1000000: return f"{v/1000000:.1f}M"
            if v >= 1000: return f"{v/1000:.1f}K"
            return str(v)
        except: return "0"
        
    def _format_date(self, timestamp):
        if not timestamp: return "N/A"
        try: return datetime.fromtimestamp(int(timestamp)).strftime("%d/%m/%Y")
        except: return "N/A"
        
    def _format_duration(self, seconds):
        try:
            s = int(seconds)
            m = s // 60
            s = s % 60
            return f"{m:02d}:{s:02d}"
        except: return "00:00"

class AspectRatioLabel(QLabel):
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.setMinimumSize(1, 1)
        self.setScaledContents(False) 
        self.pixmap_original = None
        self.setAlignment(Qt.AlignCenter)

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
            super().setPixmap(scaled)


class InstagramUI(PlatformUI):
    def __init__(self, parent_widget: QWidget, console_lock: Lock):
        super().__init__(parent_widget, "Instagram")
        self.console_lock = console_lock
        self.downloader = InstagramDownloader()
        self.is_downloading = False
        self.download_thread = None

    def build(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        # Header Title
        title = QLabel("DESCARGA DE CONTENIDO - INSTAGRAM")
        title.setFont(QFont("Segoe UI", 20, QFont.Bold)) 
        title.setStyleSheet(f"color: {TEXT_MAIN}; background-color: transparent;")
        main_layout.addWidget(title)
        
        # Opciones Superiores (Video vs Imagen)
        tabs_container = QWidget()
        tabs_layout = QHBoxLayout(tabs_container)
        tabs_layout.setContentsMargins(0,0,0,0)
        tabs_layout.setAlignment(Qt.AlignLeft)
        
        self.btn_video = QPushButton("Video")
        self.btn_image = QPushButton("Imagen")
        
        for btn in (self.btn_video, self.btn_image):
            btn.setFixedSize(120, 35)
            btn.setCursor(Qt.PointingHandCursor)
            tabs_layout.addWidget(btn)
        tabs_layout.addStretch()
        
        main_layout.addWidget(tabs_container)
        
        # Content Stack
        self.content_stack = QStackedWidget()
        self.page_video = QWidget()
        self.page_image = QWidget()
        
        self.setup_video_page()
        self.setup_image_page()
        
        self.content_stack.addWidget(self.page_video)
        self.content_stack.addWidget(self.page_image)
        
        main_layout.addWidget(self.content_stack)
        
        # Connect tabs
        self.btn_video.clicked.connect(lambda: self.switch_tab(0))
        self.btn_image.clicked.connect(lambda: self.switch_tab(1))
        
        self.switch_tab(0) # Default video
        self.apply_styles()

    def switch_tab(self, index):
        self.content_stack.setCurrentIndex(index)
        if index == 0:
            self.btn_video.setProperty("active", "true")
            self.btn_image.setProperty("active", "false")
        else:
            self.btn_video.setProperty("active", "false")
            self.btn_image.setProperty("active", "true")
        
        self.btn_video.style().unpolish(self.btn_video)
        self.btn_video.style().polish(self.btn_video)
        self.btn_image.style().unpolish(self.btn_image)
        self.btn_image.style().polish(self.btn_image)

    def setup_video_page(self):
        layout = QVBoxLayout(self.page_video)
        layout.setContentsMargins(0,0,0,0)
        layout.setSpacing(15)

        # URL Input
        url_container = QWidget()
        url_layout = QVBoxLayout(url_container)
        url_layout.setContentsMargins(0,0,0,0)
        url_layout.addWidget(QLabel("URL del Reel/Post de Instagram"))
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("https://www.instagram.com/reel/...")
        url_layout.addWidget(self.url_input)
        layout.addWidget(url_container)

        # Destino
        dest_container = QWidget()
        dest_layout = QHBoxLayout(dest_container)
        dest_layout.setContentsMargins(0,0,0,0)
        lbl_dest = QLabel("Carpeta destino")
        lbl_dest.setFixedWidth(110)
        dest_layout.addWidget(lbl_dest)
        self.path = QLineEdit("C:/Descargas")
        self.path.setReadOnly(True)
        dest_layout.addWidget(self.path, 1)
        btn_choose = QPushButton("Elegir")
        btn_choose.setFixedWidth(100)
        btn_choose.setFixedHeight(40)
        btn_choose.setProperty("secondary", "true")
        btn_choose.clicked.connect(self.select_folder)
        dest_layout.addWidget(btn_choose)
        layout.addWidget(dest_container)
        
        # Splitted layout (Info/Console | Preview)
        split_layout = QHBoxLayout()
        left_col = QVBoxLayout()
        
        info_frame = QFrame()
        info_frame.setProperty("panel", "true")
        info_layout = QVBoxLayout(info_frame)
        
        def add_row(txt, w):
            r = QHBoxLayout()
            l = QLabel(txt)
            l.setFixedWidth(80)
            r.addWidget(l)
            r.addWidget(w)
            info_layout.addLayout(r)

        self.lbl_author = QLabel("N/A")
        self.lbl_date = QLabel("N/A")
        self.lbl_duration = QLabel("N/A")
        
        add_row("Autor:", self.lbl_author)
        add_row("Fecha:", self.lbl_date)
        add_row("Duración:", self.lbl_duration)
        
        left_col.addWidget(info_frame)
        
        # Console
        chBox = QHBoxLayout()
        chBox.addWidget(QLabel("Consola"))
        chBox.addStretch()
        btn_clear = QPushButton("Limpiar consola")
        btn_clear.setFixedSize(120, 32)
        btn_clear.setProperty("secondary", "true")
        btn_clear.clicked.connect(self.clear_console)
        chBox.addWidget(btn_clear)
        left_col.addLayout(chBox)
        
        cFrame = QFrame()
        cFrame.setProperty("panel", "true")
        cl = QVBoxLayout(cFrame)
        self.console = QPlainTextEdit()
        self.console.setReadOnly(True)
        cl.addWidget(self.console)
        left_col.addWidget(cFrame, 1)
        
        split_layout.addLayout(left_col, 6)
        
        # Preview
        right_col = QVBoxLayout()
        right_col.addWidget(QLabel("Vista Previa"), 0, Qt.AlignCenter)
        self.preview = AspectRatioLabel("Sin vista previa")
        self.preview.setFixedWidth(270)
        self.preview.setProperty("panel", "true")
        right_col.addWidget(self.preview, 1, Qt.AlignHCenter)
        split_layout.addLayout(right_col, 4)
        
        layout.addLayout(split_layout, 1)
        
        # Footer
        footer = QHBoxLayout()
        footer.addWidget(QLabel("Progreso:"))
        self.progress = QProgressBar()
        self.progress.setValue(0)
        self.progress.setFixedHeight(8)
        self.progress.setTextVisible(False)
        footer.addWidget(self.progress, 1)
        self.btn_dl = QPushButton("DESCARGAR")
        self.btn_dl.setObjectName("btn_dl")
        self.btn_dl.setFixedSize(160, 45)
        self.btn_dl.setFont(QFont("Segoe UI", 10, QFont.Bold))
        self.btn_dl.setCursor(Qt.PointingHandCursor)
        self.btn_dl.clicked.connect(self.start_download)
        footer.addWidget(self.btn_dl)
        
        layout.addLayout(footer)

    def setup_image_page(self):
        layout = QVBoxLayout(self.page_image)
        layout.setAlignment(Qt.AlignCenter)
        lbl = QLabel("Funcionalidad de Imágenes próximamente")
        lbl.setFont(QFont("Segoe UI", 16))
        layout.addWidget(lbl)

    def apply_styles(self):
        self.setStyleSheet(f"""
            QWidget {{ background-color: transparent; color: white; }}
            QLabel {{ color: {TEXT_SEC}; }}
            QLineEdit {{ background-color: {BG_PANEL}; border:none; border-radius:8px; padding:0 10px; height:40px; }}
            QPlainTextEdit {{ background-color: transparent; border:none; color:white; }}
            QProgressBar {{ background-color:{BG_PANEL}; border:none; border-radius:3px; }}
            QProgressBar::chunk {{ background-color:{SUCCESS}; border-radius:3px; }}
            QFrame[panel="true"] {{ background-color:{BG_PANEL}; border-radius:{RADIUS}px; }}
            QPushButton {{ background-color:{BG_PANEL}; border:none; border-radius:8px; color:white; padding:5px; text-align:center; }}
            QPushButton:hover {{ background-color: #1C2230; }}
            QPushButton[active="true"] {{ background-color: {ACCENT}; font-weight:bold; }}
            QPushButton[active="true"]:hover {{ background-color: #6487E5; }}
            QPushButton[secondary="true"] {{ background-color: #1C2230; }}
            QPushButton[secondary="true"]:hover {{ background-color: #252B3A; }}
            QPushButton#btn_dl {{ background-color: {ACCENT}; }}
            QPushButton#btn_dl:hover {{ background-color: #6487E5; }}
        """)

    def select_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Seleccionar carpeta")
        if folder: self.path.setText(folder)

    def clear_console(self):
        with self.console_lock: self.console.clear()

    @Slot(int)
    def update_progress(self, percent):
        self.progress.setValue(percent)

    @Slot(str, str, str, str, str, str, str)
    def update_info(self, author, views, date, res, duration, size, desc):
        self.lbl_author.setText(author)
        self.lbl_date.setText(date)
        self.lbl_duration.setText(duration)

    @Slot(bytes)
    def update_preview(self, img_data):
        pixmap = QPixmap()
        if pixmap.loadFromData(img_data):
            self.preview.setPixmap(pixmap)

    @Slot(str, str)
    def push_msg(self, msg, status):
        with self.console_lock:
            self.console.appendPlainText(msg)

    def start_download(self):
        if self.is_downloading: return
        self.clear_console()
        
        url = self.url_input.text().strip()
        if not url:
            self.push_msg("✖ Ingresa una URL válida", "error")
            return
            
        out = self.path.text()
        if not os.path.isdir(out):
            self.push_msg("✖ Carpeta inválida", "error")
            return
            
        self.is_downloading = True
        self.btn_dl.setEnabled(False)
        self.progress.setValue(0)
        
        self.download_thread = InstagramDownloadThread(url, out, self.downloader)
        self.download_thread.progress_updated.connect(self.update_progress)
        self.download_thread.info_updated.connect(self.update_info)
        self.download_thread.preview_updated.connect(self.update_preview)
        self.download_thread.console_message.connect(self.push_msg)
        self.download_thread.download_finished.connect(self.on_dl_finished)
        self.download_thread.start()

    @Slot()
    def on_dl_finished(self):
        self.is_downloading = False
        self.btn_dl.setEnabled(True)
        self.progress.setValue(100)

    def show(self): super().show()
    def hide(self): super().hide()
    def get_widget(self) -> QWidget: return self
