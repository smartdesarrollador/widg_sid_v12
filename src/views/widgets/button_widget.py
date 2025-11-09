"""
Category Button Widget
"""
from PyQt6.QtWidgets import QPushButton
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QFont
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from styles.futuristic_theme import get_theme


class CategoryButton(QPushButton):
    """Custom category button widget for sidebar"""

    def __init__(self, category_id: str, category_name: str, parent=None):
        super().__init__(parent)
        self.category_id = category_id
        self.category_name = category_name
        self.is_active = False
        self.theme = get_theme()  # Obtener tema futurista

        self.init_ui()

    def init_ui(self):
        """Initialize button UI"""
        # Set button text
        self.setText(self.category_name)

        # Set tooltip with full category name
        self.setToolTip(self.category_name)

        # Set fixed size - Altura reducida para visualizar más categorías
        self.setFixedSize(70, 45)

        # Set font
        font = QFont()
        font.setPointSize(9)
        font.setBold(False)
        self.setFont(font)

        # Enable cursor change on hover
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        # Apply default style
        self.update_style()

    def update_style(self):
        """Update button style based on state"""
        if self.is_active:
            self.setStyleSheet(f"""
                QPushButton {{
                    background-color: {self.theme.get_color('background_deep')};
                    color: {self.theme.get_color('text_primary')};
                    border: none;
                    border-left: 3px solid {self.theme.get_color('accent')};
                    padding: 5px;
                    text-align: center;
                    font-weight: bold;
                }}
                QPushButton:hover {{
                    background: qlineargradient(
                        x1:0, y1:0, x2:1, y2:0,
                        stop:0 {self.theme.get_color('secondary')},
                        stop:1 transparent
                    );
                    border-left: 3px solid {self.theme.get_color('primary')};
                }}
            """)
        else:
            self.setStyleSheet(f"""
                QPushButton {{
                    background-color: transparent;
                    color: {self.theme.get_color('text_secondary')};
                    border: none;
                    border-left: 3px solid transparent;
                    padding: 5px;
                    text-align: center;
                }}
                QPushButton:hover {{
                    background-color: {self.theme.get_color('surface')};
                    color: {self.theme.get_color('text_primary')};
                    border-left: 3px solid {self.theme.get_color('primary')};
                }}
                QPushButton:pressed {{
                    background: qlineargradient(
                        x1:0, y1:0, x2:1, y2:0,
                        stop:0 {self.theme.get_color('primary')},
                        stop:1 transparent
                    );
                }}
            """)

    def set_active(self, active: bool):
        """Set button active state"""
        self.is_active = active
        self.update_style()

    def sizeHint(self) -> QSize:
        """Recommended size"""
        return QSize(70, 45)
