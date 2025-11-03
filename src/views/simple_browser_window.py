"""
Simple Browser Window - Ventana flotante con navegador embebido
Author: Widget Sidebar Team
Date: 2025-11-02
"""

import sys
import logging
import ctypes
from ctypes import wintypes
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit,
    QPushButton, QLabel, QApplication, QTabWidget, QTabBar
)
from PyQt6.QtCore import Qt, QUrl, pyqtSignal, QTimer
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEngineSettings

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


class SimpleBrowserWindow(QWidget):
    """
    Ventana flotante con navegador embebido QWebEngineView.

    Características:
    - Una sola instancia de QWebEngineView
    - Barra de navegación mínima (URL + Reload)
    - Ventana AppBar que reserva espacio en el escritorio
    - Ocupa toda la altura de la pantalla
    - Timeout de carga para prevenir cuelgues
    - Tema futurista simple
    """

    # Señales
    closed = pyqtSignal()

    def __init__(self, url: str = "https://www.google.com"):
        """
        Inicializa la ventana del navegador.

        Args:
            url: URL inicial a cargar
        """
        super().__init__()
        self.url = url
        self.appbar_registered = False  # Estado del AppBar

        # Variables para redimensionamiento
        self.resizing = False
        self.resize_edge_width = 10  # Ancho del área sensible en el borde izquierdo
        self.resize_start_pos = None
        self.resize_start_width = None
        self.resize_start_x = None

        # Sistema de pestañas
        self.tabs = []  # Lista de QWebEngineView (una por pestaña)
        self.tab_widget = None  # QTabWidget
        self.is_loading = False  # Estado de carga

        logger.info(f"Inicializando SimpleBrowserWindow con URL: {url}")

        self._setup_window()
        self._setup_ui()
        self._setup_timer()
        self._apply_styles()

        # Habilitar rastreo de mouse para detectar hover en el borde
        self.setMouseTracking(True)

        # Cargar URL inicial de forma asíncrona (evita bloqueo del hilo principal)
        QTimer.singleShot(100, lambda: self.load_url(self.url))

    def _setup_window(self):
        """Configura propiedades de la ventana."""
        # Ventana flotante que permanece arriba
        self.setWindowFlags(
            Qt.WindowType.Tool |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.FramelessWindowHint
        )

        self.setWindowTitle("Widget Sidebar Browser")

        # Calcular tamaño para ocupar toda la altura de la pantalla (excepto taskbar)
        screen = QApplication.primaryScreen()
        screen_geometry = screen.availableGeometry()

        # Altura: 100% del área disponible (excluye automáticamente la barra de tareas)
        window_height = screen_geometry.height()
        window_width = 500  # Ancho inicial (redimensionable)

        self.resize(window_width, window_height)

    def _setup_ui(self):
        """Configura la interfaz de usuario con sistema de pestañas."""
        # Layout principal
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Barra de navegación
        nav_bar = self._create_nav_bar()
        main_layout.addLayout(nav_bar)

        # QTabWidget para pestañas
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabsClosable(True)  # Permitir cerrar pestañas
        self.tab_widget.setMovable(True)  # Permitir mover pestañas
        self.tab_widget.setDocumentMode(True)  # Apariencia más limpia

        # Conectar señales del tab widget
        self.tab_widget.currentChanged.connect(self._on_tab_changed)
        self.tab_widget.tabCloseRequested.connect(self._on_close_tab)

        main_layout.addWidget(self.tab_widget)

        # Botón "+" para agregar nueva pestaña (colocado en la esquina del tab widget)
        self.tab_widget.setCornerWidget(self._create_new_tab_button())

        self.setLayout(main_layout)

        # Crear primera pestaña con la URL inicial
        self.add_new_tab(self.url, "Nueva pestaña")

    def _create_nav_bar(self) -> QHBoxLayout:
        """Crea la barra de navegación."""
        nav_layout = QHBoxLayout()
        nav_layout.setContentsMargins(5, 5, 5, 5)
        nav_layout.setSpacing(5)

        # Label de estado
        self.status_label = QLabel("●")
        self.status_label.setFixedWidth(20)
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        nav_layout.addWidget(self.status_label)

        # Campo URL
        self.url_bar = QLineEdit()
        self.url_bar.setPlaceholderText("Ingresa una URL...")
        self.url_bar.setText(self.url)
        self.url_bar.returnPressed.connect(self._on_url_entered)
        nav_layout.addWidget(self.url_bar)

        # Botón reload
        self.reload_btn = QPushButton("↻")
        self.reload_btn.setFixedWidth(40)
        self.reload_btn.setToolTip("Recargar página")
        self.reload_btn.clicked.connect(self.reload_page)
        nav_layout.addWidget(self.reload_btn)

        # Botón cerrar
        self.close_btn = QPushButton("✕")
        self.close_btn.setFixedWidth(40)
        self.close_btn.setToolTip("Cerrar navegador")
        self.close_btn.clicked.connect(self.close)
        nav_layout.addWidget(self.close_btn)

        return nav_layout

    def _setup_timer(self):
        """Configura timer de timeout para prevenir cuelgues."""
        self.load_timer = QTimer()
        self.load_timer.setSingleShot(True)
        self.load_timer.timeout.connect(self._on_load_timeout)

    def _apply_styles(self):
        """Aplica estilos futuristas simples."""
        self.setStyleSheet("""
            SimpleBrowserWindow {
                background-color: #1a1a2e;
                border: 2px solid #00d4ff;
            }

            QLineEdit {
                background-color: #16213e;
                color: #00d4ff;
                border: 1px solid #0f3460;
                border-radius: 5px;
                padding: 5px;
                font-size: 11px;
            }

            QLineEdit:focus {
                border: 1px solid #00d4ff;
            }

            QPushButton {
                background-color: #0f3460;
                color: #00d4ff;
                border: 1px solid #00d4ff;
                border-radius: 5px;
                padding: 5px;
                font-size: 14px;
                font-weight: bold;
            }

            QPushButton:hover {
                background-color: #16213e;
                border: 2px solid #00d4ff;
            }

            QPushButton:pressed {
                background-color: #00d4ff;
                color: #1a1a2e;
            }

            QLabel {
                color: #00ff00;
                font-size: 14px;
            }

            /* Estilos para QTabWidget */
            QTabWidget::pane {
                background-color: #1a1a2e;
                border: 1px solid #0f3460;
                border-top: 2px solid #00d4ff;
            }

            QTabBar::tab {
                background-color: #0f3460;
                color: #00d4ff;
                border: 1px solid #00d4ff;
                border-bottom: none;
                border-top-left-radius: 5px;
                border-top-right-radius: 5px;
                padding: 8px 12px;
                margin-right: 2px;
                font-size: 11px;
                min-width: 100px;
                max-width: 200px;
            }

            QTabBar::tab:selected {
                background-color: #16213e;
                border: 2px solid #00d4ff;
                border-bottom: none;
                color: #00d4ff;
                font-weight: bold;
            }

            QTabBar::tab:hover:!selected {
                background-color: #16213e;
                border: 1px solid #00d4ff;
            }

            QTabBar::close-button {
                image: none;
                background: transparent;
                border: none;
                padding: 0px;
                margin: 0px 2px;
            }

            QTabBar::close-button:hover {
                background-color: #ff0000;
                border-radius: 3px;
            }

            /* Botón de cerrar pestaña personalizado */
            QTabBar QToolButton {
                background-color: transparent;
                border: none;
                color: #00d4ff;
            }

            QTabBar QToolButton:hover {
                background-color: rgba(255, 0, 0, 0.5);
                border-radius: 3px;
            }
        """)

    # ==================== Sistema de Pestañas ====================

    def _create_new_tab_button(self) -> QPushButton:
        """Crea el botón '+' para agregar nuevas pestañas."""
        new_tab_btn = QPushButton("+")
        new_tab_btn.setFixedSize(30, 30)
        new_tab_btn.setToolTip("Nueva pestaña")
        new_tab_btn.clicked.connect(lambda: self.add_new_tab("https://www.google.com", "Nueva pestaña"))
        new_tab_btn.setStyleSheet("""
            QPushButton {
                background-color: #0f3460;
                color: #00d4ff;
                border: 1px solid #00d4ff;
                border-radius: 5px;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #16213e;
                border: 2px solid #00d4ff;
            }
        """)
        return new_tab_btn

    def add_new_tab(self, url: str = "https://www.google.com", title: str = "Nueva pestaña"):
        """
        Agrega una nueva pestaña al navegador.

        Args:
            url: URL inicial de la pestaña
            title: Título de la pestaña
        """
        # Crear nuevo QWebEngineView
        browser = QWebEngineView()

        # Configurar el navegador
        settings = browser.settings()
        settings.setAttribute(QWebEngineSettings.WebAttribute.JavascriptEnabled, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.PluginsEnabled, False)
        settings.setAttribute(QWebEngineSettings.WebAttribute.LocalStorageEnabled, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, False)

        # Conectar señales
        browser.loadStarted.connect(lambda: self._on_load_started())
        browser.loadProgress.connect(lambda progress: self._on_load_progress(progress))
        browser.loadFinished.connect(lambda success: self._on_load_finished(success))
        browser.urlChanged.connect(lambda url: self._on_url_changed(url))
        browser.titleChanged.connect(lambda title: self._on_title_changed(title))

        # Agregar a la lista de pestañas
        self.tabs.append(browser)

        # Agregar pestaña al widget
        tab_index = self.tab_widget.addTab(browser, title)

        # Activar la nueva pestaña
        self.tab_widget.setCurrentIndex(tab_index)

        # Cargar URL
        if url:
            browser.setUrl(QUrl(url if url.startswith(('http://', 'https://')) else 'https://' + url))

        logger.info(f"Nueva pestaña agregada: {title} ({url})")

    def _on_tab_changed(self, index: int):
        """Handler cuando cambia la pestaña activa."""
        if index >= 0 and index < len(self.tabs):
            browser = self.tabs[index]
            # Actualizar barra de URL con la URL de la pestaña activa
            current_url = browser.url().toString()
            if current_url:
                self.url_bar.setText(current_url)
            logger.debug(f"Pestaña activa cambiada a índice {index}")

    def _on_close_tab(self, index: int):
        """
        Handler para cerrar una pestaña.

        Args:
            index: Índice de la pestaña a cerrar
        """
        if self.tab_widget.count() == 1:
            # Si es la última pestaña, no permitir cerrarla (o cerrar la ventana)
            logger.warning("No se puede cerrar la última pestaña")
            return

        # Remover de la lista
        if 0 <= index < len(self.tabs):
            browser = self.tabs.pop(index)
            browser.deleteLater()

        # Remover del widget
        self.tab_widget.removeTab(index)

        logger.info(f"Pestaña cerrada en índice {index}")

    def get_current_browser(self) -> QWebEngineView:
        """
        Obtiene el QWebEngineView de la pestaña actualmente activa.

        Returns:
            QWebEngineView de la pestaña activa, o None si no hay pestañas
        """
        current_index = self.tab_widget.currentIndex()
        if 0 <= current_index < len(self.tabs):
            return self.tabs[current_index]
        return None

    # ==================== Métodos Públicos ====================

    def load_url(self, url: str):
        """
        Carga una URL en la pestaña activa.

        Args:
            url: URL a cargar
        """
        browser = self.get_current_browser()
        if not browser:
            return

        # Asegurar que la URL tenga protocolo
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url

        logger.info(f"Cargando URL: {url}")

        # Iniciar timer de timeout (10 segundos)
        self.load_timer.start(10000)

        # Cargar URL en la pestaña activa
        browser.setUrl(QUrl(url))

    def reload_page(self):
        """Recarga la página de la pestaña activa."""
        browser = self.get_current_browser()
        if browser:
            logger.info("Recargando página")
            browser.reload()

    # ==================== Slots ====================

    def _on_url_entered(self):
        """Handler cuando se presiona Enter en el campo URL."""
        url = self.url_bar.text().strip()
        if url:
            self.load_url(url)

    def _on_load_started(self):
        """Handler cuando inicia la carga de la página."""
        self.is_loading = True
        self.status_label.setText("●")
        self.status_label.setStyleSheet("color: #ffaa00;")  # Naranja
        self.reload_btn.setEnabled(False)
        logger.debug("Carga iniciada")

    def _on_load_progress(self, progress: int):
        """Handler del progreso de carga."""
        logger.debug(f"Progreso de carga: {progress}%")

    def _on_load_finished(self, success: bool):
        """Handler cuando termina la carga."""
        self.is_loading = False
        self.load_timer.stop()
        self.reload_btn.setEnabled(True)

        if success:
            self.status_label.setText("●")
            self.status_label.setStyleSheet("color: #00ff00;")  # Verde
            logger.info("Página cargada exitosamente")
        else:
            self.status_label.setText("●")
            self.status_label.setStyleSheet("color: #ff0000;")  # Rojo
            logger.warning("Error al cargar la página")

    def _on_url_changed(self, url: QUrl):
        """Handler cuando cambia la URL."""
        self.url_bar.setText(url.toString())
        logger.debug(f"URL cambiada a: {url.toString()}")

    def _on_title_changed(self, title: str):
        """
        Handler cuando cambia el título de una página.
        Actualiza el título de la pestaña correspondiente.
        """
        # Encontrar qué pestaña emitió la señal
        sender_browser = self.sender()
        if sender_browser in self.tabs:
            index = self.tabs.index(sender_browser)
            # Limitar el título a 20 caracteres para que no sea muy largo
            short_title = title[:20] + "..." if len(title) > 20 else title
            self.tab_widget.setTabText(index, short_title or "Nueva pestaña")
            logger.debug(f"Título de pestaña {index} actualizado a: {short_title}")

    def _on_load_timeout(self):
        """Handler para timeout de carga."""
        if self.is_loading:
            logger.warning("Timeout de carga alcanzado")
            browser = self.get_current_browser()
            if browser:
                browser.stop()
            self.status_label.setText("●")
            self.status_label.setStyleSheet("color: #ff0000;")
            self.reload_btn.setEnabled(True)

    # ==================== Posicionamiento ====================

    def position_near_sidebar(self, sidebar_window):
        """
        Posiciona la ventana del navegador al lado del sidebar.
        Ocupa toda la altura disponible de la pantalla.

        Args:
            sidebar_window: Referencia a la ventana del sidebar (MainWindow)
        """
        # Obtener geometría del sidebar
        sidebar_x = sidebar_window.x()

        # Obtener área disponible de la pantalla (excluye taskbar)
        screen = QApplication.primaryScreen()
        screen_geometry = screen.availableGeometry()

        # Posicionar a la izquierda del sidebar con un gap de 10px
        panel_x = sidebar_x - self.width() - 10  # 10px gap
        panel_y = screen_geometry.y()  # Inicio del área disponible (normalmente 0)

        # Ajustar altura para que ocupe todo el espacio disponible
        panel_height = screen_geometry.height()

        # Aplicar posición y tamaño
        self.setGeometry(int(panel_x), panel_y, self.width(), panel_height)
        logger.debug(f"Navegador posicionado en ({panel_x}, {panel_y}) con altura {panel_height}px")

    # ==================== Redimensionamiento ====================

    def is_on_left_edge(self, pos):
        """
        Verifica si el mouse está en el borde izquierdo para redimensionar.

        Args:
            pos: Posición del mouse (QPoint)

        Returns:
            bool: True si está en el borde izquierdo
        """
        return pos.x() <= self.resize_edge_width

    def mouseMoveEvent(self, event):
        """Maneja el movimiento del mouse para redimensionamiento."""
        pos = event.pos()

        if self.resizing:
            # Redimensionar mientras se arrastra
            delta_x = event.globalPosition().x() - self.resize_start_pos.x()
            new_width = max(300, self.resize_start_width - int(delta_x))  # Mínimo 300px
            new_x = self.resize_start_x + (self.resize_start_width - new_width)

            # Aplicar nuevo tamaño y posición
            self.setGeometry(int(new_x), self.y(), new_width, self.height())
            event.accept()
        elif self.is_on_left_edge(pos):
            # Cambiar cursor a resize horizontal
            self.setCursor(Qt.CursorShape.SizeHorCursor)
        else:
            # Restaurar cursor normal
            self.setCursor(Qt.CursorShape.ArrowCursor)

        event.accept()

    def mousePressEvent(self, event):
        """Inicia el redimensionamiento al hacer click en el borde."""
        if event.button() == Qt.MouseButton.LeftButton:
            pos = event.pos()
            if self.is_on_left_edge(pos):
                # Iniciar redimensionamiento
                self.resizing = True
                self.resize_start_pos = event.globalPosition()
                self.resize_start_width = self.width()
                self.resize_start_x = self.x()
                event.accept()
                return

        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        """Finaliza el redimensionamiento."""
        if event.button() == Qt.MouseButton.LeftButton and self.resizing:
            self.resizing = False

            # Actualizar AppBar con el nuevo tamaño
            if self.appbar_registered:
                self.unregister_appbar()
                self.register_appbar()
                logger.info(f"AppBar actualizado - nuevo ancho: {self.width()}px")

            event.accept()
            return

        super().mouseReleaseEvent(event)

    # ==================== AppBar Management ====================

    def register_appbar(self):
        """
        Registra la ventana como AppBar de Windows para reservar espacio permanentemente.
        Esto empuja las ventanas maximizadas para que no cubran el navegador.
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

            # Definir el rectángulo del AppBar (para ABE_RIGHT: desde el navegador hasta el borde derecho)
            abd.rc.left = self.x()  # Borde izquierdo del navegador
            abd.rc.top = screen_geometry.y()
            abd.rc.right = screen_geometry.x() + screen_geometry.width()  # Borde derecho de la pantalla
            abd.rc.bottom = screen_geometry.y() + screen_geometry.height()

            # Registrar el AppBar
            result = ctypes.windll.shell32.SHAppBarMessage(ABM_NEW, ctypes.byref(abd))
            if result:
                logger.info("Navegador registrado como AppBar - espacio reservado en el escritorio")
                self.appbar_registered = True

                # Consultar y establecer posición para reservar espacio
                ctypes.windll.shell32.SHAppBarMessage(ABM_QUERYPOS, ctypes.byref(abd))
                ctypes.windll.shell32.SHAppBarMessage(ABM_SETPOS, ctypes.byref(abd))
            else:
                logger.warning("No se pudo registrar el navegador como AppBar")

        except Exception as e:
            logger.error(f"Error al registrar navegador como AppBar: {e}")

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
            logger.info("Navegador desregistrado como AppBar - espacio liberado")

        except Exception as e:
            logger.error(f"Error al desregistrar navegador como AppBar: {e}")

    # ==================== Eventos ====================

    def closeEvent(self, event):
        """Handler al cerrar la ventana."""
        logger.info("Cerrando SimpleBrowserWindow")

        # Desregistrar AppBar antes de cerrar
        self.unregister_appbar()

        # Detener carga en todas las pestañas si está en proceso
        if self.is_loading:
            for browser in self.tabs:
                try:
                    browser.stop()
                except:
                    pass

        # Emitir señal
        self.closed.emit()

        event.accept()
