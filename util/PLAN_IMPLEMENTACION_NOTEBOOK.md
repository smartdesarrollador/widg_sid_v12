# 📋 PLAN DE IMPLEMENTACIÓN - BLOC DE NOTAS CON PESTAÑAS PERSISTENTES

**Proyecto:** Widget Sidebar v3.0
**Feature:** Sistema de Bloc de Notas Multi-Pestaña con guardado de Items
**Fecha:** 2025-11-03
**Complejidad:** Alta
**Tiempo estimado:** 8-12 horas

---

## 🎯 OBJETIVO

Implementar un bloc de notas integrado en el sidebar que permita:
1. Crear múltiples pestañas persistentes para trabajar en paralelo
2. Guardar borradores automáticamente
3. Convertir notas en items definitivos con todos los campos (categoría, tags, tipo, etc.)
4. Reservar espacio en el escritorio de Windows empujando otras aplicaciones
5. Posicionarse automáticamente al lado del sidebar principal

---

## 📐 ARQUITECTURA GENERAL

```
┌─────────────────────────────────────────────────────────────┐
│                    FLUJO DE DATOS                            │
└─────────────────────────────────────────────────────────────┘

Sidebar (📓) → MainController → NotebookWindow
                     ↓                   ↓
              NotebookManager      QTabWidget
                     ↓                   ↓
              notebook_tabs         NotebookTab
              (BD temporal)        (formulario)
                     ↓                   ↓
              [Auto-guardado]    [Click Guardar]
                                       ↓
                                  items table
                                 (BD definitiva)

WorkareaManager ←→ Windows API (SystemParametersInfo)
       ↓
  Reserva espacio en pantalla
```

---

## 🗂️ FASE 0: ANÁLISIS Y PREPARACIÓN (30 min)

### ✅ 0.1 Revisar arquitectura actual
- [ ] Estudiar `src/views/main_window.py` y `sidebar.py`
- [ ] Revisar `src/database/db_manager.py` para entender CRUD patterns
- [ ] Analizar `src/views/floating_panel.py` como referencia de ventanas auxiliares
- [ ] Revisar sistema de settings existente

### ✅ 0.2 Preparar entorno
- [ ] Hacer backup de la base de datos actual
- [ ] Crear rama git: `feature/notebook-tabs`
- [ ] Documentar estado actual en logs

### ✅ 0.3 Definir constantes
Crear en `src/utils/constants.py`:
```python
# Notebook constants
NOTEBOOK_WIDTH = 450
NOTEBOOK_MIN_HEIGHT = 600
NOTEBOOK_AUTOSAVE_INTERVAL = 5000  # 5 segundos en ms
NOTEBOOK_MAX_TABS = 10
NOTEBOOK_DEFAULT_TAB_TITLE = "Sin título"
```

---

## 🗄️ FASE 1: BASE DE DATOS (1-2 horas)

### ✅ 1.1 Crear migración para tabla `notebook_tabs`

**Archivo:** `src/database/migrations/add_notebook_tabs_table.py`

```python
"""
Migración: Agregar tabla notebook_tabs para pestañas persistentes
Fecha: 2025-11-03
"""

def upgrade(conn):
    """Crear tabla notebook_tabs"""
    conn.execute("""
        CREATE TABLE IF NOT EXISTS notebook_tabs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL DEFAULT 'Sin título',
            content TEXT DEFAULT '',
            category_id INTEGER,
            item_type TEXT DEFAULT 'TEXT',
            tags TEXT DEFAULT '',
            description TEXT DEFAULT '',
            is_sensitive INTEGER DEFAULT 0,
            is_active INTEGER DEFAULT 1,
            is_archived INTEGER DEFAULT 0,
            position INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE SET NULL
        )
    """)

    # Índices para optimizar consultas
    conn.execute("CREATE INDEX idx_notebook_tabs_position ON notebook_tabs(position)")
    conn.execute("CREATE INDEX idx_notebook_tabs_category ON notebook_tabs(category_id)")

    print("✅ Tabla notebook_tabs creada exitosamente")

def downgrade(conn):
    """Revertir migración"""
    conn.execute("DROP TABLE IF EXISTS notebook_tabs")
    print("✅ Tabla notebook_tabs eliminada")
```

### ✅ 1.2 Agregar settings del notebook

**Archivo:** `src/database/migrations/add_notebook_settings.py`

```python
def upgrade(conn):
    """Agregar configuraciones del notebook"""
    settings = [
        ('notebook_width', '450'),
        ('notebook_autosave_interval', '5000'),
        ('notebook_reserve_workspace', 'true'),
        ('notebook_last_active_tab', '0'),
        ('notebook_position', 'right'),  # left, right
        ('notebook_show_on_startup', 'false'),
    ]

    for key, value in settings:
        conn.execute("""
            INSERT OR IGNORE INTO settings (key, value)
            VALUES (?, ?)
        """, (key, value))

    print("✅ Settings del notebook agregadas")
```

### ✅ 1.3 Extender DBManager con métodos CRUD

**Archivo:** `src/database/db_manager.py`

Agregar al final de la clase `DBManager`:

```python
# ========================================
# NOTEBOOK TABS CRUD
# ========================================

def get_notebook_tabs(self, order_by='position'):
    """Obtener todas las pestañas del notebook ordenadas"""
    query = f"SELECT * FROM notebook_tabs ORDER BY {order_by} ASC"
    return self.conn.execute(query).fetchall()

def get_notebook_tab(self, tab_id):
    """Obtener una pestaña específica"""
    query = "SELECT * FROM notebook_tabs WHERE id = ?"
    return self.conn.execute(query, (tab_id,)).fetchone()

def add_notebook_tab(self, title='Sin título', position=None):
    """Crear nueva pestaña"""
    if position is None:
        # Obtener última posición
        result = self.conn.execute(
            "SELECT MAX(position) FROM notebook_tabs"
        ).fetchone()
        position = (result[0] or -1) + 1

    with self.transaction() as conn:
        cursor = conn.execute("""
            INSERT INTO notebook_tabs (title, position)
            VALUES (?, ?)
        """, (title, position))
        return cursor.lastrowid

def update_notebook_tab(self, tab_id, **fields):
    """Actualizar campos de una pestaña"""
    allowed_fields = [
        'title', 'content', 'category_id', 'item_type', 'tags',
        'description', 'is_sensitive', 'is_active', 'is_archived', 'position'
    ]

    updates = []
    values = []

    for field, value in fields.items():
        if field in allowed_fields:
            updates.append(f"{field} = ?")
            values.append(value)

    if not updates:
        return False

    updates.append("updated_at = CURRENT_TIMESTAMP")
    values.append(tab_id)

    query = f"UPDATE notebook_tabs SET {', '.join(updates)} WHERE id = ?"

    with self.transaction() as conn:
        conn.execute(query, values)

    return True

def delete_notebook_tab(self, tab_id):
    """Eliminar una pestaña"""
    with self.transaction() as conn:
        conn.execute("DELETE FROM notebook_tabs WHERE id = ?", (tab_id,))
    return True

def reorder_notebook_tabs(self, tab_ids_in_order):
    """Reordenar pestañas según lista de IDs"""
    with self.transaction() as conn:
        for position, tab_id in enumerate(tab_ids_in_order):
            conn.execute(
                "UPDATE notebook_tabs SET position = ? WHERE id = ?",
                (position, tab_id)
            )
```

