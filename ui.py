import customtkinter as ctk
from tkinter import filedialog
from datetime import datetime
import threading
import re
import os
from youtube import download_youtube_audio

# ================== CONFIG ==================
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

# ===== PALETA =====
BG_MAIN  = "#0E1116"
BG_PANEL = "#151A21"
ACCENT   = "#3B5998"
SUCCESS  = "#9ECE6A"
TEXT_SEC = "#A9B1D6"
ERROR    = "#F7768E"
RADIUS   = 16


class NovaHub(ctk.CTk):

    def __init__(self):
        super().__init__()

        self.title("Nova Hub")
        self.geometry("1280x760")
        self.minsize(1180, 700)
        self.configure(fg_color=BG_MAIN)

        self.successful_downloads = []
        self.failed_downloads = []
        self.is_downloading = False

        self.title("Nova Hub")
        self.geometry("1280x760")
        self.minsize(1180, 700)
        self.configure(fg_color=BG_MAIN)

        # ================== SIDEBAR ==================
        sidebar = ctk.CTkFrame(
            self,
            width=240,
            fg_color=BG_PANEL,
            corner_radius=0
        )
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        ctk.CTkLabel(
            sidebar,
            text="╫ Nova Hub",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=ACCENT
        ).pack(pady=28)

        PLATFORMS = [
            ("◈", "YouTube"),
            ("◈", "TikTok"),
            ("◈", "Instagram"),
            ("◈", "Facebook"),
            ("◈", "X / Twitter"),
        ]

        for icon, name in PLATFORMS:
            ctk.CTkButton(
                sidebar,
                text=f"{icon}  {name}",
                height=44,
                anchor="w",
                fg_color=BG_PANEL,
                hover_color="#1C2230",
                text_color=TEXT_SEC,
                font=ctk.CTkFont(size=14)
            ).pack(fill="x", padx=18, pady=6)

        # ================== FOOTER ==================
        footer = ctk.CTkFrame(sidebar, fg_color="transparent")
        footer.pack(side="bottom", fill="x", padx=12, pady=20)

        ctk.CTkLabel(
            footer,
            text=f"© Copyright {datetime.now().year}",
            text_color=TEXT_SEC,
            font=ctk.CTkFont(size=14)
        ).pack()

        # ================== MAIN ==================
        main = ctk.CTkFrame(self, fg_color=BG_MAIN)
        main.pack(side="left", fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(
            main,
            text="DESCARGA DE CONTENIDO",
            font=ctk.CTkFont(size=22, weight="bold")
        ).pack(anchor="w", pady=(0, 20))

        # ================== LINKS + PREVIEW ==================
        top = ctk.CTkFrame(main, fg_color="transparent")
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
            border_width=0
        )
        self.links.pack(fill="both", pady=(8, 0))

        # -------- PREVIEW (ALIGNED HEIGHT) --------
        preview = ctk.CTkFrame(
            top,
            width=320,
            height=160,
            fg_color=BG_PANEL,
            corner_radius=RADIUS
        )
        preview.grid(row=0, column=1, sticky="nsew")
        preview.pack_propagate(False)

        ctk.CTkLabel(
            preview,
            text="Vista previa",
            text_color=TEXT_SEC
        ).pack(expand=True)

        # ================== VIDEO INFO ==================
        info = ctk.CTkFrame(main, fg_color=BG_PANEL, corner_radius=RADIUS)
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
        stats = ctk.CTkFrame(main, fg_color="transparent")
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
        dest = ctk.CTkFrame(main, fg_color=BG_PANEL, corner_radius=RADIUS)
        dest.pack(fill="x", pady=(20, 10))

        ctk.CTkLabel(
            dest,
            text="Destino de descarga",
            text_color=TEXT_SEC
        ).pack(anchor="w", padx=16, pady=(12, 4))

        row = ctk.CTkFrame(dest, fg_color="transparent")
        row.pack(fill="x", padx=16, pady=(0, 12))

        self.path = ctk.CTkEntry(row, fg_color=BG_MAIN, border_width=0)
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
        ctk.CTkLabel(
            main,
            text="Resultado de la cola",
            text_color=TEXT_SEC
        ).pack(anchor="w", pady=(14, 6))

        self.console = ctk.CTkTextbox(
            main,
            height=140,
            fg_color=BG_PANEL,
            border_width=0,
            state="normal"
        )
        self.console.pack(fill="both", expand=True)
        # Inicializar consola con títulos
        self.console.insert("end", "✔ Exitosos:\n\n✖ Fallidos:\n")
        self.console.configure(state="disabled")

    # ================== CARD ==================
    def card(self, parent, title, value, color="white"):
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

    def select_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.path.delete(0, "end")
            self.path.insert(0, folder)

    def update_card_value(self, card_frame, value):
        """Actualiza el valor de una tarjeta"""
        for widget in card_frame.winfo_children():
            if isinstance(widget, ctk.CTkLabel):
                if hasattr(widget, '_text'):
                    widget.configure(text=value)
                    break

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

    def update_console(self, successful, failed):
        """Actualiza la consola con resultados finales"""
        self.console.configure(state="normal")
        self.console.delete("1.0", "end")
        
        success_text = "✔ Exitosos:\n"
        for i, title in enumerate(successful, 1):
            success_text += f"  {i}. {title}\n"
        
        failed_text = "\n✖ Fallidos:\n"
        for i, title in enumerate(failed, 1):
            failed_text += f"  {i}. {title}\n"
        
        self.console.insert("end", success_text + failed_text)
        self.console.configure(state="disabled")

    def add_success_to_console(self, title):
        """Agrega un título exitoso a la consola en vivo"""
        self.console.configure(state="normal")
        # Buscar la línea de "✖ Fallidos:" e insertar antes
        content = self.console.get("1.0", "end")
        failed_pos = content.find("✖ Fallidos:")
        
        if failed_pos != -1:
            # Contar líneas antes de "✖ Fallidos:"
            before_text = content[:failed_pos]
            line_num = before_text.count('\n') + 1
            self.console.insert(f"{line_num}.0", f"  {len(self.successful_downloads)}. {title}\n")
        else:
            self.console.insert("end", f"  {len(self.successful_downloads)}. {title}\n")
        
        self.console.configure(state="disabled")
    
    def add_failed_to_console(self, title):
        """Agrega un título fallido a la consola en vivo"""
        self.console.configure(state="normal")
        self.console.insert("end", f"  {len(self.failed_downloads)}. {title}\n")
        self.console.configure(state="disabled")
    
    def show_console_error(self, message):
        """Muestra un error en la consola"""
        self.console.configure(state="normal")
        self.console.insert("end", f"\n❌ {message}\n")
        self.console.configure(state="disabled")

    def start_download(self):
        """Inicia el proceso de descarga"""
        if self.is_downloading:
            self.show_console_error("Ya hay una descarga en progreso")
            return
        
        # Obtener enlaces
        links_text = self.links.get("1.0", "end").strip()
        if not links_text:
            self.show_console_error("Por favor ingresa al menos un enlace")
            return
        
        urls = [line.strip() for line in links_text.split('\n') if line.strip()]
        
        # Obtener carpeta de destino y validar
        output_path = self.path.get()
        if not output_path or not os.path.exists(output_path) or not os.path.isdir(output_path):
            self.show_console_error("Por favor selecciona una carpeta válida que exista")
            return
        
        # Resetear variables
        self.successful_downloads = []
        self.failed_downloads = []
        self.is_downloading = True
        self.download_button.configure(state="disabled")
        
        # Limpiar consola manteniendo los títulos
        self.console.configure(state="normal")
        self.console.delete("1.0", "end")
        self.console.insert("end", "✔ Exitosos:\n\n✖ Fallidos:\n")
        self.console.configure(state="disabled")
        
        # Iniciar descarga en thread separado
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
                
                # Actualizar estadísticas
                self.update_stats(
                    queue_count=total - idx,
                    progress="0%",
                    successful=len(self.successful_downloads),
                    failed=len(self.failed_downloads)
                )
                
                # Callback de progreso
                def progress_callback(percent, speed, eta):
                    # Extraer solo el porcentaje usando regex
                    match = re.search(r'[\d.]+%', percent)
                    percent_only = match.group() if match else "0%"
                    self.update_stats(
                        queue_count=total - idx - 1,
                        progress=percent_only,
                        successful=len(self.successful_downloads),
                        failed=len(self.failed_downloads)
                    )
                
                # Callback para actualizar el título inmediatamente
                def title_callback(title):
                    self.video_title.configure(text=title)
                
                # Descargar
                success, title = download_youtube_audio(url, output_path, progress_callback, title_callback)
                
                if success and title:
                    self.successful_downloads.append(title)
                    self.add_success_to_console(title)
                    # Actualizar contador visual de exitosos
                    self.update_stats(
                        queue_count=total - idx - 1,
                        progress="100%",
                        successful=len(self.successful_downloads),
                        failed=len(self.failed_downloads)
                    )
                else:
                    self.failed_downloads.append(url)
                    self.add_failed_to_console(url)
                    # Actualizar contador visual de fallidos
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


if __name__ == "__main__":
    app = NovaHub()
    app.mainloop()
