import customtkinter as ctk
from tkinter import filedialog
import threading
import time
import re
import os
from PIL import Image
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
RADIUS   = 14


class YouTubeUI(PlatformUI):
    
    def __init__(self, parent_frame: ctk.CTkFrame, console_lock: Lock):
        super().__init__(parent_frame, "YouTube")
        self.console_lock = console_lock
        self.downloader = YouTubeDownloader()
        self.successful_downloads = []
        self.failed_downloads = []
        self.is_downloading = False
        self.main_frame = None
        
    def build(self):
        """Construye la interfaz de YouTube"""
        self.main_frame = ctk.CTkFrame(self.parent_frame, fg_color=BG_MAIN)
        
        ctk.CTkLabel(
            self.main_frame,
            text="DESCARGA DE CONTENIDO - YOUTUBE",
            font=ctk.CTkFont(size=22, weight="bold")
        ).pack(anchor="w", pady=(0, 20))

        # ================== LINKS + PREVIEW ==================
        top = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        top.pack(fill="x", pady=(0, 18))
        top.grid_columnconfigure(0, weight=1)

        # -------- LINKS --------
        left = ctk.CTkFrame(top, fg_color="transparent")
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 16))

        ctk.CTkLabel(
            left,
            text="Enlaces (uno por línea)",
            text_color=TEXT_SEC
        ).pack(anchor="w")

        self.links = ctk.CTkTextbox(
            left,
            height=160,
            fg_color=BG_PANEL,
            border_width=0,
            corner_radius=RADIUS
        )
        self.links.pack(fill="both", pady=(8, 0))
        self.links.bind('<KeyRelease>', self.clean_links)

        # -------- PREVIEW --------
        preview = ctk.CTkFrame(
            top,
            width=180,
            height=160,
            fg_color=BG_PANEL,
            corner_radius=RADIUS
        )
        preview.grid(row=0, column=1, sticky="nsew")
        preview.pack_propagate(False)

        try:
            img = Image.open("assets/NovaHub_title.png")
            img.thumbnail((320, 160), Image.Resampling.LANCZOS)
            photo = ctk.CTkImage(light_image=img, dark_image=img, size=img.size)
            self.preview_label = ctk.CTkLabel(preview, image=photo, text="")
            self.preview_label.image = photo
            self.preview_label.pack(expand=True)
        except Exception as e:
            print(f"Error cargando imagen: {e}")
            self.preview_label = ctk.CTkLabel(
                preview,
                text="Vista previa",
                text_color=TEXT_SEC
            )
            self.preview_label.pack(expand=True)

        # ================== VIDEO INFO ==================
        info = ctk.CTkFrame(self.main_frame, fg_color=BG_PANEL, corner_radius=RADIUS)
        info.pack(fill="x", pady=(0, 18))

        ctk.CTkLabel(
            info,
            text="Título del video",
            font=ctk.CTkFont(size=15, weight="bold")
        ).pack(anchor="w", padx=16, pady=(12, 2))

        self.video_title = ctk.CTkLabel(
            info,
            text="Esperando descarga",
            text_color=TEXT_SEC
        )
        self.video_title.pack(anchor="w", padx=16, pady=(0, 12))

        # ================== STATS ==================
        stats = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        stats.pack(fill="x", pady=10)

        for i in range(5):
            stats.grid_columnconfigure(i, weight=1)

        self.queue_label = self.card(stats, "EN COLA", "0")
        self.queue_label.grid(row=0, column=0, padx=6)

        self.progress_label = self.card(stats, "PROGRESO", "0%")
        self.progress_label.grid(row=0, column=1, padx=6)

        self.success_label = self.card(stats, "EXITOSOS", "0", SUCCESS)
        self.success_label.grid(row=0, column=2, padx=6)

        self.failed_label = self.card(stats, "FALLIDOS", "0", ERROR)
        self.failed_label.grid(row=0, column=3, padx=6)

        stats.grid_columnconfigure(4, minsize=190)

        self.download_button = ctk.CTkButton(
            stats,
            text="INICIAR DESCARGA",
            height=56,
            width=180,
            fg_color=ACCENT,
            hover_color="#6487E5",
            font=ctk.CTkFont(size=14, weight="bold"),
            command=self.start_download
        )
        self.download_button.grid(row=0, column=4, sticky="nsew", padx=6)

        # ================== DESTINO ==================
        dest = ctk.CTkFrame(self.main_frame, fg_color=BG_PANEL, corner_radius=RADIUS)
        dest.pack(fill="x", pady=(20, 10))

        ctk.CTkLabel(
            dest,
            text="Destino de descarga",
            text_color=TEXT_SEC
        ).pack(anchor="w", padx=16, pady=(12, 4))

        row = ctk.CTkFrame(dest, fg_color="transparent")
        row.pack(fill="x", padx=16, pady=(0, 12))

        self.path = ctk.CTkEntry(row, fg_color=BG_MAIN, border_width=0, corner_radius=RADIUS)
        self.path.insert(0, "C:/Descargas")
        self.path.pack(side="left", fill="x", expand=True, padx=(0, 8))

        ctk.CTkButton(
            row,
            text="Elegir",
            width=90,
            fg_color="#1C2230",
            hover_color="#252B3A",
            command=self.select_folder
        ).pack(side="right")

        # ================== CONSOLE ==================
        console_header = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        console_header.pack(fill="x", pady=(14, 6))

        ctk.CTkLabel(
            console_header,
            text="Resultado de la cola",
            text_color=TEXT_SEC
        ).pack(side="left", anchor="w")

        ctk.CTkButton(
            console_header,
            text="Limpiar consola",
            width=106,
            height=32,
            fg_color="#1C2230",
            hover_color="#252B3A",
            font=ctk.CTkFont(size=12),
            command=self.clear_console
        ).pack(side="right", anchor="e")

        self.console = ctk.CTkTextbox(
            self.main_frame,
            height=140,
            fg_color=BG_PANEL,
            border_width=0,
            corner_radius=RADIUS,
            state="normal"
        )
        self.console.pack(fill="both", expand=True)
        self.console.insert("end", "✔ Exitosos:\n✖ Fallidos:\n")
        self.console.configure(state="disabled")

    def show(self):
        """Muestra la interfaz"""
        if self.main_frame:
            self.main_frame.pack(side="left", fill="both", expand=True, padx=20, pady=20)

    def hide(self):
        """Oculta la interfaz"""
        if self.main_frame:
            self.main_frame.pack_forget()

    def get_frame(self) -> ctk.CTkFrame:
        """Retorna el frame principal"""
        return self.main_frame

    def card(self, parent, title, value, color="white"):
        """Crea una tarjeta de estadísticas"""
        frame = ctk.CTkFrame(
            parent,
            height=100,
            fg_color=BG_PANEL,
            corner_radius=RADIUS
        )
        frame.pack_propagate(False)

        ctk.CTkLabel(
            frame,
            text=value,
            font=ctk.CTkFont(size=26, weight="bold"),
            text_color=color
        ).pack(pady=(22, 2))

        ctk.CTkLabel(
            frame,
            text=title,
            text_color=TEXT_SEC
        ).pack()

        return frame

    def clean_links(self, event=None):
        """Elimina dobles saltos de línea en el textbox de links"""
        content = self.links.get("1.0", "end")
        cleaned = '\n'.join(line for line in content.split('\n') if line.strip())
        
        if content != cleaned:
            self.links.delete("1.0", "end")
            self.links.insert("1.0", cleaned)

    def select_folder(self):
        """Abre el diálogo para seleccionar carpeta"""
        folder = filedialog.askdirectory()
        if folder:
            self.path.delete(0, "end")
            self.path.insert(0, folder)

    def update_stats(self, queue_count, progress, successful, failed):
        """Actualiza las estadísticas"""
        for widget in self.queue_label.winfo_children():
            if isinstance(widget, ctk.CTkLabel):
                widget.configure(text=str(queue_count))
                break

        for widget in self.progress_label.winfo_children():
            if isinstance(widget, ctk.CTkLabel):
                widget.configure(text=progress)
                break

        for widget in self.success_label.winfo_children():
            if isinstance(widget, ctk.CTkLabel):
                widget.configure(text=str(successful))
                break

        for widget in self.failed_label.winfo_children():
            if isinstance(widget, ctk.CTkLabel):
                widget.configure(text=str(failed))
                break

    def add_success_to_console(self, title):
        """Agrega un título exitoso a la consola"""
        with self.console_lock:
            self.console.configure(state="normal")
            content = self.console.get("1.0", "end")
            failed_pos = content.find("✖ Fallidos:")

            if failed_pos != -1:
                before_text = content[:failed_pos]
                line_num = before_text.count('\n') + 1
                self.console.insert(f"{line_num}.0", f"  {len(self.successful_downloads)}. {title}\n")
            else:
                self.console.insert("end", f"  {len(self.successful_downloads)}. {title}\n")

            self.console.configure(state="disabled")

        time.sleep(1)

    def add_failed_to_console(self, title):
        """Agrega un título fallido a la consola"""
        with self.console_lock:
            self.console.configure(state="normal")
            self.console.insert("end", f"  {len(self.failed_downloads)}. {title}\n")
            self.console.configure(state="disabled")

        time.sleep(1)

    def show_console_error(self, message):
        """Muestra un error en la consola"""
        with self.console_lock:
            self.console.configure(state="normal")
            self.console.insert("end", f"\n❌ {message}\n")
            self.console.configure(state="disabled")

    def clear_console(self):
        """Limpia la consola"""
        with self.console_lock:
            self.console.configure(state="normal")
            self.console.delete("1.0", "end")
            self.console.insert("end", "✔ Exitosos:\n✖ Fallidos:\n")
            self.console.configure(state="disabled")

    def start_download(self):
        """Inicia el proceso de descarga"""
        if self.is_downloading:
            self.show_console_error("Ya hay una descarga en progreso")
            return

        links_text = self.links.get("1.0", "end").strip()
        if not links_text:
            self.show_console_error("Por favor ingresa al menos un enlace")
            return

        urls = [line.strip() for line in links_text.split('\n') if line.strip()]

        output_path = self.path.get()
        if not output_path or not os.path.exists(output_path) or not os.path.isdir(output_path):
            self.show_console_error("Por favor selecciona una carpeta válida que exista")
            return

        self.successful_downloads = []
        self.failed_downloads = []
        self.is_downloading = True
        self.download_button.configure(state="disabled")

        with self.console_lock:
            self.console.configure(state="normal")
            self.console.delete("1.0", "end")
            self.console.insert("end", "✔ Exitosos:\n✖ Fallidos:\n")
            self.console.configure(state="disabled")

        thread = threading.Thread(target=self._download_thread, args=(urls, output_path))
        thread.daemon = True
        thread.start()

    def _download_thread(self, urls, output_path):
        """Thread de descarga"""
        try:
            total = len(urls)

            for idx, url in enumerate(urls):
                if not self.is_downloading:
                    break

                self.update_stats(
                    queue_count=total - idx,
                    progress="0%",
                    successful=len(self.successful_downloads),
                    failed=len(self.failed_downloads)
                )

                def progress_callback(percent, speed, eta):
                    match = re.search(r'[\d.]+%', percent)
                    percent_only = match.group() if match else "0%"
                    self.update_stats(
                        queue_count=total - idx - 1,
                        progress=percent_only,
                        successful=len(self.successful_downloads),
                        failed=len(self.failed_downloads)
                    )

                def title_callback(title):
                    self.video_title.configure(text=title)

                success, title = self.downloader.download_audio(url, output_path, progress_callback, title_callback)

                if success and title:
                    self.successful_downloads.append(title)
                    self.add_success_to_console(title)
                    self.update_stats(
                        queue_count=total - idx - 1,
                        progress="100%",
                        successful=len(self.successful_downloads),
                        failed=len(self.failed_downloads)
                    )
                else:
                    self.failed_downloads.append(url)
                    self.add_failed_to_console(url)
                    self.update_stats(
                        queue_count=total - idx - 1,
                        progress="0%",
                        successful=len(self.successful_downloads),
                        failed=len(self.failed_downloads)
                    )

        except Exception as e:
            self.show_console_error(f"Error durante la descarga: {str(e)}")

        finally:
            self.is_downloading = False
            self.download_button.configure(state="normal")
