import sys
from PySide6.QtWidgets import QApplication
from ui.main import NovaHub

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = NovaHub()
    window.showMaximized()
    try:
        sys.exit(app.exec())
    except KeyboardInterrupt:
        print("Aplicación cerrada por el usuario.")
        sys.exit(0)
