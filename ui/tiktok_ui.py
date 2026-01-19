import customtkinter as ctk
from threading import Lock

from ui.base_ui import PlatformUI

# ===== PALETA =====
BG_MAIN  = "#0E1116"
BG_PANEL = "#151A21"
ACCENT   = "#3B5998"
TEXT_SEC = "#A9B1D6"
RADIUS   = 14


class TikTokUI(PlatformUI):
    
    def __init__(self, parent_frame: ctk.CTkFrame, console_lock: Lock):
        super().__init__(parent_frame, "TikTok")
        self.console_lock = console_lock
        self.main_frame = None
        
    def build(self):
        """Construye la interfaz de TikTok"""
        self.main_frame = ctk.CTkFrame(self.parent_frame, fg_color=BG_MAIN)
        
        # Título
        ctk.CTkLabel(
            self.main_frame,
            text="DESCARGA DE CONTENIDO - TIKTOK",
            font=ctk.CTkFont(size=22, weight="bold")
        ).pack(anchor="w", pady=(0, 20))

        # Mensaje de trabajo en progreso
        info = ctk.CTkFrame(self.main_frame, fg_color=BG_PANEL, corner_radius=RADIUS)
        info.pack(fill="both", expand=True, pady=(0, 20))

        ctk.CTkLabel(
            info,
            text="🚀 En Desarrollo",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=ACCENT
        ).pack(pady=(40, 20))

        ctk.CTkLabel(
            info,
            text="Esta interfaz de TikTok está en desarrollo.",
            text_color=TEXT_SEC,
            font=ctk.CTkFont(size=14)
        ).pack(pady=10)

        ctk.CTkLabel(
            info,
            text="Los controles y la funcionalidad serán añadidos pronto.",
            text_color=TEXT_SEC,
            font=ctk.CTkFont(size=14)
        ).pack(pady=(10, 40))

        # Volver a YouTube
        ctk.CTkButton(
            info,
            text="Volver a YouTube",
            height=40,
            fg_color=ACCENT,
            hover_color="#6487E5",
            font=ctk.CTkFont(size=12, weight="bold"),
            state="disabled"
        ).pack(pady=20)

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
