"""
Script de testing para NotebookTab widget
Permite probar el widget de forma standalone
"""

import sys
from pathlib import Path

# Agregar src al path
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir / 'src'))

from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QLabel
from PyQt6.QtCore import Qt
from views.widgets.notebook_tab import NotebookTab


class TestWindow(QMainWindow):
    """Ventana de prueba para el widget NotebookTab"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Test - NotebookTab Widget")
        self.setGeometry(100, 100, 500, 700)

        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)

        # Header
        header = QLabel("NotebookTab Widget Test")
        header.setStyleSheet("""
            QLabel {
                background-color: #2D2D2D;
                color: #FFFFFF;
                padding: 15px;
                font-size: 16px;
                font-weight: bold;
            }
        """)
        layout.addWidget(header)

        # Mock categories para testing
        mock_categories = [
            {'id': 1, 'name': 'Git', 'icon': '🔧'},
            {'id': 2, 'name': 'Docker', 'icon': '🐳'},
            {'id': 3, 'name': 'Python', 'icon': '🐍'},
            {'id': 4, 'name': 'JavaScript', 'icon': '⚡'},
            {'id': 5, 'name': 'Linux', 'icon': '🐧'},
        ]

        # Crear widget NotebookTab
        self.notebook_tab = NotebookTab(
            tab_id=1,
            categories=mock_categories
        )

        # Conectar señales para debugging
        self.notebook_tab.save_requested.connect(self.on_save_requested)
        self.notebook_tab.content_changed.connect(self.on_content_changed)
        self.notebook_tab.cancel_requested.connect(self.on_cancel_requested)

        layout.addWidget(self.notebook_tab)

        # Estilo de ventana
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1E1E1E;
            }
        """)

    def on_save_requested(self, data):
        """Callback cuando se solicita guardar"""
        print("\n" + "="*60)
        print("SAVE REQUESTED")
        print("="*60)
        print(f"Label: {data['label']}")
        print(f"Content: {data['content'][:100]}..." if len(data['content']) > 100 else f"Content: {data['content']}")
        print(f"Category ID: {data['category_id']}")
        print(f"Type: {data['item_type']}")
        print(f"Tags: {data['tags']}")
        print(f"Description: {data['description']}")
        print(f"Is Sensitive: {data['is_sensitive']}")
        print(f"Is Active: {data['is_active']}")
        print(f"Is Archived: {data['is_archived']}")
        print("="*60)

    def on_content_changed(self, data):
        """Callback cuando cambia el contenido (auto-guardado)"""
        print(f"[AUTO-SAVE] Content changed - Label: '{data['label']}'")

    def on_cancel_requested(self):
        """Callback cuando se hace click en cancelar"""
        print("[CANCEL] Cancel button clicked")


def test_widget_basic():
    """Test básico del widget"""
    app = QApplication(sys.argv)

    # Crear ventana de test
    window = TestWindow()
    window.show()

    print("\n" + "="*60)
    print("NOTEBOOK TAB WIDGET - TEST MODE")
    print("="*60)
    print("\nInstrucciones:")
    print("1. Llena el formulario con datos de prueba")
    print("2. Observa la consola para ver los eventos de auto-guardado")
    print("3. Click en 'Guardar como Item' para ver los datos capturados")
    print("4. Click en 'Cancelar' para probar el evento de cancelación")
    print("\nPresiona Ctrl+C o cierra la ventana para salir")
    print("="*60 + "\n")

    sys.exit(app.exec())


def test_widget_with_data():
    """Test del widget con datos pre-cargados"""
    app = QApplication(sys.argv)

    # Crear ventana de test
    window = TestWindow()

    # Cargar datos de prueba
    test_data = {
        'title': 'Comando Git Push',
        'content': 'git add .\ngit commit -m "mensaje"\ngit push origin main',
        'category_id': 1,  # Git
        'item_type': 'CODE',
        'tags': 'git, versionado, deploy',
        'description': 'Comandos para hacer push a la rama main',
        'is_sensitive': False,
        'is_active': True,
        'is_archived': False
    }

    window.notebook_tab.load_data(test_data)

    window.show()

    print("\n" + "="*60)
    print("NOTEBOOK TAB WIDGET - TEST MODE (WITH DATA)")
    print("="*60)
    print("\nDatos pre-cargados:")
    print(f"- Título: {test_data['title']}")
    print(f"- Tipo: {test_data['item_type']}")
    print(f"- Tags: {test_data['tags']}")
    print("\nModifica los datos y observa el auto-guardado en la consola")
    print("="*60 + "\n")

    sys.exit(app.exec())


def test_form_validation():
    """Test de validación del formulario"""
    app = QApplication(sys.argv)

    window = TestWindow()
    window.show()

    print("\n" + "="*60)
    print("NOTEBOOK TAB WIDGET - VALIDATION TEST")
    print("="*60)
    print("\nPrueba de validación:")
    print("1. Intenta guardar sin llenar el nombre (debe fallar)")
    print("2. Intenta guardar sin llenar el contenido (debe fallar)")
    print("3. Llena ambos campos y guarda (debe funcionar)")
    print("\nObserva los warnings en la consola")
    print("="*60 + "\n")

    sys.exit(app.exec())


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Test NotebookTab Widget')
    parser.add_argument(
        '--mode',
        choices=['basic', 'with-data', 'validation'],
        default='basic',
        help='Modo de testing (default: basic)'
    )

    args = parser.parse_args()

    if args.mode == 'basic':
        test_widget_basic()
    elif args.mode == 'with-data':
        test_widget_with_data()
    elif args.mode == 'validation':
        test_form_validation()
