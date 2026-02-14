import json
import re
from io import BytesIO

import qrcode
from PIL import Image
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QTextEdit, QComboBox, QFrame, 
    QStackedWidget, QLineEdit, QFormLayout, QFileDialog
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QPixmap, QImage, QFont

from ui.base_ui import PlatformUI

# Define styles internally or import if shared
# Reusing some colors from main.py for consistency
BG_PANEL = "#151A21"
ACCENT   = "#3B5998"
TEXT_SEC = "#A9B1D6"
TEXT_MAIN = "#FFFFFF"

class QRUI(PlatformUI):
    def __init__(self, parent_widget: QWidget, console_lock):
        super().__init__(parent_widget, "QR")
        self.console_lock = console_lock if console_lock else None
        self.current_qr_image = None # Store PIL image
        
        # Main Layout
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(20, 20, 20, 20)
        self.layout.setSpacing(15)

        # Header
        header = QLabel("Generador de Códigos QR")
        header.setFont(QFont("Segoe UI", 18, QFont.Bold))
        header.setStyleSheet(f"color: {TEXT_MAIN};")
        self.layout.addWidget(header)

        # Type Selector
        type_layout = QHBoxLayout()
        type_label = QLabel("Tipo de contenido:")
        type_label.setStyleSheet(f"color: {TEXT_SEC}; font-size: 14px;")
        
        self.type_combo = QComboBox()
        self.type_combo.addItems(["URL", "JSON", "WiFi"])
        self.type_combo.currentIndexChanged.connect(self.on_type_changed)
        self.type_combo.setStyleSheet(f"""
            QComboBox {{
                background-color: {BG_PANEL};
                color: {TEXT_MAIN};
                padding: 8px 10px 8px 15px;
                border-radius: 8px;
                border: 1px solid #333;
                min-width: 80px;
            }}
            QComboBox::drop-down {{
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 30px;
                border-left: 1px solid #333;
                border-top-right-radius: 8px;
                border-bottom-right-radius: 8px;
                background-color: transparent;
            }}
        """)
        
        type_layout.addWidget(type_label)
        type_layout.addWidget(self.type_combo)
        type_layout.addStretch()
        self.layout.addLayout(type_layout)

        # Input Area (Stacked for different inputs)
        self.input_stack = QStackedWidget()
        
        # Page 1: Text Input (URL / JSON)
        # Page 1: Text Input (URL / JSON)
        # Wrapper para Input con bordes redondeados
        self.text_input_frame = QFrame()
        self.text_input_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {BG_PANEL};
                border-radius: 14px;
                border: 1px solid #333;
            }}
        """)
        text_input_layout = QVBoxLayout(self.text_input_frame)
        text_input_layout.setContentsMargins(10, 10, 10, 10)

        self.text_input = QTextEdit()
        self.text_input.setPlaceholderText("Escribe aquí tu URL o JSON...")
        self.text_input.setFrameShape(QFrame.NoFrame)
        self.text_input.setStyleSheet(f"""
            QTextEdit {{
                background-color: transparent;
                color: {TEXT_MAIN};
                border: none;
            }}
        """)
        text_input_layout.addWidget(self.text_input)
        self.input_stack.addWidget(self.text_input_frame)
        
        # Page 2: WiFi Input
        self.wifi_widget = QWidget()
        wifi_layout = QFormLayout(self.wifi_widget)
        
        self.wifi_ssid = QLineEdit()
        self.wifi_ssid.setPlaceholderText("Nombre de la red (SSID)")
        self.style_line_edit(self.wifi_ssid)
        
        # Wrapper para Password con botón de ojo
        self.pass_frame = QFrame()
        self.pass_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {BG_PANEL};
                border: 1px solid #333;
                border-radius: 5px;
            }}
        """)
        pass_layout = QHBoxLayout(self.pass_frame)
        pass_layout.setContentsMargins(0, 0, 5, 0)
        pass_layout.setSpacing(0)

        self.wifi_password = QLineEdit()
        self.wifi_password.setPlaceholderText("Contraseña")
        self.wifi_password.setEchoMode(QLineEdit.Password)
        self.wifi_password.setStyleSheet(f"""
            QLineEdit {{
                background-color: transparent;
                color: {TEXT_MAIN};
                border: none;
                padding: 8px;
            }}
        """)
        
        self.toggle_pass_btn = QPushButton("Mostrar")
        self.toggle_pass_btn.setCursor(Qt.PointingHandCursor)
        self.toggle_pass_btn.setFixedWidth(80)
        self.toggle_pass_btn.setToolTip("Mostrar contraseña")
        self.toggle_pass_btn.clicked.connect(self.toggle_password)
        self.toggle_pass_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #A9B1D6;
                border: none;
                font-size: 13px;
                font-weight: bold;
            }
            QPushButton:hover {
                color: #FFFFFF;
            }
        """)
        
        pass_layout.addWidget(self.wifi_password)
        pass_layout.addWidget(self.toggle_pass_btn)
        
        self.wifi_encryption = QComboBox()
        self.wifi_encryption.addItems(["WPA/WPA2", "WEP", "Sin encriptación"])
        self.wifi_encryption.setStyleSheet(self.type_combo.styleSheet())
        
        wifi_layout.addRow(self.create_label("SSID:"), self.wifi_ssid)
        wifi_layout.addRow(self.create_label("Contraseña:"), self.pass_frame)
        wifi_layout.addRow(self.create_label("Seguridad:"), self.wifi_encryption)
        
        self.input_stack.addWidget(self.wifi_widget)
        
        self.layout.addWidget(self.input_stack)

        # Generate Button
        self.generate_btn = QPushButton("Generar Código QR")
        self.generate_btn.setCursor(Qt.PointingHandCursor)
        self.generate_btn.clicked.connect(self.generate_qr)
        self.generate_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {ACCENT};
                color: white;
                font-weight: bold;
                padding: 12px;
                border-radius: 8px;
                font-size: 14px;
                text-align: center;
            }}
            QPushButton:hover {{
                background-color: #4B6CB7;
            }}
        """)
        self.layout.addWidget(self.generate_btn)

        # Results Area (Horizontal: QR Image | Console)
        results_layout = QHBoxLayout()
        
        # QR Image Area
        # QR Image Area Container
        qr_container = QWidget()
        qr_container_layout = QVBoxLayout(qr_container)
        qr_container_layout.setContentsMargins(0, 0, 0, 0)
        qr_container_layout.setSpacing(10)

        self.qr_label = QLabel()
        self.qr_label.setAlignment(Qt.AlignCenter)
        self.qr_label.setFixedSize(300, 300)
        self.qr_label.setText("El QR aparecerá aquí")
        self.qr_label.setStyleSheet(f"""
            QLabel {{
                background-color: white; 
                border-radius: 14px; 
                border: 2px solid #333;
                padding: 10px;
                color: black;
            }}
        """)
        
        # Download Button
        self.save_btn = QPushButton("Descargar PNG (720x720)")
        self.save_btn.setCursor(Qt.PointingHandCursor)
        self.save_btn.setEnabled(False) # Disabled until generated
        self.save_btn.clicked.connect(self.save_qr_image)
        self.save_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: #2D3748;
                color: {TEXT_SEC};
                border: none;
                border-radius: 8px;
                padding: 10px;
                font-weight: bold;
                text-align: center;
            }}
            QPushButton:hover {{
                background-color: #4A5568;
                color: white;
            }}
            QPushButton:disabled {{
                background-color: #1A202C;
                color: #555;
            }}
        """)

        qr_container_layout.addWidget(self.qr_label)
        qr_container_layout.addWidget(self.save_btn)

        # Console Area
        console_container = QWidget()
        console_layout = QVBoxLayout(console_container)
        console_layout.setContentsMargins(0, 0, 0, 0)
        
        console_header_layout = QHBoxLayout()
        console_label = QLabel("Consola de Estado")
        console_label.setStyleSheet(f"color: {TEXT_SEC}; font-weight: bold;")
        
        self.clear_btn = QPushButton("Limpiar Consola")
        self.clear_btn.setCursor(Qt.PointingHandCursor)
        self.clear_btn.clicked.connect(self.clear_console)
        self.clear_btn.setFixedWidth(140)
        self.clear_btn.setFixedHeight(32)
        self.clear_btn.setFont(QFont("Segoe UI", 10))
        self.clear_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: #2D3748;
                color: {TEXT_SEC};
                border: none;
                border-radius: 8px;
                text-align: center;
                padding: 5px;
            }}
            QPushButton:hover {{
                background-color: #4A5568;
            }}
        """)
        
        console_header_layout.addWidget(console_label)
        console_header_layout.addStretch()
        console_header_layout.addWidget(self.clear_btn)
        
        # Wrapper para Consola
        console_wrapper = QFrame()
        console_wrapper.setStyleSheet(f"""
            QFrame {{
                background-color: #000;
                border-radius: 14px;
                border: 1px solid #333;
            }}
        """)
        console_wrapper_layout = QVBoxLayout(console_wrapper)
        console_wrapper_layout.setContentsMargins(10, 10, 10, 10)

        self.console = QTextEdit()
        self.console.setReadOnly(True)
        self.console.setFrameShape(QFrame.NoFrame)
        self.console.setStyleSheet(f"""
            QTextEdit {{
                background-color: transparent;
                color: #0F0;
                font-family: Consolas, monospace;
                font-size: 12px;
                border: none;
            }}
        """)
        console_wrapper_layout.addWidget(self.console)
        
        console_layout.addLayout(console_header_layout)
        console_layout.addWidget(console_wrapper)
        
        results_layout.addWidget(qr_container)
        results_layout.addWidget(console_container)
        
        self.layout.addLayout(results_layout)
        self.layout.setStretch(2, 1) # Expand results area

    def style_line_edit(self, widget):
        widget.setStyleSheet(f"""
            QLineEdit {{
                background-color: {BG_PANEL};
                color: {TEXT_MAIN};
                padding: 8px;
                border: 1px solid #333;
                border-radius: 5px;
            }}
        """)

    def create_label(self, text):
        lbl = QLabel(text)
        lbl.setStyleSheet(f"color: {TEXT_SEC}; font-size: 14px;")
        return lbl

    def toggle_password(self):
        if self.wifi_password.echoMode() == QLineEdit.Password:
            self.wifi_password.setEchoMode(QLineEdit.Normal)
            self.toggle_pass_btn.setText("Ocultar")
            self.toggle_pass_btn.setStyleSheet("""
                QPushButton {
                    background-color: transparent;
                    color: #FFFFFF; /* Highlight when visible */
                    border: none;
                    font-size: 13px;
                    font-weight: bold;
                }
            """)
            self.toggle_pass_btn.setToolTip("Ocultar contraseña")
        else:
            self.wifi_password.setEchoMode(QLineEdit.Password)
            self.toggle_pass_btn.setText("Mostrar")
            self.toggle_pass_btn.setStyleSheet("""
                QPushButton {
                    background-color: transparent;
                    color: #A9B1D6;
                    border: none;
                    font-size: 13px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    color: #FFFFFF;
                }
            """)
            self.toggle_pass_btn.setToolTip("Mostrar contraseña")

    def on_type_changed(self, index):
        # 0: URL, 1: JSON, 2: WiFi
        if index == 2:
            self.input_stack.setCurrentIndex(1)
        else:
            self.input_stack.setCurrentIndex(0)
            if index == 1:
                self.text_input.setPlaceholderText("Pega tu objeto JSON o JS aquí...")
            else:
                self.text_input.setPlaceholderText("https://ejemplo.com")

    def log_message(self, message, is_error=False):
        color = "#FF5555" if is_error else "#50FA7B"
        prefix = "[ERROR]" if is_error else "[SUCCESS]"
        self.console.append(f'<span style="color:{color};"><b>{prefix}</b> {message}</span>')
        # Scroll to bottom
        sb = self.console.verticalScrollBar()
        sb.setValue(sb.maximum())

    def clear_console(self):
        self.console.clear()

    def generate_qr(self):
        # Limpiar consola al iniciar generación
        self.clear_console()
        
        content = ""
        mode = self.type_combo.currentText()
        
        try:
            if mode == "WiFi":
                ssid = self.wifi_ssid.text().strip()
                password = self.wifi_password.text()
                enc_idx = self.wifi_encryption.currentIndex()
                
                if not ssid:
                    raise ValueError("El nombre de la red (SSID) es obligatorio.")
                
                # Format: WIFI:T:WPA;S:mynetwork;P:mypass;;
                enc_type = "WPA" # Default
                if enc_idx == 1: enc_type = "WEP"
                elif enc_idx == 2: enc_type = "nopass"
                
                content = f"WIFI:T:{enc_type};S:{ssid};P:{password};;"
                
            elif mode == "JSON":
                raw_text = self.text_input.toPlainText().strip()
                if not raw_text:
                    raise ValueError("El campo de texto está vacío.")
                
                # Intentar limpiar input JS para hacerlo JSON válido
                # 1. Reemplazar keys sin comillas: {key: -> {"key":
                # Esto es una aproximación básica
                cleaned_text = re.sub(r'(?<=[\{\s,])(\w+)(?=:)', r'"\1"', raw_text)
                
                # Si tiene comillas simples, cambiar a dobles (cuidado con el contenido)
                # Una mejor aproximación si falla json.loads es intentar ast.literal_eval
                # pero ast.literal_eval es de python, no JS.
                # Vamos a intentar json.loads primero
                
                try:
                    json_obj = json.loads(raw_text)
                    content = json.dumps(json_obj, indent=2) # Formatear bonito para el QR si se desea, o compacto
                except json.JSONDecodeError:
                    self.log_message("JSON inválido directo. Intentando conversión de objeto JS...", is_error=True)
                    try:
                        # Intento con regex simple para claves
                        # y reemplazo de ' por "
                        # O usamos un parser más permisivo
                        # Aquí usaremos la transformación que hicimos antes como fallback
                        json_obj = json.loads(cleaned_text)
                        content = json.dumps(json_obj)
                        self.log_message("Conversión de JS a JSON exitosa.")
                    except:
                        # Último intento: reemplazar ' por " y tratar de parsear
                         try:
                             fixed_quotes = raw_text.replace("'", '"')
                             # Regex para poner comillas a las claves si faltan
                             fixed_keys = re.sub(r'(?<=[\{\s,])(\w+)(?=:)', r'"\1"', fixed_quotes)
                             json_obj = json.loads(fixed_keys)
                             content = json.dumps(json_obj)
                             self.log_message("Conversión forzada exitosa.", is_error=False)
                         except Exception as e:
                             raise ValueError(f"No se pudo convertir el texto a JSON válido: {str(e)}")
            
            else: # URL
                content = self.text_input.toPlainText().strip()
                if not content:
                    raise ValueError("La URL está vacía.")
                if not (content.startswith("http://") or content.startswith("https://")):
                    self.log_message("Advertencia: La URL no comienza con http:// o https://", is_error=True)

            # Generar QR
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(content)
            qr.make(fit=True)

            img = qr.make_image(fill_color="black", back_color="white")
            self.current_qr_image = img # Guardar referencia PIL
            self.save_btn.setEnabled(True) # Habilitar botón de guardar
            
            # Convertir a QPixmap para mostrar en QLabel
            buffer = BytesIO()
            img.save(buffer, format="PNG")
            qt_img = QImage.fromData(buffer.getvalue())
            pixmap = QPixmap.fromImage(qt_img)
            
            # Escalar considerando el padding (300 - 20 = 280)
            self.qr_label.setPixmap(pixmap.scaled(280, 280, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            self.log_message("Código QR generado exitosamente.")
            
        except Exception as e:
            self.log_message(str(e), is_error=True)

    def save_qr_image(self):
        """Guarda la imagen QR actual en 720x720 PNG"""
        if not self.current_qr_image:
            self.log_message("No hay código QR generado para guardar.", is_error=True)
            return

        try:
            # Abrir diálogo de guardado
            file_path, _ = QFileDialog.getSaveFileName(
                self, 
                "Guardar Código QR", 
                "codigo_qr.png", 
                "Imágenes PNG (*.png)"
            )
            
            if file_path:
                # Asegurar extensión
                if not file_path.lower().endswith('.png'):
                    file_path += '.png'
                
                # Redimensionar a 720x720 con alta calidad
                # Convertir a RGB por si acaso es modo 1 (bitmap)
                final_img = self.current_qr_image.convert("RGB")
                
                # Compatibility for Pillow < 9.1.0
                if hasattr(Image, 'Resampling'):
                    resample_method = Image.Resampling.LANCZOS
                else:
                    resample_method = Image.LANCZOS
                
                final_img = final_img.resize((720, 720), resample_method)
                
                final_img.save(file_path, format="PNG")
                self.log_message(f"Imagen guardada en: {file_path}")
                
        except Exception as e:
            self.log_message(f"Error al guardar imagen: {str(e)}", is_error=True)

    # Implementación de métodos abstractos de BaseUI
    def build(self):
        pass

    def show(self):
        super().show()

    def hide(self):
        super().hide()

    def get_widget(self) -> QWidget:
        return self