### ✅ 1.4 Ejecutar migraciones

```python
# Crear script: util/migrations/run_notebook_migration.py
from pathlib import Path
import sys

# Agregar src al path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))

from database.db_manager import DBManager
from database.migrations.add_notebook_tabs_table import upgrade as upgrade_tabs
from database.migrations.add_notebook_settings import upgrade as upgrade_settings

def main():
    db = DBManager('widget_sidebar.db')

    print("🚀 Ejecutando migraciones del notebook...")

    with db.transaction() as conn:
        upgrade_tabs(conn)
        upgrade_settings(conn)

    print("✅ Migraciones completadas exitosamente")
    db.close()

if __name__ == '__main__':
    main()
```

**Ejecutar:** `python util/migrations/run_notebook_migration.py`

---

## 🎨 FASE 2: COMPONENTES UI - NOTEBOOK TAB WIDGET (2-3 horas)

### ✅ 2.1 Crear widget de pestaña individual

**Archivo:** `src/views/widgets/notebook_tab.py`

```python
"""
NotebookTab Widget
Formulario completo para editar una nota y convertirla en item
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QTextEdit,
    QComboBox, QCheckBox, QPushButton, QLabel, QGroupBox
)
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QFont


class NotebookTab(QWidget):
    """Widget de pestaña individual del notebook"""

    # Señales
    save_requested = pyqtSignal(dict)  # Emite datos del formulario
    content_changed = pyqtSignal(dict)  # Para auto-guardado

    def __init__(self, tab_id=None, tab_data=None, categories=None, parent=None):
        super().__init__(parent)
        self.tab_id = tab_id
        self.categories = categories or []
        self.setup_ui()

        if tab_data:
            self.load_data(tab_data)

        # Conectar señales para auto-guardado
        self.connect_autosave_signals()

    def setup_ui(self):
        """Configurar interfaz del formulario"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(12)

        # === NOMBRE DEL ITEM ===
        name_label = QLabel("Nombre del ítem:")
        name_label.setStyleSheet("color: #B0B0B0; font-size: 11px;")
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Ej: Script de backup, API endpoint, etc.")
        self.name_input.setMinimumHeight(32)
        self.style_input(self.name_input)

        layout.addWidget(name_label)
        layout.addWidget(self.name_input)

        # === CONTENIDO (ÁREA GRANDE) ===
        content_label = QLabel("Contenido:")
        content_label.setStyleSheet("color: #B0B0B0; font-size: 11px;")
        self.content_input = QTextEdit()
        self.content_input.setPlaceholderText("Escribe tu contenido aquí...")
        self.content_input.setMinimumHeight(250)

        # Font monospace para contenido
        font = QFont("Consolas", 10)
        self.content_input.setFont(font)

        self.style_text_edit(self.content_input)

        layout.addWidget(content_label)
        layout.addWidget(self.content_input, 1)  # Stretch factor

        # === ROW: CATEGORÍA + TIPO ===
        row_layout = QHBoxLayout()

        # Categoría
        cat_group = QVBoxLayout()
        cat_label = QLabel("Categoría:")
        cat_label.setStyleSheet("color: #B0B0B0; font-size: 11px;")
        self.category_combo = QComboBox()
        self.category_combo.setMinimumHeight(32)
        self.load_categories()
        self.style_combo(self.category_combo)
        cat_group.addWidget(cat_label)
        cat_group.addWidget(self.category_combo)

        # Tipo
        type_group = QVBoxLayout()
        type_label = QLabel("Tipo:")
        type_label.setStyleSheet("color: #B0B0B0; font-size: 11px;")
        self.type_combo = QComboBox()
        self.type_combo.setMinimumHeight(32)
        self.type_combo.addItems(['TEXT', 'CODE', 'URL', 'PATH'])
        self.style_combo(self.type_combo)
        type_group.addWidget(type_label)
        type_group.addWidget(self.type_combo)

        row_layout.addLayout(cat_group, 2)
        row_layout.addLayout(type_group, 1)
        layout.addLayout(row_layout)

        # === TAGS ===
        tags_label = QLabel("Tags (opcional):")
        tags_label.setStyleSheet("color: #B0B0B0; font-size: 11px;")
        self.tags_input = QLineEdit()
        self.tags_input.setPlaceholderText("tag1, tag2, tag3")
        self.tags_input.setMinimumHeight(32)
        self.style_input(self.tags_input)

        layout.addWidget(tags_label)
        layout.addWidget(self.tags_input)

        # === DESCRIPCIÓN ===
        desc_label = QLabel("Descripción (opcional):")
        desc_label.setStyleSheet("color: #B0B0B0; font-size: 11px;")
        self.description_input = QLineEdit()
        self.description_input.setPlaceholderText("Breve descripción del ítem")
        self.description_input.setMinimumHeight(32)
        self.style_input(self.description_input)

        layout.addWidget(desc_label)
        layout.addWidget(self.description_input)

        # === CHECKBOXES ===
        self.sensitive_check = QCheckBox("🔒 Marcar como sensible (cifrar contenido)")
        self.active_check = QCheckBox("✅ Ítem activo (puede ser usado)")
        self.archived_check = QCheckBox("📦 Ítem archivado (ocultar de vista)")

        self.active_check.setChecked(True)  # Default: activo

        self.style_checkbox(self.sensitive_check)
        self.style_checkbox(self.active_check)
        self.style_checkbox(self.archived_check)

        layout.addWidget(self.sensitive_check)
        layout.addWidget(self.active_check)
        layout.addWidget(self.archived_check)

        # === BOTONES ===
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self.cancel_btn = QPushButton("Cancelar")
        self.save_btn = QPushButton("💾 Guardar como Item")

        self.cancel_btn.setMinimumSize(100, 36)
        self.save_btn.setMinimumSize(150, 36)

        self.style_button(self.cancel_btn, secondary=True)
        self.style_button(self.save_btn, primary=True)

        button_layout.addWidget(self.cancel_btn)
        button_layout.addWidget(self.save_btn)

        layout.addLayout(button_layout)

        # Conectar botones
        self.save_btn.clicked.connect(self.on_save_clicked)
        self.cancel_btn.clicked.connect(self.on_cancel_clicked)

        # Estilo general
        self.setStyleSheet("""
            QWidget {
                background-color: #1E1E1E;
                color: #FFFFFF;
            }
        """)

    def load_categories(self):
        """Cargar categorías en el combo"""
        self.category_combo.clear()
        for cat in self.categories:
            # Format: "🔧 Git"
            display_text = f"{cat.get('icon', '')} {cat.get('name', '')}"
            self.category_combo.addItem(display_text, cat.get('id'))

    def connect_autosave_signals(self):
        """Conectar señales para auto-guardado"""
        self.name_input.textChanged.connect(self.on_content_modified)
        self.content_input.textChanged.connect(self.on_content_modified)
        self.tags_input.textChanged.connect(self.on_content_modified)
        self.description_input.textChanged.connect(self.on_content_modified)

    def on_content_modified(self):
        """Emitir señal cuando el contenido cambia"""
        self.content_changed.emit(self.get_data())

    def on_save_clicked(self):
        """Validar y emitir señal de guardado"""
        data = self.get_data()

        # Validación básica
        if not data['label'].strip():
            # TODO: mostrar mensaje de error
            return

        if not data['content'].strip():
            # TODO: mostrar mensaje de error
            return

        self.save_requested.emit(data)

    def on_cancel_clicked(self):
        """Limpiar formulario o cerrar tab"""
        # TODO: implementar lógica de cancelación
        pass

    def get_data(self):
        """Obtener datos del formulario"""
        return {
            'label': self.name_input.text(),
            'content': self.content_input.toPlainText(),
            'category_id': self.category_combo.currentData(),
            'item_type': self.type_combo.currentText(),
            'tags': self.tags_input.text(),
            'description': self.description_input.text(),
            'is_sensitive': self.sensitive_check.isChecked(),
            'is_active': self.active_check.isChecked(),
            'is_archived': self.archived_check.isChecked(),
        }

    def load_data(self, data):
        """Cargar datos en el formulario"""
        self.name_input.setText(data.get('title', ''))
        self.content_input.setPlainText(data.get('content', ''))
        self.tags_input.setText(data.get('tags', ''))
        self.description_input.setText(data.get('description', ''))

        # Seleccionar categoría
        category_id = data.get('category_id')
        if category_id:
            index = self.category_combo.findData(category_id)
            if index >= 0:
                self.category_combo.setCurrentIndex(index)

        # Seleccionar tipo
        item_type = data.get('item_type', 'TEXT')
        index = self.type_combo.findText(item_type)
        if index >= 0:
            self.type_combo.setCurrentIndex(index)

        # Checkboxes
        self.sensitive_check.setChecked(bool(data.get('is_sensitive', 0)))
        self.active_check.setChecked(bool(data.get('is_active', 1)))
        self.archived_check.setChecked(bool(data.get('is_archived', 0)))

    # === ESTILOS ===

    def style_input(self, widget):
        widget.setStyleSheet("""
            QLineEdit {
                background-color: #2D2D2D;
                border: 1px solid #3D3D3D;
                border-radius: 4px;
                padding: 6px 10px;
                color: #FFFFFF;
                font-size: 12px;
            }
            QLineEdit:focus {
                border: 1px solid #0078D4;
            }
        """)

    def style_text_edit(self, widget):
        widget.setStyleSheet("""
            QTextEdit {
                background-color: #2D2D2D;
                border: 1px solid #3D3D3D;
                border-radius: 4px;
                padding: 8px;
                color: #FFFFFF;
                font-size: 12px;
            }
            QTextEdit:focus {
                border: 1px solid #0078D4;
            }
        """)

    def style_combo(self, widget):
        widget.setStyleSheet("""
            QComboBox {
                background-color: #2D2D2D;
                border: 1px solid #3D3D3D;
                border-radius: 4px;
                padding: 6px 10px;
                color: #FFFFFF;
                font-size: 12px;
            }
            QComboBox:focus {
                border: 1px solid #0078D4;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox QAbstractItemView {
                background-color: #2D2D2D;
                color: #FFFFFF;
                selection-background-color: #0078D4;
            }
        """)

    def style_checkbox(self, widget):
        widget.setStyleSheet("""
            QCheckBox {
                color: #B0B0B0;
                font-size: 11px;
                spacing: 8px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border: 1px solid #3D3D3D;
                border-radius: 3px;
                background-color: #2D2D2D;
            }
            QCheckBox::indicator:checked {
                background-color: #0078D4;
                border-color: #0078D4;
            }
        """)

    def style_button(self, widget, primary=False, secondary=False):
        if primary:
            widget.setStyleSheet("""
                QPushButton {
                    background-color: #0078D4;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    font-size: 12px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #005A9E;
                }
                QPushButton:pressed {
                    background-color: #004578;
                }
            """)
        elif secondary:
            widget.setStyleSheet("""
                QPushButton {
                    background-color: #3D3D3D;
                    color: #B0B0B0;
                    border: 1px solid #4D4D4D;
                    border-radius: 4px;
                    font-size: 12px;
                }
                QPushButton:hover {
                    background-color: #4D4D4D;
                    color: #FFFFFF;
                }
            """)
```

