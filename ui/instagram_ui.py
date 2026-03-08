from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QPlainTextEdit, QLineEdit, QFrame, QFileDialog, QProgressBar, QStackedWidget,
    QScrollArea
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

class InstagramImageFetchThread(QThread):
    """Thread para extraer las URLs de las imágenes sin congelar la UI"""
    fetch_finished = Signal(dict) # info dictionary
    console_message = Signal(str, str)
    
    def __init__(self, url, downloader):
        super().__init__()
        self.url = url
        self.downloader = downloader
        
    def run(self):
        try:
            self.console_message.emit("ℹ Obteniendo imágenes...", "info")
            info = self.downloader.get_images_info(self.url)
            
            if not info or not info.get('images'):
                self.console_message.emit("✖ No se encontraron imágenes en el link provisto.", "error")
                self.fetch_finished.emit({})
                return
                
            self.console_message.emit(f"✓ Se encontraron {len(info['images'])} imágenes.", "success")
            self.fetch_finished.emit(info)
            
        except Exception as e:
            self.console_message.emit(f"✖ Error extracting images: {str(e)}", "error")
            self.fetch_finished.emit({})

class InstagramImagesDownloadThread(QThread):
    """Thread para descargar masivamente una lista de imágenes"""
    progress_updated = Signal(int, int) # completed, total
    console_message = Signal(str, str)
    download_finished = Signal()
    
    def __init__(self, images_to_download, output_path):
        super().__init__()
        self.images = images_to_download
        self.output_path = output_path
        
    def run(self):
        try:
            total = len(self.images)
            self.console_message.emit(f"↓ Iniciando descarga de {total} imágenes...", "info")
            
            for index, img_data in enumerate(self.images):
                url = img_data['url']
                filename = img_data['filename']
                filepath = os.path.join(self.output_path, filename)
                
                try:
                    response = requests.get(url, stream=True, timeout=15)
                    if response.status_code == 200:
                        with open(filepath, 'wb') as f:
                            for chunk in response.iter_content(chunk_size=8192):
                                if chunk:
                                    f.write(chunk)
                        
                        self.console_message.emit(f"✓ Guardado: {filename}", "success")
                    else:
                        self.console_message.emit(f"✖ Error al descargar {filename}", "error")
                except Exception as e:
                    self.console_message.emit(f"✖ Error de red con {filename}: {e}", "error")
                
                # Emitir progreso actualizando 1 a 1
                self.progress_updated.emit(index + 1, total)
                
            self.console_message.emit("⭐ Proceso de descarga finalizado.", "success")
        except Exception as e:
            self.console_message.emit(f"✖ Error general en descarga: {str(e)}", "error")
        finally:
            self.download_finished.emit()

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

class ImageLoaderThread(QThread):
    """Thread ligero para descargar miniaturas sin congelar la UI"""
    finished = Signal(bytes)
    
    def __init__(self, url):
        super().__init__()
        self.url = url
        
    def run(self):
        try:
            resp = requests.get(self.url, timeout=5)
            if resp.status_code == 200:
                self.finished.emit(resp.content)
            else:
                self.finished.emit(b"") # Error
        except:
            self.finished.emit(b"")

class ImageSelectButton(QFrame):
    """Custom widget: A picture that acts like a toggle button"""
    toggled = Signal(bool, dict) # emite estado y la metadata de la imagen
    
    def __init__(self, img_data):
        super().__init__()
        self.img_data = img_data
        self.is_selected = True
        
        self.setFixedSize(150, 150)
        self.setCursor(Qt.PointingHandCursor)
        self.setProperty("selected", "true")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        self.image_label = AspectRatioLabel("Cargando...")
        layout.addWidget(self.image_label)
        
        # Iniciar thread asíncrono para la miniatura
        self.loader_thread = ImageLoaderThread(self.img_data['url'])
        self.loader_thread.finished.connect(self._on_image_loaded)
        self.loader_thread.start()
        
    @Slot(bytes)
    def _on_image_loaded(self, data):
        if data:
            pixmap = QPixmap()
            pixmap.loadFromData(data)
            self.image_label.setPixmap(pixmap)
        else:
            self.image_label.setText("Error")

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.is_selected = not self.is_selected
            self.setProperty("selected", "true" if self.is_selected else "false")
            self.style().unpolish(self)
            self.style().polish(self)
            self.toggled.emit(self.is_selected, self.img_data)
        super().mousePressEvent(event)


