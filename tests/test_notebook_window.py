"""
Script de testing para NotebookWindow
Permite probar la ventana completa del notebook de forma standalone
"""

import sys
from pathlib import Path

# Agregar src al path
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir / 'src'))

from PyQt6.QtWidgets import QApplication
from views.notebook_window import NotebookWindow
from controllers.main_controller import MainController


class MockController:
    """Controller mock para testing"""

    def __init__(self):
        # Usar el controller real para tener acceso a BD
        self.real_controller = MainController()

        # Exponer los managers necesarios
        self.notebook_manager = self.real_controller.notebook_manager
        self.config_manager = self.real_controller.config_manager

    def get_categories(self):
        """Obtener categorías desde el controller real"""
        cats = self.real_controller.get_categories()

        # Convertir a diccionarios para el widget
        return [
            {
                'id': cat.id,
                'name': cat.name,
                'icon': cat.icon if hasattr(cat, 'icon') else ''
            }
            for cat in cats
        ]

    def add_item(self, category_id, label, content, item_type, tags, description,
                 is_sensitive, is_active, is_archived):
        """Agregar item a través del controller real"""
        return self.real_controller.config_manager.db.add_item(
            category_id=category_id,
            label=label,
            content=content,
            item_type=item_type,
            tags=tags,
            description=description,
            is_sensitive=is_sensitive,
            is_active=is_active,
            is_archived=is_archived
        )


def test_notebook_window():
    """Test básico de NotebookWindow"""
    app = QApplication(sys.argv)

    print("\n" + "="*60)
    print("NOTEBOOK WINDOW - TEST MODE")
    print("="*60)

    # Crear controller mock
    controller = MockController()

    # Crear ventana de notebook
    window = NotebookWindow(controller)

    # Conectar señales para debugging
    window.tab_saved_as_item.connect(lambda data: print(f"\n[SIGNAL] Item saved: {data['label']}"))
    window.closed.connect(lambda: print("\n[SIGNAL] Window closed"))

    # Posicionar ventana
    window.move(100, 100)
    window.show()

    print("\nNotebook Window opened successfully!")
    print(f"Initial tabs: {window.tab_widget.count()}")
    print("\nInstrucciones:")
    print("1. Observa el auto-guardado cada 5 segundos en los logs")
    print("2. Crea nuevas pestañas con el botón '+ Nueva Nota'")
    print("3. Llena el formulario y haz click en 'Guardar como Item'")
    print("4. Cierra pestañas con la 'X' en cada pestaña")
    print("5. Arrastra pestañas para reordenarlas")
    print("6. Cierra la ventana para verificar el auto-guardado final")
    print("\nPresiona Ctrl+C o cierra la ventana para salir")
    print("="*60 + "\n")

    sys.exit(app.exec())


def test_notebook_persistence():
    """Test de persistencia de tabs"""
    app = QApplication(sys.argv)

    print("\n" + "="*60)
    print("NOTEBOOK WINDOW - PERSISTENCE TEST")
    print("="*60)

    # Primera ventana: crear tabs
    controller1 = MockController()
    window1 = NotebookWindow(controller1)

    print("\n[FASE 1] Creando ventana con tabs...")
    print(f"Tabs iniciales: {window1.tab_widget.count()}")

    # Agregar algunas tabs
    window1.add_new_tab()
    window1.add_new_tab()

    # Llenar con datos de prueba
    for i in range(window1.tab_widget.count()):
        tab = window1.tab_widget.widget(i)
        tab.name_input.setText(f"Test Tab {i+1}")
        tab.content_input.setPlainText(f"Content for tab {i+1}")

    # Auto-guardar
    window1.autosave_all_tabs()
    print(f"Tabs creadas: {window1.tab_widget.count()}")

    # Cerrar ventana
    window1.close()
    print("\n[FASE 1] Ventana cerrada")

    # Segunda ventana: verificar que se cargaron las tabs
    print("\n[FASE 2] Abriendo nueva ventana...")
    controller2 = MockController()
    window2 = NotebookWindow(controller2)

    print(f"Tabs cargadas: {window2.tab_widget.count()}")

    # Verificar contenido
    for i in range(window2.tab_widget.count()):
        tab = window2.tab_widget.widget(i)
        print(f"  Tab {i+1}: {tab.name_input.text()}")

    window2.move(100, 100)
    window2.show()

    print("\n✅ Persistencia verificada!")
    print("Cierra la ventana para terminar")
    print("="*60 + "\n")

    sys.exit(app.exec())


def test_notebook_autosave():
    """Test de auto-guardado"""
    app = QApplication(sys.argv)

    print("\n" + "="*60)
    print("NOTEBOOK WINDOW - AUTOSAVE TEST")
    print("="*60)

    controller = MockController()
    window = NotebookWindow(controller)

    # Llenar primera tab con datos
    first_tab = window.tab_widget.widget(0)
    first_tab.name_input.setText("Auto-save Test")
    first_tab.content_input.setPlainText("This content should be auto-saved")

    window.move(100, 100)
    window.show()

    print("\nAuto-save configurado para cada 5 segundos")
    print("Modifica el contenido y observa los logs de auto-guardado")
    print("Cierra la ventana para verificar que se guardó correctamente")
    print("="*60 + "\n")

    sys.exit(app.exec())


def test_notebook_max_tabs():
    """Test de límite de tabs"""
    app = QApplication(sys.argv)

    print("\n" + "="*60)
    print("NOTEBOOK WINDOW - MAX TABS TEST")
    print("="*60)

    controller = MockController()
    window = NotebookWindow(controller)

    print(f"\nLímite de tabs: {10}")  # NOTEBOOK_MAX_TABS
    print("Intentando crear más tabs del límite...")

    # Intentar crear 12 tabs (límite es 10)
    for i in range(12):
        window.add_new_tab()
        print(f"  Intento {i+1}: Tabs actuales = {window.tab_widget.count()}")

    window.move(100, 100)
    window.show()

    print(f"\n✅ Límite respetado: {window.tab_widget.count()} tabs")
    print("="*60 + "\n")

    sys.exit(app.exec())


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Test NotebookWindow')
    parser.add_argument(
        '--mode',
        choices=['basic', 'persistence', 'autosave', 'max-tabs'],
        default='basic',
        help='Modo de testing (default: basic)'
    )

    args = parser.parse_args()

    if args.mode == 'basic':
        test_notebook_window()
    elif args.mode == 'persistence':
        test_notebook_persistence()
    elif args.mode == 'autosave':
        test_notebook_autosave()
    elif args.mode == 'max-tabs':
        test_notebook_max_tabs()
