"""
NotebookWindow - Ventana principal del bloc de notas con pestañas
"""

import sys
import ctypes
from ctypes import wintypes
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
    QPushButton, QLabel, QMessageBox, QApplication
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QPoint
from PyQt6.QtGui import QIcon
from views.widgets.notebook_tab import NotebookTab
import logging

logger = logging.getLogger(__name__)

# ===========================================================================
# Windows AppBar API Constants and Structures
# ===========================================================================
ABM_NEW = 0x00000000
ABM_REMOVE = 0x00000001
ABM_QUERYPOS = 0x00000002
ABM_SETPOS = 0x00000003
ABE_RIGHT = 2  # Lado derecho de la pantalla


class APPBARDATA(ctypes.Structure):
    _fields_ = [
        ("cbSize", wintypes.DWORD),
        ("hWnd", wintypes.HWND),
        ("uCallbackMessage", wintypes.UINT),
        ("uEdge", wintypes.UINT),
        ("rc", wintypes.RECT),
        ("lParam", wintypes.LPARAM),
    ]

# Constantes
NOTEBOOK_WIDTH = 450
NOTEBOOK_MIN_HEIGHT = 600
NOTEBOOK_AUTOSAVE_INTERVAL = 5000  # 5 segundos
NOTEBOOK_MAX_TABS = 10


