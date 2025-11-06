"""
Tag Group Selector Widget - Widget reutilizable para seleccionar tag groups
Se puede integrar en cualquier dialog de crear/editar items
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QCheckBox, QPushButton, QFrame, QLineEdit, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
import sys
from pathlib import Path
import logging

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from core.tag_groups_manager import TagGroupsManager

logger = logging.getLogger(__name__)


class TagGroupSelector(QWidget):
    """Widget para seleccionar y aplicar tag groups"""

    # Señal emitida cuando cambian los tags seleccionados
    tags_changed = pyqtSignal(list)  # list[str]

    def __init__(self, db_path: str, parent=None):
        super().__init__(parent)
        self.db_path = db_path
        self.manager = TagGroupsManager(self.db_path)
        self.current_tags = []
        self.tag_checkboxes = []
        self.init_ui()
        self.load_groups()

    def init_ui(self):
        """Inicializar UI"""
        self.setStyleSheet("""
            QWidget {
                background-color: transparent;
            }
            QLabel {
                color: #cccccc;
            }
            QComboBox {
                background-color: #3c3c3c;
                border: 1px solid #5a5a5a;
                border-radius: 4px;
                padding: 3px 6px;
                color: #cccccc;
                min-height: 20px;
                font-size: 9pt;
            }
            QComboBox:hover {
                border-color: #007acc;
            }
            QComboBox::drop-down {
                border: none;
                padding-right: 8px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid #cccccc;
                margin-right: 5px;
            }
            QComboBox QAbstractItemView {
                background-color: #2d2d30;
                border: 1px solid #007acc;
                selection-background-color: #007acc;
                color: #cccccc;
            }
            QCheckBox {
                color: #cccccc;
                spacing: 4px;
                font-size: 9pt;
            }
            QCheckBox::indicator {
                width: 14px;
                height: 14px;
                border: 1px solid #5a5a5a;
                border-radius: 3px;
                background-color: #3c3c3c;
            }
            QCheckBox::indicator:hover {
                border-color: #007acc;
            }
            QCheckBox::indicator:checked {
                background-color: #007acc;
                border-color: #007acc;
            }
            QCheckBox::indicator:checked:hover {
                background-color: #005a9e;
            }
            QLineEdit {
                background-color: #3c3c3c;
                border: 1px solid #5a5a5a;
                border-radius: 4px;
                padding: 3px 6px;
                color: #cccccc;
                font-size: 9pt;
            }
            QLineEdit:focus {
                border-color: #007acc;
            }
            QPushButton {
                background-color: #3c3c3c;
                color: #cccccc;
                border: 1px solid #5a5a5a;
                border-radius: 4px;
                padding: 3px 8px;
                font-size: 8pt;
            }
            QPushButton:hover {
                background-color: #505050;
                border-color: #007acc;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        # Container con borde para visualizar mejor
        container = QFrame()
        container.setFrameShape(QFrame.Shape.StyledPanel)
        container.setStyleSheet("""
            QFrame {
                background-color: #252526;
                border: 1px solid #3e3e42;
                border-radius: 6px;
                padding: 6px;
            }
        """)
        container_layout = QVBoxLayout(container)
        container_layout.setSpacing(6)

        # Header
        header_layout = QHBoxLayout()
        header_icon = QLabel("🏷️")
        header_icon.setStyleSheet("font-size: 12pt;")
        header_layout.addWidget(header_icon)

        header_label = QLabel("Plantillas de Tags")
        header_font = QFont()
        header_font.setPointSize(9)
        header_font.setBold(True)
        header_label.setFont(header_font)
        header_layout.addWidget(header_label)

        header_layout.addStretch()

        # Botón para gestionar tag groups
        manage_btn = QPushButton("⚙️ Gestionar")
        manage_btn.setToolTip("Abrir gestor de Tag Groups")
        manage_btn.clicked.connect(self.open_tag_groups_manager)
        header_layout.addWidget(manage_btn)

        container_layout.addLayout(header_layout)

        # Selector de tag group
        selector_layout = QHBoxLayout()
        selector_label = QLabel("💡 Usar plantilla:")
        selector_label.setStyleSheet("font-size: 9pt;")
        selector_layout.addWidget(selector_label)

        self.group_combo = QComboBox()
        self.group_combo.currentIndexChanged.connect(self.on_group_selected)
        selector_layout.addWidget(self.group_combo, 1)

        container_layout.addLayout(selector_layout)

        # Área de checkboxes para tags del grupo
        self.tags_area = QWidget()
        self.tags_layout = QVBoxLayout(self.tags_area)
        self.tags_layout.setSpacing(4)
        self.tags_layout.setContentsMargins(5, 2, 5, 2)
        container_layout.addWidget(self.tags_area)

        self.tags_area.hide()  # Ocultar inicialmente

        # Separador
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setStyleSheet("background-color: #3e3e42; max-height: 1px;")
        container_layout.addWidget(separator)

        # Tags adicionales (custom)
        additional_label = QLabel("Tags adicionales (opcionales):")
        additional_label.setStyleSheet("font-weight: bold; font-size: 8pt;")
        container_layout.addWidget(additional_label)

        self.additional_tags_input = QLineEdit()
        self.additional_tags_input.setPlaceholderText("Agrega más tags separados por comas...")
        self.additional_tags_input.textChanged.connect(self.on_additional_tags_changed)
        container_layout.addWidget(self.additional_tags_input)

        # Vista previa de tags finales
        preview_label = QLabel("Tags finales:")
        preview_label.setStyleSheet("font-weight: bold; font-size: 8pt; margin-top: 2px;")
        container_layout.addWidget(preview_label)

        self.preview_label = QLabel("(Ningún tag seleccionado)")
        self.preview_label.setStyleSheet("""
            color: #808080;
            font-size: 8pt;
            padding: 4px;
            background-color: #1e1e1e;
            border-radius: 4px;
            font-style: italic;
        """)
        self.preview_label.setWordWrap(True)
        container_layout.addWidget(self.preview_label)

        layout.addWidget(container)

    def load_groups(self):
        """Cargar tag groups disponibles"""
        try:
            self.group_combo.clear()
            self.group_combo.addItem("-- Selecciona una plantilla --", None)

            groups = self.manager.get_all_groups(active_only=True)
            for group in groups:
                icon = group.get('icon', '🏷️')
                name = group['name']
                self.group_combo.addItem(f"{icon} {name}", group['id'])

            logger.debug(f"Loaded {len(groups)} tag groups")

        except Exception as e:
            logger.error(f"Error loading tag groups: {e}", exc_info=True)

    def on_group_selected(self, index: int):
        """Manejar selección de tag group"""
        try:
            group_id = self.group_combo.itemData(index)

            # Limpiar checkboxes anteriores
            self.clear_tag_checkboxes()

            if group_id is None:
                # No se seleccionó grupo
                self.tags_area.hide()
                self.update_current_tags()
                return

            # Obtener tags del grupo
            group = self.manager.get_group(group_id)
            if not group:
                return

            tags_list = self.manager.get_tags_as_list(group_id)

            if not tags_list:
                return

            # Mostrar área de tags
            self.tags_area.show()

            # Crear checkboxes para cada tag
            instructions = QLabel("Selecciona los tags que necesites:")
            instructions.setStyleSheet("font-size: 8pt; color: #a0a0a0; margin-bottom: 2px;")
            self.tags_layout.addWidget(instructions)

            # Crear grid layout para mejor distribución
            from PyQt6.QtWidgets import QGridLayout
            grid_widget = QWidget()
            grid_layout = QGridLayout(grid_widget)
            grid_layout.setSpacing(4)
            grid_layout.setContentsMargins(0, 0, 0, 0)

            for idx, tag in enumerate(tags_list):
                checkbox = QCheckBox(f"🏷️ {tag}")
                checkbox.setChecked(True)  # Por defecto todos seleccionados
                checkbox.stateChanged.connect(self.on_tag_checkbox_changed)
                checkbox.setProperty("tag_name", tag)

                row = idx // 3  # 3 columnas
                col = idx % 3
                grid_layout.addWidget(checkbox, row, col)

                self.tag_checkboxes.append(checkbox)

            self.tags_layout.addWidget(grid_widget)

            # Actualizar tags actuales
            self.update_current_tags()

        except Exception as e:
            logger.error(f"Error on group selected: {e}", exc_info=True)

    def clear_tag_checkboxes(self):
        """Limpiar checkboxes de tags"""
        while self.tags_layout.count():
            child = self.tags_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        self.tag_checkboxes.clear()

    def on_tag_checkbox_changed(self):
        """Manejar cambio en checkboxes de tags"""
        self.update_current_tags()

    def on_additional_tags_changed(self):
        """Manejar cambio en tags adicionales"""
        self.update_current_tags()

    def update_current_tags(self):
        """Actualizar lista de tags actuales y emitir señal"""
        tags = []

        # Tags del grupo (seleccionados)
        for checkbox in self.tag_checkboxes:
            if checkbox.isChecked():
                tag_name = checkbox.property("tag_name")
                if tag_name:
                    tags.append(tag_name)

        # Tags adicionales
        additional_text = self.additional_tags_input.text().strip()
        if additional_text:
            additional_tags = [tag.strip() for tag in additional_text.split(',') if tag.strip()]
            tags.extend(additional_tags)

        # Eliminar duplicados manteniendo el orden
        seen = set()
        unique_tags = []
        for tag in tags:
            if tag.lower() not in seen:
                seen.add(tag.lower())
                unique_tags.append(tag)

        self.current_tags = unique_tags

        # Actualizar preview
        self.update_preview()

        # Emitir señal
        self.tags_changed.emit(self.current_tags)

    def update_preview(self):
        """Actualizar vista previa de tags"""
        if not self.current_tags:
            self.preview_label.setText("(Ningún tag seleccionado)")
            self.preview_label.setStyleSheet("""
                color: #808080;
                font-size: 8pt;
                padding: 4px;
                background-color: #1e1e1e;
                border-radius: 4px;
                font-style: italic;
            """)
        else:
            # Crear texto con chips
            chips = [f"🏷️ {tag}" for tag in self.current_tags]
            preview_text = "  ".join(chips)

            self.preview_label.setText(preview_text)
            self.preview_label.setStyleSheet("""
                color: #cccccc;
                font-size: 8pt;
                padding: 4px;
                background-color: #1e1e1e;
                border: 1px solid #007acc;
                border-radius: 4px;
            """)

    def get_selected_tags(self) -> list:
        """Obtener lista de tags seleccionados"""
        return self.current_tags.copy()

    def set_tags(self, tags: list):
        """Establecer tags externamente (útil al editar items)"""
        if not tags:
            return

        # Poner los tags en el campo de tags adicionales
        self.additional_tags_input.setText(", ".join(tags))

    def open_tag_groups_manager(self):
        """Abrir el diálogo de gestión de Tag Groups"""
        try:
            from views.dialogs.tag_groups_dialog import TagGroupsDialog

            dialog = TagGroupsDialog(self)
            if dialog.exec():
                # Recargar grupos después de gestionar
                self.load_groups()

        except Exception as e:
            logger.error(f"Error opening tag groups manager: {e}", exc_info=True)
            QMessageBox.warning(
                self,
                "Error",
                "No se pudo abrir el gestor de Tag Groups"
            )


if __name__ == "__main__":
    """Test del widget"""
    from PyQt6.QtWidgets import QApplication, QMainWindow
    import sys

    app = QApplication(sys.argv)

    # Configurar logging
    logging.basicConfig(level=logging.DEBUG)

    # Crear ventana de test
    window = QMainWindow()
    window.setWindowTitle("Test Tag Group Selector")
    window.setMinimumSize(600, 500)

    db_path = Path(__file__).parent.parent.parent.parent / "widget_sidebar.db"
    selector = TagGroupSelector(str(db_path))

    # Conectar señal para ver cambios
    def on_tags_changed(tags):
        print(f"Tags changed: {tags}")

    selector.tags_changed.connect(on_tags_changed)

    window.setCentralWidget(selector)
    window.show()

    sys.exit(app.exec())
