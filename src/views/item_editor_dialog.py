"""
Item Editor Dialog
Dialog for creating and editing items
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QTextEdit, QComboBox, QPushButton, QFormLayout, QMessageBox, QCheckBox,
    QFrame, QScrollArea
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
import sys
from pathlib import Path
import re
import uuid
import logging

sys.path.insert(0, str(Path(__file__).parent.parent))
from models.item import Item, ItemType
from views.widgets.tag_group_selector import TagGroupSelector

# Get logger
logger = logging.getLogger(__name__)


class ResizableTextEdit(QTextEdit):
    """QTextEdit con resize grip en la esquina inferior derecha que permite redimensionar en altura"""

    def __init__(self, parent=None):
        super().__init__(parent)

        # Variables para el resize
        self.resizing = False
        self.resize_start_y = 0
        self.resize_start_height = 0
        self.resize_edge_height = 15  # Altura del área de resize en píxeles

        # Habilitar mouse tracking
        self.setMouseTracking(True)

    def is_on_bottom_edge(self, pos):
        """Check if mouse position is on the bottom edge for resizing"""
        return pos.y() >= self.height() - self.resize_edge_height

    def mousePressEvent(self, event):
        """Handle mouse press for resizing"""
        if event.button() == Qt.MouseButton.LeftButton:
            if self.is_on_bottom_edge(event.pos()):
                # Start resizing
                self.resizing = True
                self.resize_start_y = event.globalPosition().toPoint().y()
                self.resize_start_height = self.height()
                event.accept()
                return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        """Handle mouse move for resizing or cursor change"""
        if self.resizing:
            # Calculate new height
            current_y = event.globalPosition().toPoint().y()
            delta_y = current_y - self.resize_start_y
            new_height = self.resize_start_height + delta_y

            # Apply constraints
            new_height = max(120, min(new_height, 600))  # Min 120px, Max 600px

            # Resize usando setFixedHeight para forzar el tamaño exacto
            self.setFixedHeight(new_height)

            # Notificar al layout padre que el tamaño cambió
            self.updateGeometry()

            # Ajustar el tamaño del diálogo padre si es necesario
            if self.parent() and hasattr(self.parent(), 'adjustSize'):
                self.parent().adjustSize()

            event.accept()
        else:
            # Change cursor when hovering over bottom edge
            if self.is_on_bottom_edge(event.pos()):
                self.setCursor(Qt.CursorShape.SizeVerCursor)
            else:
                self.setCursor(Qt.CursorShape.IBeamCursor)
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        """Handle mouse release to end resizing"""
        if event.button() == Qt.MouseButton.LeftButton:
            if self.resizing:
                self.resizing = False
                event.accept()
                return
        super().mouseReleaseEvent(event)


class ItemEditorDialog(QDialog):
    """
    Dialog for creating or editing items
    Modal dialog with form fields for item properties
    """

    def __init__(self, item=None, category_id=None, controller=None, parent=None):
        """
        Initialize item editor dialog

        Args:
            item: Item to edit (None for new item)
            category_id: ID of the category to add item to (required for new items)
            controller: MainController instance (required for database operations)
            parent: Parent widget
        """
        super().__init__(parent)
        self.item = item
        self.category_id = category_id
        self.controller = controller
        self.is_edit_mode = item is not None

        self.init_ui()
        self.load_item_data()

    def init_ui(self):
        """Initialize the dialog UI"""
        # Window properties
        title = "Editar Item" if self.is_edit_mode else "Nuevo Item"
        self.setWindowTitle(title)

        # Hacer la ventana redimensionable
        self.setMinimumSize(550, 500)  # Tamaño mínimo
        self.resize(600, 570)  # Tamaño inicial

        self.setModal(True)

        # Apply dark theme
        self.setStyleSheet("""
            QDialog {
                background-color: #2b2b2b;
                color: #cccccc;
            }
            QLabel {
                color: #cccccc;
                font-size: 10pt;
            }
            QLineEdit, QTextEdit, QComboBox {
                background-color: #2d2d2d;
                color: #cccccc;
                border: 1px solid #3d3d3d;
                border-radius: 4px;
                padding: 5px;
            }
            QLineEdit:focus, QTextEdit:focus, QComboBox:focus {
                border: 1px solid #007acc;
            }
            QPushButton {
                background-color: #2d2d2d;
                color: #cccccc;
                border: 1px solid #3d3d3d;
                border-radius: 4px;
                padding: 8px 16px;
                font-size: 10pt;
            }
            QPushButton:hover {
                background-color: #3d3d3d;
                border: 1px solid #007acc;
            }
            QPushButton#save_button {
                background-color: #007acc;
                color: #ffffff;
                border: none;
            }
            QPushButton#save_button:hover {
                background-color: #005a9e;
            }
        """)

        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)

        # Form layout
        form_layout = QFormLayout()
        form_layout.setSpacing(10)

        # Label field (required)
        self.label_input = QLineEdit()
        self.label_input.setPlaceholderText("Nombre del item")
        form_layout.addRow("Label *:", self.label_input)

        # Type combobox
        self.type_combo = QComboBox()
        for item_type in ItemType:
            self.type_combo.addItem(item_type.value.upper(), item_type)
        form_layout.addRow("Tipo:", self.type_combo)

        # Content field (required, multiline) - con resize grip
        content_label = QLabel("Content *:")
        self.content_input = ResizableTextEdit()
        self.content_input.setPlaceholderText("Contenido a copiar al portapapeles")
        self.content_input.setMinimumHeight(120)
        form_layout.addRow(content_label, self.content_input)

        # Tags field (optional)
        self.tags_input = QLineEdit()
        self.tags_input.setPlaceholderText("tag1, tag2, tag3 (opcional)")
        form_layout.addRow("Tags:", self.tags_input)

        # Tag Group Selector (optional) - wrapped in scroll area
        if self.controller and hasattr(self.controller, 'config_manager'):
            try:
                db_path = str(self.controller.config_manager.db.db_path)
                self.tag_group_selector = TagGroupSelector(db_path, self)
                self.tag_group_selector.tags_changed.connect(self.on_tag_group_changed)

                # Create scroll area for tag group selector
                scroll_area = QScrollArea()
                scroll_area.setWidget(self.tag_group_selector)
                scroll_area.setWidgetResizable(True)
                scroll_area.setFixedHeight(120)  # Fixed height with scroll
                scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
                scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
                scroll_area.setStyleSheet("""
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

                form_layout.addRow("", scroll_area)
            except Exception as e:
                logger.warning(f"Could not initialize TagGroupSelector: {e}")
                self.tag_group_selector = None
        else:
            self.tag_group_selector = None

        # Add vertical spacer after tag section
        spacer_label = QLabel("")
        spacer_label.setFixedHeight(25)
        form_layout.addRow("", spacer_label)

        # Description field (optional)
        self.description_input = QLineEdit()
        self.description_input.setPlaceholderText("Descripción del item (opcional)")
        form_layout.addRow("Descripción:", self.description_input)

        # Working directory field (optional, only for CODE items)
        self.working_dir_label = QLabel("Directorio:")
        self.working_dir_input = QLineEdit()
        self.working_dir_input.setPlaceholderText("Ruta donde ejecutar (opcional, ej: C:\\Projects\\myapp)")
        self.working_dir_input.setToolTip(
            "Directorio de trabajo donde se ejecutará el comando.\n"
            "Si está vacío, se ejecuta en el directorio de la aplicación."
        )
        form_layout.addRow(self.working_dir_label, self.working_dir_input)

        # Initially hide working dir field (show only for CODE type)
        self.working_dir_label.hide()
        self.working_dir_input.hide()

        # Connect type change to show/hide working dir field
        self.type_combo.currentIndexChanged.connect(self.on_type_changed)

        # Sensitive checkbox
        self.sensitive_checkbox = QCheckBox("Marcar como sensible (cifrar contenido)")
        self.sensitive_checkbox.setStyleSheet("""
            QCheckBox {
                color: #cccccc;
                font-size: 10pt;
                spacing: 8px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border: 2px solid #3d3d3d;
                border-radius: 3px;
                background-color: #2d2d2d;
            }
            QCheckBox::indicator:hover {
                border: 2px solid #007acc;
            }
            QCheckBox::indicator:checked {
                background-color: #cc0000;
                border: 2px solid #cc0000;
                image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTIiIGhlaWdodD0iMTIiIHZpZXdCb3g9IjAgMCAxMiAxMiIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cGF0aCBkPSJNMTAuNSAzTDQuNSA5IDEuNSA2IiBzdHJva2U9IndoaXRlIiBzdHJva2Utd2lkdGg9IjIiIGZpbGw9Im5vbmUiIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIgc3Ryb2tlLWxpbmVqb2luPSJyb3VuZCIvPjwvc3ZnPg==);
            }
            QCheckBox::indicator:checked:hover {
                background-color: #9e0000;
                border: 2px solid #9e0000;
            }
        """)
        self.sensitive_checkbox.setToolTip(
            "Los items sensibles se cifran con AES-256 en la base de datos.\n"
            "El contenido será visible solo en esta aplicación."
        )
        form_layout.addRow("", self.sensitive_checkbox)

        # Active checkbox
        self.active_checkbox = QCheckBox("Item activo (puede ser usado)")
        self.active_checkbox.setChecked(True)  # Default: active
        self.active_checkbox.setStyleSheet("""
            QCheckBox {
                color: #cccccc;
                font-size: 10pt;
                spacing: 8px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border: 2px solid #3d3d3d;
                border-radius: 3px;
                background-color: #2d2d2d;
            }
            QCheckBox::indicator:hover {
                border: 2px solid #007acc;
            }
            QCheckBox::indicator:checked {
                background-color: #00cc00;
                border: 2px solid #00cc00;
                image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTIiIGhlaWdodD0iMTIiIHZpZXdCb3g9IjAgMCAxMiAxMiIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cGF0aCBkPSJNMTAuNSAzTDQuNSA5IDEuNSA2IiBzdHJva2U9IndoaXRlIiBzdHJva2Utd2lkdGg9IjIiIGZpbGw9Im5vbmUiIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIgc3Ryb2tlLWxpbmVqb2luPSJyb3VuZCIvPjwvc3ZnPg==);
            }
            QCheckBox::indicator:checked:hover {
                background-color: #009e00;
                border: 2px solid #009e00;
            }
        """)
        self.active_checkbox.setToolTip(
            "Items activos pueden ser usados normalmente.\n"
            "Items inactivos no pueden ser copiados al portapapeles."
        )
        form_layout.addRow("", self.active_checkbox)

        # Archived checkbox
        self.archived_checkbox = QCheckBox("Item archivado (ocultar de vista)")
        self.archived_checkbox.setChecked(False)  # Default: not archived
        self.archived_checkbox.setStyleSheet("""
            QCheckBox {
                color: #cccccc;
                font-size: 10pt;
                spacing: 8px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border: 2px solid #3d3d3d;
                border-radius: 3px;
                background-color: #2d2d2d;
            }
            QCheckBox::indicator:hover {
                border: 2px solid #007acc;
            }
            QCheckBox::indicator:checked {
                background-color: #cc8800;
                border: 2px solid #cc8800;
                image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTIiIGhlaWdodD0iMTIiIHZpZXdCb3g9IjAgMCAxMiAxMiIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cGF0aCBkPSJNMTAuNSAzTDQuNSA5IDEuNSA2IiBzdHJva2U9IndoaXRlIiBzdHJva2Utd2lkdGg9IjIiIGZpbGw9Im5vbmUiIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIgc3Ryb2tlLWxpbmVqb2luPSJyb3VuZCIvPjwvc3ZnPg==);
            }
            QCheckBox::indicator:checked:hover {
                background-color: #9e6600;
                border: 2px solid #9e6600;
            }
        """)
        self.archived_checkbox.setToolTip(
            "Items archivados no se muestran en la vista normal.\n"
            "Pueden ser accedidos desde la vista de archivados."
        )
        form_layout.addRow("", self.archived_checkbox)

        main_layout.addLayout(form_layout)

        # Required fields note
        note_label = QLabel("* Campos requeridos")
        note_label.setStyleSheet("color: #666666; font-size: 9pt;")
        main_layout.addWidget(note_label)

        # Spacer
        main_layout.addStretch()

        # Buttons layout
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(10)

        # Cancel button
        self.cancel_button = QPushButton("Cancelar")
        self.cancel_button.clicked.connect(self.reject)
        buttons_layout.addWidget(self.cancel_button)

        buttons_layout.addStretch()

        # Save button
        self.save_button = QPushButton("Guardar")
        self.save_button.setObjectName("save_button")
        self.save_button.clicked.connect(self.on_save)
        buttons_layout.addWidget(self.save_button)

        main_layout.addLayout(buttons_layout)

    def on_type_changed(self):
        """Handle type combo change - show/hide working dir field"""
        selected_type = self.type_combo.currentData()
        is_code = (selected_type == ItemType.CODE)

        self.working_dir_label.setVisible(is_code)
        self.working_dir_input.setVisible(is_code)

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

    def load_item_data(self):
        """Load existing item data if in edit mode"""
        if not self.is_edit_mode or not self.item:
            return

        # Load item data
        self.label_input.setText(self.item.label)
        self.content_input.setPlainText(self.item.content)

        # Set type combobox
        for i in range(self.type_combo.count()):
            if self.type_combo.itemData(i) == self.item.type:
                self.type_combo.setCurrentIndex(i)
                break

        # Load tags
        if self.item.tags:
            self.tags_input.setText(", ".join(self.item.tags))
            # También cargar en el tag group selector si existe
            if self.tag_group_selector:
                self.tag_group_selector.set_tags(self.item.tags)

        # Load description
        if hasattr(self.item, 'description') and self.item.description:
            self.description_input.setText(self.item.description)

        # Load working directory
        if hasattr(self.item, 'working_dir') and self.item.working_dir:
            self.working_dir_input.setText(self.item.working_dir)

        # Load sensitive state
        if hasattr(self.item, 'is_sensitive'):
            self.sensitive_checkbox.setChecked(self.item.is_sensitive)

        # Load active state
        if hasattr(self.item, 'is_active'):
            self.active_checkbox.setChecked(self.item.is_active)

        # Load archived state
        if hasattr(self.item, 'is_archived'):
            self.archived_checkbox.setChecked(self.item.is_archived)

        # Update visibility of working dir field
        self.on_type_changed()

    def validate(self) -> bool:
        """
        Validate form fields

        Returns:
            True if all fields are valid
        """
        # Check required fields
        label = self.label_input.text().strip()
        content = self.content_input.toPlainText().strip()

        if not label:
            QMessageBox.warning(
                self,
                "Campo requerido",
                "El campo 'Label' es requerido."
            )
            self.label_input.setFocus()
            return False

        if not content:
            QMessageBox.warning(
                self,
                "Campo requerido",
                "El campo 'Content' es requerido."
            )
            self.content_input.setFocus()
            return False

        # Validate URL if type is URL
        selected_type = self.type_combo.currentData()
        if selected_type == ItemType.URL:
            if not self.validate_url(content):
                QMessageBox.warning(
                    self,
                    "URL inválida",
                    "El contenido debe ser una URL válida (http:// o https://)."
                )
                self.content_input.setFocus()
                return False

        # Validate PATH if type is PATH
        if selected_type == ItemType.PATH:
            if not self.validate_path(content):
                # Show warning but allow to save anyway
                reply = QMessageBox.question(
                    self,
                    "Ruta no encontrada",
                    f"La ruta '{content}' no existe en el sistema.\n\n¿Deseas guardarla de todas formas?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No
                )
                if reply == QMessageBox.StandardButton.No:
                    self.content_input.setFocus()
                    return False

        return True

    def validate_url(self, url: str) -> bool:
        """
        Validate URL format

        Args:
            url: URL string to validate

        Returns:
            True if valid URL
        """
        # Simple URL validation
        url_pattern = re.compile(
            r'^https?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain
            r'localhost|'  # localhost
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # or IP
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)
        return url_pattern.match(url) is not None

    def validate_path(self, path_str: str) -> bool:
        """
        Validate if path exists

        Args:
            path_str: Path string to validate

        Returns:
            True if path exists
        """
        try:
            from pathlib import Path
            path = Path(path_str)
            return path.exists()
        except Exception:
            return False

    def get_item_data(self) -> dict:
        """
        Get item data from form fields

        Returns:
            Dictionary with item data
        """
        # Get tags list
        tags_text = self.tags_input.text().strip()
        tags = [tag.strip() for tag in tags_text.split(",") if tag.strip()] if tags_text else []

        # Get description
        description = self.description_input.text().strip() or None

        # Get working directory (only if CODE type)
        working_dir = None
        if self.type_combo.currentData() == ItemType.CODE:
            working_dir = self.working_dir_input.text().strip() or None

        return {
            "label": self.label_input.text().strip(),
            "content": self.content_input.toPlainText().strip(),
            "type": self.type_combo.currentData(),
            "tags": tags,
            "description": description,
            "is_sensitive": self.sensitive_checkbox.isChecked(),
            "working_dir": working_dir,
            "is_active": self.active_checkbox.isChecked(),
            "is_archived": self.archived_checkbox.isChecked()
        }

    def on_save(self):
        """Handle save button click - saves directly to database"""
        # Validate form data
        if not self.validate():
            return

        # Check if we have necessary dependencies
        if not self.controller:
            QMessageBox.critical(
                self,
                "Error",
                "No se puede guardar: falta el controlador de la aplicación."
            )
            return

        try:
            # Get item data from form
            item_data = self.get_item_data()

            if self.is_edit_mode:
                # UPDATE existing item
                if not self.item or not self.item.id:
                    QMessageBox.critical(
                        self,
                        "Error",
                        "No se puede actualizar: item inválido."
                    )
                    return

                logger.info(f"[ItemEditorDialog] Updating item: {self.item.id}")

                # Update item in database
                # Convert ItemType to uppercase string for database
                item_type_str = item_data["type"].value.upper() if isinstance(item_data["type"], ItemType) else str(item_data["type"]).upper()

                # update_item() returns None, so we catch exceptions instead
                self.controller.config_manager.db.update_item(
                    item_id=self.item.id,
                    label=item_data["label"],
                    content=item_data["content"],
                    item_type=item_type_str,
                    tags=item_data["tags"],
                    description=item_data.get("description"),
                    is_sensitive=item_data.get("is_sensitive", False),
                    working_dir=item_data.get("working_dir"),
                    is_active=item_data.get("is_active", True),
                    is_archived=item_data.get("is_archived", False)
                )

                # If no exception was raised, the update was successful
                logger.info(f"[ItemEditorDialog] Item updated successfully: {item_data['label']}")
                QMessageBox.information(
                    self,
                    "Éxito",
                    f"El item '{item_data['label']}' se actualizó correctamente."
                )
                # Invalidate filter cache
                if hasattr(self.controller, 'invalidate_filter_cache'):
                    self.controller.invalidate_filter_cache()
                self.accept()

            else:
                # ADD new item
                if not self.category_id:
                    QMessageBox.critical(
                        self,
                        "Error",
                        "No se puede crear: falta la categoría."
                    )
                    return

                logger.info(f"[ItemEditorDialog] Adding new item to category: {self.category_id}")

                # Add item to database
                # Convert ItemType to uppercase string for database
                item_type_str = item_data["type"].value.upper() if isinstance(item_data["type"], ItemType) else str(item_data["type"]).upper()

                item_id = self.controller.config_manager.db.add_item(
                    category_id=self.category_id,
                    label=item_data["label"],
                    content=item_data["content"],
                    item_type=item_type_str,
                    tags=item_data["tags"],
                    description=item_data.get("description"),
                    is_sensitive=item_data.get("is_sensitive", False),
                    working_dir=item_data.get("working_dir"),
                    is_active=item_data.get("is_active", True),
                    is_archived=item_data.get("is_archived", False)
                )

                if item_id:
                    logger.info(f"[ItemEditorDialog] Item added successfully with ID: {item_id}")
                    QMessageBox.information(
                        self,
                        "Éxito",
                        f"El item '{item_data['label']}' se guardó correctamente."
                    )
                    # Invalidate filter cache
                    if hasattr(self.controller, 'invalidate_filter_cache'):
                        self.controller.invalidate_filter_cache()
                    self.accept()
                else:
                    logger.error(f"[ItemEditorDialog] Failed to add item")
                    QMessageBox.critical(
                        self,
                        "Error",
                        "No se pudo guardar el item en la base de datos."
                    )

        except Exception as e:
            logger.error(f"[ItemEditorDialog] Error saving item: {e}", exc_info=True)
            QMessageBox.critical(
                self,
                "Error",
                f"Error al guardar el item:\n{str(e)}"
            )