### ✅ 2.2 Testing del widget

**Archivo:** `tests/test_notebook_tab_widget.py`

```python
"""Script de testing para NotebookTab widget"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from PyQt6.QtWidgets import QApplication
from views.widgets.notebook_tab import NotebookTab

def test_widget():
    app = QApplication(sys.argv)

    # Mock categories
    categories = [
        {'id': 1, 'name': 'Git', 'icon': '🔧'},
        {'id': 2, 'name': 'Docker', 'icon': '🐳'},
        {'id': 3, 'name': 'Python', 'icon': '🐍'},
    ]

    # Crear widget
    tab = NotebookTab(categories=categories)
    tab.setMinimumSize(450, 600)

    # Conectar señales para debugging
    tab.save_requested.connect(lambda data: print("SAVE:", data))
    tab.content_changed.connect(lambda data: print("CHANGED:", data['label']))

    tab.show()

    sys.exit(app.exec())

if __name__ == '__main__':
    test_widget()
```

**Ejecutar:** `python tests/test_notebook_tab_widget.py`

---

## 🪟 FASE 3: VENTANA PRINCIPAL DEL NOTEBOOK (2-3 horas)

### ✅ 3.1 Crear NotebookWindow

**Archivo:** `src/views/notebook_window.py`

```python
"""
NotebookWindow - Ventana principal del bloc de notas con pestañas
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
    QPushButton, QLabel, QMessageBox
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QIcon
from views.widgets.notebook_tab import NotebookTab
from utils.constants import (
    NOTEBOOK_WIDTH, NOTEBOOK_MIN_HEIGHT,
    NOTEBOOK_AUTOSAVE_INTERVAL, NOTEBOOK_MAX_TABS
)


class NotebookWindow(QWidget):
    """Ventana del bloc de notas con pestañas persistentes"""

    # Señales
    closed = pyqtSignal()
    tab_saved_as_item = pyqtSignal(dict)  # Cuando se guarda un item

    def __init__(self, controller, parent=None):
        super().__init__(parent)
        self.controller = controller
        self.notebook_manager = controller.notebook_manager

        # Configuración de ventana
        self.setWindowTitle("📓 Bloc de Notas")
        self.setMinimumSize(NOTEBOOK_WIDTH, NOTEBOOK_MIN_HEIGHT)

        # Frameless window con borde
        self.setWindowFlags(
            Qt.WindowType.Window |
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint
        )

        self.setup_ui()
        self.load_tabs()
        self.setup_autosave()

        # Aplicar estilos
        self.apply_styles()

    def setup_ui(self):
        """Configurar interfaz"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # === BARRA DE TÍTULO CUSTOM ===
        title_bar = self.create_title_bar()
        layout.addWidget(title_bar)

        # === TAB WIDGET ===
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabsClosable(True)
        self.tab_widget.setMovable(True)

        # Conectar señales
        self.tab_widget.tabCloseRequested.connect(self.close_tab)
        self.tab_widget.currentChanged.connect(self.on_tab_changed)

        layout.addWidget(self.tab_widget)

        # Botón flotante para agregar tab
        self.add_tab_button = QPushButton("+ Nueva Nota")
        self.add_tab_button.clicked.connect(self.add_new_tab)
        layout.addWidget(self.add_tab_button)

    def create_title_bar(self):
        """Crear barra de título personalizada"""
        title_bar = QWidget()
        title_bar.setFixedHeight(36)
        title_bar.setObjectName("titleBar")

        layout = QHBoxLayout(title_bar)
        layout.setContentsMargins(10, 0, 5, 0)

        # Icono + título
        icon_label = QLabel("📓")
        title_label = QLabel("Bloc de Notas")
        title_label.setStyleSheet("font-weight: bold; font-size: 13px;")

        layout.addWidget(icon_label)
        layout.addWidget(title_label)
        layout.addStretch()

        # Botones de control
        min_btn = QPushButton("−")
        close_btn = QPushButton("×")

        min_btn.setFixedSize(30, 30)
        close_btn.setFixedSize(30, 30)

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
            self.add_new_tab()
            return

        # Cargar cada tab
        for tab_data in tabs:
            self.add_tab_from_data(tab_data)

        # Restaurar tab activa
        last_active = self.controller.config_manager.get_setting(
            'notebook_last_active_tab', 0
        )
        if 0 <= last_active < self.tab_widget.count():
            self.tab_widget.setCurrentIndex(last_active)

    def add_new_tab(self):
        """Agregar nueva pestaña vacía"""
        # Verificar límite
        if self.tab_widget.count() >= NOTEBOOK_MAX_TABS:
            QMessageBox.warning(
                self, "Límite alcanzado",
                f"No puedes tener más de {NOTEBOOK_MAX_TABS} pestañas abiertas."
            )
            return

        # Crear tab en BD
        tab_id = self.notebook_manager.create_tab()

        # Crear widget
        categories = self.controller.get_categories()
        tab_widget = NotebookTab(tab_id=tab_id, categories=categories)

        # Conectar señales
        tab_widget.save_requested.connect(self.on_save_as_item)
        tab_widget.content_changed.connect(self.on_tab_content_changed)

        # Agregar al tab widget
        index = self.tab_widget.addTab(tab_widget, "Sin título")
        self.tab_widget.setCurrentIndex(index)

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

        # Agregar al tab widget
        title = tab_data.get('title', 'Sin título')
        self.tab_widget.addTab(tab_widget, title)

    def close_tab(self, index):
        """Cerrar pestaña"""
        if self.tab_widget.count() <= 1:
            QMessageBox.information(
                self, "Info",
                "Debe haber al menos una pestaña abierta."
            )
            return

        # Obtener tab widget
        tab_widget = self.tab_widget.widget(index)

        # Confirmar si hay contenido no guardado
        data = tab_widget.get_data()
        if data['label'] or data['content']:
            reply = QMessageBox.question(
                self, "Confirmar cierre",
                "¿Cerrar esta pestaña? Los cambios no guardados se perderán.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )

            if reply == QMessageBox.StandardButton.No:
                return

        # Eliminar de BD
        if tab_widget.tab_id:
            self.notebook_manager.delete_tab(tab_widget.tab_id)

        # Remover del widget
        self.tab_widget.removeTab(index)

    def on_tab_changed(self, index):
        """Cuando cambia la pestaña activa"""
        # Guardar índice en settings
        self.controller.config_manager.update_setting(
            'notebook_last_active_tab', str(index)
        )

    def on_tab_content_changed(self, data):
        """Cuando cambia el contenido (para actualizar título)"""
        # Obtener tab actual
        current_widget = self.tab_widget.currentWidget()
        current_index = self.tab_widget.currentIndex()

        # Actualizar título de la pestaña
        title = data.get('label', 'Sin título')
        if not title.strip():
            title = 'Sin título'

        self.tab_widget.setTabText(current_index, title[:20])

    def on_save_as_item(self, data):
        """Guardar nota como item definitivo"""
        try:
            # Obtener tab actual
            current_widget = self.tab_widget.currentWidget()

            # Crear item en BD
            item_id = self.controller.add_item(
                category_id=data['category_id'],
                label=data['label'],
                content=data['content'],
                item_type=data['item_type'],
                tags=data['tags'],
                description=data['description'],
                is_sensitive=data['is_sensitive'],
                is_active=data['is_active'],
                is_archived=data['is_archived']
            )

            # Emitir señal
            self.tab_saved_as_item.emit(data)

            # Mostrar confirmación
            QMessageBox.information(
                self, "Éxito",
                f"Item '{data['label']}' guardado exitosamente."
            )

            # Opcionalmente: limpiar tab o cerrarla
            reply = QMessageBox.question(
                self, "Limpiar pestaña",
                "¿Deseas limpiar esta pestaña para crear una nueva nota?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )

            if reply == QMessageBox.StandardButton.Yes:
                # Limpiar formulario
                current_widget.name_input.clear()
                current_widget.content_input.clear()
                current_widget.tags_input.clear()
                current_widget.description_input.clear()

                # Actualizar título
                self.tab_widget.setTabText(
                    self.tab_widget.currentIndex(),
                    "Sin título"
                )

        except Exception as e:
            QMessageBox.critical(
                self, "Error",
                f"Error al guardar item: {str(e)}"
            )

    def setup_autosave(self):
        """Configurar auto-guardado periódico"""
        self.autosave_timer = QTimer()
        self.autosave_timer.timeout.connect(self.autosave_all_tabs)
        self.autosave_timer.start(NOTEBOOK_AUTOSAVE_INTERVAL)

    def autosave_all_tabs(self):
        """Auto-guardar todas las pestañas en BD"""
        for i in range(self.tab_widget.count()):
            tab_widget = self.tab_widget.widget(i)
            data = tab_widget.get_data()

            if tab_widget.tab_id:
                self.notebook_manager.update_tab(
                    tab_widget.tab_id,
                    title=data['label'] or 'Sin título',
                    content=data['content'],
                    category_id=data['category_id'],
                    item_type=data['item_type'],
                    tags=data['tags'],
                    description=data['description'],
                    is_sensitive=data['is_sensitive'],
                    is_active=data['is_active'],
                    is_archived=data['is_archived']
                )

    def closeEvent(self, event):
        """Antes de cerrar, guardar todo"""
        self.autosave_all_tabs()
        self.closed.emit()
        super().closeEvent(event)

    # === DRAGGING ===

    def start_drag(self, event):
        """Iniciar arrastre de ventana"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()

    def do_drag(self, event):
        """Realizar arrastre"""
        if event.buttons() == Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self.drag_position)

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
                font-size: 18px;
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
                border: 1px solid #3D3D3D;
                background-color: #1E1E1E;
            }

            QTabBar::tab {
                background-color: #2D2D2D;
                color: #B0B0B0;
                padding: 8px 16px;
                margin-right: 2px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }

            QTabBar::tab:selected {
                background-color: #1E1E1E;
                color: #FFFFFF;
                border-bottom: 2px solid #0078D4;
            }

            QTabBar::tab:hover {
                background-color: #3D3D3D;
            }

            QPushButton {
                background-color: #0078D4;
                color: white;
                border: none;
                padding: 10px;
                font-size: 12px;
                font-weight: bold;
            }

            QPushButton:hover {
                background-color: #005A9E;
            }
        """)
```

