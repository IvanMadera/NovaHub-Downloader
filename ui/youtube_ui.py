from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QPlainTextEdit, QLineEdit, QFrame, QFileDialog
)
from PySide6.QtCore import Qt, QThread, Signal, Slot
from PySide6.QtGui import QFont, QPixmap
import time
import re
import os
from threading import Lock

from downloaders.youtube import YouTubeDownloader
from ui.base_ui import PlatformUI

# ===== PALETA =====
BG_MAIN  = "#0E1116"
BG_PANEL = "#151A21"
ACCENT   = "#3B5998"
SUCCESS  = "#9ECE6A"
TEXT_SEC = "#A9B1D6"
ERROR    = "#F7768E"
TEXT_MAIN = "#FFFFFF"
RADIUS   = 14


class DownloadThread(QThread):
    """Thread de descarga con signals"""
    progress_updated = Signal(int, str)  # queue_count, progress_percentage
    stats_updated = Signal(int, int, int, int)  # queue, progress_num, successful, failed
    title_updated = Signal(str)
    success_added = Signal(str)
    failed_added = Signal(str)
    error_occurred = Signal(str)
    download_finished = Signal()
    
    def __init__(self, urls, output_path, downloader):
        super().__init__()
        self.urls = urls
        self.output_path = output_path
        self.downloader = downloader
        self.successful_downloads = []
        self.failed_downloads = []
        self.is_running = True
    
    def run(self):
        """Ejecuta las descargas"""
        try:
            total = len(self.urls)
            
            for idx, url in enumerate(self.urls):
                if not self.is_running:
                    break
                
                self.stats_updated.emit(
                    total - idx,
                    0,
                    len(self.successful_downloads),
                    len(self.failed_downloads)
                )
                
                def progress_callback(percent, speed, eta):
                    match = re.search(r'[\d.]+%', percent)
                    percent_only = match.group() if match else "0%"
                    self.progress_updated.emit(total - idx - 1, percent_only)
                
                def title_callback(title):
                    self.title_updated.emit(title)
                
                success, title = self.downloader.download_audio(
                    url, self.output_path, progress_callback, title_callback
                )
                
                if success and title:
                    self.successful_downloads.append(title)
                    self.success_added.emit(title)
                    self.stats_updated.emit(
                        total - idx - 1,
                        100,
                        len(self.successful_downloads),
                        len(self.failed_downloads)
                    )
                else:
                    self.failed_downloads.append(url)
                    self.failed_added.emit(url)
                    self.stats_updated.emit(
                        total - idx - 1,
                        0,
                        len(self.successful_downloads),
                        len(self.failed_downloads)
                    )
        
        except Exception as e:
            self.error_occurred.emit(f"Error durante la descarga: {str(e)}")
        
        finally:
            self.download_finished.emit()
    
    def stop(self):
        """Detiene el thread"""
        self.is_running = False


