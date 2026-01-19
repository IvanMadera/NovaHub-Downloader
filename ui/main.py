import customtkinter as ctk
from datetime import datetime
from threading import Lock

from ui.youtube_ui import YouTubeUI
from ui.tiktok_ui import TikTokUI

# ================== CONFIG ==================
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

# ===== PALETA =====
BG_MAIN  = "#0E1116"
BG_PANEL = "#151A21"
ACCENT   = "#3B5998"
TEXT_SEC = "#A9B1D6"


class NovaHub(ctk.CTk):

    def __init__(self):
        super().__init__()

        self.title("Nova Hub")
        self.geometry("1280x760")
        self.minsize(1180, 700)
        self.configure(fg_color=BG_MAIN)

        self.console_lock = Lock()
        self.current_platform = "YouTube"
        
        # Instancias de UIs
        self.platform_uis = {}

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

        # Crear botones dinámicamente
        self.platform_buttons = {}
        platforms_list = ["YouTube", "TikTok"]
        
        for platform_name in platforms_list:
            btn = ctk.CTkButton(
                sidebar,
                text=f"◈  {platform_name}",
                height=44,
                anchor="w",
                fg_color=BG_PANEL,
                hover_color="#1C2230",
                text_color=TEXT_SEC,
                font=ctk.CTkFont(size=14),
                command=lambda p=platform_name: self.set_platform(p)
            )
            btn.pack(fill="x", padx=18, pady=6)
            self.platform_buttons[platform_name] = btn
        
        # ================== FOOTER ==================
        footer = ctk.CTkFrame(sidebar, fg_color="transparent")
        footer.pack(side="bottom", fill="x", padx=12, pady=20)

        ctk.CTkLabel(
            footer,
            text=f"© Copyright {datetime.now().year}",
            text_color=TEXT_SEC,
            font=ctk.CTkFont(size=14)
        ).pack()

        # ================== CONTENT AREA ==================
        self.content_frame = ctk.CTkFrame(self, fg_color=BG_MAIN)
        self.content_frame.pack(side="left", fill="both", expand=True)

        # Construir UIs
        self.platform_uis["YouTube"] = YouTubeUI(self.content_frame, self.console_lock)
        self.platform_uis["YouTube"].build()
        
        self.platform_uis["TikTok"] = TikTokUI(self.content_frame, self.console_lock)
        self.platform_uis["TikTok"].build()

        # Mostrar YouTube por defecto
        self.set_platform("YouTube")

    def set_platform(self, platform_name: str):
        """Cambia la plataforma activa"""
        # Ocultar plataforma anterior
        if self.current_platform in self.platform_uis:
            self.platform_uis[self.current_platform].hide()

        # Cambiar plataforma
        self.current_platform = platform_name
        
        # Mostrar nueva plataforma
        if platform_name in self.platform_uis:
            self.platform_uis[platform_name].show()

        # Destacar botón
        self.highlight_platform(platform_name)

    def highlight_platform(self, platform_name: str):
        """Destaca el botón de la plataforma activa"""
        for name, btn in self.platform_buttons.items():
            if name == platform_name:
                btn.configure(fg_color=ACCENT, text_color="white")
            else:
                btn.configure(fg_color=BG_PANEL, text_color=TEXT_SEC)


if __name__ == "__main__":
    app = NovaHub()
    app.mainloop()
