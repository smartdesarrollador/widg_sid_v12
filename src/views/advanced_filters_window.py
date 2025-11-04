"""
Advanced Filters Window - Ventana flotante independiente para filtros avanzados
"""
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QHBoxLayout, QLabel
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QCursor
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from views.widgets.advanced_filter_panel import AdvancedFilterPanel


class AdvancedFiltersWindow(QWidget):
    """Ventana flotante independiente para filtros avanzados"""

    # Señales
    filters_changed = pyqtSignal(dict)  # Emite filtros al panel principal
    filters_cleared = pyqtSignal()
    window_closed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.drag_position = None  # Inicializar posición de arrastre
        self.init_ui()

    def init_ui(self):
        """Inicializar la interfaz de la ventana"""
        # Window properties
        self.setWindowTitle("Filtros Avanzados")
        self.setWindowFlags(
            Qt.WindowType.Window |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.FramelessWindowHint
        )

        # Set window size
        self.setFixedSize(400, 800)  # Aumentado de 700 a 800

        # Set window opacity
        self.setWindowOpacity(0.95)

        # Set background
        self.setStyleSheet("""
            AdvancedFiltersWindow {
                background-color: #252525;
                border: 2px solid #007acc;
                border-radius: 8px;
            }
        """)

        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Header con título y botón de cerrar
        header_widget = QWidget()
        header_widget.setStyleSheet("""
            QWidget {
                background-color: #007acc;
                border-radius: 6px 6px 0 0;
            }
        """)
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(15, 10, 10, 10)
        header_layout.setSpacing(5)

        # Título
        title_label = QLabel("🔍 Filtros Avanzados")
        title_label.setStyleSheet("""
            QLabel {
                background-color: transparent;
                color: #ffffff;
                font-size: 12pt;
                font-weight: bold;
            }
        """)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(title_label)

        # Botón cerrar
        close_button = QPushButton("✕")
        close_button.setFixedSize(24, 24)
        close_button.setCursor(Qt.CursorShape.PointingHandCursor)
        close_button.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 255, 255, 0.1);
                color: #ffffff;
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 12px;
                font-size: 12pt;
                font-weight: bold;
                padding: 0px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.2);
                border: 1px solid rgba(255, 255, 255, 0.4);
            }
            QPushButton:pressed {
                background-color: rgba(255, 255, 255, 0.3);
            }
        """)
        close_button.clicked.connect(self.hide)
        header_layout.addWidget(close_button)

        main_layout.addWidget(header_widget)

        # Panel de filtros (reutilizamos el existente)
        self.filter_panel = AdvancedFilterPanel()
        self.filter_panel.filters_changed.connect(self.on_filters_changed)
        self.filter_panel.filters_cleared.connect(self.on_filters_cleared)

        # Forzar que el panel esté siempre expandido en esta ventana
        self.filter_panel.is_expanded = True
        self.filter_panel.expand_icon.setText("🔽")
        self.filter_panel.content_widget.setMaximumHeight(750)  # Aumentado de 650 a 750

        # Deshabilitar el click en el header (mantener siempre expandido)
        self.filter_panel.header_widget.mousePressEvent = lambda event: None

        main_layout.addWidget(self.filter_panel)

    def update_available_tags(self, items):
        """Actualizar tags disponibles desde los items"""
        self.filter_panel.update_available_tags(items)

    def on_filters_changed(self, filters):
        """Reenviar señal de filtros cambiados"""
        self.filters_changed.emit(filters)

    def on_filters_cleared(self):
        """Reenviar señal de filtros limpiados"""
        self.filters_cleared.emit()

    def position_near_panel(self, floating_panel):
        """Posicionar la ventana cerca del panel flotante"""
        # Obtener posición del panel flotante
        panel_x = floating_panel.x()
        panel_y = floating_panel.y()
        panel_width = floating_panel.width()

        # Posicionar a la izquierda del panel flotante
        window_x = panel_x - self.width() - 10  # 10px gap
        window_y = panel_y

        self.move(window_x, window_y)

    def mousePressEvent(self, event):
        """Handle mouse press para arrastrar la ventana"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        """Handle mouse move para arrastrar la ventana"""
        if event.buttons() == Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()

    def closeEvent(self, event):
        """Handle window close event"""
        self.window_closed.emit()
        event.accept()
