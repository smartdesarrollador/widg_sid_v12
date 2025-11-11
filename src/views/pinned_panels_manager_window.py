"""
Pinned Panels Manager Window - Ventana de gestión de paneles anclados
Permite ver, editar, duplicar y eliminar paneles guardados
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QListWidget, QListWidgetItem, QLineEdit, QTextEdit,
    QGroupBox, QSplitter, QMessageBox, QComboBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QColor
import logging
from typing import Optional, Dict, List
import json

logger = logging.getLogger(__name__)


class PinnedPanelsManagerWindow(QWidget):
    """
    Ventana de gestión de paneles anclados

    Signals:
        panel_open_requested(int): Emitido cuando se solicita abrir un panel
        panel_deleted(int): Emitido cuando se elimina un panel
        panel_updated(int): Emitido cuando se actualiza un panel
    """

    # Señales
    panel_open_requested = pyqtSignal(int)  # panel_id
    panel_deleted = pyqtSignal(int)          # panel_id
    panel_updated = pyqtSignal(int)          # panel_id

    def __init__(self, config_manager, pinned_panels_manager, main_window, parent=None):
        """
        Initialize the Pinned Panels Manager Window

        Args:
            config_manager: ConfigManager instance
            pinned_panels_manager: PinnedPanelsManager instance
            main_window: Reference to MainWindow (para acceder a paneles abiertos)
            parent: Parent widget
        """
        super().__init__(parent)

        self.config_manager = config_manager
        self.panels_manager = pinned_panels_manager
        self.main_window = main_window

        self.current_selected_panel_id = None
        self.all_panels = []  # Lista de todos los paneles

        self.init_ui()
        self.load_panels()

    def init_ui(self):
        """Initialize the UI"""
        self.setWindowTitle("Gestion de Paneles Anclados")
        self.setMinimumSize(900, 600)

        # Configurar como ventana independiente
        self.setWindowFlags(
            Qt.WindowType.Window |
            Qt.WindowType.WindowStaysOnTopHint
        )

        # Importante: No cerrar la aplicación al cerrar esta ventana
        self.setAttribute(Qt.WidgetAttribute.WA_QuitOnClose, False)

        # Layout principal
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)

        # Header
        header = self._create_header()
        main_layout.addWidget(header)

        # Splitter: Lista de paneles | Detalles
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Panel izquierdo: Lista de paneles
        left_panel = self._create_left_panel()
        splitter.addWidget(left_panel)

        # Panel derecho: Detalles del panel seleccionado
        right_panel = self._create_right_panel()
        splitter.addWidget(right_panel)

        # Proporciones del splitter (40% lista, 60% detalles)
        splitter.setStretchFactor(0, 4)
        splitter.setStretchFactor(1, 6)

        main_layout.addWidget(splitter, 1)

        # Botón de cerrar
        close_btn = QPushButton("Cerrar")
        close_btn.clicked.connect(self.close)
        main_layout.addWidget(close_btn, alignment=Qt.AlignmentFlag.AlignRight)

        # Aplicar estilos
        self.apply_styles()

    def _create_header(self) -> QWidget:
        """Crear header con título y filtros"""
        header_widget = QWidget()
        header_layout = QVBoxLayout(header_widget)

        # Título
        title = QLabel("Gestion de Paneles Anclados")
        title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        header_layout.addWidget(title)

        # Búsqueda y filtros
        search_layout = QHBoxLayout()

        # Campo de búsqueda
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Buscar por nombre o categoria...")
        self.search_input.textChanged.connect(self.filter_panels)
        search_layout.addWidget(self.search_input, 3)

        # Filtro: Estado del panel
        self.status_filter_combo = QComboBox()
        self.status_filter_combo.addItem("📌 Paneles Activos", "active")
        self.status_filter_combo.addItem("📦 Paneles Archivados", "archived")
        self.status_filter_combo.currentIndexChanged.connect(self.on_status_filter_changed)
        search_layout.addWidget(self.status_filter_combo, 2)

        # Filtro: Solo con filtros activos
        self.filter_combo = QComboBox()
        self.filter_combo.addItem("Todos los paneles", "all")
        self.filter_combo.addItem("Solo con filtros activos", "with_filters")
        self.filter_combo.addItem("Solo con nombre personalizado", "with_name")
        self.filter_combo.currentIndexChanged.connect(self.filter_panels)
        search_layout.addWidget(self.filter_combo, 2)

        # Ordenar por
        self.sort_combo = QComboBox()
        self.sort_combo.addItem("Ordenar por: Ultima apertura", "last_opened")
        self.sort_combo.addItem("Ordenar por: Mas usado", "most_used")
        self.sort_combo.addItem("Ordenar por: Nombre", "name")
        self.sort_combo.addItem("Ordenar por: Categoria", "category")
        self.sort_combo.currentIndexChanged.connect(self.sort_panels)
        search_layout.addWidget(self.sort_combo, 2)

        # Botón refresh
        refresh_btn = QPushButton("Actualizar")
        refresh_btn.setToolTip("Actualizar lista")
        refresh_btn.setMaximumWidth(100)
        refresh_btn.clicked.connect(self.refresh_panel_list)
        search_layout.addWidget(refresh_btn)

        header_layout.addLayout(search_layout)

        return header_widget

    def _create_left_panel(self) -> QWidget:
        """Crear panel izquierdo con lista de paneles"""
        left_widget = QGroupBox("Paneles Guardados")
        left_layout = QVBoxLayout(left_widget)

        # Lista de paneles
        self.panels_list = QListWidget()
        self.panels_list.itemSelectionChanged.connect(self.on_panel_selected)
        self.panels_list.itemDoubleClicked.connect(self.on_panel_double_clicked)
        left_layout.addWidget(self.panels_list)

        # Contador de paneles
        self.panel_count_label = QLabel("0 paneles")
        self.panel_count_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        left_layout.addWidget(self.panel_count_label)

        return left_widget

    def _create_right_panel(self) -> QWidget:
        """Crear panel derecho con detalles del panel seleccionado"""
        right_widget = QGroupBox("Detalles del Panel")
        right_layout = QVBoxLayout(right_widget)

        # Información básica
        info_group = QGroupBox("Informacion Basica")
        info_layout = QVBoxLayout(info_group)

        self.name_label = QLabel("<i>Selecciona un panel</i>")
        self.category_label = QLabel("")
        self.shortcut_label = QLabel("")
        self.status_label = QLabel("")

        info_layout.addWidget(QLabel("<b>Nombre:</b>"))
        info_layout.addWidget(self.name_label)
        info_layout.addWidget(QLabel("<b>Categoria:</b>"))
        info_layout.addWidget(self.category_label)
        info_layout.addWidget(QLabel("<b>Atajo de teclado:</b>"))
        info_layout.addWidget(self.shortcut_label)
        info_layout.addWidget(QLabel("<b>Estado:</b>"))
        info_layout.addWidget(self.status_label)

        right_layout.addWidget(info_group)

        # Filtros activos
        filters_group = QGroupBox("Filtros Aplicados")
        filters_layout = QVBoxLayout(filters_group)

        self.filters_display = QTextEdit()
        self.filters_display.setReadOnly(True)
        self.filters_display.setMaximumHeight(150)
        filters_layout.addWidget(self.filters_display)

        right_layout.addWidget(filters_group)

        # Estadísticas
        stats_group = QGroupBox("Estadisticas")
        stats_layout = QVBoxLayout(stats_group)

        self.stats_label = QLabel("")
        stats_layout.addWidget(self.stats_label)

        right_layout.addWidget(stats_group)

        # Botones de acción
        actions_layout = QHBoxLayout()

        self.open_btn = QPushButton("🚀 Abrir")
        self.open_btn.setEnabled(False)
        self.open_btn.clicked.connect(self.open_panel)
        actions_layout.addWidget(self.open_btn)

        self.restore_btn = QPushButton("♻️ Restaurar")
        self.restore_btn.setEnabled(False)
        self.restore_btn.setVisible(False)  # Solo visible para paneles archivados
        self.restore_btn.clicked.connect(self.restore_panel)
        actions_layout.addWidget(self.restore_btn)

        self.edit_btn = QPushButton("✏️ Editar")
        self.edit_btn.setEnabled(False)
        self.edit_btn.clicked.connect(self.edit_panel)
        actions_layout.addWidget(self.edit_btn)

        self.duplicate_btn = QPushButton("📋 Duplicar")
        self.duplicate_btn.setEnabled(False)
        self.duplicate_btn.clicked.connect(self.duplicate_panel)
        actions_layout.addWidget(self.duplicate_btn)

        self.delete_btn = QPushButton("🗑️ Eliminar")
        self.delete_btn.setEnabled(False)
        self.delete_btn.clicked.connect(self.delete_panel)
        actions_layout.addWidget(self.delete_btn)

        right_layout.addLayout(actions_layout)

        # Espaciador
        right_layout.addStretch()

        return right_widget

    def load_panels(self):
        """Cargar todos los paneles desde la base de datos"""
        try:
            # Obtener todos los paneles (activos e inactivos)
            self.all_panels = self.panels_manager.get_all_panels(active_only=False)

            logger.info(f"Loaded {len(self.all_panels)} panels")

            # Aplicar filtros y actualizar UI
            self.filter_panels()

        except Exception as e:
            logger.error(f"Error loading panels: {e}", exc_info=True)
            QMessageBox.critical(self, "Error", f"Error al cargar paneles: {e}")

    def on_status_filter_changed(self):
        """Handle cuando cambia el filtro de estado (activos/archivados)"""
        logger.info("Status filter changed - reloading panels")
        self.filter_panels()

    def refresh_panel_list(self):
        """Refrescar lista de paneles"""
        logger.info("Refreshing panel list")
        self.load_panels()

    def filter_panels(self):
        """Filtrar y mostrar paneles según criterios de búsqueda"""
        search_text = self.search_input.text().lower()
        filter_type = self.filter_combo.currentData()
        status_filter = self.status_filter_combo.currentData()

        # Filtrar paneles
        filtered_panels = []

        for panel in self.all_panels:
            # Aplicar filtro de estado (activo/archivado)
            is_active = panel.get('is_active', 1)
            if status_filter == "active" and not is_active:
                continue
            elif status_filter == "archived" and is_active:
                continue

            # Aplicar filtro de búsqueda
            if search_text:
                panel_name = panel.get('custom_name', '')
                category_name = self._get_category_name(panel['category_id'])

                if search_text not in panel_name.lower() and search_text not in category_name.lower():
                    continue

            # Aplicar filtro de tipo
            if filter_type == "with_filters":
                if not panel.get('filter_config'):
                    continue
            elif filter_type == "with_name":
                if not panel.get('custom_name'):
                    continue

            filtered_panels.append(panel)

        # Ordenar y mostrar paneles
        self.display_panels(filtered_panels)

    def sort_panels(self):
        """Reordenar y mostrar paneles"""
        self.filter_panels()  # Re-aplicar filtros con nuevo orden

    def display_panels(self, panels: List[Dict]):
        """Mostrar paneles en la lista"""
        self.panels_list.clear()

        sort_by = self.sort_combo.currentData()

        # Ordenar paneles
        if sort_by == "last_opened":
            panels = sorted(panels, key=lambda p: p.get('last_opened', ''), reverse=True)
        elif sort_by == "most_used":
            panels = sorted(panels, key=lambda p: p.get('open_count', 0), reverse=True)
        elif sort_by == "name":
            panels = sorted(panels, key=lambda p: p.get('custom_name', self._get_category_name(p['category_id'])))
        elif sort_by == "category":
            panels = sorted(panels, key=lambda p: self._get_category_name(p['category_id']))

        # Crear items de lista
        for panel in panels:
            item_widget = PanelListItemWidget(panel, self.config_manager)
            item = QListWidgetItem(self.panels_list)
            # Ajustar sizeHint para incluir el borde de selección (2px en cada lado = 4px total)
            widget_size = item_widget.sizeHint()
            item.setSizeHint(widget_size)
            item.setData(Qt.ItemDataRole.UserRole, panel['id'])
            self.panels_list.addItem(item)
            self.panels_list.setItemWidget(item, item_widget)

        # Actualizar contador
        self.panel_count_label.setText(f"{len(panels)} panel(es)")

    def on_panel_selected(self):
        """Evento cuando se selecciona un panel de la lista"""
        selected_items = self.panels_list.selectedItems()

        if not selected_items:
            self.clear_details()
            return

        panel_id = selected_items[0].data(Qt.ItemDataRole.UserRole)
        self.current_selected_panel_id = panel_id

        # Mostrar detalles del panel
        self.show_panel_details(panel_id)

        # Habilitar botones
        self.open_btn.setEnabled(True)
        self.edit_btn.setEnabled(True)
        self.duplicate_btn.setEnabled(True)
        self.delete_btn.setEnabled(True)

    def on_panel_double_clicked(self, item):
        """Evento cuando se hace doble clic en un panel"""
        panel_id = item.data(Qt.ItemDataRole.UserRole)
        self.open_panel_by_id(panel_id)

    def show_panel_details(self, panel_id: int):
        """Mostrar detalles del panel seleccionado"""
        try:
            panel = self.panels_manager.get_panel_by_id(panel_id)

            if not panel:
                self.clear_details()
                return

            # Información básica
            panel_name = panel.get('custom_name') or self._get_category_name(panel['category_id'])
            category_name = self._get_category_name(panel['category_id'])
            shortcut = panel.get('keyboard_shortcut', 'Ninguno')
            is_active = panel.get('is_active', False)

            self.name_label.setText(f"<b>{panel_name}</b>")
            self.category_label.setText(category_name)
            self.shortcut_label.setText(shortcut)

            # Estado
            if is_active:
                # Verificar si está actualmente abierto
                is_open = self._is_panel_open(panel_id)
                status_text = "<span style='color: #00ff00;'>Abierto actualmente</span>" if is_open else "<span style='color: #ffaa00;'>Activo (cerrado)</span>"
            else:
                status_text = "<span style='color: #888;'>Inactivo</span>"

            self.status_label.setText(status_text)

            # Filtros
            filter_config = panel.get('filter_config')
            if filter_config:
                filters = self.panels_manager._deserialize_filter_config(filter_config)
                self.display_filters(filters)
            else:
                self.filters_display.setText("<i>Sin filtros aplicados</i>")

            # Estadísticas
            open_count = panel.get('open_count', 0)
            last_opened = panel.get('last_opened', 'Nunca')
            created_at = panel.get('created_at', 'Desconocido')

            stats_text = f"""
            <p><b>Veces abierto:</b> {open_count}</p>
            <p><b>Ultima apertura:</b> {last_opened}</p>
            <p><b>Creado:</b> {created_at}</p>
            """
            self.stats_label.setText(stats_text)

            # Mostrar/ocultar botones según el estado del panel
            if is_active:
                # Panel activo: mostrar todos los botones excepto Restaurar
                self.open_btn.setVisible(True)
                self.edit_btn.setVisible(True)
                self.duplicate_btn.setVisible(True)
                self.restore_btn.setVisible(False)
            else:
                # Panel archivado: solo mostrar Restaurar y Eliminar
                self.open_btn.setVisible(False)
                self.edit_btn.setVisible(False)
                self.duplicate_btn.setVisible(False)
                self.restore_btn.setVisible(True)

            # Habilitar botones
            self.open_btn.setEnabled(True)
            self.edit_btn.setEnabled(True)
            self.duplicate_btn.setEnabled(True)
            self.delete_btn.setEnabled(True)
            self.restore_btn.setEnabled(True)

        except Exception as e:
            logger.error(f"Error showing panel details: {e}", exc_info=True)

    def display_filters(self, filters: Dict):
        """Mostrar filtros del panel en formato legible"""
        filter_lines = []

        # Filtros avanzados
        advanced = filters.get('advanced_filters', {})
        if advanced:
            filter_lines.append("<b>Filtros Avanzados:</b>")
            for key, value in advanced.items():
                filter_lines.append(f"  - {key}: {value}")

        # Filtro de estado
        state = filters.get('state_filter', 'normal')
        if state != 'normal':
            filter_lines.append(f"<b>Estado:</b> {state}")

        # Texto de búsqueda
        search = filters.get('search_text', '')
        if search:
            filter_lines.append(f"<b>Busqueda:</b> \"{search}\"")

        if not filter_lines:
            self.filters_display.setText("<i>Sin filtros aplicados</i>")
        else:
            self.filters_display.setText("<br>".join(filter_lines))

    def clear_details(self):
        """Limpiar panel de detalles"""
        self.name_label.setText("<i>Selecciona un panel</i>")
        self.category_label.setText("")
        self.shortcut_label.setText("")
        self.status_label.setText("")
        self.filters_display.setText("")
        self.stats_label.setText("")

        self.open_btn.setEnabled(False)
        self.edit_btn.setEnabled(False)
        self.duplicate_btn.setEnabled(False)
        self.delete_btn.setEnabled(False)

        self.current_selected_panel_id = None

    def open_panel(self):
        """Abrir el panel seleccionado"""
        if not self.current_selected_panel_id:
            return

        self.open_panel_by_id(self.current_selected_panel_id)

    def open_panel_by_id(self, panel_id: int):
        """Abrir un panel por su ID"""
        try:
            logger.info(f"[PANEL MANAGER] Opening panel {panel_id}")
            logger.debug(f"[PANEL MANAGER] Main window reference: {self.main_window is not None}")

            # Verificar si el panel ya está abierto
            is_open = self._is_panel_open(panel_id)
            logger.debug(f"[PANEL MANAGER] Panel {panel_id} is_open: {is_open}")

            if is_open:
                # Enfocar el panel existente
                self._focus_panel(panel_id)
                logger.info(f"[PANEL MANAGER] Panel {panel_id} already open, focusing...")
            else:
                # Emitir señal para que MainWindow abra el panel
                logger.info(f"[PANEL MANAGER] Emitting signal to open panel {panel_id}")
                self.panel_open_requested.emit(panel_id)
                logger.info(f"[PANEL MANAGER] Signal emitted successfully for panel {panel_id}")

        except Exception as e:
            logger.error(f"[PANEL MANAGER] Error opening panel: {e}", exc_info=True)
            QMessageBox.critical(self, "Error", f"Error al abrir panel: {e}")

    def edit_panel(self):
        """Editar el panel seleccionado"""
        if not self.current_selected_panel_id:
            return

        try:
            panel = self.panels_manager.get_panel_by_id(self.current_selected_panel_id)

            if not panel:
                QMessageBox.warning(self, "Error", "Panel no encontrado")
                return

            # Abrir diálogo de personalización
            from views.dialogs.panel_customization_dialog import PanelCustomizationDialog

            dialog = PanelCustomizationDialog(
                panel=panel,
                panels_manager=self.panels_manager,
                config_manager=self.config_manager,
                parent=self
            )

            if dialog.exec():
                # Obtener datos actualizados
                updated_data = dialog.get_customization_data()

                # Actualizar en BD
                self.panels_manager.update_panel_customization(
                    panel_id=self.current_selected_panel_id,
                    custom_name=updated_data.get('custom_name'),
                    custom_color=updated_data.get('custom_color'),
                    keyboard_shortcut=updated_data.get('keyboard_shortcut')
                )

                # Emitir señal de actualización
                self.panel_updated.emit(self.current_selected_panel_id)

                # Refrescar lista
                self.refresh_panel_list()

                logger.info(f"Panel {self.current_selected_panel_id} updated")
                QMessageBox.information(self, "Exito", "Panel actualizado correctamente")

        except Exception as e:
            logger.error(f"Error editing panel: {e}", exc_info=True)
            QMessageBox.critical(self, "Error", f"Error al editar panel: {e}")

    def duplicate_panel(self):
        """Duplicar el panel seleccionado"""
        if not self.current_selected_panel_id:
            return

        try:
            panel = self.panels_manager.get_panel_by_id(self.current_selected_panel_id)

            if not panel:
                QMessageBox.warning(self, "Error", "Panel no encontrado")
                return

            # Confirmar duplicación
            reply = QMessageBox.question(
                self,
                "Duplicar Panel",
                f"¿Duplicar el panel '{panel.get('custom_name') or 'Sin nombre'}'?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )

            if reply != QMessageBox.StandardButton.Yes:
                return

            # Crear copia en BD
            filter_config = panel.get('filter_config')
            new_name = f"{panel.get('custom_name', 'Panel')} (copia)"

            new_panel_id = self.config_manager.db.save_pinned_panel(
                category_id=panel['category_id'],
                x_pos=panel['x_position'] + 20,  # Offset para que no queden exactamente encima
                y_pos=panel['y_position'] + 20,
                width=panel['width'],
                height=panel['height'],
                is_minimized=False,
                custom_name=new_name,
                custom_color=panel.get('custom_color'),
                filter_config=filter_config,
                keyboard_shortcut=None  # Se asignará automáticamente
            )

            # Refrescar lista
            self.refresh_panel_list()

            logger.info(f"Panel {self.current_selected_panel_id} duplicated as {new_panel_id}")
            QMessageBox.information(self, "Exito", f"Panel duplicado correctamente (ID: {new_panel_id})")

        except Exception as e:
            logger.error(f"Error duplicating panel: {e}", exc_info=True)
            QMessageBox.critical(self, "Error", f"Error al duplicar panel: {e}")

    def delete_panel(self):
        """Eliminar el panel seleccionado"""
        if not self.current_selected_panel_id:
            return

        try:
            panel = self.panels_manager.get_panel_by_id(self.current_selected_panel_id)

            if not panel:
                QMessageBox.warning(self, "Error", "Panel no encontrado")
                return

            panel_name = panel.get('custom_name') or self._get_category_name(panel['category_id'])

            # Confirmar eliminación
            reply = QMessageBox.question(
                self,
                "Eliminar Panel",
                f"¿Eliminar permanentemente el panel '{panel_name}'?\n\n"
                f"Esta accion no se puede deshacer.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )

            if reply != QMessageBox.StandardButton.Yes:
                return

            # Verificar si el panel está abierto
            if self._is_panel_open(self.current_selected_panel_id):
                QMessageBox.warning(
                    self,
                    "Panel Abierto",
                    "Por favor cierra el panel antes de eliminarlo."
                )
                return

            # Eliminar de BD
            self.panels_manager.delete_panel(self.current_selected_panel_id)

            # Emitir señal de eliminación
            self.panel_deleted.emit(self.current_selected_panel_id)

            # Limpiar detalles y refrescar lista
            self.clear_details()
            self.refresh_panel_list()

            logger.info(f"Panel {self.current_selected_panel_id} deleted")
            QMessageBox.information(self, "Exito", "Panel eliminado correctamente")

        except Exception as e:
            logger.error(f"Error deleting panel: {e}", exc_info=True)
            QMessageBox.critical(self, "Error", f"Error al eliminar panel: {e}")

    def restore_panel(self):
        """Restaurar un panel archivado (marcarlo como activo)"""
        if not self.current_selected_panel_id:
            return

        try:
            panel = self.panels_manager.get_panel_by_id(self.current_selected_panel_id)

            if not panel:
                QMessageBox.warning(self, "Error", "Panel no encontrado")
                return

            panel_name = panel.get('custom_name') or self._get_category_name(panel['category_id'])

            # Confirmar restauración
            reply = QMessageBox.question(
                self,
                "Restaurar Panel",
                f"¿Restaurar el panel '{panel_name}'?\n\n"
                f"El panel volverá a estar activo y se podrá anclar nuevamente.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )

            if reply != QMessageBox.StandardButton.Yes:
                return

            # Restaurar panel (marcarlo como activo)
            self.panels_manager.restore_panel(self.current_selected_panel_id)

            # Refrescar lista para mostrar el cambio
            self.refresh_panel_list()

            logger.info(f"Panel {self.current_selected_panel_id} restored")
            QMessageBox.information(self, "Éxito", "Panel restaurado correctamente")

        except Exception as e:
            logger.error(f"Error restoring panel: {e}", exc_info=True)
            QMessageBox.critical(self, "Error", f"Error al restaurar panel: {e}")

    def _get_category_name(self, category_id: int) -> str:
        """Obtener nombre de categoría por ID"""
        try:
            category = self.config_manager.get_category(str(category_id))
            if category:
                return f"{category.icon} {category.name}"
            return f"Categoria {category_id}"
        except:
            return f"Categoria {category_id}"

    def _is_panel_open(self, panel_id: int) -> bool:
        """Verificar si un panel está actualmente abierto"""
        try:
            if not self.main_window:
                return False

            for panel in self.main_window.pinned_panels:
                if panel.panel_id == panel_id:
                    return True

            return False
        except:
            return False

    def _focus_panel(self, panel_id: int):
        """Enfocar un panel abierto"""
        try:
            logger.info(f"[PANEL MANAGER] Attempting to focus panel {panel_id}")

            if not self.main_window:
                logger.warning("[PANEL MANAGER] No main_window reference available")
                return

            for panel in self.main_window.pinned_panels:
                if panel.panel_id == panel_id:
                    logger.info(f"[PANEL MANAGER] Found panel {panel_id}, focusing...")

                    # Si está minimizado, restaurar primero
                    if panel.is_minimized:
                        logger.info(f"[PANEL MANAGER] Panel {panel_id} is minimized, restoring...")
                        panel.toggle_minimize()

                    # Mostrar el panel si está oculto
                    if not panel.isVisible():
                        logger.info(f"[PANEL MANAGER] Panel {panel_id} is hidden, showing...")
                        panel.show()

                    # Traer al frente y enfocar
                    panel.raise_()
                    panel.activateWindow()
                    panel.setFocus()

                    logger.info(f"[PANEL MANAGER] Panel {panel_id} focused successfully")
                    break
        except Exception as e:
            logger.error(f"[PANEL MANAGER] Error focusing panel: {e}", exc_info=True)

    def apply_styles(self):
        """Aplicar estilos a la ventana"""
        self.setStyleSheet("""
            QWidget {
                background-color: #1e1e1e;
                color: #e0e0e0;
                font-family: 'Segoe UI';
            }

            QGroupBox {
                border: 1px solid #3d3d3d;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
                font-weight: bold;
            }

            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 5px;
                color: #00aaff;
            }

            QPushButton {
                background-color: #2d2d2d;
                border: 1px solid #3d3d3d;
                border-radius: 3px;
                padding: 5px 10px;
                color: #e0e0e0;
            }

            QPushButton:hover {
                background-color: #3d3d3d;
                border: 1px solid #00aaff;
            }

            QPushButton:pressed {
                background-color: #1a1a1a;
            }

            QPushButton:disabled {
                background-color: #2d2d2d;
                color: #555;
            }

            QLineEdit, QComboBox {
                background-color: #2d2d2d;
                border: 1px solid #3d3d3d;
                border-radius: 3px;
                padding: 5px;
                color: #e0e0e0;
            }

            QLineEdit:focus, QComboBox:focus {
                border: 1px solid #00aaff;
            }

            QListWidget {
                background-color: #1e1e1e;
                border: 1px solid #3d3d3d;
                border-radius: 3px;
                padding: 5px;
            }

            QListWidget::item {
                padding: 1px;
                margin: 4px 3px;
                background-color: transparent;
                border: 2px solid transparent;
                border-radius: 8px;
            }

            QListWidget::item:selected {
                background-color: transparent;
                border: 2px solid #00aaff;
                border-radius: 8px;
            }

            QTextEdit {
                background-color: #2d2d2d;
                border: 1px solid #3d3d3d;
                border-radius: 3px;
                padding: 5px;
            }
        """)

    def closeEvent(self, event):
        """Handle window close event"""
        logger.info("Pinned Panels Manager Window closed")
        # Ocultar en lugar de cerrar para poder reutilizar la ventana
        self.hide()
        event.accept()


class PanelListItemWidget(QWidget):
    """
    Widget personalizado para mostrar un panel en la lista
    Muestra: nombre, categoría, indicadores de filtros, shortcut
    """

    def __init__(self, panel_data: Dict, config_manager, parent=None):
        super().__init__(parent)

        self.panel_data = panel_data
        self.config_manager = config_manager

        self.setup_ui()

    def setup_ui(self):
        """Configurar UI del widget"""
        # Establecer altura mínima del widget para que se vea completo el texto
        self.setMinimumHeight(65)

        # Aplicar estilo de fondo uniforme
        self.setStyleSheet("""
            PanelListItemWidget {
                background-color: #252525;
                border-radius: 6px;
                border: none;
            }
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        # Icono de estado
        status_label = QLabel()
        if self.panel_data.get('is_active'):
            status_label.setText("[A]")
            status_label.setToolTip("Activo")
            status_label.setStyleSheet("color: #00ff00;")
        else:
            status_label.setText("[I]")
            status_label.setToolTip("Inactivo")
            status_label.setStyleSheet("color: #888;")
        layout.addWidget(status_label)

        # Información del panel
        info_layout = QVBoxLayout()

        # Nombre del panel
        panel_name = self.panel_data.get('custom_name')
        if not panel_name:
            category = self.config_manager.get_category(str(self.panel_data['category_id']))
            panel_name = f"{category.icon} {category.name}" if category else f"Panel {self.panel_data['id']}"

        name_label = QLabel(f"<b>{panel_name}</b>")
        info_layout.addWidget(name_label)

        # Información adicional (categoría, filtros, shortcut)
        details = []

        # Categoría (si tiene nombre personalizado)
        if self.panel_data.get('custom_name'):
            category = self.config_manager.get_category(str(self.panel_data['category_id']))
            if category:
                details.append(f"Cat: {category.name}")

        # Indicador de filtros
        if self.panel_data.get('filter_config'):
            details.append("Filtros")

        # Shortcut
        if self.panel_data.get('keyboard_shortcut'):
            details.append(f"{self.panel_data['keyboard_shortcut']}")

        if details:
            details_label = QLabel(" | ".join(details))
            details_label.setStyleSheet("color: #888;")
            info_layout.addWidget(details_label)

        layout.addLayout(info_layout, 1)

        # Contador de usos
        usage_label = QLabel(f"Usos: {self.panel_data.get('open_count', 0)}")
        usage_label.setToolTip(f"Abierto {self.panel_data.get('open_count', 0)} veces")
        usage_label.setStyleSheet("color: #00aaff;")
        layout.addWidget(usage_label)