class InstagramUI(PlatformUI):
    def __init__(self, parent_widget: QWidget, console_lock: Lock):
        super().__init__(parent_widget, "Instagram")
        self.console_lock = console_lock
        self.downloader = InstagramDownloader()
        self.is_downloading = False
        self.download_thread = None
        self.image_fetch_thread = None
        self.images_download_thread = None
        
        # Estado de imagenes
        self.fetched_images = []
        self.selected_images = []

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
        self.url_input.setFixedHeight(40)
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
        self.path.setFixedHeight(40)
        self.path.setReadOnly(True)
        dest_layout.addWidget(self.path, 1)
        btn_choose = QPushButton("Elegir")
        btn_choose.setFont(QFont("Segoe UI", 10))
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
        info_layout.setContentsMargins(15, 15, 15, 15)
        info_layout.setSpacing(10)
        
        def add_row(txt, w):
            r = QHBoxLayout()
            l = QLabel(txt)
            l.setStyleSheet(f"color: {TEXT_SEC}; font-weight: bold;")
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
        chBox.addWidget(QLabel("Resultado de la consola"))
        chBox.addStretch()
        btn_clear = QPushButton("Limpiar consola")
        btn_clear.setFont(QFont("Segoe UI", 10))
        btn_clear.setFixedSize(120, 32)
        btn_clear.setProperty("secondary", "true")
        btn_clear.clicked.connect(self.clear_console)
        chBox.addWidget(btn_clear)
        left_col.addLayout(chBox)
        
        cFrame = QFrame()
        cFrame.setProperty("panel", "true")
        cl = QVBoxLayout(cFrame)
        cl.setContentsMargins(10, 10, 10, 10)
        self.console = QPlainTextEdit()
        self.console.setMinimumHeight(150)
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
        layout.setContentsMargins(0,0,0,0)
        layout.setSpacing(15)
        
        # 1. Input URL e Iniciar Busqueda
        header_layout = QHBoxLayout()
        lbl_url = QLabel("URL del Carrusel")
        lbl_url.setFixedWidth(110)
        header_layout.addWidget(lbl_url)
        self.img_url_input = QLineEdit()
        self.img_url_input.setFixedHeight(40)
        self.img_url_input.setPlaceholderText("https://www.instagram.com/p/...")
        header_layout.addWidget(self.img_url_input, 1)
        
        self.btn_fetch = QPushButton("Buscar")
        self.btn_fetch.setFont(QFont("Segoe UI", 10))
        self.btn_fetch.setFixedSize(100, 40)
        self.btn_fetch.setProperty("secondary", "true")
        self.btn_fetch.clicked.connect(self.start_image_fetch)
        header_layout.addWidget(self.btn_fetch)
        layout.addLayout(header_layout)
        
        # 2. Destino
        dest_layout = QHBoxLayout()
        lbl_dest = QLabel("Carpeta destino")
        lbl_dest.setFixedWidth(110)
        dest_layout.addWidget(lbl_dest)
        
        self.img_path = QLineEdit("C:/Descargas")
        self.img_path.setFixedHeight(40)
        self.img_path.setReadOnly(True)
        dest_layout.addWidget(self.img_path, 1)
        
        btn_choose = QPushButton("Elegir")
        btn_choose.setFont(QFont("Segoe UI", 10))
        btn_choose.setFixedSize(100, 40)
        btn_choose.setProperty("secondary", "true")
        btn_choose.clicked.connect(self.select_img_folder)
        dest_layout.addWidget(btn_choose)
        layout.addLayout(dest_layout)
        
        # 3. Area Central (Galeria + Consola)
        split_layout = QHBoxLayout()
        
        # Galeria
        gallery_container = QWidget()
        gal_layout = QVBoxLayout(gallery_container)
        gal_layout.setContentsMargins(0,0,0,0)
        gal_layout.addWidget(QLabel("Galería (Clic para seleccionar/deseleccionar)"))
        
        # Scroll Area para imagenes
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setProperty("panel", "true")
        self.scroll_area.setStyleSheet("QScrollArea { border: none; background-color: transparent; }")
        
        self.gallery_widget = QWidget()
        self.gallery_widget.setStyleSheet("background-color: transparent;")
        # Usamos Flow o Wrap. En un QVBoxLayout meteremos filas (QHBoxLayout)
        self.gallery_layout = QVBoxLayout(self.gallery_widget)
        self.gallery_layout.setAlignment(Qt.AlignTop)
        
        self.scroll_area.setWidget(self.gallery_widget)
        gal_layout.addWidget(self.scroll_area)
        
        split_layout.addWidget(gallery_container, 6)
        
        # Consola Imagnes
        console_container = QWidget()
        cons_layout = QVBoxLayout(console_container)
        cons_layout.setContentsMargins(0,0,0,0)
        
        chBox = QHBoxLayout()
        chBox.addWidget(QLabel("Resultado de la consola"))
        chBox.addStretch()
        btn_clear = QPushButton("Limpiar consola")
        btn_clear.setFont(QFont("Segoe UI", 10))
        btn_clear.setFixedSize(120, 32)
        btn_clear.setProperty("secondary", "true")
        btn_clear.clicked.connect(self.clear_img_console)
        chBox.addWidget(btn_clear)
        cons_layout.addLayout(chBox)
        
        cFrame = QFrame()
        cFrame.setProperty("panel", "true")
        cl = QVBoxLayout(cFrame)
        cl.setContentsMargins(10, 10, 10, 10)
        self.img_console = QPlainTextEdit()
        self.img_console.setMinimumHeight(150)
        self.img_console.setReadOnly(True)
        cl.addWidget(self.img_console)
        cons_layout.addWidget(cFrame, 1)
        
        split_layout.addWidget(console_container, 4)
        
        layout.addLayout(split_layout, 1)
        
        # 4. Footer (Progress + Download Selected)
        footer = QHBoxLayout()
        footer.addWidget(QLabel("Progreso:"))
        self.img_progress = QProgressBar()
        self.img_progress.setValue(0)
        self.img_progress.setFixedHeight(8)
        self.img_progress.setTextVisible(False)
        footer.addWidget(self.img_progress, 1)
        
        self.btn_img_dl = QPushButton("DESCARGAR SELECCIONADAS")
        self.btn_img_dl.setObjectName("btn_dl")
        self.btn_img_dl.setFixedSize(220, 45)
        self.btn_img_dl.setFont(QFont("Segoe UI", 10, QFont.Bold))
        self.btn_img_dl.setCursor(Qt.PointingHandCursor)
        self.btn_img_dl.setEnabled(False)
        self.btn_img_dl.clicked.connect(self.start_images_download)
        footer.addWidget(self.btn_img_dl)
        
        layout.addLayout(footer)

    def apply_styles(self):
        self.setStyleSheet(f"""
            QWidget {{ background-color: transparent; color: white; }}
            QLabel {{ color: {TEXT_SEC}; }}
            QLineEdit {{
                background-color: {BG_PANEL};
                border: none;
                border-radius: 8px;
                padding: 0 10px;
                color: white;
                selection-background-color: {BG_PANEL}; 
                selection-color: white;
            }}
            QPlainTextEdit {{ background-color: transparent; border:none; color:white; }}
            QProgressBar {{ background-color:{BG_PANEL}; border:none; border-radius:3px; }}
            QProgressBar::chunk {{ background-color:{SUCCESS}; border-radius:3px; }}
            QFrame[panel="true"] {{ background-color:{BG_PANEL}; border-radius:{RADIUS}px; }}
            
            QScrollBar:vertical {{
                border: none;
                background-color: {BG_MAIN};
                width: 12px;
                margin: 0px 0px 0px 0px;
                border-radius: 6px;
            }}
            QScrollBar::handle:vertical {{
                background-color: {BG_PANEL};
                min-height: 20px;
                border-radius: 6px;
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0px; }}
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{ background: none; }}
            
            QPushButton {{ background-color:{BG_PANEL}; border:none; border-radius:8px; color:white; padding:5px; text-align:center; }}
            QPushButton:hover {{ background-color: #1C2230; }}
            QPushButton[active="true"] {{ background-color: {ACCENT}; font-weight:bold; }}
            QPushButton[active="true"]:hover {{ background-color: #6487E5; }}
            QPushButton[secondary="true"] {{ background-color: #1C2230; }}
            QPushButton[secondary="true"]:hover {{ background-color: #252B3A; }}
            QPushButton#btn_dl {{ background-color: {ACCENT}; }}
            QPushButton#btn_dl:hover {{ background-color: #6487E5; }}
            QPushButton#btn_dl:disabled {{ background-color: #555; color: #aaa; }}
            
            /* Galeria Selection Style */
            ImageSelectButton {{ background-color: {BG_PANEL}; border-radius: 8px; border: 2px solid transparent; }}
            ImageSelectButton[selected="true"] {{ border: 2px solid {ACCENT}; }}
        """)

    def select_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Seleccionar carpeta")
        if folder: self.path.setText(folder)
        
    def select_img_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Seleccionar carpeta")
        if folder: self.img_path.setText(folder)

    def clear_console(self):
        with self.console_lock: self.console.clear()
        
    def clear_img_console(self):
        with self.console_lock: self.img_console.clear()

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
            
    @Slot(str, str)
    def push_img_msg(self, msg, status):
        with self.console_lock:
            self.img_console.appendPlainText(msg)

    # ================= FUNCIONES DE VIDEO =================

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

    # ================= FUNCIONES DE IMÁGENES =================
    
    def start_image_fetch(self):
        if self.is_downloading: return
        self.clear_img_console()
        
        url = self.img_url_input.text().strip()
        if not url:
            self.push_img_msg("✖ Ingresa una URL válida", "error")
            return
            
        self.btn_fetch.setEnabled(False)
        self.btn_img_dl.setEnabled(False)
        self.clear_gallery()
        
        self.image_fetch_thread = InstagramImageFetchThread(url, self.downloader)
        self.image_fetch_thread.console_message.connect(self.push_img_msg)
        self.image_fetch_thread.fetch_finished.connect(self.on_fetch_finished)
        self.image_fetch_thread.start()

    def clear_gallery(self):
        self.fetched_images.clear()
        self.selected_images.clear()
        # Eliminar widgets del layout
        while self.gallery_layout.count():
            item = self.gallery_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
            elif item.layout() is not None:
                # Si es un row layout
                while item.layout().count():
                    subitem = item.layout().takeAt(0)
                    if subitem.widget(): subitem.widget().deleteLater()
                item.layout().deleteLater()

    @Slot(dict)
    def on_fetch_finished(self, info):
        self.btn_fetch.setEnabled(True)
        if not info or not info.get('images'):
            return
            
        images = info['images']
        self.fetched_images = images
        self.selected_images = list(images) # Por defecto todas seleccionadas
        
        # Llenar grilla (3 columnas por simplicidad)
        columns = 3
        current_row_layout = None
        
        for i, img_data in enumerate(images):
            if i % columns == 0:
                current_row_layout = QHBoxLayout()
                current_row_layout.setAlignment(Qt.AlignLeft)
                self.gallery_layout.addLayout(current_row_layout)
                
            btn = ImageSelectButton(img_data)
            btn.toggled.connect(self.on_image_toggled)
            current_row_layout.addWidget(btn)
        
        self.btn_img_dl.setText(f"DESCARGAR SELECCIONADAS ({len(self.selected_images)})")
        self.btn_img_dl.setEnabled(True)

    @Slot(bool, dict)
    def on_image_toggled(self, is_selected, img_data):
        if is_selected:
            if img_data not in self.selected_images:
                self.selected_images.append(img_data)
        else:
            if img_data in self.selected_images:
                self.selected_images.remove(img_data)
                
        count = len(self.selected_images)
        self.btn_img_dl.setText(f"DESCARGAR SELECCIONADAS ({count})")
        self.btn_img_dl.setEnabled(count > 0)

    def start_images_download(self):
        if not self.selected_images: return
        
        out = self.img_path.text()
        if not os.path.isdir(out):
            self.push_img_msg("✖ Carpeta inválida", "error")
            return
            
        self.is_downloading = True
        self.btn_img_dl.setEnabled(False)
        self.btn_fetch.setEnabled(False)
        self.img_progress.setValue(0)
        
        self.images_download_thread = InstagramImagesDownloadThread(self.selected_images, out)
        self.images_download_thread.progress_updated.connect(self.update_img_progress)
        self.images_download_thread.console_message.connect(self.push_img_msg)
        self.images_download_thread.download_finished.connect(self.on_img_dl_finished)
        self.images_download_thread.start()

    @Slot(int, int)
    def update_img_progress(self, completed, total):
        pct = int((completed / total) * 100)
        self.img_progress.setValue(pct)

    @Slot()
    def on_img_dl_finished(self):
        self.is_downloading = False
        self.btn_fetch.setEnabled(True)
        self.btn_img_dl.setEnabled(True)
        # self.img_progress.setValue(100)

    def show(self): super().show()
    def hide(self): super().hide()
    def get_widget(self) -> QWidget: return self
