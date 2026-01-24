import customtkinter as ctk
from tkinter import filedialog
from threading import Lock
import threading
import os
from PIL import Image

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


class TikTokUI(PlatformUI):
    
    def __init__(self, parent_frame: ctk.CTkFrame, console_lock: Lock):
        super().__init__(parent_frame, "TikTok")
        self.console_lock = console_lock
        self.main_frame = None
        self.is_downloading = False
        self.downloader = TikTokDownloader()
        self.current_photo = None
        
    def build(self):
        """Construye la interfaz de TikTok"""
        self.main_frame = ctk.CTkFrame(self.parent_frame, fg_color=BG_MAIN)

        # Grid configuration
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(0, weight=0)
        self.main_frame.grid_rowconfigure(1, weight=1)
        self.main_frame.grid_rowconfigure(2, weight=0)
        self.main_frame.grid_rowconfigure(3, weight=0, minsize=140)

        # ================== TITULO ==================
        title = ctk.CTkLabel(
            self.main_frame,
            text="DESCARGA DE CONTENIDO - TIKTOK",
            font=ctk.CTkFont(size=22, weight="bold")
        )
        title.grid(row=0, column=0, sticky="w", padx=20, pady=(20, 16))

        # ================== CONTENIDO PRINCIPAL ==================
        main_content = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        main_content.grid(row=1, column=0, sticky="nsew", padx=20, pady=(0, 16))
        main_content.grid_columnconfigure(0, weight=1)
        main_content.grid_columnconfigure(1, weight=0, minsize=340)
        main_content.grid_rowconfigure(0, weight=1)

        # -------- PANEL IZQUIERDO --------
        left_panel = ctk.CTkFrame(main_content, fg_color="transparent")
        left_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 20))
        left_panel.grid_columnconfigure(0, weight=1)
        left_panel.grid_rowconfigure(0, weight=0)
        left_panel.grid_rowconfigure(1, weight=0)
        left_panel.grid_rowconfigure(2, weight=0)
        left_panel.grid_rowconfigure(3, weight=0)
        left_panel.grid_rowconfigure(4, weight=1)

        # URL INPUT
        url_frame = ctk.CTkFrame(left_panel, fg_color=BG_PANEL, corner_radius=RADIUS)
        url_frame.grid(row=0, column=0, sticky="ew", pady=(0, 12))

        ctk.CTkLabel(
            url_frame,
            text="URL del video TikTok",
            text_color=TEXT_SEC,
            font=ctk.CTkFont(size=12, weight="bold")
        ).pack(anchor="w", padx=16, pady=(12, 4))

        self.url_input = ctk.CTkEntry(
            url_frame,
            placeholder_text="Pega aqui la URL...",
            fg_color=BG_MAIN,
            border_width=0,
            corner_radius=RADIUS,
            height=40
        )
        self.url_input.pack(fill="x", padx=16, pady=(0, 12))

        # DESTINO
        dest = ctk.CTkFrame(left_panel, fg_color=BG_PANEL, corner_radius=RADIUS)
        dest.grid(row=1, column=0, sticky="ew", pady=(0, 12))

        ctk.CTkLabel(
            dest,
            text="Destino de descarga",
            text_color=TEXT_SEC,
            font=ctk.CTkFont(size=12, weight="bold")
        ).pack(anchor="w", padx=16, pady=(12, 4))

        row = ctk.CTkFrame(dest, fg_color="transparent")
        row.pack(fill="x", padx=16, pady=(0, 12))

        self.path = ctk.CTkEntry(row, fg_color=BG_MAIN, border_width=0, corner_radius=RADIUS, height=36)
        self.path.insert(0, "C:/Descargas")
        self.path.pack(side="left", fill="x", expand=True, padx=(0, 8))

        ctk.CTkButton(
            row,
            text="Elegir",
            width=80,
            height=36,
            fg_color="#1C2230",
            hover_color="#252B3A",
            command=self.select_folder
        ).pack(side="right")

        # INFORMACION
        info = ctk.CTkFrame(left_panel, fg_color=BG_PANEL, corner_radius=RADIUS)
        info.grid(row=2, column=0, sticky="ew", pady=(0, 10))

        ctk.CTkLabel(
            info,
            text="Informacion del video",
            font=ctk.CTkFont(size=11, weight="bold")
        ).pack(anchor="w", padx=16, pady=(10, 6))

        info_grid = ctk.CTkFrame(info, fg_color="transparent")
        info_grid.pack(fill="x", padx=16, pady=(0, 10))
        info_grid.grid_columnconfigure(0, weight=0)
        info_grid.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(info_grid, text="Autor:", text_color=TEXT_SEC, font=ctk.CTkFont(size=9)).grid(row=0, column=0, sticky="w", pady=1, padx=(0, 6))
        self.author_label = ctk.CTkLabel(info_grid, text="-", text_color="white", font=ctk.CTkFont(size=8))
        self.author_label.grid(row=0, column=1, sticky="w", pady=1)

        ctk.CTkLabel(info_grid, text="Vistas:", text_color=TEXT_SEC, font=ctk.CTkFont(size=9)).grid(row=1, column=0, sticky="w", pady=1, padx=(0, 6))
        self.views_label = ctk.CTkLabel(info_grid, text="-", text_color="white", font=ctk.CTkFont(size=8))
        self.views_label.grid(row=1, column=1, sticky="w", pady=1)

        ctk.CTkLabel(info_grid, text="Fecha:", text_color=TEXT_SEC, font=ctk.CTkFont(size=9)).grid(row=2, column=0, sticky="w", pady=1, padx=(0, 6))
        self.date_label = ctk.CTkLabel(info_grid, text="-", text_color="white", font=ctk.CTkFont(size=8))
        self.date_label.grid(row=2, column=1, sticky="w", pady=1)

        ctk.CTkLabel(info_grid, text="Resolucion:", text_color=TEXT_SEC, font=ctk.CTkFont(size=9)).grid(row=3, column=0, sticky="w", pady=1, padx=(0, 6))
        self.resolution_label = ctk.CTkLabel(info_grid, text="-", text_color="white", font=ctk.CTkFont(size=8))
        self.resolution_label.grid(row=3, column=1, sticky="w", pady=1)

        ctk.CTkLabel(info_grid, text="Duracion:", text_color=TEXT_SEC, font=ctk.CTkFont(size=9)).grid(row=4, column=0, sticky="w", pady=1, padx=(0, 6))
        self.duration_label = ctk.CTkLabel(info_grid, text="-", text_color="white", font=ctk.CTkFont(size=8))
        self.duration_label.grid(row=4, column=1, sticky="w", pady=1)

        ctk.CTkLabel(info_grid, text="Tamano:", text_color=TEXT_SEC, font=ctk.CTkFont(size=9)).grid(row=5, column=0, sticky="w", pady=1, padx=(0, 6))
        self.size_label = ctk.CTkLabel(info_grid, text="-", text_color="white", font=ctk.CTkFont(size=8))
        self.size_label.grid(row=5, column=1, sticky="w", pady=1)

        # PROGRESO
        progress_container = ctk.CTkFrame(left_panel, fg_color=BG_PANEL, corner_radius=RADIUS)
        progress_container.grid(row=3, column=0, sticky="ew", pady=(0, 12))

        ctk.CTkLabel(
            progress_container,
            text="Progreso",
            text_color=TEXT_SEC,
            font=ctk.CTkFont(size=12, weight="bold")
        ).pack(anchor="w", padx=16, pady=(12, 8))

        self.progress_bar = ctk.CTkProgressBar(
            progress_container,
            fg_color="#2A2F3A",
            progress_color=ACCENT,
            corner_radius=RADIUS,
            height=8
        )
        self.progress_bar.pack(fill="x", padx=16, pady=(0, 4))
        self.progress_bar.set(0)

        self.progress_text = ctk.CTkLabel(
            progress_container,
            text="0%",
            text_color=TEXT_SEC,
            font=ctk.CTkFont(size=10)
        )
        self.progress_text.pack(anchor="e", padx=16, pady=(0, 12))

        # DOWNLOAD BUTTON
        self.download_button = ctk.CTkButton(
            left_panel,
            text="DESCARGAR",
            height=52,
            fg_color=ACCENT,
            hover_color="#6487E5",
            font=ctk.CTkFont(size=14, weight="bold"),
            command=self.start_download
        )
        self.download_button.grid(row=4, column=0, sticky="ew", pady=(0, 0))

        # -------- PANEL DERECHO (PREVIEW) --------
        right_panel = ctk.CTkFrame(main_content, fg_color="transparent")
        right_panel.grid(row=0, column=1, sticky="nsew")

        preview_container = ctk.CTkFrame(
            right_panel,
            width=300,
            height=480,
            fg_color=BG_PANEL,
            corner_radius=RADIUS
        )
        preview_container.pack(fill="both", expand=True)
        preview_container.grid_propagate(False)

        preview_inner = ctk.CTkFrame(preview_container, fg_color="transparent")
        preview_inner.pack(fill="both", expand=True, padx=8, pady=8)

        self.preview_label = ctk.CTkLabel(
            preview_inner,
            text="Vista\nprevia",
            text_color=TEXT_SEC,
            font=ctk.CTkFont(size=14),
            anchor="center"
        )
        self.preview_label.pack(fill="both", expand=True)

        # ================== CONSOLE HEADER ==================
        console_header = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        console_header.grid(row=2, column=0, sticky="ew", padx=20, pady=(12, 6))

        ctk.CTkLabel(
            console_header,
            text="Estado",
            text_color=TEXT_SEC,
            font=ctk.CTkFont(size=12)
        ).pack(side="left")

        ctk.CTkButton(
            console_header,
            text="Limpiar consola",
            width=130,
            height=32,
            fg_color="#1C2230",
            hover_color="#252B3A",
            font=ctk.CTkFont(size=12),
            command=self.clear_console
        ).pack(side="right")

        # ================== CONSOLE ==================
        self.console = ctk.CTkTextbox(
            self.main_frame,
            fg_color=BG_PANEL,
            border_width=0,
            corner_radius=RADIUS,
            state="normal"
        )
        self.console.grid(row=3, column=0, sticky="nsew", padx=20, pady=(0, 20))
        self.console.insert("end", "Esperando entrada...\n")
        self.console.configure(state="disabled")

    def show(self):
        if self.main_frame:
            self.main_frame.pack(side="left", fill="both", expand=True)

    def hide(self):
        if self.main_frame:
            self.main_frame.pack_forget()

    def get_frame(self) -> ctk.CTkFrame:
        return self.main_frame

    def select_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.path.delete(0, "end")
            self.path.insert(0, folder)

    def clear_console(self):
        with self.console_lock:
            self.console.configure(state="normal")
            self.console.delete("1.0", "end")
            self.console.insert("end", "Esperando entrada...\n")
            self.console.configure(state="disabled")

    def update_progress(self, percent_value):
        self.progress_bar.set(percent_value)
        percent_display = int(percent_value * 100)
        self.progress_text.configure(text=f"{percent_display}%")

    def update_video_info(self, author, views, date, resolution, duration, size, description=""):
        self.author_label.configure(text=author)
        self.views_label.configure(text=views)
        self.date_label.configure(text=date)
        self.resolution_label.configure(text=resolution)
        self.duration_label.configure(text=duration)
        self.size_label.configure(text=size)

    def set_preview_image_from_pil(self, pil_image):
        """Actualiza la imagen de preview correctamente"""
        try:
            pil_image.thumbnail((284, 464), Image.Resampling.LANCZOS)
            
            self.current_photo = ctk.CTkImage(
                light_image=pil_image, 
                dark_image=pil_image, 
                size=pil_image.size
            )
            
            self.preview_label.configure(image=self.current_photo, text="")
            self.preview_label.update()
            
        except Exception as e:
            print(f"Error cargando preview: {e}")
            self.preview_label.configure(text="Error en\npreview", image="")

    def add_to_console(self, message, status="info"):
        with self.console_lock:
            self.console.configure(state="normal")
            if status == "success":
                prefix = "[OK]"
            elif status == "error":
                prefix = "[ERROR]"
            elif status == "validation":
                prefix = "[AVISO]"
            else:
                prefix = "[INFO]"
            self.console.insert("end", f"{prefix} {message}\n")
            self.console.see("end")
            self.console.configure(state="disabled")

    def start_download(self):
        if self.is_downloading:
            self.add_to_console("Ya hay una descarga en progreso", "validation")
            return

        url = self.url_input.get().strip()
        if not url:
            self.add_to_console("Por favor ingresa una URL", "validation")
            return

        output_path = self.path.get()
        if not output_path or not os.path.exists(output_path) or not os.path.isdir(output_path):
            self.add_to_console("Por favor selecciona una carpeta valida", "validation")
            return

        self.is_downloading = True
        self.download_button.configure(state="disabled")
        thread = threading.Thread(target=self._download_thread, args=(url, output_path))
        thread.daemon = True
        thread.start()

    def _download_thread(self, url: str, output_path: str):
        try:
            self.add_to_console("Obteniendo informacion del video...", "info")

            info = self.downloader.get_video_info(url)
            if not info:
                self.add_to_console("No se pudo obtener informacion del video", "error")
                return

            self.update_video_info(
                info.get('author', 'Desconocido'),
                self._format_views(info.get('view_count', 0)),
                self._format_date(info.get('upload_date', '')),
                self._format_resolution(info.get('width', 0), info.get('height', 0)),
                self._format_duration(info.get('duration', 0)),
                self._format_filesize(info.get('filesize', 0))
            )

            if info.get('thumbnail'):
                try:
                    import requests
                    from io import BytesIO
                    response = requests.get(info['thumbnail'], timeout=5)
                    img = Image.open(BytesIO(response.content))
                    self.set_preview_image_from_pil(img)
                except Exception as thumb_error:
                    print(f"No se pudo cargar thumbnail: {thumb_error}")

            self.add_to_console("Iniciando descarga...", "info")

            def progress_callback(percent_value):
                self.update_progress(percent_value)

            success, title = self.downloader.download_audio(url, output_path, progress_callback)

            if success:
                self.add_to_console(f"{title} - Descargado exitosamente", "success")
            else:
                self.add_to_console("Error durante la descarga", "error")

        except Exception as e:
            self.add_to_console(f"Error: {str(e)}", "error")

        finally:
            self.is_downloading = False
            self.download_button.configure(state="normal")

    def _format_views(self, views):
        """Formatea el numero de vistas en formato legible"""
        if not views:
            return "-"
        if views >= 1_000_000:
            return f"{views / 1_000_000:.1f}M"
        elif views >= 1_000:
            return f"{views / 1_000:.1f}K"
        else:
            return str(views)

    def _format_date(self, date_str):
        """Formatea la fecha de publicacion (YYYYMMDD -> DD/MM/YYYY)"""
        if not date_str or date_str == "":
            return "-"
        try:
            return f"{date_str[6:8]}/{date_str[4:6]}/{date_str[0:4]}"
        except:
            return "-"

    def _format_resolution(self, width, height):
        """Formatea la resolucion"""
        if not width or not height:
            return "-"
        return f"{width}x{height}"

    def _truncate_description(self, description):
        """Trunca la descripcion a 150 caracteres"""
        if not description:
            return ""
        if len(description) > 150:
            return description[:150] + "..."
        return description

    def _format_duration(self, seconds):
        """Formatea la duracion en HH:MM:SS"""
        if not seconds:
            return "-"
        mins, secs = divmod(int(seconds), 60)
        hours, mins = divmod(mins, 60)
        if hours:
            return f"{hours}:{mins:02d}:{secs:02d}"
        return f"{mins}:{secs:02d}"

    def _format_filesize(self, size_bytes):
        """Formatea el tamaño del archivo"""
        if not size_bytes:
            return "-"
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024
        return f"{size_bytes:.1f} TB"