"""AI Bulk Creation Step - Paso 5: Creación masiva de items"""
import sys
from pathlib import Path
import logging
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QProgressBar, QTextEdit
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from core.ai_bulk_manager import AIBulkItemManager
from models.bulk_item_data import BulkItemData

logger = logging.getLogger(__name__)

class CreationStep(QWidget):
    """Step 5: Creación masiva con progress y resultado"""

    def __init__(self, manager: AIBulkItemManager, parent=None):
        super().__init__(parent)
        self.manager = manager
        self.items = []
        self.category_id = None
        self.result = None
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)

        # Título
        title = QLabel("✨ Creando Items...")
        font = QFont()
        font.setPointSize(14)
        font.setBold(True)
        title.setFont(font)
        title.setStyleSheet("color: #00d4ff;")
        layout.addWidget(title, alignment=Qt.AlignmentFlag.AlignCenter)

        # Progress bar
        self.progress = QProgressBar()
        self.progress.setStyleSheet("""
            QProgressBar {
                border: 2px solid #3d3d3d;
                border-radius: 5px;
                text-align: center;
                background-color: #1e1e1e;
                color: #ffffff;
                font-size: 12pt;
                font-weight: bold;
            }
            QProgressBar::chunk {
                background-color: #00d4ff;
                border-radius: 3px;
            }
        """)
        self.progress.setMinimum(0)
        self.progress.setMaximum(100)
        self.progress.setValue(0)
        self.progress.setFixedHeight(40)
        layout.addWidget(self.progress)

        # Status label
        self.status_label = QLabel("Listo para crear items...")
        self.status_label.setStyleSheet("color: #888888; font-size: 11pt;")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_label)

        # Log
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #00ff88;
                border: 1px solid #3d3d3d;
                border-radius: 3px;
                padding: 10px;
                font-family: Consolas, monospace;
                font-size: 10pt;
            }
        """)
        layout.addWidget(self.log_text)

        # Summary
        self.summary_label = QLabel()
        self.summary_label.setWordWrap(True)
        self.summary_label.setStyleSheet("""
            QLabel {
                background-color: #1e3a1e;
                color: #00ff88;
                border-left: 4px solid #00ff88;
                border-radius: 3px;
                padding: 15px;
                font-size: 12pt;
                font-weight: bold;
            }
        """)
        self.summary_label.setVisible(False)
        layout.addWidget(self.summary_label)

    def set_items(self, items: list, category_id: int):
        """Establece items a crear"""
        self.items = items
        self.category_id = category_id
        self.log(f"📝 {len(items)} items listos para crear")

    def create_items(self):
        """Ejecuta la creación masiva"""
        if not self.items or not self.category_id:
            self.log("❌ Error: No hay items o categoría")
            return

        self.log(f"🚀 Iniciando creación de {len(self.items)} items...")
        self.progress.setValue(10)

        try:
            # Crear items
            self.result = self.manager.create_items_bulk(self.items, self.category_id)
            self.progress.setValue(90)

            # Mostrar resultado
            if self.result.success:
                self.progress.setValue(100)
                self.status_label.setText(f"✓ ¡Completado!")
                self.status_label.setStyleSheet("color: #00ff88; font-size: 14pt; font-weight: bold;")

                summary = (
                    f"✓ Creación Exitosa\n\n"
                    f"• {self.result.created_count} items creados\n"
                    f"• {self.result.failed_count} items fallidos\n"
                    f"• Tiempo: {self.result.duration_ms}ms"
                )
                self.summary_label.setText(summary)
                self.summary_label.setVisible(True)

                self.log(f"✓ Creados: {self.result.created_count}")
                if self.result.failed_count > 0:
                    self.log(f"⚠ Fallidos: {self.result.failed_count}")
                    for error in self.result.errors[:5]:
                        self.log(f"  • {error}")

                logger.info(f"Bulk creation success: {self.result.created_count} items")
            else:
                self.status_label.setText("✗ Error en creación")
                self.status_label.setStyleSheet("color: #ff4444; font-size: 14pt; font-weight: bold;")
                self.summary_label.setStyleSheet(self.summary_label.styleSheet().replace("#1e3a1e", "#3d1e1e").replace("#00ff88", "#ff4444"))
                self.summary_label.setText(f"✗ Error:\n{self.result.errors[0] if self.result.errors else 'Unknown error'}")
                self.summary_label.setVisible(True)
                self.log(f"❌ Error: {self.result.errors[0] if self.result.errors else 'Unknown'}")

        except Exception as e:
            logger.error(f"Creation error: {e}", exc_info=True)
            self.status_label.setText("✗ Error")
            self.status_label.setStyleSheet("color: #ff4444; font-size: 14pt; font-weight: bold;")
            self.log(f"❌ Excepción: {str(e)}")

    def log(self, message: str):
        """Agrega mensaje al log"""
        self.log_text.append(message)

    def get_result(self):
        """Retorna resultado de la creación"""
        return self.result
