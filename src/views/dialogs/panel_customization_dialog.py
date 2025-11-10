"""
Panel Customization Dialog - Permite editar nombre, color y shortcut de un panel
"""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QColorDialog, QComboBox, QGroupBox, QMessageBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QColor
import logging

logger = logging.getLogger(__name__)


class PanelCustomizationDialog(QDialog):
    """Diálogo para personalizar un panel anclado"""

    def __init__(self, panel, panels_manager, config_manager, parent=None):
        super().__init__(parent)

        self.panel = panel
        self.panels_manager = panels_manager
        self.config_manager = config_manager

        self.selected_color = panel.get('custom_color', '#00aaff')

        self.init_ui()
        self.load_current_values()

    def init_ui(self):
        """Inicializar UI"""
        self.setWindowTitle("Personalizar Panel")
        self.setModal(True)
        self.setMinimumWidth(400)

        layout = QVBoxLayout(self)

        # Título
        title = QLabel("Personalizar Panel Anclado")
        title.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        layout.addWidget(title)

        # Grupo: Nombre
        name_group = QGroupBox("Nombre del Panel")
        name_layout = QVBoxLayout(name_group)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Nombre personalizado (opcional)")
        name_layout.addWidget(self.name_input)

        help_label = QLabel("Si se deja vacio, se usara el nombre de la categoria")
        help_label.setStyleSheet("color: #888; font-size: 10px;")
        name_layout.addWidget(help_label)

        layout.addWidget(name_group)

        # Grupo: Color
        color_group = QGroupBox("Color del Header")
        color_layout = QHBoxLayout(color_group)

        self.color_preview = QPushButton()
        self.color_preview.setFixedSize(100, 40)
        self.update_color_preview()
        color_layout.addWidget(self.color_preview)

        choose_color_btn = QPushButton("Elegir Color...")
        choose_color_btn.clicked.connect(self.choose_color)
        color_layout.addWidget(choose_color_btn)

        reset_color_btn = QPushButton("Restablecer")
        reset_color_btn.clicked.connect(self.reset_color)
        color_layout.addWidget(reset_color_btn)

        layout.addWidget(color_group)

        # Grupo: Shortcut
        shortcut_group = QGroupBox("Atajo de Teclado")
        shortcut_layout = QVBoxLayout(shortcut_group)

        self.shortcut_combo = QComboBox()
        self.populate_shortcuts()
        shortcut_layout.addWidget(self.shortcut_combo)

        layout.addWidget(shortcut_group)

        # Botones
        buttons_layout = QHBoxLayout()

        save_btn = QPushButton("Guardar")
        save_btn.clicked.connect(self.accept)
        buttons_layout.addWidget(save_btn)

        cancel_btn = QPushButton("Cancelar")
        cancel_btn.clicked.connect(self.reject)
        buttons_layout.addWidget(cancel_btn)

        layout.addLayout(buttons_layout)

        self.apply_styles()

    def load_current_values(self):
        """Cargar valores actuales del panel"""
        # Nombre
        current_name = self.panel.get('custom_name', '')
        self.name_input.setText(current_name)

        # Color
        self.selected_color = self.panel.get('custom_color', '#00aaff')
        self.update_color_preview()

        # Shortcut
        current_shortcut = self.panel.get('keyboard_shortcut', '')
        if current_shortcut:
            index = self.shortcut_combo.findData(current_shortcut)
            if index >= 0:
                self.shortcut_combo.setCurrentIndex(index)

    def populate_shortcuts(self):
        """Poblar combo box con shortcuts disponibles"""
        # Obtener shortcuts ya usados
        all_panels = self.panels_manager.get_all_panels()
        used_shortcuts = {p.get('keyboard_shortcut') for p in all_panels if p.get('keyboard_shortcut')}

        # Shortcut actual del panel
        current_shortcut = self.panel.get('keyboard_shortcut')

        # Agregar opciones
        self.shortcut_combo.addItem("Sin atajo", None)

        for i in range(1, 10):
            shortcut = f"Ctrl+Shift+{i}"

            if shortcut == current_shortcut:
                # El shortcut actual siempre está disponible
                self.shortcut_combo.addItem(f"{shortcut} (actual)", shortcut)
            elif shortcut in used_shortcuts:
                # Shortcut usado por otro panel
                self.shortcut_combo.addItem(f"{shortcut} (en uso)", shortcut)
                self.shortcut_combo.model().item(self.shortcut_combo.count() - 1).setEnabled(False)
            else:
                # Shortcut disponible
                self.shortcut_combo.addItem(shortcut, shortcut)

    def choose_color(self):
        """Abrir diálogo de selección de color"""
        current_color = QColor(self.selected_color)
        color = QColorDialog.getColor(current_color, self, "Elegir Color del Header")

        if color.isValid():
            self.selected_color = color.name()
            self.update_color_preview()

    def reset_color(self):
        """Restablecer color por defecto"""
        self.selected_color = '#00aaff'
        self.update_color_preview()

    def update_color_preview(self):
        """Actualizar preview del color"""
        self.color_preview.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.selected_color};
                border: 2px solid #3d3d3d;
                border-radius: 5px;
            }}
        """)

    def get_customization_data(self) -> dict:
        """Obtener datos de personalización"""
        return {
            'custom_name': self.name_input.text().strip() or None,
            'custom_color': self.selected_color,
            'keyboard_shortcut': self.shortcut_combo.currentData()
        }

    def validate_inputs(self) -> bool:
        """Validar entradas"""
        # Por ahora, todo es válido (nombre y shortcut son opcionales)
        return True

    def accept(self):
        """Aceptar cambios"""
        if not self.validate_inputs():
            return

        super().accept()

    def apply_styles(self):
        """Aplicar estilos"""
        self.setStyleSheet("""
            QDialog {
                background-color: #1e1e1e;
                color: #e0e0e0;
            }

            QGroupBox {
                border: 1px solid #3d3d3d;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
                font-weight: bold;
            }

            QLineEdit, QComboBox {
                background-color: #2d2d2d;
                border: 1px solid #3d3d3d;
                border-radius: 3px;
                padding: 5px;
                color: #e0e0e0;
            }

            QPushButton {
                background-color: #2d2d2d;
                border: 1px solid #3d3d3d;
                border-radius: 3px;
                padding: 5px 10px;
            }

            QPushButton:hover {
                background-color: #3d3d3d;
                border: 1px solid #00aaff;
            }
        """)
