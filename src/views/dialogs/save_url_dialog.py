"""
Save URL Dialog - Dialog para guardar la URL actual del navegador como item
"""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QTextEdit, QComboBox, QPushButton, QMessageBox, QScrollArea
)
from PyQt6.QtCore import Qt
import sys
from pathlib import Path
import logging

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from views.widgets.tag_group_selector import TagGroupSelector

logger = logging.getLogger(__name__)


class SaveUrlDialog(QDialog):
    """
    Dialog para guardar URL actual del navegador como item.

    Permite seleccionar:
    - Categoría destino
    - Label del item (auto: título de página)
    - Descripción (opcional)
    - Tags (opcional)
    """

    def __init__(self, current_url: str, page_title: str, categories: list, db_path: str = None, parent=None):
        """
        Inicializa el dialog.

        Args:
            current_url: URL actual del navegador
            page_title: Título de la página actual
            categories: Lista de categorías disponibles
            db_path: Path a la base de datos para TagGroupSelector
            parent: Widget padre
        """
        super().__init__(parent)
        self.current_url = current_url
        self.page_title = page_title
        self.categories = categories
        self.db_path = db_path
        self.selected_category_id = None

        self.init_ui()

    def init_ui(self):
        """Inicializa la interfaz del dialog."""
        self.setWindowTitle("Guardar URL")
        self.setModal(True)
        self.setMinimumWidth(500)

        # Layout principal
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # === URL (solo lectura) ===
        url_label = QLabel("URL:")
        url_label.setStyleSheet("font-weight: bold; color: #00d4ff;")
        layout.addWidget(url_label)

        self.url_display = QLineEdit()
        self.url_display.setText(self.current_url)
        self.url_display.setReadOnly(True)
        self.url_display.setStyleSheet("""
            QLineEdit {
                background-color: #1e1e1e;
                color: #888888;
                border: 1px solid #3d3d3d;
                border-radius: 3px;
                padding: 8px;
                font-size: 10pt;
            }
        """)
        layout.addWidget(self.url_display)

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

        # === Label (auto-completado con título) ===
        label_label = QLabel("Nombre del Item: *")
        label_label.setStyleSheet("font-weight: bold; color: #00d4ff;")
        layout.addWidget(label_label)

        self.label_input = QLineEdit()
        # Auto-completar con título de página (primeros 50 chars)
        auto_label = self.page_title[:50] if self.page_title else "Nueva URL"
        self.label_input.setText(auto_label)
        self.label_input.setPlaceholderText("Ej: Documentación React")
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
        self.tags_input.setPlaceholderText("Ej: react, documentación, web")
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

        # Tag Group Selector (optional) - wrapped in scroll area
        if self.db_path:
            try:
                self.tag_group_selector = TagGroupSelector(self.db_path, self)
                self.tag_group_selector.tags_changed.connect(self.on_tag_group_changed)

                # Create scroll area for tag group selector
                tags_scroll_area = QScrollArea()
                tags_scroll_area.setWidget(self.tag_group_selector)
                tags_scroll_area.setWidgetResizable(True)
                tags_scroll_area.setFixedHeight(120)  # Fixed height with scroll
                tags_scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
                tags_scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
                tags_scroll_area.setFrameShape(QScrollArea.Shape.NoFrame)
                tags_scroll_area.setStyleSheet("""
                    QScrollArea {
                        border: 1px solid #3d3d3d;
                        border-radius: 4px;
                        background-color: #2d2d2d;
                    }
                    QScrollBar:vertical {
                        background-color: #2d2d2d;
                        width: 12px;
                        border-radius: 6px;
                    }
                    QScrollBar::handle:vertical {
                        background-color: #5a5a5a;
                        border-radius: 6px;
                        min-height: 20px;
                    }
                    QScrollBar::handle:vertical:hover {
                        background-color: #007acc;
                    }
                    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                        height: 0px;
                    }
                """)

                layout.addWidget(tags_scroll_area)
            except Exception as e:
                logger.warning(f"Could not initialize TagGroupSelector: {e}")
                self.tag_group_selector = None
        else:
            self.tag_group_selector = None

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

    def on_tag_group_changed(self, tags: list):
        """Handle tag group selector changes"""
        try:
            # Actualizar el campo de tags con los tags seleccionados
            if tags:
                self.tags_input.setText(", ".join(tags))
            else:
                self.tags_input.setText("")
            logger.debug(f"Tags updated from tag group selector: {tags}")
        except Exception as e:
            logger.error(f"Error updating tags from tag group selector: {e}")

    def validate_and_accept(self):
        """Valida los campos antes de aceptar."""
        # Validar que haya categoría seleccionada
        if self.category_combo.currentIndex() < 0:
            QMessageBox.warning(self, "Error", "Debes seleccionar una categoría")
            return

        # Validar que haya label
        if not self.label_input.text().strip():
            QMessageBox.warning(self, "Error", "Debes ingresar un nombre para el item")
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

        # Procesar tags (separar por comas y limpiar)
        tags_text = self.tags_input.text().strip()
        tags = [tag.strip() for tag in tags_text.split(',') if tag.strip()] if tags_text else []

        return {
            'category_id': category_id,
            'label': self.label_input.text().strip(),
            'content': self.current_url,
            'description': self.description_input.toPlainText().strip() or None,
            'tags': tags,
            'type': 'URL'
        }