---

## 🔧 FASE 4: MANAGER Y LÓGICA DE NEGOCIO (1-2 horas)

### ✅ 4.1 Crear NotebookManager

**Archivo:** `src/core/notebook_manager.py`

```python
"""
NotebookManager - Gestión de pestañas del notebook
"""

from datetime import datetime


class NotebookManager:
    """Manager para operaciones de notebook tabs"""

    def __init__(self, db_manager):
        self.db = db_manager

    def get_all_tabs(self):
        """Obtener todas las pestañas ordenadas"""
        return self.db.get_notebook_tabs()

    def get_tab(self, tab_id):
        """Obtener una pestaña específica"""
        return self.db.get_notebook_tab(tab_id)

    def create_tab(self, title='Sin título'):
        """Crear nueva pestaña vacía"""
        return self.db.add_notebook_tab(title=title)

    def update_tab(self, tab_id, **fields):
        """Actualizar campos de una pestaña"""
        return self.db.update_notebook_tab(tab_id, **fields)

    def delete_tab(self, tab_id):
        """Eliminar una pestaña"""
        return self.db.delete_notebook_tab(tab_id)

    def reorder_tabs(self, tab_ids_in_order):
        """Reordenar pestañas"""
        return self.db.reorder_notebook_tabs(tab_ids_in_order)

    def convert_tab_to_item(self, tab_id, delete_after=False):
        """
        Convertir una pestaña en un item definitivo

        Args:
            tab_id: ID de la pestaña
            delete_after: Si True, elimina la pestaña después de convertir

        Returns:
            ID del item creado
        """
        tab_data = self.get_tab(tab_id)

        if not tab_data:
            raise ValueError(f"Tab {tab_id} no encontrada")

        # Crear item
        item_id = self.db.add_item(
            category_id=tab_data['category_id'],
            label=tab_data['title'],
            content=tab_data['content'],
            item_type=tab_data['item_type'],
            tags=tab_data['tags'],
            description=tab_data['description'],
            is_sensitive=bool(tab_data['is_sensitive']),
            is_active=bool(tab_data['is_active']),
            is_archived=bool(tab_data['is_archived'])
        )

        # Eliminar pestaña si se solicita
        if delete_after:
            self.delete_tab(tab_id)

        return item_id
```

