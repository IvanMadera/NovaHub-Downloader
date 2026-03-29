from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QLineEdit, QFrame, QFileDialog, QProgressBar,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView, QMenu
)
from PySide6.QtCore import Qt, QThread, Signal, Slot, QSize
from PySide6.QtGui import QFont, QPixmap, QIcon, QAction
from threading import Lock
import os
import requests
import io
import concurrent.futures

from ui.base_ui import PlatformUI
from downloaders.spotify import SpotifyDownloader

# ===== PALETA ORO VERDE =====
BG_MAIN  = "#0E1116"
BG_PANEL = "#151A21"
ACCENT   = "#3B5998"
SUCCESS  = "#9ECE6A"
TEXT_SEC = "#A9B1D6"
TEXT_MAIN = "#FFFFFF"
ERROR    = "#F7768E"
RADIUS   = 14

class CoverLoaderThread(QThread):
    cover_loaded = Signal(int, bytes) # fila_index, image_bytes
    def __init__(self, row_index, url):
        super().__init__()
        self.row_index = row_index
        self.url = url
    def run(self):
        try:
            r = requests.get(self.url, timeout=5)
            if r.status_code == 200:
                self.cover_loaded.emit(self.row_index, r.content)
        except:
            pass

class SpotifySearchThread(QThread):
    results_ready = Signal(list)
    error_occurred = Signal(str)
    
    def __init__(self, downloader, query):
        super().__init__()
        self.downloader = downloader
        self.query = query
        
    def run(self):
        try:
            results = self.downloader.search_track(self.query)
            if results:
                self.results_ready.emit(results)
            else:
                self.error_occurred.emit("No se encontraron resultados.")
        except Exception as e:
            self.error_occurred.emit(str(e))

class SpotifyWorkerThread(QThread):
    """
    Ejecuta un trabajo de la cola y reporta progreso para ESA fila
    """
    progress = Signal(int, int) # row_idx_queue, progress_val
    finished = Signal(int, bool, str) # row_idx_queue, success, output_msg
    
    def __init__(self, row_idx, track_data, output_path, downloader):
        super().__init__()
        self.row_idx = row_idx
        self.track_data = track_data
        self.output_path = output_path
        self.downloader = downloader
        
    def run(self):
        def cb(progress_ratio):
            self.progress.emit(self.row_idx, int(progress_ratio*100))
            
        try:
            success, msg = self.downloader.download_audio_with_tags(
                self.track_data, self.output_path, progress_callback=cb
            )
            self.finished.emit(self.row_idx, success, msg)
        except Exception as e:
            self.finished.emit(self.row_idx, False, str(e))

