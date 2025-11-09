"""
Stats Floating Panel - Panel flotante para mostrar estadísticas
"""
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QHBoxLayout
from PyQt6.QtCore import Qt, pyqtSignal, QEvent
from PyQt6.QtGui import QFont, QCursor
import sys
import logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from views.widgets.stats_widget import StatsWidget
from styles.futuristic_theme import get_theme
from styles.animations import AnimationSystem, AnimationDurations

logger = logging.getLogger(__name__)


class StatsFloatingPanel(QWidget):
    """Panel flotante para estadísticas"""

    # Señales
    window_closed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.theme = get_theme()  # Tema futurista
        self.animation_system = AnimationSystem()  # Sistema de animaciones

        # Resize handling
        self.resizing = False
        self.resize_start_x = 0
        self.resize_start_width = 0
        self.resize_edge_width = 15

        # Flag para controlar si es la primera vez que se muestra
        self._first_show = True

        self.init_ui()

    def init_ui(self):
        """Inicializar UI"""
        # Window properties
        self.setWindowTitle("📊 Estadísticas")
        self.setWindowFlags(
            Qt.WindowType.Window |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.FramelessWindowHint
        )

        # Tamaño
        self.setMinimumWidth(250)
        self.setMaximumWidth(500)
        self.setFixedHeight(350)
        self.resize(280, 350)
        self.setWindowOpacity(0.95)
        self.setMouseTracking(True)
        self.setAttribute(Qt.WidgetAttribute.WA_Hover, True)

        # Layout principal
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Header con gradiente futurista
        header = QWidget()
        header.setStyleSheet(self.theme.get_header_style())
        header_layout = QVBoxLayout(header)
        header_layout.setContentsMargins(15, 15, 15, 10)

        # Título
        title = QLabel("📊 ESTADÍSTICAS")
        title.setStyleSheet(self.theme.get_label_style('title'))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(title)

        # Botón cerrar
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)

        close_btn = QPushButton("✕ Cerrar")
        close_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: rgba(255, 255, 255, 0.15);
                color: {self.theme.get_color('text_primary')};
                border: 1px solid rgba(255, 255, 255, 0.3);
                padding: 6px 12px;
                border-radius: 4px;
                font-size: 9pt;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background-color: {self.theme.get_color('error')};
                border-color: {self.theme.get_color('error')};
            }}
            QPushButton:pressed {{
                background-color: rgba(255, 50, 50, 0.7);
            }}
        """)
        close_btn.clicked.connect(self.close)
        btn_layout.addStretch()
        btn_layout.addWidget(close_btn)
        btn_layout.addStretch()

        header_layout.addLayout(btn_layout)
        main_layout.addWidget(header)

        # Stats widget con glassmorphism
        self.stats_widget = StatsWidget(self)
        self.stats_widget.setStyleSheet(f"""
            QWidget#stats_widget {{
                background-color: {self.theme.get_color('background_deep')};
                border: none;
                border-radius: 0 0 10px 10px;
            }}
        """)
        main_layout.addWidget(self.stats_widget)

        # Borde del panel con glassmorphism
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {self.theme.get_color('background_deep')};
                border: 2px solid {self.theme.get_color('primary')};
                border-radius: 12px;
            }}
        """)

    def refresh(self):
        """Refrescar estadísticas"""
        self.stats_widget.refresh()

    def position_near_sidebar(self, sidebar_window):
        """Posicionar cerca del sidebar - a la izquierda"""
        sidebar_geo = sidebar_window.geometry()
        # Posicionar a la izquierda del sidebar
        x = sidebar_geo.x() - self.width() - 5
        y = sidebar_geo.y()
        self.move(x, y)

    def showEvent(self, event):
        """Handler al mostrar ventana - aplicar animación"""
        super().showEvent(event)

        if self._first_show:
            self._first_show = False
            # Aplicar animación combinada de fade + slide desde la izquierda
            animation = self.animation_system.combined_fade_slide(
                self,
                duration=AnimationDurations.NORMAL,
                direction='left',
                distance=50
            )
            animation.start()
            # Guardar referencia para que no se destruya
            self._show_animation = animation

    def closeEvent(self, event):
        """Handler al cerrar ventana"""
        self.window_closed.emit()
        super().closeEvent(event)

    def is_on_left_edge(self, pos):
        """Check if mouse position is on the left edge for resizing"""
        return pos.x() <= self.resize_edge_width

    def event(self, event):
        """Override event to handle hover for cursor changes"""
        if event.type() == QEvent.Type.HoverMove:
            pos = event.position().toPoint()
            if self.is_on_left_edge(pos):
                self.setCursor(QCursor(Qt.CursorShape.SizeHorCursor))
            else:
                self.setCursor(QCursor(Qt.CursorShape.ArrowCursor))
        return super().event(event)

    def mousePressEvent(self, event):
        """Handler para poder mover la ventana o redimensionarla"""
        if event.button() == Qt.MouseButton.LeftButton:
            if self.is_on_left_edge(event.pos()):
                # Start resizing
                self.resizing = True
                self.resize_start_x = event.globalPosition().toPoint().x()
                self.resize_start_width = self.width()
                event.accept()
            else:
                # Start dragging
                self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
                event.accept()

    def mouseMoveEvent(self, event):
        """Handler para mover o redimensionar la ventana"""
        if event.buttons() == Qt.MouseButton.LeftButton:
            if self.resizing:
                # Calculate new width
                current_x = event.globalPosition().toPoint().x()
                delta_x = current_x - self.resize_start_x
                new_width = self.resize_start_width - delta_x

                # Apply constraints
                new_width = max(self.minimumWidth(), min(new_width, self.maximumWidth()))

                # Resize and reposition
                old_width = self.width()
                old_x = self.x()
                self.resize(new_width, self.height())

                # Adjust position to keep right edge fixed
                width_diff = self.width() - old_width
                self.move(old_x - width_diff, self.y())

                event.accept()
            else:
                # Dragging
                self.move(event.globalPosition().toPoint() - self.drag_position)
                event.accept()

    def mouseReleaseEvent(self, event):
        """Handle mouse release to end resizing"""
        if event.button() == Qt.MouseButton.LeftButton:
            if self.resizing:
                self.resizing = False
                event.accept()