### ✅ 4.2 Integrar NotebookManager en MainController

**Archivo:** `src/controllers/main_controller.py`

Agregar al `__init__`:

```python
from core.notebook_manager import NotebookManager

class MainController:
    def __init__(self):
        # ... código existente ...

        # Agregar notebook manager
        self.notebook_manager = NotebookManager(self.config_manager.db)
        logger.info("NotebookManager initialized")
```

---

## 🔗 FASE 5: INTEGRACIÓN CON SIDEBAR (1 hora)

### ✅ 5.1 Agregar botón de notebook en Sidebar

**Archivo:** `src/views/sidebar.py`

Buscar el método `setup_ui()` y agregar:

```python
def setup_ui(self):
    # ... código existente ...

    # AGREGAR: Botón de notebook en la parte superior
    self.notebook_btn = QPushButton("📓")
    self.notebook_btn.setFixedSize(50, 50)
    self.notebook_btn.setToolTip("Bloc de Notas (Ctrl+N)")
    self.notebook_btn.setObjectName("notebookBtn")
    self.notebook_btn.clicked.connect(self.toggle_notebook)

    # Estilos del botón
    self.notebook_btn.setStyleSheet("""
        QPushButton#notebookBtn {
            background-color: #2D2D2D;
            border: 2px solid #3D3D3D;
            border-radius: 8px;
            font-size: 24px;
            color: #FFFFFF;
        }
        QPushButton#notebookBtn:hover {
            background-color: #0078D4;
            border-color: #0078D4;
        }
        QPushButton#notebookBtn:pressed {
            background-color: #005A9E;
        }
    """)

    # Insertar en layout (al inicio, antes de las categorías)
    self.category_layout.insertWidget(0, self.notebook_btn)
    self.category_layout.insertSpacing(1, 10)  # Espaciado

def toggle_notebook(self):
    """Abrir/cerrar ventana de notebook"""
    if not hasattr(self, 'notebook_window') or self.notebook_window is None:
        # Crear ventana
        from views.notebook_window import NotebookWindow
        self.notebook_window = NotebookWindow(self.controller)

        # Posicionar al lado del sidebar
        self.position_notebook_window()

        # Conectar señales
        self.notebook_window.closed.connect(self.on_notebook_closed)
        self.notebook_window.tab_saved_as_item.connect(self.on_item_saved_from_notebook)

        self.notebook_window.show()
    else:
        if self.notebook_window.isVisible():
            self.notebook_window.hide()
        else:
            self.notebook_window.show()
            self.position_notebook_window()

def position_notebook_window(self):
    """Posicionar notebook al lado del sidebar"""
    if not hasattr(self, 'notebook_window') or self.notebook_window is None:
        return

    # Obtener geometría del main window (sidebar)
    main_geo = self.window().geometry()

    # Posicionar a la izquierda del sidebar
    x = main_geo.x() - NOTEBOOK_WIDTH - 10  # 10px de separación
    y = main_geo.y()
    height = main_geo.height()

    self.notebook_window.setGeometry(x, y, NOTEBOOK_WIDTH, height)

def on_notebook_closed(self):
    """Cuando se cierra la ventana de notebook"""
    self.notebook_window = None

def on_item_saved_from_notebook(self, data):
    """Cuando se guarda un item desde el notebook"""
    # Refrescar la vista si la categoría actual es la del item guardado
    if hasattr(self, 'current_category_id'):
        if self.current_category_id == data['category_id']:
            # Recargar items de la categoría
            self.load_category_items(self.current_category_id)
```

### ✅ 5.2 Agregar hotkey para abrir notebook

**Archivo:** `src/core/hotkey_manager.py`

Agregar en `setup_hotkeys()`:

```python
def setup_hotkeys(self):
    # ... hotkeys existentes ...

    # Agregar hotkey para notebook: Ctrl+Shift+N
    self.register_hotkey(
        '<ctrl>+<shift>+n',
        self.on_notebook_hotkey
    )

def on_notebook_hotkey(self):
    """Hotkey para abrir/cerrar notebook"""
    self.notebook_toggle.emit()
```