class SpotifyUI(PlatformUI):
    def __init__(self, parent_widget: QWidget, console_lock: Lock):
        super().__init__(parent_widget, "Spotify")
        self.console_lock = console_lock
        self.downloader = SpotifyDownloader()
        self.current_results = []
        self.download_queue = []
        self.active_workers = []
        self.cover_threads = []
        
    def build(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)
        
        # Header
        title = QLabel("BUSCADOR & DESCARGA - SPOTIFY (HQ AUDIO)")
        title.setFont(QFont("Segoe UI", 20, QFont.Bold)) 
        title.setStyleSheet(f"color: {TEXT_MAIN}; background-color: transparent;")
        main_layout.addWidget(title)
        
        # Buscador Box
        search_box = QHBoxLayout()
        search_box.setSpacing(10)
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Ingresa nombre de la canción/artista o link de Spotify...")
        self.search_input.setFixedHeight(45)
        self.search_input.setFont(QFont("Segoe UI", 11))
        self.search_input.setStyleSheet(f"QLineEdit {{ background-color: {BG_PANEL}; border: none; border-radius: {RADIUS}px; padding: 0 15px; color: white; }}")
        self.search_input.returnPressed.connect(self.perform_search)
        search_box.addWidget(self.search_input)
        
        self.btn_search = QPushButton("BUSCAR")
        self.btn_search.setFixedSize(120, 45)
        self.btn_search.setCursor(Qt.PointingHandCursor)
        self.btn_search.clicked.connect(self.perform_search)
        search_box.addWidget(self.btn_search)
        
        main_layout.addLayout(search_box)
        
        # Destino Box
        dest_layout = QHBoxLayout()
        dest_layout.setSpacing(10)
        
        dest_label = QLabel("Guardar música en:")
        dest_label.setStyleSheet(f"color: {TEXT_SEC};")
        dest_layout.addWidget(dest_label)
        
        self.path = QLineEdit("C:/Descargas")
        self.path.setFixedHeight(40)
        self.path.setReadOnly(True)
        self.path.setStyleSheet(f"QLineEdit {{ background-color: {BG_PANEL}; border: none; border-radius: {RADIUS}px; padding: 0 15px; color: white; }}")
        dest_layout.addWidget(self.path, 1)
        
        btn_choose = QPushButton("Elegir")
        btn_choose.setFixedSize(120, 40)
        btn_choose.setProperty("secondary", "true")
        btn_choose.clicked.connect(self.select_folder)
        dest_layout.addWidget(btn_choose)
        main_layout.addLayout(dest_layout)
        
        # === SPLIT LAYOUT (Tablas) ===
        split_layout = QHBoxLayout()
        split_layout.setSpacing(20)
        
        # --- LEFT: Búsqueda (Resultados)
        left_panel = QVBoxLayout()
        lbl_results = QLabel("Resultados de Búsqueda")
        lbl_results.setFont(QFont("Segoe UI", 12, QFont.Bold))
        left_panel.addWidget(lbl_results)
        
        self.table_res = QTableWidget(0, 4)
        self.table_res.setHorizontalHeaderLabels(["Portada", "Canción", "Artista / Álbum", "Acción"])
        self.table_res.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table_res.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.table_res.setColumnWidth(0, 60)
        self.table_res.setColumnWidth(3, 100)
        self.table_res.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table_res.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table_res.verticalHeader().setVisible(False)
        self.table_res.setIconSize(QSize(50, 50))
        self.table_res.setStyleSheet(f"""
            QTableWidget {{ background-color: {BG_PANEL}; border-radius: {RADIUS}px; gridline-color: transparent; border: none; color: white; }}
            QHeaderView::section {{ background-color: #1C2230; color: {TEXT_SEC}; border: none; padding: 5px; font-weight: bold; }}
            QTableWidget::item {{ border-bottom: 1px solid #1f2536; padding: 5px; }}
            QTableWidget::item:selected {{ background-color: #1C2230; }}
        """)
        left_panel.addWidget(self.table_res)
        split_layout.addLayout(left_panel, 6) # 60% Ancho
        
        # --- RIGHT: Cola de Descargas
        right_panel = QVBoxLayout()
        lbl_queue = QLabel("Cola Activa")
        lbl_queue.setFont(QFont("Segoe UI", 12, QFont.Bold))
        right_panel.addWidget(lbl_queue)
        
        self.table_queue = QTableWidget(0, 3)
        self.table_queue.setHorizontalHeaderLabels(["Track", "Progreso", "Estado"])
        self.table_queue.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table_queue.setColumnWidth(1, 100)
        self.table_queue.setColumnWidth(2, 60)
        self.table_queue.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table_queue.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table_queue.verticalHeader().setVisible(False)
        self.table_queue.setStyleSheet(f"""
            QTableWidget {{ background-color: {BG_PANEL}; border-radius: {RADIUS}px; border: none; gridline-color: transparent; color: white; }}
            QHeaderView::section {{ background-color: #1C2230; color: {TEXT_SEC}; border: none; padding: 5px; font-weight: bold; }}
            QTableWidget::item {{ border-bottom: 1px solid #1f2536; padding: 5px; }}
        """)
        right_panel.addWidget(self.table_queue)
        split_layout.addLayout(right_panel, 4) # 40% Ancho
        
        main_layout.addLayout(split_layout)
        
        # Status Bar final
        self.status_lbl = QLabel("Listo. Busca una canción.")
        self.status_lbl.setStyleSheet(f"color: {TEXT_SEC};")
        main_layout.addWidget(self.status_lbl)
        
        self.apply_styles()
        
    def apply_styles(self):
        self.setStyleSheet(f"""
            QWidget {{ background-color: {BG_MAIN}; color: white; }}
            QLabel {{ color: {TEXT_SEC}; }}
            QPushButton {{ background-color: {ACCENT}; border: none; border-radius: 8px; color: white; font-weight: bold; padding: 5px; }}
            QPushButton:hover {{ background-color: #6487E5; }}
            QPushButton[secondary="true"] {{ background-color: #1C2230; font-weight: normal; }}
            QPushButton[secondary="true"]:hover {{ background-color: #252B3A; }}
            QProgressBar {{ background-color: transparent; border: 1px solid #333; text-align: center; color: white; border-radius: 4px; }}
            QProgressBar::chunk {{ background-color: {ACCENT}; border-radius: 4px; }}
        """)

    def select_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Seleccionar carpeta")
        if folder: self.path.setText(folder)

    def perform_search(self):
        query = self.search_input.text().strip()
        if not query:
            self.status_lbl.setText("Error: Ingresa un parámetro de búsqueda.")
            return
            
        self.table_res.setRowCount(0)
        self.btn_search.setEnabled(False)
        self.status_lbl.setText("Buscando en Spotify...")
        self.search_input.setEnabled(False)
        
        self.search_thread = SpotifySearchThread(self.downloader, query)
        self.search_thread.results_ready.connect(self.on_search_results)
        self.search_thread.error_occurred.connect(self.on_search_error)
        self.search_thread.start()

    @Slot(list)
    def on_search_results(self, results):
        self.current_results = results
        self.table_res.setRowCount(len(results))
        self.cover_threads.clear()
        
        for i, track in enumerate(results):
            # 0. Portada (Icono)
            lbl_cover = QLabel()
            lbl_cover.setFixedSize(50, 50)
            lbl_cover.setStyleSheet("background-color: #222; border-radius: 4px;")
            self.table_res.setCellWidget(i, 0, lbl_cover)
            
            # Subproceso para cargar portada sin congelar
            if track.get('cover_url'):
                th = CoverLoaderThread(i, track['cover_url'])
                th.cover_loaded.connect(self.inject_cover)
                self.cover_threads.append(th)
                th.start()
                
            # 1. Canción
            item_title = QTableWidgetItem(track['title'])
            item_title.setToolTip(track['title'])
            self.table_res.setItem(i, 1, item_title)
            
            # 2. Artista/Album
            txt_artist = f"{track['artist']}\n{track['album']}"
            item_artist = QTableWidgetItem(txt_artist)
            item_artist.setToolTip(txt_artist)
            self.table_res.setItem(i, 2, item_artist)
            
            # 3. Botón Añadir a Cola
            btn_add = QPushButton("Al Queue")
            btn_add.setFixedSize(90, 30)
            btn_add.setProperty("secondary", "true")
            btn_add.style().unpolish(btn_add)
            btn_add.style().polish(btn_add)
            # bind index safely
            btn_add.clicked.connect(lambda _, idx=i: self.add_to_queue(idx))
            self.table_res.setCellWidget(i, 3, btn_add)
            
            self.table_res.setRowHeight(i, 60)
            
        self.status_lbl.setText(f"Mostrando {len(results)} resultados de Spotify.")
        self.btn_search.setEnabled(True)
        self.search_input.setEnabled(True)
        
    @Slot(int, bytes)
    def inject_cover(self, row_idx, image_data):
        try:
            lbl = self.table_res.cellWidget(row_idx, 0)
            if lbl:
                pixmap = QPixmap()
                pixmap.loadFromData(image_data)
                lbl.setPixmap(pixmap.scaled(50, 50, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        except:
            pass

    @Slot(str)
    def on_search_error(self, err_msg):
        self.status_lbl.setText(f"Error de Búsqueda: {err_msg}")
        self.btn_search.setEnabled(True)
        self.search_input.setEnabled(True)

    def add_to_queue(self, result_index):
        track = self.current_results[result_index]
        out_path = self.path.text()
        if not out_path or not os.path.exists(out_path):
            self.status_lbl.setText("Directorio inválido.")
            return
            
        # Añadir al UI de Cola
        row_idx = self.table_queue.rowCount()
        self.table_queue.insertRow(row_idx)
        
        # Track Info
        item_track = QTableWidgetItem(f"{track['title']} - {track['artist']}")
        self.table_queue.setItem(row_idx, 0, item_track)
        
        # Progress Bar Widget
        bar = QProgressBar()
        bar.setValue(0)
        bar.setFixedHeight(12)
        bar.setTextVisible(False)
        self.table_queue.setCellWidget(row_idx, 1, bar)
        
        # Estado label
        lbl_status = QLabel("...")
        lbl_status.setAlignment(Qt.AlignCenter)
        self.table_queue.setCellWidget(row_idx, 2, lbl_status)
        
        # Iniciar Worker en plano de fondo (Descarga Independiente y Simultánea)
        worker = SpotifyWorkerThread(row_idx, track, out_path, self.downloader)
        worker.progress.connect(self.update_queue_progress)
        worker.finished.connect(self.on_queue_finished)
        
        self.active_workers.append(worker)
        worker.start()
        
        self.status_lbl.setText(f"Añadido a cola: {track['title']}")
        
    @Slot(int, int)
    def update_queue_progress(self, row_idx, val):
        try:
            bar = self.table_queue.cellWidget(row_idx, 1)
            if bar:
                bar.setValue(val)
        except: pass
        
    @Slot(int, bool, str)
    def on_queue_finished(self, row_idx, success, msg):
        try:
            bar = self.table_queue.cellWidget(row_idx, 1)
            lbl = self.table_queue.cellWidget(row_idx, 2)
            if bar:
                bar.setValue(100 if success else 0)
            if lbl:
                lbl.setText("✔" if success else "✖")
                lbl.setStyleSheet("color: #9ECE6A" if success else "color: #F7768E")
            
            if success:
                self.status_lbl.setText(f"✔ Finalizado: {msg}")
            else:
                self.status_lbl.setText(f"✖ Error en descarga: {msg}")
        except: pass

    def get_widget(self):
        return self
