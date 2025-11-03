"""
Save Snippet Dialog - Dialog para guardar texto seleccionado como snippet
"""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QTextEdit, QComboBox, QPushButton, QMessageBox,
    QRadioButton, QButtonGroup
)
from PyQt6.QtCore import Qt
import logging

logger = logging.getLogger(__name__)


class SaveSnippetDialog(QDialog):
    """
    Dialog para guardar texto seleccionado del navegador como snippet.

    Permite seleccionar:
    - Categoría destino
    - Tipo de item (CODE o TEXT)
    - Label del item
    - Descripción (opcional)
    - Tags (opcional)
    """

    def __init__(self, selected_text: str, categories: list, parent=None):
        """
        Inicializa el dialog.

        Args:
            selected_text: Texto seleccionado en el navegador
            categories: Lista de categorías disponibles
            parent: Widget padre
        """
        super().__init__(parent)
        self.selected_text = selected_text
        self.categories = categories
        self.selected_category_id = None
        self.selected_type = 'TEXT'  # Default

        self.init_ui()

    def init_ui(self):
        """Inicializa la interfaz del dialog."""
        self.setWindowTitle("Guardar Snippet")
        self.setModal(True)
        self.setMinimumWidth(600)
        self.setMinimumHeight(500)

        # Layout principal
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # === Preview del texto seleccionado ===
        preview_label = QLabel("Texto seleccionado:")
        preview_label.setStyleSheet("font-weight: bold; color: #00d4ff;")
        layout.addWidget(preview_label)

        self.text_preview = QTextEdit()
        self.text_preview.setPlainText(self.selected_text)
        self.text_preview.setReadOnly(True)
        self.text_preview.setMaximumHeight(150)
        self.text_preview.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #888888;
                border: 1px solid #3d3d3d;
                border-radius: 3px;
                padding: 8px;
                font-size: 10pt;
                font-family: 'Consolas', 'Courier New', monospace;
            }
        """)
        layout.addWidget(self.text_preview)

        # === Tipo de snippet (CODE o TEXT) ===
        type_label = QLabel("Tipo de snippet: *")
        type_label.setStyleSheet("font-weight: bold; color: #00d4ff;")
        layout.addWidget(type_label)

        type_layout = QHBoxLayout()
        self.type_group = QButtonGroup(self)

        self.text_radio = QRadioButton("📝 TEXT (Texto general)")
        self.text_radio.setChecked(True)  # Default
        self.text_radio.setStyleSheet("""
            QRadioButton {
                color: #ffffff;
                font-size: 10pt;
                spacing: 8px;
            }
            QRadioButton::indicator {
                width: 18px;
                height: 18px;
            }
            QRadioButton::indicator:checked {
                background-color: #00d4ff;
                border: 2px solid #00d4ff;
                border-radius: 9px;
            }
            QRadioButton::indicator:unchecked {
                background-color: #2d2d2d;
                border: 2px solid #3d3d3d;
                border-radius: 9px;
            }
        """)
        self.type_group.addButton(self.text_radio)
        type_layout.addWidget(self.text_radio)

        self.code_radio = QRadioButton("💻 CODE (Código)")
        self.code_radio.setStyleSheet("""
            QRadioButton {
                color: #ffffff;
                font-size: 10pt;
                spacing: 8px;
            }
            QRadioButton::indicator {
                width: 18px;
                height: 18px;
            }
            QRadioButton::indicator:checked {
                background-color: #00d4ff;
                border: 2px solid #00d4ff;
                border-radius: 9px;
            }
            QRadioButton::indicator:unchecked {
                background-color: #2d2d2d;
                border: 2px solid #3d3d3d;
                border-radius: 9px;
            }
        """)
        self.type_group.addButton(self.code_radio)
        type_layout.addWidget(self.code_radio)

        type_layout.addStretch()
        layout.addLayout(type_layout)

        # === Categoría ===
        category_label = QLabel("Categoría: *")
        category_label.setStyleSheet("font-weight: bold; color: #00d4ff;")
        layout.addWidget(category_label)

        self.category_combo = QComboBox()
        self.category_combo.setStyleSheet("""
            QComboBox {
                background-color: #2d2d2d;
                color: #ffffff;
                border: 1px solid #3d3d3d;
                border-radius: 3px;
                padding: 8px;
                font-size: 10pt;
            }
            QComboBox:hover {
                border: 1px solid #00d4ff;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox QAbstractItemView {
                background-color: #2d2d2d;
                color: #ffffff;
                selection-background-color: #00d4ff;
                selection-color: #000000;
            }
        """)

        # Agregar categorías al combo
        for category in self.categories:
            display_text = f"{category.icon} {category.name}" if hasattr(category, 'icon') else category.name
            self.category_combo.addItem(display_text, category.id)

        layout.addWidget(self.category_combo)

        # === Label ===
        label_label = QLabel("Nombre del Snippet: *")
        label_label.setStyleSheet("font-weight: bold; color: #00d4ff;")
        layout.addWidget(label_label)

        self.label_input = QLineEdit()
        # Auto-sugerir primeras palabras del texto
        auto_label = self._generate_auto_label()
        self.label_input.setText(auto_label)
        self.label_input.setPlaceholderText("Ej: Función para validar email")
        self.label_input.setStyleSheet("""
            QLineEdit {
                background-color: #2d2d2d;
                color: #ffffff;
                border: 1px solid #3d3d3d;
                border-radius: 3px;
                padding: 8px;
                font-size: 10pt;
            }
            QLineEdit:focus {
                border: 1px solid #00d4ff;
            }
        """)
        layout.addWidget(self.label_input)

        # === Descripción (opcional) ===
        desc_label = QLabel("Descripción: (opcional)")
        desc_label.setStyleSheet("font-weight: bold; color: #888888;")
        layout.addWidget(desc_label)

        self.description_input = QTextEdit()
        self.description_input.setPlaceholderText("Agrega una descripción opcional...")
        self.description_input.setMaximumHeight(80)
        self.description_input.setStyleSheet("""
            QTextEdit {
                background-color: #2d2d2d;
                color: #ffffff;
                border: 1px solid #3d3d3d;
                border-radius: 3px;
                padding: 8px;
                font-size: 10pt;
            }
            QTextEdit:focus {
                border: 1px solid #00d4ff;
            }
        """)
        layout.addWidget(self.description_input)

        # === Tags (opcional) ===
        tags_label = QLabel("Tags: (opcional, separados por comas)")
        tags_label.setStyleSheet("font-weight: bold; color: #888888;")
        layout.addWidget(tags_label)

        self.tags_input = QLineEdit()
        self.tags_input.setPlaceholderText("Ej: python, validación, regex")
        self.tags_input.setStyleSheet("""
            QLineEdit {
                background-color: #2d2d2d;
                color: #ffffff;
                border: 1px solid #3d3d3d;
                border-radius: 3px;
                padding: 8px;
                font-size: 10pt;
            }
            QLineEdit:focus {
                border: 1px solid #00d4ff;
            }
        """)
        layout.addWidget(self.tags_input)

        # === Botones ===
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()

        cancel_btn = QPushButton("Cancelar")
        cancel_btn.setFixedWidth(100)
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #3d3d3d;
                color: #ffffff;
                border: none;
                border-radius: 3px;
                padding: 10px;
                font-size: 10pt;
            }
            QPushButton:hover {
                background-color: #4d4d4d;
            }
        """)
        cancel_btn.clicked.connect(self.reject)
        buttons_layout.addWidget(cancel_btn)

        save_btn = QPushButton("Guardar")
        save_btn.setFixedWidth(100)
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: #00d4ff;
                color: #000000;
                border: none;
                border-radius: 3px;
                padding: 10px;
                font-size: 10pt;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #00b8d4;
            }
        """)
        save_btn.clicked.connect(self.validate_and_accept)
        buttons_layout.addWidget(save_btn)

        layout.addLayout(buttons_layout)

        # Aplicar estilo general al dialog
        self.setStyleSheet("""
            QDialog {
                background-color: #1e1e1e;
            }
            QLabel {
                color: #ffffff;
            }
        """)

    def _generate_auto_label(self):
        """Genera un label automático basado en el texto seleccionado."""
        # Tomar primeras palabras (máx 50 chars)
        text = self.selected_text.strip()
        if len(text) <= 50:
            return text
        else:
            # Cortar en la última palabra completa antes de 50 chars
            truncated = text[:50]
            last_space = truncated.rfind(' ')
            if last_space > 20:  # Si hay un espacio razonable
                return truncated[:last_space] + "..."
            else:
                return truncated + "..."

    def validate_and_accept(self):
        """Valida los campos antes de aceptar."""
        # Validar que haya categoría seleccionada
        if self.category_combo.currentIndex() < 0:
            QMessageBox.warning(self, "Error", "Debes seleccionar una categoría")
            return

        # Validar que haya label
        if not self.label_input.text().strip():
            QMessageBox.warning(self, "Error", "Debes ingresar un nombre para el snippet")
            return

        self.accept()

    def get_data(self):
        """
        Obtiene los datos ingresados en el dialog.

        Returns:
            dict: Diccionario con los datos del item a crear
        """
        # Obtener category_id del combo
        category_id = self.category_combo.currentData()

        # Determinar tipo basado en radio button seleccionado
        item_type = 'CODE' if self.code_radio.isChecked() else 'TEXT'

        # Procesar tags (separar por comas y limpiar)
        tags_text = self.tags_input.text().strip()
        tags = [tag.strip() for tag in tags_text.split(',') if tag.strip()] if tags_text else []

        return {
            'category_id': category_id,
            'label': self.label_input.text().strip(),
            'content': self.selected_text,
            'description': self.description_input.toPlainText().strip() or None,
            'tags': tags,
            'type': item_type
        }