Conectar señal en `MainWindow`:

```python
# En MainWindow.__init__()
self.controller.hotkey_manager.notebook_toggle.connect(
    self.sidebar.toggle_notebook
)
```

---

## 🖥️ FASE 6: WORKAREA MANAGER (OPCIONAL - 2 horas)

Esta fase implementa la funcionalidad de reservar espacio en Windows.

### ✅ 6.1 Crear WorkareaManager

**Archivo:** `src/core/workarea_manager.py`

```python
"""
WorkareaManager - Manipulación del área de trabajo de Windows
"""

import ctypes
from ctypes import wintypes
import logging

logger = logging.getLogger(__name__)


class WorkareaManager:
    """
    Manager para reservar espacio en el escritorio de Windows

    Usa SystemParametersInfo con SPI_SETWORKAREA para modificar
    el área disponible para otras aplicaciones.
    """

    def __init__(self):
        self.original_workarea = None
        self.is_space_reserved = False

        # Guardar área original
        self.save_original_workarea()

    def save_original_workarea(self):
        """Guardar el área de trabajo original"""
        try:
            workarea = wintypes.RECT()
            SPI_GETWORKAREA = 0x0030

            result = ctypes.windll.user32.SystemParametersInfoW(
                SPI_GETWORKAREA,
                0,
                ctypes.byref(workarea),
                0
            )

            if result:
                self.original_workarea = {
                    'left': workarea.left,
                    'top': workarea.top,
                    'right': workarea.right,
                    'bottom': workarea.bottom
                }
                logger.info(f"Original workarea saved: {self.original_workarea}")
            else:
                logger.error("Failed to get original workarea")

        except Exception as e:
            logger.error(f"Error saving original workarea: {e}")

    def reserve_space_left(self, width):
        """
        Reservar espacio en el lado izquierdo de la pantalla

        Args:
            width: Ancho en píxeles a reservar
        """
        if not self.original_workarea:
            logger.error("Original workarea not available")
            return False

        try:
            workarea = wintypes.RECT()
            workarea.left = self.original_workarea['left'] + width
            workarea.top = self.original_workarea['top']
            workarea.right = self.original_workarea['right']
            workarea.bottom = self.original_workarea['bottom']

            SPI_SETWORKAREA = 0x002F
            SPIF_UPDATEINIFILE = 0x01
            SPIF_SENDCHANGE = 0x02

            result = ctypes.windll.user32.SystemParametersInfoW(
                SPI_SETWORKAREA,
                0,
                ctypes.byref(workarea),
                SPIF_UPDATEINIFILE | SPIF_SENDCHANGE
            )

            if result:
                self.is_space_reserved = True
                logger.info(f"Reserved {width}px on left side")
                return True
            else:
                logger.error("Failed to reserve space")
                return False

        except Exception as e:
            logger.error(f"Error reserving space: {e}")
            return False

    def reserve_space_right(self, width):
        """
        Reservar espacio en el lado derecho de la pantalla

        Args:
            width: Ancho en píxeles a reservar
        """
        if not self.original_workarea:
            logger.error("Original workarea not available")
            return False

        try:
            workarea = wintypes.RECT()
            workarea.left = self.original_workarea['left']
            workarea.top = self.original_workarea['top']
            workarea.right = self.original_workarea['right'] - width
            workarea.bottom = self.original_workarea['bottom']

            SPI_SETWORKAREA = 0x002F
            SPIF_UPDATEINIFILE = 0x01
            SPIF_SENDCHANGE = 0x02

            result = ctypes.windll.user32.SystemParametersInfoW(
                SPI_SETWORKAREA,
                0,
                ctypes.byref(workarea),
                SPIF_UPDATEINIFILE | SPIF_SENDCHANGE
            )

            if result:
                self.is_space_reserved = True
                logger.info(f"Reserved {width}px on right side")
                return True
            else:
                logger.error("Failed to reserve space")
                return False

        except Exception as e:
            logger.error(f"Error reserving space: {e}")
            return False

    def restore_workarea(self):
        """Restaurar el área de trabajo original"""
        if not self.original_workarea:
            logger.error("No original workarea to restore")
            return False

        try:
            workarea = wintypes.RECT()
            workarea.left = self.original_workarea['left']
            workarea.top = self.original_workarea['top']
            workarea.right = self.original_workarea['right']
            workarea.bottom = self.original_workarea['bottom']

            SPI_SETWORKAREA = 0x002F
            SPIF_UPDATEINIFILE = 0x01
            SPIF_SENDCHANGE = 0x02

            result = ctypes.windll.user32.SystemParametersInfoW(
                SPI_SETWORKAREA,
                0,
                ctypes.byref(workarea),
                SPIF_UPDATEINIFILE | SPIF_SENDCHANGE
            )

            if result:
                self.is_space_reserved = False
                logger.info("Workarea restored to original")
                return True
            else:
                logger.error("Failed to restore workarea")
                return False

        except Exception as e:
            logger.error(f"Error restoring workarea: {e}")
            return False

    def __del__(self):
        """Restaurar al destruir el objeto"""
        if self.is_space_reserved:
            self.restore_workarea()
```

### ✅ 6.2 Integrar WorkareaManager

**En MainController:**

```python
from core.workarea_manager import WorkareaManager

class MainController:
    def __init__(self):
        # ... código existente ...

        # Agregar workarea manager
        self.workarea_manager = WorkareaManager()
        logger.info("WorkareaManager initialized")
```

**En Sidebar.toggle_notebook():**

```python
def toggle_notebook(self):
    """Abrir/cerrar ventana de notebook"""
    # ... código existente de crear ventana ...

    # Verificar si debe reservar espacio
    reserve_space = self.controller.config_manager.get_setting(
        'notebook_reserve_workspace', 'true'
    ) == 'true'

    if reserve_space:
        # Calcular espacio total: sidebar + notebook + margen
        total_width = 70 + NOTEBOOK_WIDTH + 20

        # Reservar espacio en el lado derecho
        self.controller.workarea_manager.reserve_space_right(total_width)
```

**Al cerrar:**

```python
def on_notebook_closed(self):
    """Cuando se cierra la ventana de notebook"""
    # Restaurar área de trabajo
    self.controller.workarea_manager.restore_workarea()

    self.notebook_window = None
```

---

## 🧪 FASE 7: TESTING Y REFINAMIENTO (2-3 horas)

### ✅ 7.1 Tests unitarios

**Archivo:** `tests/test_notebook_manager.py`

