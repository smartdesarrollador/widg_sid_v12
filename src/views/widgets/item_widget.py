"""
Item Button Widget
"""
from PyQt6.QtWidgets import QPushButton, QWidget, QHBoxLayout, QVBoxLayout, QLabel, QFrame
from PyQt6.QtCore import Qt, pyqtSignal, QSize, QTimer
from PyQt6.QtGui import QFont
import sys
import webbrowser
import os
import subprocess
import platform
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from models.item import Item, ItemType
from core.usage_tracker import UsageTracker
from core.favorites_manager import FavoritesManager
from core.file_manager import FileManager
from core.config_manager import ConfigManager
from views.command_output_dialog import CommandOutputDialog
from views.dialogs.item_details_dialog import ItemDetailsDialog
import time
import logging

logger = logging.getLogger(__name__)


class ItemButton(QFrame):
    """Custom item button widget for content panel with tags support"""

    # Signals
    item_clicked = pyqtSignal(object)
    favorite_toggled = pyqtSignal(int, bool)  # item_id, is_favorite (deprecated - kept for compatibility)
    archived_toggled = pyqtSignal(int, bool)  # item_id, is_archived (deprecated - kept for compatibility)
    url_open_requested = pyqtSignal(str)  # url to open in embedded browser

    def __init__(self, item: Item, show_category: bool = False, parent=None):
        super().__init__(parent)
        self.item = item
        self.show_category = show_category  # Show category badge in global search
        self.is_copied = False
        self.is_revealed = False  # Track if sensitive content is revealed
        self.reveal_timer = None  # Timer for auto-hide
        self.clipboard_clear_timer = None  # Timer for clipboard clearing

        # Usage tracking
        self.usage_tracker = UsageTracker()
        self.execution_start_time = None

        # Favorites management
        self.favorites_manager = FavoritesManager()

        self.init_ui()

    def _resolve_path(self, content_path: str) -> Path:
        """
        Resuelve una ruta, convirtiendo rutas relativas a absolutas si es necesario

        Args:
            content_path: Ruta desde item.content (puede ser relativa o absoluta)

        Returns:
            Path: Ruta absoluta resuelta
        """
        path = Path(content_path)

        # Si la ruta es absoluta y existe, usarla directamente
        if path.is_absolute():
            return path

        # Si es relativa, intentar construir ruta absoluta desde config
        # Formato relativo: "IMAGENES/test.jpg" o "IMAGENES\test.jpg"
        try:
            # Intentar obtener FileManager para construir ruta absoluta
            db_path = Path(__file__).parent.parent.parent.parent / "widget_sidebar.db"
            config_manager = ConfigManager(str(db_path))
            file_manager = FileManager(config_manager)

            # Convertir ruta relativa a absoluta
            absolute_path = file_manager.get_absolute_path(content_path)
            config_manager.close()

            return Path(absolute_path)

        except Exception as e:
            logger.warning(f"Could not resolve relative path '{content_path}': {e}")
            # Fallback: asumir que es ruta absoluta
            return path

    def init_ui(self):
        """Initialize button UI"""
        # Set frame properties
        self.setMinimumHeight(50)
        # Remove maximum height to allow widget to grow with content
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setSizePolicy(
            self.sizePolicy().horizontalPolicy(),
            self.sizePolicy().Policy.MinimumExpanding
        )

        # Set tooltip with description and content info
        tooltip_parts = []

        # Add description if available
        if hasattr(self.item, 'description') and self.item.description:
            tooltip_parts.append(self.item.description)

        # Add content preview for non-sensitive items
        if not self.item.is_sensitive and self.item.content:
            content_preview = self.item.content[:100]  # First 100 chars
            if len(self.item.content) > 100:
                content_preview += "..."
            if tooltip_parts:  # If there's already a description, add separator
                tooltip_parts.append("\n---\n")
            tooltip_parts.append(f"Contenido: {content_preview}")

        # Add item type
        if tooltip_parts:
            tooltip_parts.append("\n")
        tooltip_parts.append(f"Tipo: {self.item.type.value.upper()}")

        # Add file metadata if available (for PATH items with file info)
        if (self.item.type == ItemType.PATH and
            hasattr(self.item, 'file_hash') and self.item.file_hash):
            tooltip_parts.append("\n\n📦 Archivo Guardado:")

            # Original filename
            if hasattr(self.item, 'original_filename') and self.item.original_filename:
                tooltip_parts.append(f"\n📄 Nombre: {self.item.original_filename}")

            # File size
            if hasattr(self.item, 'file_size') and self.item.file_size:
                # Use Item's get_formatted_file_size if available
                if hasattr(self.item, 'get_formatted_file_size'):
                    size_str = self.item.get_formatted_file_size()
                else:
                    # Fallback to simple formatting
                    size = self.item.file_size
                    if size < 1024:
                        size_str = f"{size} B"
                    elif size < 1024 * 1024:
                        size_str = f"{size / 1024:.2f} KB"
                    elif size < 1024 * 1024 * 1024:
                        size_str = f"{size / (1024 * 1024):.2f} MB"
                    else:
                        size_str = f"{size / (1024 * 1024 * 1024):.2f} GB"
                tooltip_parts.append(f"\n💾 Tamaño: {size_str}")

            # File type with icon
            if hasattr(self.item, 'file_type') and self.item.file_type:
                # Get icon if method available
                if hasattr(self.item, 'get_file_type_icon'):
                    icon = self.item.get_file_type_icon()
                    tooltip_parts.append(f"\n{icon} Tipo: {self.item.file_type}")
                else:
                    tooltip_parts.append(f"\n📎 Tipo: {self.item.file_type}")

            # File extension
            if hasattr(self.item, 'file_extension') and self.item.file_extension:
                tooltip_parts.append(f"\n🔖 Extensión: {self.item.file_extension}")

        # Set the complete tooltip
        if tooltip_parts:
            self.setToolTip(''.join(tooltip_parts))

        # Main layout
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(15, 8, 15, 8)
        main_layout.setSpacing(10)

        # Color indicator (if item has color)
        if hasattr(self.item, 'color') and self.item.color:
            color_indicator = QLabel()
            color_indicator.setFixedSize(6, 30)  # Barra vertical delgada
            color_indicator.setStyleSheet(f"""
                QLabel {{
                    background-color: {self.item.color};
                    border-radius: 2px;
                }}
            """)
            color_indicator.setToolTip(f"Color: {self.item.color}")
            main_layout.addWidget(color_indicator)

        # Left side: Item info (label + badges + tags + stats)
        left_layout = QVBoxLayout()
        left_layout.setSpacing(5)

        # Top row: Label + Badge
        label_row = QHBoxLayout()
        label_row.setSpacing(8)

        # Item label (ofuscar si es sensible y no revelado)
        label_text = self.get_display_label()
        self.label_widget = QLabel(label_text)
        label_font = QFont()
        label_font.setPointSize(10)
        self.label_widget.setFont(label_font)
        # Enable word wrap to allow multiple lines
        self.label_widget.setWordWrap(True)
        self.label_widget.setSizePolicy(
            self.label_widget.sizePolicy().Policy.Expanding,
            self.label_widget.sizePolicy().Policy.Minimum
        )
        label_row.addWidget(self.label_widget)

        # Category badge (for global search)
        if self.show_category and hasattr(self.item, 'category_name') and self.item.category_name:
            category_badge = QLabel(f"📁 {self.item.category_name}")
            category_badge.setStyleSheet("""
                QLabel {
                    background-color: #3d3d3d;
                    color: #f093fb;
                    border-radius: 3px;
                    padding: 2px 8px;
                    font-size: 8pt;
                    font-weight: bold;
                }
            """)
            label_row.addWidget(category_badge)

        # Badge (Popular / Nuevo / Archivo Guardado)
        badge = self.get_badge()
        if badge:
            badge_label = QLabel(badge)
            badge_label.setStyleSheet("""
                QLabel {
                    background-color: transparent;
                    color: #cccccc;
                    font-size: 14pt;
                    padding: 0px;
                }
            """)
            label_row.addWidget(badge_label)

        # File badge (for PATH items with saved files)
        if (self.item.type == ItemType.PATH and
            hasattr(self.item, 'file_hash') and self.item.file_hash):
            file_badge = QLabel("📦")
            file_badge.setStyleSheet("""
                QLabel {
                    background-color: transparent;
                    color: #4CAF50;
                    font-size: 14pt;
                    padding: 0px;
                }
            """)
            file_badge.setToolTip("Archivo guardado en almacenamiento organizado")
            label_row.addWidget(file_badge)

        label_row.addStretch()
        left_layout.addLayout(label_row)

        # Tags container (only if item has tags)
        if self.item.tags and len(self.item.tags) > 0:
            tags_layout = QHBoxLayout()
            tags_layout.setContentsMargins(0, 0, 0, 0)
            tags_layout.setSpacing(5)

            for tag in self.item.tags:
                tag_label = QLabel(tag)
                tag_label.setStyleSheet("""
                    QLabel {
                        background-color: #007acc;
                        color: #ffffff;
                        border-radius: 3px;
                        padding: 2px 8px;
                        font-size: 8pt;
                    }
                """)
                tags_layout.addWidget(tag_label)

            tags_layout.addStretch()
            left_layout.addLayout(tags_layout)

        # Usage stats (use_count + last_used) - DISABLED
        # stats_text = self.get_usage_stats()
        # if stats_text:
        #     stats_label = QLabel(stats_text)
        #     stats_label.setStyleSheet("""
        #         QLabel {
        #             color: #858585;
        #             font-size: 8pt;
        #             font-style: italic;
        #             background-color: transparent;
        #             border: none;
        #         }
        #     """)
        #     stats_label.setWordWrap(True)
        #     stats_label.setSizePolicy(
        #         stats_label.sizePolicy().Policy.Expanding,
        #         stats_label.sizePolicy().Policy.Minimum
        #     )
        #     left_layout.addWidget(stats_label)

        main_layout.addLayout(left_layout, 1)

        # Favorite button removed - now available in Item Details Dialog

        # Info button (show details)
        self.info_btn = QPushButton("ℹ️")
        self.info_btn.setFixedSize(30, 30)
        self.info_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.info_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                font-size: 14pt;
            }
            QPushButton:hover {
                background-color: #3e3e42;
                border-radius: 3px;
            }
        """)
        self.info_btn.setToolTip("Ver detalles del item")
        self.info_btn.clicked.connect(self.show_details)
        main_layout.addWidget(self.info_btn)

        # Reveal button for sensitive items
        if hasattr(self.item, 'is_sensitive') and self.item.is_sensitive:
            self.reveal_button = QPushButton("👁")
            self.reveal_button.setFixedSize(35, 35)
            self.reveal_button.setStyleSheet("""
                QPushButton {
                    background-color: #cc0000;
                    color: #ffffff;
                    border: none;
                    border-radius: 4px;
                    font-size: 16pt;
                }
                QPushButton:hover {
                    background-color: #9e0000;
                }
                QPushButton:pressed {
                    background-color: #780000;
                }
            """)
            self.reveal_button.setCursor(Qt.CursorShape.PointingHandCursor)
            self.reveal_button.setToolTip("Revelar/Ocultar contenido sensible")
            self.reveal_button.clicked.connect(self.toggle_reveal)
            main_layout.addWidget(self.reveal_button)

        # Right side: Action buttons based on item type
        if self.item.type == ItemType.CODE:
            # Execute command button (only for CODE items)
            self.execute_button = QPushButton("⚡")
            self.execute_button.setFixedSize(35, 35)
            self.execute_button.setStyleSheet("""
                QPushButton {
                    background-color: #cc7a00;
                    color: #ffffff;
                    border: none;
                    border-radius: 4px;
                    font-size: 16pt;
                }
                QPushButton:hover {
                    background-color: #ff9900;
                }
                QPushButton:pressed {
                    background-color: #9e5e00;
                }
            """)
            self.execute_button.setCursor(Qt.CursorShape.PointingHandCursor)
            self.execute_button.setToolTip("Ejecutar comando")
            self.execute_button.clicked.connect(self.execute_command)
            main_layout.addWidget(self.execute_button)

        elif self.item.type == ItemType.URL:
            # URL action buttons - two buttons layout
            url_buttons_layout = QHBoxLayout()
            url_buttons_layout.setSpacing(5)

            # Open in embedded browser button
            self.open_url_button = QPushButton("🌐")
            self.open_url_button.setFixedSize(35, 35)
            self.open_url_button.setStyleSheet("""
                QPushButton {
                    background-color: #007acc;
                    color: #ffffff;
                    border: none;
                    border-radius: 4px;
                    font-size: 16pt;
                }
                QPushButton:hover {
                    background-color: #005a9e;
                }
                QPushButton:pressed {
                    background-color: #004578;
                }
            """)
            self.open_url_button.setCursor(Qt.CursorShape.PointingHandCursor)
            self.open_url_button.setToolTip("Abrir en navegador embebido")
            self.open_url_button.clicked.connect(self.open_in_browser)
            url_buttons_layout.addWidget(self.open_url_button)

            # Open in system browser button (NEW)
            self.open_external_button = QPushButton("🔗")
            self.open_external_button.setFixedSize(35, 35)
            self.open_external_button.setStyleSheet("""
                QPushButton {
                    background-color: #0078d4;
                    color: #ffffff;
                    border: none;
                    border-radius: 4px;
                    font-size: 16pt;
                }
                QPushButton:hover {
                    background-color: #106ebe;
                }
                QPushButton:pressed {
                    background-color: #005a9e;
                }
            """)
            self.open_external_button.setCursor(Qt.CursorShape.PointingHandCursor)
            self.open_external_button.setToolTip("Abrir en navegador predeterminado del sistema")
            self.open_external_button.clicked.connect(self.open_in_system_browser)
            url_buttons_layout.addWidget(self.open_external_button)

            main_layout.addLayout(url_buttons_layout)

        elif self.item.type == ItemType.PATH:
            # PATH action buttons
            path_buttons_layout = QHBoxLayout()
            path_buttons_layout.setSpacing(5)

            # Open in explorer button
            self.open_explorer_button = QPushButton("📁")
            self.open_explorer_button.setFixedSize(35, 35)
            self.open_explorer_button.setStyleSheet("""
                QPushButton {
                    background-color: #2d7d2d;
                    color: #ffffff;
                    border: none;
                    border-radius: 4px;
                    font-size: 16pt;
                }
                QPushButton:hover {
                    background-color: #236123;
                }
                QPushButton:pressed {
                    background-color: #1a4a1a;
                }
            """)
            self.open_explorer_button.setCursor(Qt.CursorShape.PointingHandCursor)
            self.open_explorer_button.setToolTip("Abrir en explorador")
            self.open_explorer_button.clicked.connect(self.open_in_explorer)
            path_buttons_layout.addWidget(self.open_explorer_button)

            # Open file button (only if it's a file, not a directory)
            # Resolver ruta (relativa -> absoluta si es necesario)
            path = self._resolve_path(self.item.content)
            if path.exists() and path.is_file():
                self.open_file_button = QPushButton("📝")
                self.open_file_button.setFixedSize(35, 35)
                self.open_file_button.setStyleSheet("""
                    QPushButton {
                        background-color: #cc7a00;
                        color: #ffffff;
                        border: none;
                        border-radius: 4px;
                        font-size: 16pt;
                    }
                    QPushButton:hover {
                        background-color: #9e5e00;
                    }
                    QPushButton:pressed {
                        background-color: #784500;
                    }
                """)
                self.open_file_button.setCursor(Qt.CursorShape.PointingHandCursor)
                self.open_file_button.setToolTip("Abrir archivo")
                self.open_file_button.clicked.connect(self.open_file)
                path_buttons_layout.addWidget(self.open_file_button)

            main_layout.addLayout(path_buttons_layout)

        # Set initial style (different for sensitive items and file items)
        if hasattr(self.item, 'is_sensitive') and self.item.is_sensitive:
            self.setStyleSheet("""
                QFrame {
                    background-color: #3d2020;
                    border: none;
                    border-left: 3px solid #cc0000;
                    border-bottom: 1px solid #1e1e1e;
                }
                QFrame:hover {
                    background-color: #4d2525;
                }
                QLabel {
                    color: #cccccc;
                    background-color: transparent;
                    border: none;
                }
            """)
        elif (self.item.type == ItemType.PATH and
              hasattr(self.item, 'file_hash') and self.item.file_hash):
            # Special style for PATH items with saved files
            self.setStyleSheet("""
                QFrame {
                    background-color: #2d2d2d;
                    border: none;
                    border-left: 3px solid #4CAF50;
                    border-bottom: 1px solid #1e1e1e;
                }
                QFrame:hover {
                    background-color: #3d3d3d;
                }
                QLabel {
                    color: #cccccc;
                    background-color: transparent;
                    border: none;
                }
            """)
        else:
            self.setStyleSheet("""
                QFrame {
                    background-color: #2d2d2d;
                    border: none;
                    border-bottom: 1px solid #1e1e1e;
                }
                QFrame:hover {
                    background-color: #3d3d3d;
                }
                QLabel {
                    color: #cccccc;
                    background-color: transparent;
                    border: none;
                }
            """)

    def mousePressEvent(self, event):
        """Handle mouse press event"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.on_clicked()
        super().mousePressEvent(event)

    def on_clicked(self):
        """Handle button click"""
        # Track clipboard copy (comando simple)
        if self.item.type not in [ItemType.URL, ItemType.PATH]:
            start_time = self.usage_tracker.track_execution_start(self.item.id)

        # Emit signal with item
        self.item_clicked.emit(self.item)

        # Show copied feedback
        self.show_copied_feedback()

        # Track completion for clipboard copy
        if self.item.type not in [ItemType.URL, ItemType.PATH]:
            self.usage_tracker.track_execution_end(self.item.id, start_time, True, None)

        # If sensitive item, start clipboard auto-clear timer
        if hasattr(self.item, 'is_sensitive') and self.item.is_sensitive:
            self.start_clipboard_clear_timer()

    def open_in_browser(self):
        """Open URL in embedded browser"""
        if self.item.type == ItemType.URL:
            # Track execution start
            start_time = self.usage_tracker.track_execution_start(self.item.id)
            success = False
            error_msg = None

            try:
                url = self.item.content
                # Ensure URL has proper protocol
                if not url.startswith(('http://', 'https://')):
                    if url.startswith('www.'):
                        url = 'https://' + url
                    else:
                        url = 'https://' + url

                # Emit signal to open in embedded browser
                self.url_open_requested.emit(url)
                success = True
                logger.info(f"URL open requested in embedded browser: {url}")

                # Update button style briefly to show it was clicked
                original_style = self.open_url_button.styleSheet()
                self.open_url_button.setStyleSheet("""
                    QPushButton {
                        background-color: #00ff00;
                        color: #ffffff;
                        border: none;
                        border-radius: 4px;
                        font-size: 16pt;
                    }
                """)
                QTimer.singleShot(300, lambda: self.open_url_button.setStyleSheet(original_style))

            except Exception as e:
                logger.error(f"Error opening URL {self.item.label}: {e}")
                error_msg = str(e)

            finally:
                # Track execution end
                self.usage_tracker.track_execution_end(self.item.id, start_time, success, error_msg)

    def open_in_system_browser(self):
        """Open URL in system default browser (Chrome, Firefox, Edge, etc.)"""
        if self.item.type == ItemType.URL:
            # Track execution start
            start_time = self.usage_tracker.track_execution_start(self.item.id)
            success = False
            error_msg = None

            try:
                url = self.item.content
                # Ensure URL has proper protocol
                if not url.startswith(('http://', 'https://')):
                    if url.startswith('www.'):
                        url = 'https://' + url
                    else:
                        url = 'https://' + url

                # Open in system default browser
                webbrowser.open(url)
                success = True
                logger.info(f"URL opened in system browser: {url}")

                # Update button style briefly to show it was clicked
                original_style = self.open_external_button.styleSheet()
                self.open_external_button.setStyleSheet("""
                    QPushButton {
                        background-color: #00ff00;
                        color: #ffffff;
                        border: none;
                        border-radius: 4px;
                        font-size: 16pt;
                    }
                """)
                QTimer.singleShot(300, lambda: self.open_external_button.setStyleSheet(original_style))

            except Exception as e:
                logger.error(f"Error opening URL in system browser {self.item.label}: {e}")
                error_msg = str(e)

            finally:
                # Track execution end
                self.usage_tracker.track_execution_end(self.item.id, start_time, success, error_msg)

    def open_in_explorer(self):
        """Open file/folder in system file explorer"""
        if self.item.type == ItemType.PATH:
            # Track execution start
            start_time = self.usage_tracker.track_execution_start(self.item.id)
            success = False
            error_msg = None

            try:
                # Resolver ruta (relativa -> absoluta si es necesario)
                path = self._resolve_path(self.item.content)
                system = platform.system()

                if system == 'Windows':
                    # Windows: Use explorer with /select to highlight the file/folder
                    if path.exists():
                        subprocess.run(['explorer', '/select,', str(path.absolute())])
                    else:
                        # If path doesn't exist, try to open parent directory
                        parent = path.parent
                        if parent.exists():
                            subprocess.run(['explorer', str(parent.absolute())])

                elif system == 'Darwin':  # macOS
                    if path.exists():
                        subprocess.run(['open', '-R', str(path.absolute())])
                    else:
                        parent = path.parent
                        if parent.exists():
                            subprocess.run(['open', str(parent.absolute())])

                else:  # Linux
                    if path.exists():
                        if path.is_file():
                            subprocess.run(['xdg-open', str(path.parent.absolute())])
                        else:
                            subprocess.run(['xdg-open', str(path.absolute())])
                    else:
                        parent = path.parent
                        if parent.exists():
                            subprocess.run(['xdg-open', str(parent.absolute())])

                success = True

                # Visual feedback
                original_style = self.open_explorer_button.styleSheet()
                self.open_explorer_button.setStyleSheet("""
                    QPushButton {
                        background-color: #00ff00;
                        color: #ffffff;
                        border: none;
                        border-radius: 4px;
                        font-size: 16pt;
                    }
                """)
                QTimer.singleShot(300, lambda: self.open_explorer_button.setStyleSheet(original_style))

            except Exception as e:
                logger.error(f"Error opening explorer for {self.item.label}: {e}")
                error_msg = str(e)

            finally:
                # Track execution end
                self.usage_tracker.track_execution_end(self.item.id, start_time, success, error_msg)

    def open_file(self):
        """Open file with default application"""
        if self.item.type == ItemType.PATH:
            # Resolver ruta (relativa -> absoluta si es necesario)
            path = self._resolve_path(self.item.content)

            if not path.exists() or not path.is_file():
                logger.warning(f"File not found: {path}")
                return

            try:
                system = platform.system()

                if system == 'Windows':
                    # Windows: Use os.startfile
                    os.startfile(str(path.absolute()))

                elif system == 'Darwin':  # macOS
                    subprocess.run(['open', str(path.absolute())])

                else:  # Linux
                    subprocess.run(['xdg-open', str(path.absolute())])

                # Visual feedback
                original_style = self.open_file_button.styleSheet()
                self.open_file_button.setStyleSheet("""
                    QPushButton {
                        background-color: #00ff00;
                        color: #ffffff;
                        border: none;
                        border-radius: 4px;
                        font-size: 16pt;
                    }
                """)
                QTimer.singleShot(300, lambda: self.open_file_button.setStyleSheet(original_style))

            except Exception as e:
                print(f"Error opening file: {e}")

    def show_copied_feedback(self):
        """Show visual feedback that item was copied"""
        self.is_copied = True

        # Different style for sensitive items (orange/warning color)
        if hasattr(self.item, 'is_sensitive') and self.item.is_sensitive:
            self.setStyleSheet("""
                QFrame {
                    background-color: #cc7a00;
                    border: none;
                    border-bottom: 1px solid #9e5e00;
                }
                QLabel {
                    color: #ffffff;
                    background-color: transparent;
                    border: none;
                    font-weight: bold;
                }
            """)
        else:
            # Normal items: blue feedback
            self.setStyleSheet("""
                QFrame {
                    background-color: #007acc;
                    border: none;
                    border-bottom: 1px solid #005a9e;
                }
                QLabel {
                    color: #ffffff;
                    background-color: transparent;
                    border: none;
                    font-weight: bold;
                }
            """)

        # Reset after 500ms
        QTimer.singleShot(500, self.reset_style)

    def reset_style(self):
        """Reset button style to normal"""
        self.is_copied = False
        # Apply special style for sensitive items
        if hasattr(self.item, 'is_sensitive') and self.item.is_sensitive:
            self.setStyleSheet("""
                QFrame {
                    background-color: #3d2020;
                    border: none;
                    border-left: 3px solid #cc0000;
                    border-bottom: 1px solid #1e1e1e;
                }
                QFrame:hover {
                    background-color: #4d2525;
                }
                QLabel {
                    color: #cccccc;
                    background-color: transparent;
                    border: none;
                }
            """)
        elif (self.item.type == ItemType.PATH and
              hasattr(self.item, 'file_hash') and self.item.file_hash):
            # Special style for PATH items with saved files
            self.setStyleSheet("""
                QFrame {
                    background-color: #2d2d2d;
                    border: none;
                    border-left: 3px solid #4CAF50;
                    border-bottom: 1px solid #1e1e1e;
                }
                QFrame:hover {
                    background-color: #3d3d3d;
                }
                QLabel {
                    color: #cccccc;
                    background-color: transparent;
                    border: none;
                }
            """)
        else:
            self.setStyleSheet("""
                QFrame {
                    background-color: #2d2d2d;
                    border: none;
                    border-bottom: 1px solid #1e1e1e;
                }
                QFrame:hover {
                    background-color: #3d3d3d;
                }
                QLabel {
                    color: #cccccc;
                    background-color: transparent;
                    border: none;
                }
            """)

    def get_display_label(self):
        """Get display label (ofuscado si es sensible y no revelado)"""
        # Get file type icon if this is a PATH item with file metadata
        file_icon = ""
        if (self.item.type == ItemType.PATH and
            hasattr(self.item, 'file_hash') and self.item.file_hash and
            hasattr(self.item, 'get_file_type_icon')):
            file_icon = self.item.get_file_type_icon() + " "

        if hasattr(self.item, 'is_sensitive') and self.item.is_sensitive and not self.is_revealed:
            # Ofuscar: mostrar label + (********)
            content_preview = "********"
            return f"{file_icon}{self.item.label} ({content_preview})"
        elif hasattr(self.item, 'is_sensitive') and self.item.is_sensitive and self.is_revealed:
            # Revelado: mostrar label + preview del contenido
            content = self.item.content[:30] if len(self.item.content) > 30 else self.item.content
            return f"{file_icon}{self.item.label} ({content}...)" if len(self.item.content) > 30 else f"{file_icon}{self.item.label} ({content})"
        else:
            # Item normal: solo el label (con icono de archivo si aplica)
            return f"{file_icon}{self.item.label}"

    def toggle_reveal(self):
        """Toggle reveal/hide sensitive content"""
        self.is_revealed = not self.is_revealed

        # Update label
        self.label_widget.setText(self.get_display_label())

        if self.is_revealed:
            # Cambiar icono del boton
            self.reveal_button.setText("🙈")
            self.reveal_button.setToolTip("Ocultar contenido sensible")

            # Cancelar timer anterior si existe
            if self.reveal_timer:
                self.reveal_timer.stop()

            # Auto-ocultar despues de 10 segundos
            self.reveal_timer = QTimer()
            self.reveal_timer.setSingleShot(True)
            self.reveal_timer.timeout.connect(self.auto_hide)
            self.reveal_timer.start(10000)  # 10 segundos
        else:
            # Cambiar icono del boton
            self.reveal_button.setText("👁")
            self.reveal_button.setToolTip("Revelar/Ocultar contenido sensible")

            # Cancelar timer si existe
            if self.reveal_timer:
                self.reveal_timer.stop()

    def auto_hide(self):
        """Auto-hide sensitive content after timeout"""
        if self.is_revealed:
            self.toggle_reveal()

    def start_clipboard_clear_timer(self):
        """Start timer to clear clipboard after 30 seconds for sensitive items"""
        # Cancel previous timer if exists
        if self.clipboard_clear_timer:
            self.clipboard_clear_timer.stop()

        # Start 30-second timer
        self.clipboard_clear_timer = QTimer()
        self.clipboard_clear_timer.setSingleShot(True)
        self.clipboard_clear_timer.timeout.connect(self.clear_clipboard)
        self.clipboard_clear_timer.start(30000)  # 30 seconds

    def clear_clipboard(self):
        """Clear clipboard content"""
        try:
            import pyperclip
            pyperclip.copy("")  # Clear clipboard
        except Exception as e:
            print(f"Error clearing clipboard: {e}")

    def update_favorite_button(self):
        """Actualizar icono del botón de favorito"""
        is_fav = self.favorites_manager.is_favorite(self.item.id)

        if is_fav:
            self.favorite_btn.setText("⭐")
            self.favorite_btn.setToolTip("Quitar de favoritos")
        else:
            self.favorite_btn.setText("☆")
            self.favorite_btn.setToolTip("Marcar como favorito")

    def toggle_favorite(self):
        """Alternar estado de favorito"""
        try:
            is_fav = self.favorites_manager.toggle_favorite(self.item.id)

            # Actualizar botón
            self.update_favorite_button()

            # Emitir señal
            self.favorite_toggled.emit(self.item.id, is_fav)

            # Log
            msg = "agregado a" if is_fav else "quitado de"
            logger.info(f"Item '{self.item.label}' {msg} favoritos")

        except Exception as e:
            logger.error(f"Error toggling favorite for item {self.item.id}: {e}")

    def get_badge(self) -> str:
        """Obtener badge del item (🔥 Popular)"""
        use_count = getattr(self.item, 'use_count', 0)

        # Popular: más de 50 usos
        if use_count > 50:
            return "🔥"

        # Badge "Nuevo" deshabilitado
        return ""

    def get_usage_stats(self) -> str:
        """Obtener estadísticas de uso (use_count + last_used)"""
        use_count = getattr(self.item, 'use_count', 0)
        last_used = getattr(self.item, 'last_used', None)

        parts = []

        # Use count
        if use_count > 0:
            parts.append(f"{use_count} usos")
        else:
            parts.append("Sin usar")

        # Last used
        if last_used:
            from datetime import datetime
            try:
                # Parse SQLite datetime format: YYYY-MM-DD HH:MM:SS
                # Si ya es datetime, usarlo directamente
                if isinstance(last_used, datetime):
                    last_used_dt = last_used
                else:
                    last_used_dt = datetime.strptime(str(last_used), "%Y-%m-%d %H:%M:%S")

                now = datetime.now()
                diff = now - last_used_dt

                # Format relative time
                if diff.days == 0:
                    if diff.seconds < 60:
                        time_str = "hace unos segundos"
                    elif diff.seconds < 3600:
                        minutes = diff.seconds // 60
                        time_str = f"hace {minutes} min"
                    else:
                        hours = diff.seconds // 3600
                        time_str = f"hace {hours}h"
                elif diff.days == 1:
                    time_str = "ayer"
                elif diff.days < 7:
                    time_str = f"hace {diff.days} días"
                elif diff.days < 30:
                    weeks = diff.days // 7
                    time_str = f"hace {weeks} semanas"
                else:
                    months = diff.days // 30
                    time_str = f"hace {months} meses"

                parts.append(f"último: {time_str}")
            except Exception as e:
                logger.debug(f"Error parsing last_used date: {e}")

        return " | ".join(parts) if parts else ""

    def show_details(self):
        """Mostrar ventana de detalles del item"""
        try:
            # Find the FloatingPanel or GlobalSearchPanel parent to pass to dialog
            refresh_panel = None
            parent_widget = self.parent()
            while parent_widget:
                class_name = parent_widget.__class__.__name__
                if class_name in ('FloatingPanel', 'GlobalSearchPanel', 'FavoritesFloatingPanel'):
                    refresh_panel = parent_widget
                    break
                parent_widget = parent_widget.parent()

            dialog = ItemDetailsDialog(self.item, floating_panel=refresh_panel, parent=self.window())
            dialog.exec()
        except Exception as e:
            logger.error(f"Error showing item details: {e}")

    def execute_command(self):
        """Ejecutar comando de tipo CODE"""
        if self.item.type != ItemType.CODE:
            return

        # Track execution start
        start_time = self.usage_tracker.track_execution_start(self.item.id)
        success = False
        error_msg = None

        try:
            command = self.item.content.strip()

            # Visual feedback - cambiar botón a amarillo mientras ejecuta
            original_style = self.execute_button.styleSheet()
            self.execute_button.setStyleSheet("""
                QPushButton {
                    background-color: #ffff00;
                    color: #000000;
                    border: none;
                    border-radius: 4px;
                    font-size: 16pt;
                }
            """)
            self.execute_button.setText("⏳")

            # Ejecutar comando usando subprocess
            # En Windows, necesitamos usar shell=True para comandos como 'dir', 'git', etc.
            system = platform.system()

            # Determinar directorio de trabajo
            cwd = None
            if hasattr(self.item, 'working_dir') and self.item.working_dir:
                from pathlib import Path
                working_dir_path = Path(self.item.working_dir)
                if working_dir_path.exists() and working_dir_path.is_dir():
                    cwd = str(working_dir_path.absolute())
                    logger.info(f"Executing command in working directory: {cwd}")
                else:
                    logger.warning(f"Working directory does not exist: {self.item.working_dir}")

            if system == 'Windows':
                # En Windows, usar cmd.exe para ejecutar el comando
                result = subprocess.run(
                    command,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=30,  # Timeout de 30 segundos
                    cwd=cwd  # Directorio de trabajo
                )
            else:
                # En Unix-like systems, usar bash
                result = subprocess.run(
                    command,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=30,
                    executable='/bin/bash',
                    cwd=cwd  # Directorio de trabajo
                )

            # Obtener output y error
            stdout = result.stdout if result.stdout else ""
            stderr = result.stderr if result.stderr else ""
            return_code = result.returncode

            # Considerar éxito si return code es 0
            success = (return_code == 0)

            # Restaurar botón
            self.execute_button.setText("⚡")
            if success:
                # Verde si éxito
                self.execute_button.setStyleSheet("""
                    QPushButton {
                        background-color: #00ff00;
                        color: #000000;
                        border: none;
                        border-radius: 4px;
                        font-size: 16pt;
                    }
                """)
            else:
                # Rojo si error
                self.execute_button.setStyleSheet("""
                    QPushButton {
                        background-color: #ff0000;
                        color: #ffffff;
                        border: none;
                        border-radius: 4px;
                        font-size: 16pt;
                    }
                """)
                error_msg = stderr if stderr else "Error desconocido"

            # Restaurar estilo original después de 1 segundo
            QTimer.singleShot(1000, lambda: self.execute_button.setStyleSheet(original_style))

            # Mostrar dialog con el resultado
            dialog = CommandOutputDialog(
                command=command,
                output=stdout,
                error=stderr,
                return_code=return_code,
                parent=self.window()
            )
            dialog.exec()

        except subprocess.TimeoutExpired:
            logger.error(f"Command timeout: {self.item.label}")
            error_msg = "Comando excedió el tiempo de espera (30 segundos)"

            # Restaurar botón con estilo de error
            self.execute_button.setText("⚡")
            self.execute_button.setStyleSheet("""
                QPushButton {
                    background-color: #ff0000;
                    color: #ffffff;
                    border: none;
                    border-radius: 4px;
                    font-size: 16pt;
                }
            """)
            QTimer.singleShot(1000, lambda: self.execute_button.setStyleSheet(original_style))

            # Mostrar dialog de error
            dialog = CommandOutputDialog(
                command=command,
                output="",
                error=error_msg,
                return_code=-1,
                parent=self.window()
            )
            dialog.exec()

        except Exception as e:
            logger.error(f"Error executing command {self.item.label}: {e}")
            error_msg = str(e)

            # Restaurar botón con estilo de error
            self.execute_button.setText("⚡")
            self.execute_button.setStyleSheet("""
                QPushButton {
                    background-color: #ff0000;
                    color: #ffffff;
                    border: none;
                    border-radius: 4px;
                    font-size: 16pt;
                }
            """)
            QTimer.singleShot(1000, lambda: self.execute_button.setStyleSheet(original_style))

            # Mostrar dialog de error
            dialog = CommandOutputDialog(
                command=command if 'command' in locals() else self.item.content,
                output="",
                error=error_msg,
                return_code=-1,
                parent=self.window()
            )
            dialog.exec()

        finally:
            # Track execution end
            self.usage_tracker.track_execution_end(self.item.id, start_time, success, error_msg)