class YouTubeUI(PlatformUI):
    
    def __init__(self, parent_widget: QWidget, console_lock: Lock):
        super().__init__(parent_widget, "YouTube")
        self.console_lock = console_lock
        self.downloader = YouTubeDownloader()
        self.successful_downloads = []
        self.failed_downloads = []
        self.is_downloading = False
        self.download_thread = None
        
        # Referencias a widgets
        self.queue_value_label = None
        self.progress_value_label = None
        self.success_value_label = None
        self.failed_value_label = None
        
    def build(self):
        """Construye la interfaz de YouTube"""
        # Usar Grid Layout para mejor adaptación
        main_layout = QGridLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)
        
        # Columna 0 estirable (Links)
        # Columna 1 fija (Preview)
        main_layout.setColumnStretch(0, 1)
        main_layout.setColumnStretch(1, 0)
        
        # ================== 1. TÍTULO (Fila 0) ==================
        title = QLabel("DESCARGA DE CONTENIDO - YOUTUBE")
        title.setFont(QFont("Segoe UI", 20, QFont.Bold))
        title.setStyleSheet(f"color: {TEXT_MAIN}; background-color: transparent;")
        main_layout.addWidget(title, 0, 0, 1, 2)
        
        # ================== 2. LINKS Y PREVIEW (Fila 1) ==================
        
        # --- Lado Izquierdo: Links ---
        links_container = QWidget()
        links_layout = QVBoxLayout(links_container)
        links_layout.setContentsMargins(0, 0, 0, 0)
        links_layout.setSpacing(5)
        
        links_label = QLabel("Enlaces (uno por línea)")
        links_label.setStyleSheet("background-color: transparent;")
        links_layout.addWidget(links_label)
        
        # Wrapper para Links
        links_container_frame = QFrame()
        links_container_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {BG_PANEL};
                border-radius: {RADIUS}px;
            }}
        """)
        links_frame_layout = QVBoxLayout(links_container_frame)
        links_frame_layout.setContentsMargins(10, 10, 10, 10)
        
        self.links = QPlainTextEdit()
        self.links.setPlaceholderText("https://youtube.com/...")
        self.links.setMinimumHeight(120)
        self.links.setFrameShape(QFrame.NoFrame) # Quitar borde nativo
        self.links.setStyleSheet("background-color: transparent; color: white;")
        self.links.textChanged.connect(self.clean_links)
        
        links_frame_layout.addWidget(self.links)
        links_layout.addWidget(links_container_frame)
        
        main_layout.addWidget(links_container, 1, 0)
        
        # --- Lado Derecho: Preview ---
        preview_container = QWidget()
        preview_layout = QVBoxLayout(preview_container)
        preview_layout.setContentsMargins(0, 0, 0, 0)
        preview_layout.setSpacing(5)
        
        # Espaciador para alinear con el input de texto (SIN WIDGET, SOLO ESPACIO)
        # Espaciador ARRIBA para centrar verticalmente
        preview_layout.addStretch()
        
        preview_frame = QFrame()
        preview_frame.setFixedSize(220, 180) # Un poco más grande para pantallas grandes
        preview_frame.setStyleSheet("background-color: transparent; border: none;") # Quitar fondo y borde
        frame_layout = QVBoxLayout(preview_frame)
        frame_layout.setContentsMargins(0, 0, 0, 0)
        
        self.preview_label = QLabel()
        try:
            pixmap = QPixmap("assets/NovaHub_title.png")
            if not pixmap.isNull():
                scaled_pixmap = pixmap.scaled(200, 160, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                self.preview_label.setPixmap(scaled_pixmap)
        except Exception as e:
            print(f"Error cargando imagen: {e}")
            self.preview_label.setText("Vista previa")
        
        self.preview_label.setAlignment(Qt.AlignCenter)
        frame_layout.addWidget(self.preview_label)
        
        preview_layout.addWidget(preview_frame)
        
        # Espaciador ABAJO para centrar verticalmente
        preview_layout.addStretch()
        
        main_layout.addWidget(preview_container, 1, 1)
        
        # ================== 3. INFO VIDEO (Fila 2) ==================
        info_frame = QFrame()
        info_frame.setFixedHeight(80)
        info_layout = QVBoxLayout(info_frame)
        info_layout.setContentsMargins(16, 10, 16, 10)
        info_layout.setSpacing(2)
        
        info_title = QLabel("Título del video")
        info_title.setFont(QFont("Segoe UI", 13, QFont.Bold))
        info_layout.addWidget(info_title)
        
        self.video_title = QLabel("Esperando descarga")
        info_layout.addWidget(self.video_title)
        
        main_layout.addWidget(info_frame, 2, 0, 1, 2)
        
        # ================== 4. ESTADÍSTICAS Y BOTÓN (Fila 3) ==================
        stats_container = QWidget()
        stats_grid = QGridLayout(stats_container)
        stats_grid.setContentsMargins(0, 0, 0, 0)
        stats_grid.setSpacing(10)
        
        # Cards de estadísticas distribuidas
        self.queue_card = self.create_card("EN COLA", "0")
        stats_grid.addWidget(self.queue_card, 0, 0)
        
        self.progress_card = self.create_card("PROGRESO", "0%")
        stats_grid.addWidget(self.progress_card, 0, 1)
        
        self.success_card = self.create_card("EXITOSOS", "0", SUCCESS)
        stats_grid.addWidget(self.success_card, 0, 2)
        
        self.failed_card = self.create_card("FALLIDOS", "0", ERROR)
        stats_grid.addWidget(self.failed_card, 0, 3)
        
        # Botón grande a la derecha
        self.download_button = QPushButton("INICIAR DESCARGA")
        self.download_button.setMinimumWidth(200)
        self.download_button.setFixedHeight(100)
        self.download_button.setFont(QFont("Segoe UI", 12, QFont.Bold))
        self.download_button.setCursor(Qt.PointingHandCursor)
        self.download_button.clicked.connect(self.start_download)
        # Estilo específico para centrar y asegurar radius
        self.download_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {ACCENT};
                border-radius: {RADIUS}px;
                color: white;
                text-align: center;
                padding: 10px;
            }}
            QPushButton:hover {{
                background-color: #6487E5;
            }}
        """)
        
        stats_grid.addWidget(self.download_button, 0, 4)
        
        # Asegurar que las columnas de stats se distribuyan igual
        for i in range(4):
            stats_grid.setColumnStretch(i, 1)
        stats_grid.setColumnStretch(4, 0) # Botón no estira más de lo necesario
        
        main_layout.addWidget(stats_container, 3, 0, 1, 2)
        
        # ================== 5. DESTINO (Fila 4) ==================
        dest_container = QWidget()
        dest_layout = QHBoxLayout(dest_container)
        dest_layout.setContentsMargins(0, 0, 0, 0)
        
        dest_label = QLabel("Destino:")
        dest_label.setStyleSheet("background-color: transparent;")
        dest_label.setFixedWidth(70)
        dest_layout.addWidget(dest_label)
        
        self.path = QLineEdit("C:/Descargas")
        self.path.setFixedHeight(40)
        self.path.setReadOnly(True)  # Solo lectura, solo se cambia con el botón "Elegir"
        # Redondear menos el campo de destino (ej. 8px en lugar de RADIUS)
        # Forzar color de selección para evitar el rojo por defecto del sistema
        # Hacemos que la selección sea del mismo color que el fondo para que sea "invisible"
        self.path.setStyleSheet(f"""
            QLineEdit {{
                background-color: {BG_PANEL};
                border: none;
                border-radius: 8px;
                padding: 0 10px;
                color: white;
                selection-background-color: {BG_PANEL}; 
                selection-color: white;
            }}
        """)
        dest_layout.addWidget(self.path)
        
        choose_button = QPushButton("Elegir")
        choose_button.setFixedWidth(100)
        choose_button.setFixedHeight(40)
        choose_button.setFont(QFont("Segoe UI", 10))
        choose_button.clicked.connect(self.select_folder)
        # Homologar radius para botón Elegir (MENOS REDONDEADO)
        choose_button.setStyleSheet(f"""
            QPushButton {{
                background-color: #1C2230;
                border-radius: 8px;
                color: white;
                text-align: center;
            }}
            QPushButton:hover {{
                background-color: #252B3A;
            }}
        """)
        dest_layout.addWidget(choose_button)
        
        main_layout.addWidget(dest_container, 4, 0, 1, 2)
        
        # ================== 6. CONSOLA (Fila 5) ==================
        
        # Header consola
        console_header = QWidget()
        header_layout = QHBoxLayout(console_header)
        header_layout.setContentsMargins(0, 0, 0, 0)
        
        console_label = QLabel("Resultado de la cola")
        console_label.setStyleSheet("background-color: transparent;")
        header_layout.addWidget(console_label)
        header_layout.addStretch()
        
        clear_button = QPushButton("Limpiar consola")
        clear_button.setFixedSize(120, 32)
        clear_button.setFont(QFont("Segoe UI", 10))
        clear_button.clicked.connect(self.clear_console)
        # Forzar estilos específicos para este botón (MENOS REDONDEADO)
        clear_button.setStyleSheet(f"""
            QPushButton {{
                background-color: #1C2230;
                border-radius: 8px;
                color: white;
                text-align: center;
                padding: 5px;
            }}
            QPushButton:hover {{
                background-color: #252B3A;
            }}
        """)
        header_layout.addWidget(clear_button)
        
        main_layout.addWidget(console_header, 5, 0, 1, 2)
        
        # Consola log
        # Wrapper para Consola
        console_container_frame = QFrame()
        console_container_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {BG_PANEL};
                border-radius: {RADIUS}px;
            }}
        """)
        console_frame_layout = QVBoxLayout(console_container_frame)
        console_frame_layout.setContentsMargins(10, 10, 10, 10)
        
        self.console = QPlainTextEdit()
        self.console.setMinimumHeight(100)
        self.console.setReadOnly(True)
        self.console.setFrameShape(QFrame.NoFrame)
        self.console.setStyleSheet("background-color: transparent; color: white;")
        self.console.setPlainText("✔ Exitosos:\n✖ Fallidos:")
        
        console_frame_layout.addWidget(self.console)
        main_layout.addWidget(console_container_frame, 6, 0, 1, 2)
        
        # Set row stretches to make Links and Console grow
        main_layout.setRowStretch(1, 2) # Links area grows
        main_layout.setRowStretch(6, 1) # Console grows less
        
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
            
            QPushButton {{
                background-color: {ACCENT};
                border: none;
                border-radius: {RADIUS}px;
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
                border-radius: {RADIUS}px;
            }}
            
            QPushButton[secondary="true"]:hover {{
                background-color: #252B3A;
            }}
        """)
        
        # Aplicar atributo secondary a botones específicos
        if hasattr(self, 'path'):
            for child in self.findChildren(QPushButton):
                if child.text() in ["Elegir", "Limpiar consola"]:
                    child.setProperty("secondary", "true")
    
    def create_card(self, title, value, color="white"):
        """Crea una tarjeta de estadística"""
        card = QFrame()
        card.setFixedHeight(100)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(10, 22, 10, 10)
        layout.setSpacing(2)
        
        value_label = QLabel(value)
        value_label.setFont(QFont("Segoe UI", 26, QFont.Bold))
        value_label.setStyleSheet(f"color: {color};")
        value_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(value_label)
        
        title_label = QLabel(title)
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # Guardar referencia al label del valor
        if "COLA" in title:
            self.queue_value_label = value_label
        elif "PROGRESO" in title:
            self.progress_value_label = value_label
        elif "EXITOSOS" in title:
            self.success_value_label = value_label
        elif "FALLIDOS" in title:
            self.failed_value_label = value_label
        
        return card
    
    def clean_links(self):
        """Elimina líneas vacías duplicadas"""
        # No implementamos limpieza automática en Qt para evitar problemas de cursor
        pass
    
    def select_folder(self):
        """Abre diálogo para seleccionar carpeta"""
        folder = QFileDialog.getExistingDirectory(self, "Seleccionar carpeta de descarga")
        if folder:
            self.path.setText(folder)
    
    @Slot(int, int, int, int)
    def update_stats(self, queue_count, progress, successful, failed):
        """Actualiza las estadísticas"""
        if self.queue_value_label:
            self.queue_value_label.setText(str(queue_count))
        if self.progress_value_label:
            self.progress_value_label.setText(f"{progress}%")
        if self.success_value_label:
            self.success_value_label.setText(str(successful))
        if self.failed_value_label:
            self.failed_value_label.setText(str(failed))
    
    @Slot(str)
    def add_success_to_console(self, title):
        """Agrega un título exitoso a la consola"""
        with self.console_lock:
            current_text = self.console.toPlainText()
            failed_pos = current_text.find("✖ Fallidos:")
            
            if failed_pos != -1:
                before = current_text[:failed_pos]
                after = current_text[failed_pos:]
                new_text = f"{before}  {len(self.successful_downloads)}. {title}\n{after}"
                self.console.setPlainText(new_text)
            else:
                self.console.appendPlainText(f"  {len(self.successful_downloads)}. {title}")
        
        time.sleep(1)
    
    @Slot(str)
    def add_failed_to_console(self, title):
        """Agrega un título fallido a la consola"""
        with self.console_lock:
            self.console.appendPlainText(f"  {len(self.failed_downloads)}. {title}")
        time.sleep(1)
    
    @Slot(str)
    def show_console_error(self, message):
        """Muestra un error en la consola"""
        with self.console_lock:
            # Usar símbolo ✖ para consistencia y sin saltos extra
            self.console.appendPlainText(f"✖ {message}")
    
    def clear_console(self):
        """Limpia la consola"""
        with self.console_lock:
            self.console.setPlainText("✔ Exitosos:\n✖ Fallidos:")
    
    def start_download(self):
        """Inicia el proceso de descarga"""
        if self.is_downloading:
            self.show_console_error("Ya hay una descarga en progreso")
            return
        
        links_text = self.links.toPlainText().strip()
        if not links_text:
            self.show_console_error("Por favor ingresa al menos un enlace")
            return
        
        urls = [line.strip() for line in links_text.split('\n') if line.strip()]
        
        output_path = self.path.text()
        if not output_path or not os.path.exists(output_path) or not os.path.isdir(output_path):
            self.show_console_error("Por favor selecciona una carpeta válida que exista")
            return
        
        self.successful_downloads = []
        self.failed_downloads = []
        self.is_downloading = True
        self.download_button.setEnabled(False)
        
        with self.console_lock:
            self.console.setPlainText("✔ Exitosos:\n✖ Fallidos:")
        
        # Crear y conectar el thread
        self.download_thread = DownloadThread(urls, output_path, self.downloader)
        self.download_thread.progress_updated.connect(lambda q, p: self.progress_value_label.setText(p))
        self.download_thread.stats_updated.connect(self.update_stats)
        self.download_thread.title_updated.connect(lambda t: self.video_title.setText(t))
        self.download_thread.success_added.connect(self.on_success_added)
        self.download_thread.failed_added.connect(self.on_failed_added)
        self.download_thread.error_occurred.connect(self.show_console_error)
        self.download_thread.download_finished.connect(self.on_download_finished)
        self.download_thread.start()
    
    @Slot(str)
    def on_success_added(self, title):
        """Maneja cuando se añade un título exitoso"""
        self.successful_downloads.append(title)
        self.add_success_to_console(title)
    
    @Slot(str)
    def on_failed_added(self, title):
        """Maneja cuando se añade un título fallido"""
        self.failed_downloads.append(title)
        self.add_failed_to_console(title)
    
    @Slot()
    def on_download_finished(self):
        """Maneja cuando termina la descarga"""
        self.is_downloading = False
        self.download_button.setEnabled(True)
    
    def show(self):
        """Muestra la interfaz"""
        super().show()
    
    def hide(self):
        """Oculta la interfaz"""
        super().hide()
    
    def get_widget(self) -> QWidget:
        """Retorna el widget principal"""
        return self
