"""
NotebookTab Widget
Formulario completo para editar una nota y convertirla en item
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QTextEdit,
    QComboBox, QCheckBox, QPushButton, QLabel, QGroupBox, QScrollArea
)
from PyQt6.QtCore import pyqtSignal, Qt, QTimer
from PyQt6.QtGui import QFont
import sys
from pathlib import Path
import logging

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from views.widgets.tag_group_selector import TagGroupSelector

logger = logging.getLogger(__name__)


class NotebookTab(QWidget):
    """Widget de pestaña individual del notebook con formulario completo"""

    # Señales
    save_requested = pyqtSignal(dict)  # Emite datos del formulario para guardar como item
    content_changed = pyqtSignal(dict)  # Para auto-guardado (emite datos del formulario)
    cancel_requested = pyqtSignal()  # Cuando se hace click en cancelar

    def __init__(self, tab_id=None, tab_data=None, categories=None, db_path=None, parent=None):
        super().__init__(parent)
        self.tab_id = tab_id
        self.categories = categories or []
        self.db_path = db_path
        self.has_unsaved_changes = False

        # Debounce para auto-guardado
        self.autosave_timer = QTimer()
        self.autosave_timer.setSingleShot(True)
        self.autosave_timer.setInterval(1000)  # 1 segundo de debounce
        self.autosave_timer.timeout.connect(self.emit_content_changed)

        self.setup_ui()

        if tab_data:
            self.load_data(tab_data)

        # Conectar señales para auto-guardado después de cargar datos
        self.connect_autosave_signals()

    def setup_ui(self):
        """Configurar interfaz del formulario"""
        # Layout principal con scroll
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Scroll area para el contenido
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)

        # Widget contenedor del formulario
        form_widget = QWidget()
        form_layout = QVBoxLayout(form_widget)
        form_layout.setContentsMargins(20, 20, 20, 20)
        form_layout.setSpacing(15)

        # === NOMBRE DEL ITEM ===
        name_label = QLabel("Nombre del item:")
        name_label.setStyleSheet("color: #B0B0B0; font-size: 11px; font-weight: bold;")
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Ej: Script de backup, API endpoint, comando git, etc.")
        self.name_input.setMinimumHeight(36)
        self.style_input(self.name_input)

        form_layout.addWidget(name_label)
        form_layout.addWidget(self.name_input)

        # === CONTENIDO (AREA GRANDE) ===
        content_label = QLabel("Contenido:")
        content_label.setStyleSheet("color: #B0B0B0; font-size: 11px; font-weight: bold;")
        self.content_input = QTextEdit()
        self.content_input.setPlaceholderText("Escribe tu contenido aqui...\n\nPuedes escribir:\n- Comandos de terminal\n- Codigo\n- URLs\n- Rutas de archivos\n- Notas de texto")
        self.content_input.setMinimumHeight(280)

        # Font monospace para contenido
        font = QFont("Consolas", 10)
        if font.family() != "Consolas":  # Fallback si Consolas no está disponible
            font = QFont("Courier New", 10)
        self.content_input.setFont(font)

        self.style_text_edit(self.content_input)

        form_layout.addWidget(content_label)
        form_layout.addWidget(self.content_input, 1)  # Stretch factor para que ocupe espacio

        # === ROW: CATEGORIA + TIPO ===
        row_layout = QHBoxLayout()
        row_layout.setSpacing(15)

        # Categoría
        cat_group = QVBoxLayout()
        cat_group.setSpacing(5)
        cat_label = QLabel("Categoria:")
        cat_label.setStyleSheet("color: #B0B0B0; font-size: 11px; font-weight: bold;")
        self.category_combo = QComboBox()
        self.category_combo.setMinimumHeight(36)
        self.load_categories()
        self.style_combo(self.category_combo)
        cat_group.addWidget(cat_label)
        cat_group.addWidget(self.category_combo)

        # Tipo
        type_group = QVBoxLayout()
        type_group.setSpacing(5)
        type_label = QLabel("Tipo:")
        type_label.setStyleSheet("color: #B0B0B0; font-size: 11px; font-weight: bold;")
        self.type_combo = QComboBox()
        self.type_combo.setMinimumHeight(36)
        self.type_combo.addItems(['TEXT', 'CODE', 'URL', 'PATH'])
        self.style_combo(self.type_combo)
        type_group.addWidget(type_label)
        type_group.addWidget(self.type_combo)

        row_layout.addLayout(cat_group, 2)
        row_layout.addLayout(type_group, 1)
        form_layout.addLayout(row_layout)

        # === TAGS ===
        tags_label = QLabel("Tags (opcional):")
        tags_label.setStyleSheet("color: #B0B0B0; font-size: 11px; font-weight: bold;")
        self.tags_input = QLineEdit()
        self.tags_input.setPlaceholderText("Ej: python, script, backup, produccion")
        self.tags_input.setMinimumHeight(36)
        self.style_input(self.tags_input)

        form_layout.addWidget(tags_label)
        form_layout.addWidget(self.tags_input)

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

                form_layout.addWidget(tags_scroll_area)
            except Exception as e:
                logger.warning(f"Could not initialize TagGroupSelector: {e}")
                self.tag_group_selector = None
        else:
            self.tag_group_selector = None

        # Add vertical spacer after tag section
        form_layout.addSpacing(15)

        # === DESCRIPCION ===
        desc_label = QLabel("Descripcion (opcional):")
        desc_label.setStyleSheet("color: #B0B0B0; font-size: 11px; font-weight: bold;")
        self.description_input = QLineEdit()
        self.description_input.setPlaceholderText("Breve descripcion del item")
        self.description_input.setMinimumHeight(36)
        self.style_input(self.description_input)

        form_layout.addWidget(desc_label)
        form_layout.addWidget(self.description_input)

        # === CHECKBOXES ===
        self.sensitive_check = QCheckBox("Marcar como sensible (cifrar contenido)")
        self.active_check = QCheckBox("Item activo (puede ser usado)")
        self.archived_check = QCheckBox("Item archivado (ocultar de vista)")

        self.active_check.setChecked(True)  # Default: activo

        self.style_checkbox(self.sensitive_check)
        self.style_checkbox(self.active_check)
        self.style_checkbox(self.archived_check)

        form_layout.addSpacing(5)
        form_layout.addWidget(self.sensitive_check)
        form_layout.addWidget(self.active_check)
        form_layout.addWidget(self.archived_check)

        # Add stretch at the end of form (inside scroll)
        form_layout.addStretch()

        # Agregar widget al scroll
        scroll.setWidget(form_widget)
        main_layout.addWidget(scroll)

        # === BOTONES (FUERA DEL SCROLL, FIJOS EN LA PARTE INFERIOR) ===
        buttons_container = QWidget()
        buttons_container_layout = QVBoxLayout(buttons_container)
        buttons_container_layout.setContentsMargins(20, 10, 20, 20)
        buttons_container_layout.setSpacing(0)

        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self.cancel_btn = QPushButton("Cancelar")
        self.save_btn = QPushButton("Guardar como Item")

        self.cancel_btn.setMinimumSize(110, 40)
        self.save_btn.setMinimumSize(170, 40)

        self.style_button(self.cancel_btn, secondary=True)
        self.style_button(self.save_btn, primary=True)

        button_layout.addWidget(self.cancel_btn)

        # Add spacing between buttons
        button_layout.addSpacing(15)

        button_layout.addWidget(self.save_btn)

        buttons_container_layout.addLayout(button_layout)

        # Conectar botones
        self.save_btn.clicked.connect(self.on_save_clicked)
        self.cancel_btn.clicked.connect(self.on_cancel_clicked)

        # Agregar contenedor de botones al layout principal (fuera del scroll)
        main_layout.addWidget(buttons_container)

        # Estilo general del widget
        self.setStyleSheet("""
            QWidget {
                background-color: #1E1E1E;
                color: #FFFFFF;
            }
        """)

    def load_categories(self):
        """Cargar categorias en el combo"""
        self.category_combo.clear()

        if not self.categories:
            self.category_combo.addItem("Sin categorias disponibles", None)
            self.category_combo.setEnabled(False)
            return

        for cat in self.categories:
            # Format: "🔧 Git"
            # Category es un objeto, no un diccionario - acceder a atributos directamente
            icon = cat.icon if hasattr(cat, 'icon') else ''
            name = cat.name
            display_text = f"{icon} {name}" if icon else name
            self.category_combo.addItem(display_text, cat.id)

    def connect_autosave_signals(self):
        """Conectar señales para auto-guardado con debounce"""
        self.name_input.textChanged.connect(self.on_content_modified)
        self.content_input.textChanged.connect(self.on_content_modified)
        self.tags_input.textChanged.connect(self.on_content_modified)
        self.description_input.textChanged.connect(self.on_content_modified)
        self.category_combo.currentIndexChanged.connect(self.on_content_modified)
        self.type_combo.currentIndexChanged.connect(self.on_content_modified)
        self.sensitive_check.stateChanged.connect(self.on_content_modified)
        self.active_check.stateChanged.connect(self.on_content_modified)
        self.archived_check.stateChanged.connect(self.on_content_modified)

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

    def on_content_modified(self):
        """Marcar como modificado y programar auto-guardado"""
        self.has_unsaved_changes = True
        # Reiniciar timer para debounce
        self.autosave_timer.start()

    def emit_content_changed(self):
        """Emitir señal de cambio de contenido (después del debounce)"""
        data = self.get_data()
        self.content_changed.emit(data)
        logger.debug(f"Content changed emitted for tab {self.tab_id}")

    def on_save_clicked(self):
        """Validar y emitir señal de guardado"""
        data = self.get_data()

        # Validacion basica
        if not data['label'].strip():
            logger.warning("Cannot save: label is empty")
            # TODO: mostrar mensaje de error al usuario
            return

        if not data['content'].strip():
            logger.warning("Cannot save: content is empty")
            # TODO: mostrar mensaje de error al usuario
            return

        if data['category_id'] is None:
            logger.warning("Cannot save: no category selected")
            # TODO: mostrar mensaje de error
            return

        logger.info(f"Save requested for tab {self.tab_id}: {data['label']}")
        self.save_requested.emit(data)
        self.has_unsaved_changes = False

    def on_cancel_clicked(self):
        """Limpiar formulario o cerrar tab"""
        logger.debug(f"Cancel clicked for tab {self.tab_id}")
        self.cancel_requested.emit()

    def get_data(self):
        """Obtener datos del formulario"""
        return {
            'label': self.name_input.text(),
            'content': self.content_input.toPlainText(),
            'category_id': self.category_combo.currentData(),
            'item_type': self.type_combo.currentText(),
            'tags': self.tags_input.text(),
            'description': self.description_input.text(),
            'is_sensitive': self.sensitive_check.isChecked(),
            'is_active': self.active_check.isChecked(),
            'is_archived': self.archived_check.isChecked(),
        }

    def load_data(self, data):
        """Cargar datos en el formulario"""
        # Bloquear señales temporalmente para evitar auto-guardado durante carga
        self.blockSignals(True)

        self.name_input.setText(data.get('title', ''))
        self.content_input.setPlainText(data.get('content', ''))

        # Load tags
        tags_text = data.get('tags', '')
        self.tags_input.setText(tags_text)

        # También cargar en el tag group selector si existe
        if self.tag_group_selector and tags_text:
            tags_list = [tag.strip() for tag in tags_text.split(',') if tag.strip()]
            self.tag_group_selector.set_tags(tags_list)

        self.description_input.setText(data.get('description', ''))

        # Seleccionar categoria
        category_id = data.get('category_id')
        if category_id:
            index = self.category_combo.findData(category_id)
            if index >= 0:
                self.category_combo.setCurrentIndex(index)

        # Seleccionar tipo
        item_type = data.get('item_type', 'TEXT')
        index = self.type_combo.findText(item_type)
        if index >= 0:
            self.type_combo.setCurrentIndex(index)

        # Checkboxes
        self.sensitive_check.setChecked(bool(data.get('is_sensitive', 0)))
        self.active_check.setChecked(bool(data.get('is_active', 1)))
        self.archived_check.setChecked(bool(data.get('is_archived', 0)))

        self.blockSignals(False)
        logger.debug(f"Data loaded for tab {self.tab_id}")

    def clear_form(self):
        """Limpiar todos los campos del formulario"""
        self.blockSignals(True)

        self.name_input.clear()
        self.content_input.clear()
        self.tags_input.clear()
        self.description_input.clear()

        # Reset checkboxes
        self.sensitive_check.setChecked(False)
        self.active_check.setChecked(True)
        self.archived_check.setChecked(False)

        # Reset combos a primer item
        if self.category_combo.count() > 0:
            self.category_combo.setCurrentIndex(0)
        self.type_combo.setCurrentIndex(0)  # TEXT

        self.has_unsaved_changes = False

        self.blockSignals(False)
        logger.debug(f"Form cleared for tab {self.tab_id}")

    # === METODOS DE ESTILOS ===

    def style_input(self, widget):
        """Estilo para QLineEdit"""
        widget.setStyleSheet("""
            QLineEdit {
                background-color: #2D2D2D;
                border: 1px solid #3D3D3D;
                border-radius: 4px;
                padding: 8px 12px;
                color: #FFFFFF;
                font-size: 13px;
            }
            QLineEdit:focus {
                border: 1px solid #0078D4;
                background-color: #252525;
            }
            QLineEdit:hover {
                border: 1px solid #4D4D4D;
            }
        """)

    def style_text_edit(self, widget):
        """Estilo para QTextEdit"""
        widget.setStyleSheet("""
            QTextEdit {
                background-color: #2D2D2D;
                border: 1px solid #3D3D3D;
                border-radius: 4px;
                padding: 10px;
                color: #FFFFFF;
                font-size: 13px;
                line-height: 1.5;
            }
            QTextEdit:focus {
                border: 1px solid #0078D4;
                background-color: #252525;
            }
            QTextEdit:hover {
                border: 1px solid #4D4D4D;
            }
        """)

    def style_combo(self, widget):
        """Estilo para QComboBox"""
        widget.setStyleSheet("""
            QComboBox {
                background-color: #2D2D2D;
                border: 1px solid #3D3D3D;
                border-radius: 4px;
                padding: 8px 12px;
                color: #FFFFFF;
                font-size: 13px;
            }
            QComboBox:focus {
                border: 1px solid #0078D4;
            }
            QComboBox:hover {
                border: 1px solid #4D4D4D;
            }
            QComboBox::drop-down {
                border: none;
                width: 30px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid #B0B0B0;
                margin-right: 5px;
            }
            QComboBox QAbstractItemView {
                background-color: #2D2D2D;
                color: #FFFFFF;
                selection-background-color: #0078D4;
                selection-color: #FFFFFF;
                border: 1px solid #3D3D3D;
                outline: none;
            }
        """)

    def style_checkbox(self, widget):
        """Estilo para QCheckBox"""
        widget.setStyleSheet("""
            QCheckBox {
                color: #D0D0D0;
                font-size: 12px;
                spacing: 8px;
                padding: 5px;
            }
            QCheckBox::indicator {
                width: 20px;
                height: 20px;
                border: 2px solid #3D3D3D;
                border-radius: 4px;
                background-color: #2D2D2D;
            }
            QCheckBox::indicator:hover {
                border-color: #4D4D4D;
                background-color: #353535;
            }
            QCheckBox::indicator:checked {
                background-color: #0078D4;
                border-color: #0078D4;
                image: none;
            }
            QCheckBox::indicator:checked:after {
                content: "✓";
            }
        """)

    def style_button(self, widget, primary=False, secondary=False):
        """Estilo para QPushButton"""
        if primary:
            widget.setStyleSheet("""
                QPushButton {
                    background-color: #0078D4;
                    color: white;
                    border: none;
                    border-radius: 5px;
                    font-size: 13px;
                    font-weight: bold;
                    padding: 10px 20px;
                }
                QPushButton:hover {
                    background-color: #005A9E;
                }
                QPushButton:pressed {
                    background-color: #004578;
                }
                QPushButton:disabled {
                    background-color: #4D4D4D;
                    color: #888888;
                }
            """)
        elif secondary:
            widget.setStyleSheet("""
                QPushButton {
                    background-color: #3D3D3D;
                    color: #D0D0D0;
                    border: 1px solid #4D4D4D;
                    border-radius: 5px;
                    font-size: 13px;
                    padding: 10px 20px;
                }
                QPushButton:hover {
                    background-color: #4D4D4D;
                    color: #FFFFFF;
                    border-color: #5D5D5D;
                }
                QPushButton:pressed {
                    background-color: #353535;
                }
            """)