```python
"""Tests para NotebookManager"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from database.db_manager import DBManager
from core.notebook_manager import NotebookManager

def test_notebook_manager():
    # Crear BD temporal
    db = DBManager(':memory:')
    manager = NotebookManager(db)

    # Test: Crear tab
    tab_id = manager.create_tab('Test Tab')
    assert tab_id is not None
    print(f"✅ Tab created: {tab_id}")

    # Test: Obtener tab
    tab = manager.get_tab(tab_id)
    assert tab['title'] == 'Test Tab'
    print(f"✅ Tab retrieved: {tab['title']}")

    # Test: Actualizar tab
    manager.update_tab(tab_id, content='Test content', tags='test,demo')
    tab = manager.get_tab(tab_id)
    assert tab['content'] == 'Test content'
    assert tab['tags'] == 'test,demo'
    print(f"✅ Tab updated")

    # Test: Obtener todas las tabs
    tabs = manager.get_all_tabs()
    assert len(tabs) == 1
    print(f"✅ All tabs: {len(tabs)}")

    # Test: Eliminar tab
    manager.delete_tab(tab_id)
    tab = manager.get_tab(tab_id)
    assert tab is None
    print(f"✅ Tab deleted")

    print("\n🎉 All tests passed!")

if __name__ == '__main__':
    test_notebook_manager()
```

### ✅ 7.2 Test de integración completa

**Archivo:** `tests/test_notebook_integration.py`

```python
"""Test de integración completa del notebook"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from PyQt6.QtWidgets import QApplication
from controllers.main_controller import MainController
from views.notebook_window import NotebookWindow

def test_integration():
    app = QApplication(sys.argv)

    # Crear controller
    controller = MainController()

    # Crear notebook window
    window = NotebookWindow(controller)
    window.show()

    print("✅ Notebook window opened")
    print(f"✅ Tabs loaded: {window.tab_widget.count()}")

    sys.exit(app.exec())

if __name__ == '__main__':
    test_integration()
```

### ✅ 7.3 Checklist de testing manual

- [ ] **Crear pestaña nueva**: Click en botón "+"
- [ ] **Llenar formulario**: Nombre, contenido, categoría, tipo, tags
- [ ] **Auto-guardado**: Esperar 5 segundos, verificar en BD
- [ ] **Cambiar de pestaña**: Verificar que se mantiene el contenido
- [ ] **Guardar como item**: Click en "Guardar", verificar en tabla `items`
- [ ] **Cerrar pestaña**: Confirmar que se elimina de BD
- [ ] **Cerrar y reabrir**: Verificar que las tabs persisten
- [ ] **Workarea**: Verificar que otras apps se ajustan (si está activado)
- [ ] **Hotkey Ctrl+Shift+N**: Verificar que abre/cierra notebook
- [ ] **Arrastrar ventana**: Verificar que se puede mover
- [ ] **Items sensibles**: Verificar que se cifran correctamente
- [ ] **Límite de tabs**: Intentar crear más de 10 tabs

---

## 📊 FASE 8: OPTIMIZACIONES (1-2 horas)

### ✅ 8.1 Optimización de auto-guardado

Implementar debouncing para evitar escrituras excesivas:

```python
class NotebookWindow:
    def setup_autosave(self):
        """Setup con debouncing"""
        self.autosave_timer = QTimer()
        self.autosave_timer.setSingleShot(True)
        self.autosave_timer.timeout.connect(self.autosave_all_tabs)

        # Conectar señales con debounce
        for i in range(self.tab_widget.count()):
            tab = self.tab_widget.widget(i)
            tab.content_changed.connect(self.schedule_autosave)

    def schedule_autosave(self):
        """Programar auto-guardado con debounce"""
        self.autosave_timer.start(NOTEBOOK_AUTOSAVE_INTERVAL)
```

### ✅ 8.2 Añadir indicador visual de guardado

```python
class NotebookTab:
    def __init__(self, ...):
        # ...
        self.has_unsaved_changes = False
        self.create_save_indicator()

    def create_save_indicator(self):
        """Crear indicador de guardado"""
        self.save_indicator = QLabel()
        self.save_indicator.setFixedSize(16, 16)
        self.update_save_indicator(saved=True)

    def update_save_indicator(self, saved=True):
        """Actualizar indicador"""
        if saved:
            self.save_indicator.setText("✅")
            self.save_indicator.setToolTip("Guardado")
        else:
            self.save_indicator.setText("●")
            self.save_indicator.setToolTip("Cambios sin guardar")

    def on_content_modified(self):
        """Marcar como modificado"""
        self.has_unsaved_changes = True
        self.update_save_indicator(saved=False)
        self.content_changed.emit(self.get_data())
```

### ✅ 8.3 Caché de categorías

```python
class NotebookWindow:
    def __init__(self, ...):
        # Cache de categorías
        self._categories_cache = None

    def get_categories(self):
        """Obtener categorías con caché"""
        if self._categories_cache is None:
            self._categories_cache = self.controller.get_categories()
        return self._categories_cache
```

---

## 📚 FASE 9: DOCUMENTACIÓN (1 hora)

### ✅ 9.1 Actualizar CLAUDE.md

Agregar sección sobre notebook:

```markdown
### Notebook System

The application includes a multi-tab notebook for creating items:

**Components:**
- `NotebookWindow`: Main notebook window with tabs
- `NotebookTab`: Individual tab widget with form
- `NotebookManager`: Business logic for tabs CRUD
- `WorkareaManager`: Windows workspace manipulation (optional)

**Database:**
- `notebook_tabs`: Persistent tabs storage (temporary drafts)
- Auto-save every 5 seconds
- Convert tabs to items with "Save" button

**Usage:**
- Click 📓 icon in sidebar to toggle notebook
- Hotkey: `Ctrl+Shift+N`
- Tabs persist between sessions
- Can reserve screen space (pushes other apps)
```

### ✅ 9.2 Crear guía de usuario

**Archivo:** `util/documentacion/GUIA_NOTEBOOK.md`

```markdown
# 📓 Guía de Uso - Bloc de Notas

## Descripción

El bloc de notas permite crear múltiples borradores en pestañas que se guardan automáticamente. Cuando estés listo, puedes convertir cualquier nota en un item definitivo.

## Abrir el Bloc de Notas

- **Método 1:** Click en el ícono 📓 en la barra lateral
- **Método 2:** Presiona `Ctrl+Shift+N`

## Trabajar con Pestañas

### Crear Nueva Pestaña
- Click en botón "+ Nueva Nota"
- Límite: 10 pestañas simultáneas

### Cerrar Pestaña
- Click en la "X" de la pestaña
- Confirmará si hay contenido no guardado

### Cambiar Orden
- Arrastra las pestañas para reordenarlas

## Llenar el Formulario

1. **Nombre del ítem**: Título descriptivo
2. **Contenido**: Texto principal (comandos, URLs, notas, etc.)
3. **Categoría**: Selecciona categoría destino
4. **Tipo**: TEXT, CODE, URL, PATH
5. **Tags** (opcional): Etiquetas separadas por comas
6. **Descripción** (opcional): Descripción breve
7. **Opciones**:
   - 🔒 **Sensible**: Cifra el contenido
   - ✅ **Activo**: El item puede ser usado
   - 📦 **Archivado**: Oculta de la vista

## Auto-Guardado

- Las pestañas se guardan automáticamente cada 5 segundos
- El contenido NO se pierde si cierras la aplicación
- Los borradores persisten entre sesiones

## Guardar como Item Definitivo

1. Llena todos los campos requeridos
2. Click en "💾 Guardar como Item"
3. El item se crea en la categoría seleccionada
4. Opcionalmente puedes limpiar la pestaña para crear otra nota

## Reservar Espacio en Pantalla

El notebook puede "empujar" otras aplicaciones para reservar su espacio:

**Activar/Desactivar:**
- Ve a Configuración → General
- Activa "Reservar espacio para notebook"

Cuando está activado, otras ventanas se ajustarán automáticamente.

## Atajos de Teclado

- `Ctrl+Shift+N`: Abrir/cerrar notebook
- `Ctrl+T`: Nueva pestaña (dentro del notebook)
- `Ctrl+W`: Cerrar pestaña actual
- `Ctrl+S`: Guardar como item

## Consejos

- Usa el notebook como bloc de borradores temporal
- Trabaja en múltiples items en paralelo
- El auto-guardado protege tu trabajo
- Los items sensibles se cifran automáticamente
```

