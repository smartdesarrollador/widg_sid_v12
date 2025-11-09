"""
Ventana flotante para filtros avanzados de categorías

Esta ventana permite aplicar múltiples filtros a las categorías del sidebar,
incluyendo filtros por estado, popularidad, fechas y atributos.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QCheckBox, QSpinBox, QLineEdit, QGroupBox, QScrollArea,
    QFrame, QComboBox, QDateEdit
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QSettings, QDate
from PyQt6.QtGui import QFont
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class CategoryFilterWindow(QWidget):
    """
    Ventana flotante para filtros avanzados de categorías

    Señales:
        filters_changed: Emitida cuando se aplican filtros (dict con filtros activos)
        filters_cleared: Emitida cuando se limpian todos los filtros
        window_closed: Emitida cuando se cierra la ventana
    """

    filters_changed = pyqtSignal(dict)
    filters_cleared = pyqtSignal()
    window_closed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Filtro de Categorías")
        self.setWindowFlags(
            Qt.WindowType.Window |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.FramelessWindowHint
        )

        # Tamaño fijo (ampliado para filtros avanzados)
        self.setFixedSize(450, 700)

        # QSettings para persistencia
        self.settings = QSettings("WidgetSidebar", "CategoryFilters")

        # Debouncing para evitar aplicar filtros muy seguido
        self.apply_timer = QTimer()
        self.apply_timer.setSingleShot(True)
        self.apply_timer.setInterval(300)  # 300ms
        self.apply_timer.timeout.connect(self._emit_filters)

        # Para arrastrar la ventana
        self.dragging = False
        self.drag_position = None

        self._init_ui()

        # NO cargar filtros guardados al iniciar - empezar sin filtros por defecto
        # self.load_filters()

    def _init_ui(self):
        """Inicializar interfaz de usuario"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # === BARRA DE TÍTULO ===
        self._create_title_bar(main_layout)

        # === ÁREA DE SCROLL ===
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)

        # Widget contenedor para scroll
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        scroll_layout.setContentsMargins(15, 15, 15, 15)
        scroll_layout.setSpacing(12)

        # === SECCIONES DE FILTROS ===
        # Búsqueda primero (arriba)
        self._create_search_section(scroll_layout)

        # Ordenamiento justo después de búsqueda
        self._create_ordering_section(scroll_layout)

        # Luego los demás filtros
        self._create_status_section(scroll_layout)
        self._create_type_section(scroll_layout)
        self._create_pinned_section(scroll_layout)
        self._create_popularity_section(scroll_layout)

        # Filtros Avanzados restantes
        self._create_visual_attributes_section(scroll_layout)
        self._create_dates_section(scroll_layout)

        # Spacer
        scroll_layout.addStretch()

        scroll_area.setWidget(scroll_widget)
        main_layout.addWidget(scroll_area)

        # === BOTONES DE ACCIÓN ===
        self._create_action_buttons(main_layout)

        # Estilo general
        self._apply_styles()

    def _create_title_bar(self, parent_layout):
        """Crear barra de título personalizada"""
        title_bar = QWidget()
        title_bar.setFixedHeight(45)
        title_bar.setStyleSheet("""
            QWidget {
                background-color: #667eea;
            }
        """)

        title_layout = QHBoxLayout(title_bar)
        title_layout.setContentsMargins(15, 0, 10, 0)

        # Icono y título
        icon_label = QLabel("🔍")
        icon_label.setFont(QFont("Segoe UI", 16))

        title_label = QLabel("Filtro de Categorías")
        title_label.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        title_label.setStyleSheet("color: white;")

        title_layout.addWidget(icon_label)
        title_layout.addWidget(title_label)
        title_layout.addStretch()

        # Botón cerrar
        close_button = QPushButton("✕")
        close_button.setFixedSize(30, 30)
        close_button.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: white;
                border: none;
                font-size: 18px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: rgba(255, 255, 255, 0.2);
                border-radius: 15px;
            }
        """)
        close_button.clicked.connect(self.close)

        title_layout.addWidget(close_button)

        parent_layout.addWidget(title_bar)

    def _create_status_section(self, parent_layout):
        """Crear sección de filtros de estado"""
        group = QGroupBox("Estado")
        group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #e0e0e0;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)

        layout = QVBoxLayout()
        layout.setSpacing(8)

        # Checkboxes de estado
        self.active_checkbox = QCheckBox("Solo Activas")
        self.inactive_checkbox = QCheckBox("Solo Inactivas")

        layout.addWidget(self.active_checkbox)
        layout.addWidget(self.inactive_checkbox)

        # Conectar para que sean mutuamente excluyentes
        self.active_checkbox.toggled.connect(
            lambda checked: self.inactive_checkbox.setChecked(False) if checked else None
        )
        self.inactive_checkbox.toggled.connect(
            lambda checked: self.active_checkbox.setChecked(False) if checked else None
        )

        # Conectar a debouncing
        self.active_checkbox.toggled.connect(self._schedule_apply_filters)
        self.inactive_checkbox.toggled.connect(self._schedule_apply_filters)

        group.setLayout(layout)
        parent_layout.addWidget(group)

    def _create_type_section(self, parent_layout):
        """Crear sección de filtros de tipo"""
        group = QGroupBox("Tipo")
        group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #e0e0e0;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)

        layout = QVBoxLayout()
        layout.setSpacing(8)

        # Checkboxes de tipo
        self.predefined_checkbox = QCheckBox("Solo Predefinidas")
        self.custom_checkbox = QCheckBox("Solo Personalizadas")

        layout.addWidget(self.predefined_checkbox)
        layout.addWidget(self.custom_checkbox)

        # Conectar para que sean mutuamente excluyentes
        self.predefined_checkbox.toggled.connect(
            lambda checked: self.custom_checkbox.setChecked(False) if checked else None
        )
        self.custom_checkbox.toggled.connect(
            lambda checked: self.predefined_checkbox.setChecked(False) if checked else None
        )

        # Conectar a debouncing
        self.predefined_checkbox.toggled.connect(self._schedule_apply_filters)
        self.custom_checkbox.toggled.connect(self._schedule_apply_filters)

        group.setLayout(layout)
        parent_layout.addWidget(group)

    def _create_pinned_section(self, parent_layout):
        """Crear sección de filtros de anclado"""
        group = QGroupBox("Anclado")
        group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #e0e0e0;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)

        layout = QVBoxLayout()
        layout.setSpacing(8)

        # Checkboxes de anclado
        self.pinned_checkbox = QCheckBox("Solo Ancladas")
        self.pinned_first_checkbox = QCheckBox("Ancladas Primero (al ordenar)")

        layout.addWidget(self.pinned_checkbox)
        layout.addWidget(self.pinned_first_checkbox)

        # Conectar a debouncing
        self.pinned_checkbox.toggled.connect(self._schedule_apply_filters)
        self.pinned_first_checkbox.toggled.connect(self._schedule_apply_filters)

        group.setLayout(layout)
        parent_layout.addWidget(group)

    def _create_popularity_section(self, parent_layout):
        """Crear sección de filtros de popularidad"""
        group = QGroupBox("Popularidad")
        group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #e0e0e0;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)

        layout = QVBoxLayout()
        layout.setSpacing(10)

        # === Cantidad de Items ===
        item_count_layout = QVBoxLayout()
        item_count_layout.setSpacing(5)

        item_count_label = QLabel("Cantidad de Items:")
        item_count_label.setStyleSheet("font-weight: normal;")

        item_count_inputs = QHBoxLayout()

        self.item_count_min = QSpinBox()
        self.item_count_min.setMinimum(0)
        self.item_count_min.setMaximum(1000)
        self.item_count_min.setPrefix("Min: ")
        self.item_count_min.setFixedWidth(100)

        self.item_count_max = QSpinBox()
        self.item_count_max.setMinimum(0)
        self.item_count_max.setMaximum(1000)
        self.item_count_max.setValue(1000)
        self.item_count_max.setPrefix("Max: ")
        self.item_count_max.setFixedWidth(100)

        item_count_inputs.addWidget(self.item_count_min)
        item_count_inputs.addWidget(self.item_count_max)
        item_count_inputs.addStretch()

        item_count_layout.addWidget(item_count_label)
        item_count_layout.addLayout(item_count_inputs)

        # === Total de Usos ===
        total_uses_layout = QVBoxLayout()
        total_uses_layout.setSpacing(5)

        total_uses_label = QLabel("Total de Usos:")
        total_uses_label.setStyleSheet("font-weight: normal;")

        total_uses_inputs = QHBoxLayout()

        self.total_uses_min = QSpinBox()
        self.total_uses_min.setMinimum(0)
        self.total_uses_min.setMaximum(10000)
        self.total_uses_min.setPrefix("Min: ")
        self.total_uses_min.setFixedWidth(100)

        self.total_uses_max = QSpinBox()
        self.total_uses_max.setMinimum(0)
        self.total_uses_max.setMaximum(10000)
        self.total_uses_max.setValue(10000)
        self.total_uses_max.setPrefix("Max: ")
        self.total_uses_max.setFixedWidth(100)

        total_uses_inputs.addWidget(self.total_uses_min)
        total_uses_inputs.addWidget(self.total_uses_max)
        total_uses_inputs.addStretch()

        total_uses_layout.addWidget(total_uses_label)
        total_uses_layout.addLayout(total_uses_inputs)

        layout.addLayout(item_count_layout)
        layout.addLayout(total_uses_layout)

        # Conectar a debouncing
        self.item_count_min.valueChanged.connect(self._schedule_apply_filters)
        self.item_count_max.valueChanged.connect(self._schedule_apply_filters)
        self.total_uses_min.valueChanged.connect(self._schedule_apply_filters)
        self.total_uses_max.valueChanged.connect(self._schedule_apply_filters)

        group.setLayout(layout)
        parent_layout.addWidget(group)

    def _create_search_section(self, parent_layout):
        """Crear sección de búsqueda"""
        group = QGroupBox("Búsqueda")
        group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #e0e0e0;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)

        layout = QVBoxLayout()
        layout.setSpacing(8)

        search_label = QLabel("Buscar por nombre:")
        search_label.setStyleSheet("font-weight: normal;")

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Escribe para buscar...")
        self.search_input.setClearButtonEnabled(True)

        layout.addWidget(search_label)
        layout.addWidget(self.search_input)

        # Conectar a debouncing
        self.search_input.textChanged.connect(self._schedule_apply_filters)

        group.setLayout(layout)
        parent_layout.addWidget(group)

    def _create_ordering_section(self, parent_layout):
        """Crear sección de ordenamiento avanzado"""
        group = QGroupBox("Ordenamiento")
        group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #e0e0e0;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)

        layout = QVBoxLayout()
        layout.setSpacing(8)

        # Ordenar por
        order_by_label = QLabel("Ordenar por:")
        order_by_label.setStyleSheet("font-weight: normal;")

        self.order_by_combo = QComboBox()
        self.order_by_combo.addItem("Orden predefinido", "order_index")
        self.order_by_combo.addItem("Nombre", "name")
        self.order_by_combo.addItem("Cantidad de items", "item_count")
        self.order_by_combo.addItem("Usos totales", "total_uses")
        self.order_by_combo.addItem("Veces accedida", "access_count")
        self.order_by_combo.addItem("Última vez accedida", "last_accessed")
        self.order_by_combo.addItem("Fecha de creación", "created_at")
        self.order_by_combo.addItem("Última modificación", "updated_at")

        # Dirección
        direction_label = QLabel("Dirección:")
        direction_label.setStyleSheet("font-weight: normal;")

        self.order_direction_combo = QComboBox()
        self.order_direction_combo.addItem("Ascendente", "ASC")
        self.order_direction_combo.addItem("Descendente", "DESC")

        layout.addWidget(order_by_label)
        layout.addWidget(self.order_by_combo)
        layout.addWidget(direction_label)
        layout.addWidget(self.order_direction_combo)

        # Conectar a debouncing
        self.order_by_combo.currentIndexChanged.connect(self._schedule_apply_filters)
        self.order_direction_combo.currentIndexChanged.connect(self._schedule_apply_filters)

        group.setLayout(layout)
        parent_layout.addWidget(group)

    def _create_visual_attributes_section(self, parent_layout):
        """Crear sección de atributos visuales (Color/Badge)"""
        group = QGroupBox("Atributos Visuales")
        group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #e0e0e0;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)

        layout = QVBoxLayout()
        layout.setSpacing(8)

        # Color
        self.has_color_checkbox = QCheckBox("Solo con color personalizado")
        self.has_color_checkbox.setStyleSheet("font-weight: normal;")

        # Badge
        self.has_badge_checkbox = QCheckBox("Solo con badge/etiqueta")
        self.has_badge_checkbox.setStyleSheet("font-weight: normal;")

        layout.addWidget(self.has_color_checkbox)
        layout.addWidget(self.has_badge_checkbox)

        # Conectar a debouncing
        self.has_color_checkbox.stateChanged.connect(self._schedule_apply_filters)
        self.has_badge_checkbox.stateChanged.connect(self._schedule_apply_filters)

        group.setLayout(layout)
        parent_layout.addWidget(group)

    def _create_dates_section(self, parent_layout):
        """Crear sección de filtros de fechas"""
        group = QGroupBox("Filtros de Fechas")
        group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #e0e0e0;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)

        layout = QVBoxLayout()
        layout.setSpacing(8)

        # Última vez accedida
        accessed_label = QLabel("Última vez accedida:")
        accessed_label.setStyleSheet("font-weight: normal;")

        accessed_layout = QHBoxLayout()

        self.accessed_after_date = QDateEdit()
        self.accessed_after_date.setCalendarPopup(True)
        self.accessed_after_date.setSpecialValueText("No especificado")
        self.accessed_after_date.setDate(self.accessed_after_date.date().addDays(-30))  # Default: hace 30 días
        self.accessed_after_date.setEnabled(False)

        self.accessed_after_checkbox = QCheckBox("Desde:")
        self.accessed_after_checkbox.setStyleSheet("font-weight: normal;")
        self.accessed_after_checkbox.stateChanged.connect(
            lambda state: self.accessed_after_date.setEnabled(state == 2)
        )

        accessed_layout.addWidget(self.accessed_after_checkbox)
        accessed_layout.addWidget(self.accessed_after_date)

        # Nunca accedida
        self.never_accessed_checkbox = QCheckBox("Nunca accedida")
        self.never_accessed_checkbox.setStyleSheet("font-weight: normal;")

        layout.addWidget(accessed_label)
        layout.addLayout(accessed_layout)
        layout.addWidget(self.never_accessed_checkbox)

        # Conectar a debouncing
        self.accessed_after_checkbox.stateChanged.connect(self._schedule_apply_filters)
        self.accessed_after_date.dateChanged.connect(self._schedule_apply_filters)
        self.never_accessed_checkbox.stateChanged.connect(self._schedule_apply_filters)

        group.setLayout(layout)
        parent_layout.addWidget(group)

    def _create_action_buttons(self, parent_layout):
        """Crear botones de acción (Aplicar y Limpiar)"""
        button_widget = QWidget()
        button_widget.setFixedHeight(60)
        button_widget.setStyleSheet("background: #f5f5f5;")

        button_layout = QHBoxLayout(button_widget)
        button_layout.setContentsMargins(15, 10, 15, 10)

        # Botón Limpiar
        clear_button = QPushButton("Limpiar Todo")
        clear_button.setFixedHeight(35)
        clear_button.setStyleSheet("""
            QPushButton {
                background: #95a5a6;
                color: white;
                border: none;
                border-radius: 6px;
                font-weight: bold;
                padding: 8px 20px;
            }
            QPushButton:hover {
                background: #7f8c8d;
            }
            QPushButton:pressed {
                background: #6c7a7b;
            }
        """)
        clear_button.clicked.connect(self.clear_filters)

        # Botón Aplicar
        apply_button = QPushButton("Aplicar Filtros")
        apply_button.setFixedHeight(35)
        apply_button.setStyleSheet("""
            QPushButton {
                background-color: #667eea;
                color: white;
                border: none;
                border-radius: 6px;
                font-weight: bold;
                padding: 8px 20px;
            }
            QPushButton:hover {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #5568d3,
                    stop:1 #653a8b
                );
            }
            QPushButton:pressed {
                background-color: #4457bc;
            }
        """)
        apply_button.clicked.connect(self.apply_filters)

        button_layout.addWidget(clear_button)
        button_layout.addWidget(apply_button)

        parent_layout.addWidget(button_widget)

    def _apply_styles(self):
        """Aplicar estilos generales"""
        self.setStyleSheet("""
            QWidget {
                background: white;
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 10pt;
                color: #2c3e50;
            }
            QLabel {
                color: #2c3e50;
                font-weight: 500;
            }
            QCheckBox {
                spacing: 8px;
                color: #2c3e50;
                font-weight: 500;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border: 2px solid #bdc3c7;
                border-radius: 4px;
            }
            QCheckBox::indicator:checked {
                background-color: #667eea;
                border-color: #667eea;
            }
            QSpinBox {
                border: 2px solid #e0e0e0;
                border-radius: 5px;
                padding: 5px;
                color: #2c3e50;
                background: white;
            }
            QSpinBox:focus {
                border-color: #667eea;
            }
            QLineEdit {
                border: 2px solid #e0e0e0;
                border-radius: 5px;
                padding: 8px;
                color: #2c3e50;
                background: white;
            }
            QLineEdit:focus {
                border-color: #667eea;
            }
            QComboBox {
                border: 2px solid #e0e0e0;
                border-radius: 5px;
                padding: 5px;
                color: #2c3e50;
                background: white;
            }
            QComboBox:focus {
                border-color: #667eea;
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 6px solid #2c3e50;
                margin-right: 5px;
            }
            QComboBox QAbstractItemView {
                border: 2px solid #667eea;
                background: white;
                color: #2c3e50;
                selection-background-color: #667eea;
                selection-color: white;
            }
            QDateEdit {
                border: 2px solid #e0e0e0;
                border-radius: 5px;
                padding: 5px;
                color: #2c3e50;
                background: white;
            }
            QDateEdit:focus {
                border-color: #667eea;
            }
            QGroupBox {
                color: #34495e;
                font-weight: 600;
                font-size: 11pt;
                border: 2px solid #e0e0e0;
                border-radius: 6px;
                margin-top: 12px;
                padding-top: 10px;
            }
            QGroupBox::title {
                color: #667eea;
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
            QScrollBar:vertical {
                width: 10px;
                background: #f0f0f0;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical {
                background: #bdc3c7;
                border-radius: 5px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background: #95a5a6;
            }
        """)

    def _schedule_apply_filters(self):
        """Programar aplicación de filtros con debouncing"""
        self.apply_timer.start()

    def _emit_filters(self):
        """Emitir señal con filtros actuales (llamado después del debouncing)"""
        filters = self.collect_active_filters()
        logger.debug(f"Emitting filters: {filters}")

        # Guardar filtros para persistencia
        self.save_filters()

        self.filters_changed.emit(filters)

    def collect_active_filters(self) -> Dict[str, Any]:
        """
        Recolectar todos los filtros activos

        Returns:
            Diccionario con filtros activos
        """
        filters = {}

        # Estado
        if self.active_checkbox.isChecked():
            filters['is_active'] = True
        elif self.inactive_checkbox.isChecked():
            filters['is_active'] = False

        # Tipo
        if self.predefined_checkbox.isChecked():
            filters['is_predefined'] = True
        elif self.custom_checkbox.isChecked():
            filters['is_predefined'] = False

        # Anclado
        if self.pinned_checkbox.isChecked():
            filters['is_pinned'] = True

        if self.pinned_first_checkbox.isChecked():
            filters['pinned_first'] = True

        # Popularidad - Item Count
        if self.item_count_min.value() > 0:
            filters['item_count_min'] = self.item_count_min.value()

        if self.item_count_max.value() < 1000:
            filters['item_count_max'] = self.item_count_max.value()

        # Popularidad - Total Uses
        if self.total_uses_min.value() > 0:
            filters['total_uses_min'] = self.total_uses_min.value()

        if self.total_uses_max.value() < 10000:
            filters['total_uses_max'] = self.total_uses_max.value()

        # Búsqueda
        if self.search_input.text().strip():
            filters['search_text'] = self.search_input.text().strip()

        # Ordenamiento
        order_by = self.order_by_combo.currentData()
        if order_by:  # Si hay valor seleccionado
            filters['order_by'] = order_by

        order_direction = self.order_direction_combo.currentData()
        if order_direction:
            filters['order_direction'] = order_direction

        # Atributos Visuales
        if self.has_color_checkbox.isChecked():
            filters['has_color'] = True

        if self.has_badge_checkbox.isChecked():
            filters['has_badge'] = True

        # Fechas
        if self.accessed_after_checkbox.isChecked():
            date_str = self.accessed_after_date.date().toString("yyyy-MM-dd")
            filters['accessed_after'] = date_str

        if self.never_accessed_checkbox.isChecked():
            filters['never_accessed'] = True

        return filters

    def apply_filters(self):
        """Aplicar filtros manualmente (botón Aplicar)"""
        filters = self.collect_active_filters()
        logger.info(f"Applying filters manually: {filters}")
        self.filters_changed.emit(filters)

    def clear_filters(self):
        """Limpiar todos los filtros"""
        logger.info("Clearing all filters")

        # Desmarcar checkboxes
        self.active_checkbox.setChecked(False)
        self.inactive_checkbox.setChecked(False)
        self.predefined_checkbox.setChecked(False)
        self.custom_checkbox.setChecked(False)
        self.pinned_checkbox.setChecked(False)
        self.pinned_first_checkbox.setChecked(False)

        # Resetear spinboxes
        self.item_count_min.setValue(0)
        self.item_count_max.setValue(1000)
        self.total_uses_min.setValue(0)
        self.total_uses_max.setValue(10000)

        # Limpiar búsqueda
        self.search_input.clear()

        # Resetear ordenamiento
        self.order_by_combo.setCurrentIndex(0)
        self.order_direction_combo.setCurrentIndex(0)

        # Resetear atributos visuales
        self.has_color_checkbox.setChecked(False)
        self.has_badge_checkbox.setChecked(False)

        # Resetear fechas
        self.accessed_after_checkbox.setChecked(False)
        self.accessed_after_date.setEnabled(False)
        self.never_accessed_checkbox.setChecked(False)

        # Emitir señal
        self.filters_cleared.emit()

    def closeEvent(self, event):
        """Evento al cerrar la ventana"""
        logger.debug("Category filter window closing")
        self.window_closed.emit()
        super().closeEvent(event)

    # === DRAG AND DROP PARA MOVER LA VENTANA ===

    def mousePressEvent(self, event):
        """Iniciar arrastre de ventana"""
        if event.button() == Qt.MouseButton.LeftButton:
            # Solo permitir arrastrar desde la parte superior (barra de título)
            if event.position().y() < 45:
                self.dragging = True
                self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
                event.accept()

    def mouseMoveEvent(self, event):
        """Mover ventana mientras se arrastra"""
        if self.dragging and event.buttons() == Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()

    def mouseReleaseEvent(self, event):
        """Finalizar arrastre de ventana"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.dragging = False
            event.accept()

    # === PERSISTENCIA DE FILTROS ===

    def save_filters(self):
        """Guardar estado actual de filtros en QSettings"""
        try:
            filters = self.collect_active_filters()

            # Guardar cada filtro
            for key, value in filters.items():
                self.settings.setValue(f"filter/{key}", value)

            logger.debug(f"Filters saved: {len(filters)} filters persisted")

        except Exception as e:
            logger.error(f"Error saving filters: {e}")

    def load_filters(self):
        """Cargar filtros guardados desde QSettings"""
        try:
            # Estado
            if self.settings.contains("filter/is_active"):
                is_active = self.settings.value("filter/is_active", type=bool)
                self.active_checkbox.setChecked(is_active)

            if self.settings.contains("filter/is_predefined"):
                is_predefined = self.settings.value("filter/is_predefined", type=bool)
                self.predefined_checkbox.setChecked(is_predefined)

            if self.settings.contains("filter/is_pinned"):
                is_pinned = self.settings.value("filter/is_pinned", type=bool)
                self.pinned_checkbox.setChecked(is_pinned)

            # Popularidad
            if self.settings.contains("filter/item_count_min"):
                item_min = self.settings.value("filter/item_count_min", type=int)
                self.item_count_min.setValue(item_min)
                self.item_count_checkbox.setChecked(True)

            if self.settings.contains("filter/item_count_max"):
                item_max = self.settings.value("filter/item_count_max", type=int)
                self.item_count_max.setValue(item_max)

            if self.settings.contains("filter/total_uses_min"):
                uses_min = self.settings.value("filter/total_uses_min", type=int)
                self.total_uses_min.setValue(uses_min)
                self.total_uses_checkbox.setChecked(True)

            # Búsqueda
            if self.settings.contains("filter/search_text"):
                search_text = self.settings.value("filter/search_text", type=str)
                if search_text:
                    self.search_text.setText(search_text)

            # Ordenamiento
            if self.settings.contains("filter/order_by"):
                order_by = self.settings.value("filter/order_by", type=str)
                index = self.order_by_combo.findData(order_by)
                if index >= 0:
                    self.order_by_combo.setCurrentIndex(index)

            if self.settings.contains("filter/order_direction"):
                direction = self.settings.value("filter/order_direction", type=str)
                index = self.order_direction_combo.findData(direction)
                if index >= 0:
                    self.order_direction_combo.setCurrentIndex(index)

            # Atributos visuales
            if self.settings.contains("filter/has_color"):
                has_color = self.settings.value("filter/has_color", type=bool)
                self.has_color_checkbox.setChecked(has_color)

            if self.settings.contains("filter/has_badge"):
                has_badge = self.settings.value("filter/has_badge", type=bool)
                self.has_badge_checkbox.setChecked(has_badge)

            # Fechas
            if self.settings.contains("filter/accessed_after"):
                date_str = self.settings.value("filter/accessed_after", type=str)
                if date_str:
                    date = QDate.fromString(date_str, "yyyy-MM-dd")
                    if date.isValid():
                        self.accessed_after_date.setDate(date)
                        self.accessed_after_checkbox.setChecked(True)
                        self.accessed_after_date.setEnabled(True)

            if self.settings.contains("filter/never_accessed"):
                never_accessed = self.settings.value("filter/never_accessed", type=bool)
                self.never_accessed_checkbox.setChecked(never_accessed)

            logger.debug("Filters loaded from settings")

        except Exception as e:
            logger.error(f"Error loading filters: {e}")

    def clear_saved_filters(self):
        """Limpiar filtros guardados en QSettings"""
        try:
            self.settings.beginGroup("filter")
            self.settings.remove("")  # Remove all keys in "filter" group
            self.settings.endGroup()
            logger.debug("Saved filters cleared")

        except Exception as e:
            logger.error(f"Error clearing saved filters: {e}")