class NotebookWindow(QWidget):
    """Ventana del bloc de notas con pestañas persistentes"""

    # Señales
    closed = pyqtSignal()
    tab_saved_as_item = pyqtSignal(dict)  # Cuando se guarda un item

    def __init__(self, controller, parent=None):
        super().__init__(parent)
        self.controller = controller
        self.notebook_manager = controller.notebook_manager
        self.appbar_registered = False  # Estado del AppBar

        # Para dragging de ventana
        self.drag_position = QPoint()

        # Configuración de ventana
        self.setWindowTitle("Bloc de Notas")
        self.setMinimumSize(NOTEBOOK_WIDTH, NOTEBOOK_MIN_HEIGHT)

        # Frameless window con borde (Tool para no aparecer en barra de tareas)
        self.setWindowFlags(
            Qt.WindowType.Tool |  # Tool en lugar de Window para no aparecer en taskbar
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint
        )

        self.setup_ui()
        self.load_tabs()
        self.setup_autosave()

        # Aplicar estilos
        self.apply_styles()

        logger.info("NotebookWindow initialized")

    def setup_ui(self):
        """Configurar interfaz"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # === BARRA DE TITULO CUSTOM ===
        title_bar = self.create_title_bar()
        layout.addWidget(title_bar)

        # === TAB WIDGET ===
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabsClosable(True)
        self.tab_widget.setMovable(True)
        self.tab_widget.setDocumentMode(True)

        # Conectar señales
        self.tab_widget.tabCloseRequested.connect(self.close_tab)
        self.tab_widget.currentChanged.connect(self.on_tab_changed)

        layout.addWidget(self.tab_widget)

        # === BOTON PARA AGREGAR TAB ===
        add_tab_container = QWidget()
        add_tab_container.setFixedHeight(50)
        add_tab_layout = QHBoxLayout(add_tab_container)
        add_tab_layout.setContentsMargins(10, 5, 10, 5)

        self.add_tab_button = QPushButton("+ Nueva Nota")
        self.add_tab_button.setMinimumHeight(40)
        self.add_tab_button.clicked.connect(self.add_new_tab)
        self.style_add_button(self.add_tab_button)

        add_tab_layout.addWidget(self.add_tab_button)

        layout.addWidget(add_tab_container)

    def create_title_bar(self):
        """Crear barra de título personalizada"""
        title_bar = QWidget()
        title_bar.setFixedHeight(40)
        title_bar.setObjectName("titleBar")

        layout = QHBoxLayout(title_bar)
        layout.setContentsMargins(15, 0, 5, 0)
        layout.setSpacing(10)

        # Icono + título
        icon_label = QLabel("📓")
        icon_label.setStyleSheet("font-size: 18px;")

        title_label = QLabel("Bloc de Notas")
        title_label.setStyleSheet("font-weight: bold; font-size: 14px; color: #FFFFFF;")

        layout.addWidget(icon_label)
        layout.addWidget(title_label)
        layout.addStretch()

        # Botones de control
        min_btn = QPushButton("−")
        close_btn = QPushButton("×")

        min_btn.setFixedSize(35, 35)
        close_btn.setFixedSize(35, 35)

        min_btn.setObjectName("minBtn")
        close_btn.setObjectName("closeBtn")

        min_btn.clicked.connect(self.showMinimized)
        close_btn.clicked.connect(self.close)

        layout.addWidget(min_btn)
        layout.addWidget(close_btn)

        # Enable dragging
        title_bar.mousePressEvent = self.start_drag
        title_bar.mouseMoveEvent = self.do_drag

        return title_bar

    def load_tabs(self):
        """Cargar pestañas persistentes desde BD"""
        tabs = self.notebook_manager.get_all_tabs()

        if not tabs:
            # Si no hay tabs, crear una por defecto
            logger.info("No tabs found, creating default tab")
            self.add_new_tab()
            return

        # Cargar cada tab
        logger.info(f"Loading {len(tabs)} tabs from database")
        for tab_data in tabs:
            self.add_tab_from_data(tab_data)

        # Restaurar tab activa
        try:
            last_active = int(self.controller.config_manager.get_setting(
                'notebook_last_active_tab', 0
            ))
            if 0 <= last_active < self.tab_widget.count():
                self.tab_widget.setCurrentIndex(last_active)
                logger.debug(f"Restored active tab: {last_active}")
        except Exception as e:
            logger.warning(f"Could not restore active tab: {e}")

    def add_new_tab(self):
        """Agregar nueva pestaña vacía"""
        # Verificar límite
        if self.tab_widget.count() >= NOTEBOOK_MAX_TABS:
            QMessageBox.warning(
                self, "Limite alcanzado",
                f"No puedes tener mas de {NOTEBOOK_MAX_TABS} pestañas abiertas."
            )
            logger.warning(f"Max tabs limit reached: {NOTEBOOK_MAX_TABS}")
            return

        # Crear tab en BD
        tab_id = self.notebook_manager.create_tab()
        logger.info(f"Created new tab with ID: {tab_id}")

        # Crear widget
        categories = self.controller.get_categories()
        tab_widget = NotebookTab(tab_id=tab_id, categories=categories)

        # Conectar señales
        tab_widget.save_requested.connect(self.on_save_as_item)
        tab_widget.content_changed.connect(self.on_tab_content_changed)
        tab_widget.cancel_requested.connect(self.on_cancel_requested)

        # Agregar al tab widget
        index = self.tab_widget.addTab(tab_widget, "Sin titulo")
        self.tab_widget.setCurrentIndex(index)

        logger.debug(f"Tab widget added at index {index}")

    def add_tab_from_data(self, tab_data):
        """Agregar pestaña con datos existentes"""
        categories = self.controller.get_categories()

        tab_widget = NotebookTab(
            tab_id=tab_data['id'],
            tab_data=tab_data,
            categories=categories
        )

        # Conectar señales
        tab_widget.save_requested.connect(self.on_save_as_item)
        tab_widget.content_changed.connect(self.on_tab_content_changed)
        tab_widget.cancel_requested.connect(self.on_cancel_requested)

        # Agregar al tab widget
        title = tab_data.get('title', 'Sin titulo')
        if not title or title.strip() == '':
            title = 'Sin titulo'

        # Limitar longitud del título en la pestaña
        display_title = title[:25] + "..." if len(title) > 25 else title

        self.tab_widget.addTab(tab_widget, display_title)
        logger.debug(f"Tab loaded from data: {title}")

    def close_tab(self, index):
        """Cerrar pestaña"""
        if self.tab_widget.count() <= 1:
            QMessageBox.information(
                self, "Informacion",
                "Debe haber al menos una pestana abierta."
            )
            logger.warning("Attempted to close last tab")
            return

        # Obtener tab widget
        tab_widget = self.tab_widget.widget(index)

        # Confirmar si hay contenido no guardado
        if tab_widget.has_unsaved_changes:
            data = tab_widget.get_data()
            if data['label'] or data['content']:
                reply = QMessageBox.question(
                    self, "Confirmar cierre",
                    "¿Cerrar esta pestana? Los cambios no guardados se perderan.",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )

                if reply == QMessageBox.StandardButton.No:
                    logger.debug(f"Tab close cancelled by user at index {index}")
                    return

        # Eliminar de BD
        if tab_widget.tab_id:
            self.notebook_manager.delete_tab(tab_widget.tab_id)
            logger.info(f"Tab deleted from database: {tab_widget.tab_id}")

        # Remover del widget
        self.tab_widget.removeTab(index)
        logger.debug(f"Tab removed at index {index}")

    def on_tab_changed(self, index):
        """Cuando cambia la pestaña activa"""
        if index < 0:
            return

        # Guardar índice en settings
        self.controller.config_manager.set_setting(
            'notebook_last_active_tab', index
        )
        logger.debug(f"Active tab changed to index {index}")

    def on_tab_content_changed(self, data):
        """Cuando cambia el contenido (para actualizar título y auto-guardar)"""
        # Obtener tab actual
        current_widget = self.sender()
        if not current_widget:
            return

        current_index = self.tab_widget.indexOf(current_widget)
        if current_index < 0:
            return

        # Actualizar título de la pestaña
        title = data.get('label', 'Sin titulo')
        if not title or title.strip() == '':
            title = 'Sin titulo'

        # Limitar longitud
        display_title = title[:25] + "..." if len(title) > 25 else title

        self.tab_widget.setTabText(current_index, display_title)

    def on_save_as_item(self, data):
        """Guardar nota como item definitivo"""
        try:
            # Obtener tab actual
            current_widget = self.sender()

            # Crear item en BD usando el DBManager correcto
            item_id = self.controller.config_manager.db.add_item(
                category_id=data['category_id'],
                label=data['label'],
                content=data['content'],
                item_type=data['item_type'],
                tags=data['tags'].split(',') if data['tags'] else [],
                description=data['description'],
                is_sensitive=data['is_sensitive'],
                is_active=data['is_active'],
                is_archived=data['is_archived']
            )

            logger.info(f"Item created from notebook: {data['label']} (ID: {item_id})")

            # Emitir señal
            self.tab_saved_as_item.emit(data)

            # Mostrar confirmación
            QMessageBox.information(
                self, "Exito",
                f"Item '{data['label']}' guardado exitosamente."
            )

            # Preguntar si limpiar pestaña
            reply = QMessageBox.question(
                self, "Limpiar pestana",
                "¿Deseas limpiar esta pestana para crear una nueva nota?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )

            if reply == QMessageBox.StandardButton.Yes:
                current_widget.clear_form()
                current_index = self.tab_widget.indexOf(current_widget)
                self.tab_widget.setTabText(current_index, "Sin titulo")
                logger.debug("Form cleared after save")

        except Exception as e:
            logger.error(f"Error saving item from notebook: {e}", exc_info=True)
            QMessageBox.critical(
                self, "Error",
                f"Error al guardar item: {str(e)}"
            )

    def on_cancel_requested(self):
        """Cuando se hace click en cancelar"""
        current_widget = self.sender()
        current_index = self.tab_widget.indexOf(current_widget)

        logger.debug(f"Cancel requested for tab at index {current_index}")

        # Opción 1: Limpiar formulario
        # current_widget.clear_form()

        # Opción 2: Cerrar tab si está vacío
        data = current_widget.get_data()
        if not data['label'] and not data['content']:
            self.close_tab(current_index)

    def setup_autosave(self):
        """Configurar auto-guardado periódico"""
        self.autosave_timer = QTimer()
        self.autosave_timer.timeout.connect(self.autosave_all_tabs)
        self.autosave_timer.start(NOTEBOOK_AUTOSAVE_INTERVAL)
        logger.info(f"Auto-save configured: every {NOTEBOOK_AUTOSAVE_INTERVAL}ms")

    def autosave_all_tabs(self):
        """Auto-guardar todas las pestañas en BD"""
        saved_count = 0

        for i in range(self.tab_widget.count()):
            tab_widget = self.tab_widget.widget(i)
            data = tab_widget.get_data()

            if tab_widget.tab_id:
                success = self.notebook_manager.update_tab(
                    tab_widget.tab_id,
                    title=data['label'] or 'Sin titulo',
                    content=data['content'],
                    category_id=data['category_id'],
                    item_type=data['item_type'],
                    tags=data['tags'],
                    description=data['description'],
                    is_sensitive=data['is_sensitive'],
                    is_active=data['is_active'],
                    is_archived=data['is_archived']
                )

                if success:
                    saved_count += 1
                    tab_widget.has_unsaved_changes = False

        if saved_count > 0:
            logger.debug(f"Auto-saved {saved_count} tabs")

    def showEvent(self, event):
        """Cuando la ventana se muestra, registrar AppBar"""
        super().showEvent(event)
        # Registrar AppBar con un pequeño delay para asegurar que la ventana esté completamente visible
        QTimer.singleShot(100, self.register_appbar)
        logger.debug("NotebookWindow shown - registering AppBar")

    def hideEvent(self, event):
        """Cuando la ventana se oculta, desregistrar AppBar"""
        self.unregister_appbar()
        super().hideEvent(event)
        logger.debug("NotebookWindow hidden - unregistering AppBar")

    def closeEvent(self, event):
        """Al cerrar, ocultar ventana en lugar de destruirla (comportamiento como navegador embebido)"""
        logger.info("NotebookWindow close requested - hiding instead of closing")

        # Auto-guardar todas las tabs
        self.autosave_all_tabs()

        # Desregistrar AppBar antes de ocultar
        self.unregister_appbar()

        # Emitir señal para que sidebar maneje el cierre
        self.closed.emit()

        # Ocultar ventana en lugar de cerrarla (no destruir la instancia)
        event.ignore()  # Ignorar el evento de cierre
        self.hide()      # Solo ocultar la ventana

        logger.info("NotebookWindow hidden (not destroyed)")

    # === DRAGGING ===

    def start_drag(self, event):
        """Iniciar arrastre de ventana"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()

    def do_drag(self, event):
        """Realizar arrastre"""
        if event.buttons() == Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self.drag_position)

    # === ESTILOS ===

    def apply_styles(self):
        """Aplicar estilos a la ventana"""
        self.setStyleSheet("""
            QWidget {
                background-color: #1E1E1E;
                color: #FFFFFF;
            }

            #titleBar {
                background-color: #2D2D2D;
                border-bottom: 1px solid #3D3D3D;
            }

            #minBtn, #closeBtn {
                background-color: transparent;
                border: none;
                border-radius: 4px;
                font-size: 20px;
                font-weight: bold;
                color: #B0B0B0;
            }

            #minBtn:hover {
                background-color: #3D3D3D;
                color: #FFFFFF;
            }

            #closeBtn:hover {
                background-color: #E81123;
                color: #FFFFFF;
            }

            QTabWidget::pane {
                border: none;
                background-color: #1E1E1E;
            }

            QTabBar::tab {
                background-color: #2D2D2D;
                color: #B0B0B0;
                padding: 10px 20px;
                margin-right: 2px;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                min-width: 100px;
            }

            QTabBar::tab:selected {
                background-color: #1E1E1E;
                color: #FFFFFF;
                border-bottom: 2px solid #0078D4;
            }

            QTabBar::tab:hover {
                background-color: #3D3D3D;
            }

            QTabBar::tab:!selected {
                margin-top: 3px;
            }

            QTabBar::close-button {
                image: none;
                subcontrol-position: right;
                subcontrol-origin: padding;
                background: transparent;
                width: 16px;
                height: 16px;
            }

            QTabBar::close-button:hover {
                background-color: #E81123;
                border-radius: 3px;
            }
        """)

    def style_add_button(self, widget):
        """Estilo para botón de agregar tab"""
        widget.setStyleSheet("""
            QPushButton {
                background-color: #2D2D2D;
                color: #FFFFFF;
                border: 2px dashed #3D3D3D;
                border-radius: 6px;
                font-size: 13px;
                font-weight: bold;
                padding: 10px;
            }
            QPushButton:hover {
                background-color: #0078D4;
                border-color: #0078D4;
                border-style: solid;
            }
            QPushButton:pressed {
                background-color: #005A9E;
            }
        """)

    # === WINDOWS APPBAR (RESERVA DE ESPACIO) ===

    def register_appbar(self):
        """
        Registra la ventana como AppBar de Windows para reservar espacio permanentemente.
        Esto empuja las ventanas maximizadas para que no cubran el notebook.
        """
        try:
            if sys.platform != 'win32':
                logger.warning("AppBar solo funciona en Windows")
                return

            if self.appbar_registered:
                logger.debug("AppBar ya está registrada")
                return

            # Obtener handle de la ventana
            hwnd = int(self.winId())

            # Obtener geometría de la pantalla
            screen = QApplication.primaryScreen()
            screen_geometry = screen.availableGeometry()

            # Crear estructura APPBARDATA
            abd = APPBARDATA()
            abd.cbSize = ctypes.sizeof(APPBARDATA)
            abd.hWnd = hwnd
            abd.uCallbackMessage = 0
            abd.uEdge = ABE_RIGHT  # Lado derecho de la pantalla (junto al sidebar)

            # Definir el rectángulo del AppBar (para ABE_RIGHT: desde el notebook hasta el borde derecho)
            abd.rc.left = self.x()  # Borde izquierdo del notebook
            abd.rc.top = screen_geometry.y()
            abd.rc.right = screen_geometry.x() + screen_geometry.width()  # Borde derecho de la pantalla
            abd.rc.bottom = screen_geometry.y() + screen_geometry.height()

            # Registrar el AppBar
            result = ctypes.windll.shell32.SHAppBarMessage(ABM_NEW, ctypes.byref(abd))
            if result:
                logger.info("Notebook registrado como AppBar - espacio reservado en el escritorio")
                self.appbar_registered = True

                # Consultar y establecer posición para reservar espacio
                ctypes.windll.shell32.SHAppBarMessage(ABM_QUERYPOS, ctypes.byref(abd))
                ctypes.windll.shell32.SHAppBarMessage(ABM_SETPOS, ctypes.byref(abd))
            else:
                logger.warning("No se pudo registrar el notebook como AppBar")

        except Exception as e:
            logger.error(f"Error al registrar notebook como AppBar: {e}")

    def unregister_appbar(self):
        """
        Desregistra la ventana como AppBar al cerrar u ocultar.
        Esto libera el espacio reservado en el escritorio.
        """
        try:
            if not self.appbar_registered:
                return

            # Obtener handle de la ventana
            hwnd = int(self.winId())

            # Crear estructura APPBARDATA
            abd = APPBARDATA()
            abd.cbSize = ctypes.sizeof(APPBARDATA)
            abd.hWnd = hwnd

            # Desregistrar el AppBar
            ctypes.windll.shell32.SHAppBarMessage(ABM_REMOVE, ctypes.byref(abd))
            self.appbar_registered = False
            logger.info("Notebook desregistrado como AppBar - espacio liberado")

        except Exception as e:
            logger.error(f"Error al desregistrar notebook como AppBar: {e}")