---

## ✅ FASE 10: DEPLOYMENT (30 min)

### ✅ 10.1 Actualizar build.bat

Agregar migración antes de compilar:

```batch
@echo off
echo ========================================
echo  Building Widget Sidebar v3.0
echo ========================================

echo.
echo [1/4] Running notebook migrations...
python util/migrations/run_notebook_migration.py
if errorlevel 1 (
    echo ERROR: Migration failed
    pause
    exit /b 1
)

echo.
echo [2/4] Installing dependencies...
pip install -r requirements.txt

echo.
echo [3/4] Building executable...
pyinstaller widget_sidebar.spec

echo.
echo [4/4] Build complete!
echo.
echo Output: dist\WidgetSidebar.exe
pause
```

### ✅ 10.2 Actualizar spec file

Asegurar que se incluyan los nuevos archivos:

```python
# widget_sidebar.spec
added_files = [
    ('default_categories.json', '.'),
    ('.env', '.'),
    ('src/views/widgets/*', 'views/widgets'),  # Incluir notebook_tab
    ('src/database/migrations/*', 'database/migrations'),
]
```

### ✅ 10.3 Crear release notes

**Archivo:** `CHANGELOG.md`

```markdown
## v3.0.0 - Notebook Edition (2025-11-03)

### ✨ Nuevas Características

- **📓 Bloc de Notas Multi-Pestaña**
  - Sistema de pestañas persistentes para borradores
  - Auto-guardado cada 5 segundos
  - Formulario completo para crear items con todos los campos
  - Soporte para hasta 10 pestañas simultáneas
  - Hotkey global: `Ctrl+Shift+N`

- **💾 Guardado Flexible**
  - Borradores persisten entre sesiones
  - Conversión de notas a items definitivos
  - Opción de limpiar pestaña después de guardar

- **🖥️ Reserva de Espacio (Opcional)**
  - Manipulación del workspace de Windows
  - Otras aplicaciones se ajustan automáticamente
  - Configurable en Settings

### 🔧 Cambios Técnicos

- Nueva tabla `notebook_tabs` en base de datos
- `NotebookManager` para lógica de negocio
- `WorkareaManager` para manipulación de Windows API
- Integración con sistema de cifrado existente

### 📚 Documentación

- Guía de usuario en `util/documentacion/GUIA_NOTEBOOK.md`
- Plan de implementación en `util/PLAN_IMPLEMENTACION_NOTEBOOK.md`
- Actualizaciones en `CLAUDE.md`
```

---

## 📋 CHECKLIST FINAL DE IMPLEMENTACIÓN

### Base de Datos
- [ ] Tabla `notebook_tabs` creada
- [ ] Settings del notebook agregadas
- [ ] Métodos CRUD en `DBManager`
- [ ] Migración ejecutada exitosamente

### Componentes UI
- [ ] `NotebookTab` widget completado
- [ ] `NotebookWindow` implementada
- [ ] Barra de título custom
- [ ] Sistema de pestañas funcional
- [ ] Estilos aplicados

### Lógica de Negocio
- [ ] `NotebookManager` implementado
- [ ] Auto-guardado configurado
- [ ] Conversión tab → item funcional
- [ ] Validaciones de formulario

### Integración
- [ ] Botón en sidebar agregado
- [ ] Posicionamiento correcto
- [ ] Hotkey `Ctrl+Shift+N` funcional
- [ ] Señales conectadas
- [ ] Workarea manager integrado (opcional)

### Testing
- [ ] Tests unitarios pasando
- [ ] Test de integración exitoso
- [ ] Testing manual completado
- [ ] Sin memory leaks

### Documentación
- [ ] `CLAUDE.md` actualizado
- [ ] Guía de usuario creada
- [ ] Release notes escritas
- [ ] Comentarios en código

### Deployment
- [ ] `build.bat` actualizado
- [ ] `.spec` file configurado
- [ ] Ejecutable compilado y probado
- [ ] Instalador creado (si aplica)

---

## 🎯 MÉTRICAS DE ÉXITO

- ✅ Notebook se abre en <500ms
- ✅ Auto-guardado no bloquea UI
- ✅ Pestañas persisten correctamente
- ✅ Items se crean con todos los campos
- ✅ Workarea se restaura al cerrar
- ✅ Sin errores en logs durante uso normal
- ✅ Uso de memoria <50MB adicional

---

## 🚨 RIESGOS Y MITIGACIONES

### Riesgo 1: Workarea no se restaura
**Mitigación:**
- Guardar estado original al inicio
- Implementar `__del__` en `WorkareaManager`
- Agregar restore en `closeEvent`

### Riesgo 2: Pérdida de datos en auto-guardado
**Mitigación:**
- Usar transacciones SQLite
- Try-catch en `autosave_all_tabs`
- Logs detallados de errores

### Riesgo 3: Rendimiento con muchas tabs
**Mitigación:**
- Límite de 10 tabs
- Caché de categorías
- Debouncing en auto-guardado

### Riesgo 4: Conflictos con items existentes
**Mitigación:**
- Validación de nombres únicos
- Confirmación antes de sobrescribir
- Opción de "Guardar como nuevo"

---

## 📞 SOPORTE POST-IMPLEMENTACIÓN

### Debugging
```python
# Activar logs detallados
import logging
logging.getLogger('notebook_manager').setLevel(logging.DEBUG)
```

### Queries útiles
```sql
-- Ver todas las tabs
SELECT * FROM notebook_tabs ORDER BY position;

-- Ver tabs huérfanas (sin categoría)
SELECT * FROM notebook_tabs WHERE category_id IS NULL;

-- Limpiar tabs antiguas (>30 días)
DELETE FROM notebook_tabs WHERE updated_at < datetime('now', '-30 days');
```

### Performance
```python
# Ver tiempo de auto-guardado
import time
start = time.time()
self.autosave_all_tabs()
print(f"Autosave took {time.time() - start:.3f}s")
```

---

## 🎉 FIN DEL PLAN

**Tiempo total estimado:** 15-20 horas
**Complejidad:** Alta
**Prioridad:** Alta
**Status:** ⏳ Pendiente

**Siguiente paso:** Ejecutar Fase 0 - Análisis y Preparación
