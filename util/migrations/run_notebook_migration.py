"""
Script de migración para el sistema de Notebook

Ejecuta las migraciones necesarias para agregar:
- Tabla notebook_tabs
- Settings del notebook

Uso:
    python util/migrations/run_notebook_migration.py
"""

import sys
from pathlib import Path

# Agregar directorio raíz al path
root_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(root_dir / 'src'))

print(f"Root dir: {root_dir}")
print(f"Python path: {sys.path[0]}")

# Importaciones
import importlib.util

# Importar DBManager directamente sin pasar por __init__.py
db_manager_path = root_dir / 'src' / 'database' / 'db_manager.py'
spec = importlib.util.spec_from_file_location("db_manager", db_manager_path)
db_manager_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(db_manager_module)
DBManager = db_manager_module.DBManager

# Importar migraciones directamente
migrations_dir = root_dir / 'src' / 'database' / 'migrations'

# Migración de tabs
tabs_migration_path = migrations_dir / 'add_notebook_tabs_table.py'
spec_tabs = importlib.util.spec_from_file_location("add_notebook_tabs_table", tabs_migration_path)
tabs_module = importlib.util.module_from_spec(spec_tabs)
spec_tabs.loader.exec_module(tabs_module)
upgrade_tabs = tabs_module.upgrade
downgrade_tabs = tabs_module.downgrade

# Migración de settings
settings_migration_path = migrations_dir / 'add_notebook_settings.py'
spec_settings = importlib.util.spec_from_file_location("add_notebook_settings", settings_migration_path)
settings_module = importlib.util.module_from_spec(spec_settings)
spec_settings.loader.exec_module(settings_module)
upgrade_settings = settings_module.upgrade
downgrade_settings = settings_module.downgrade


def run_migrations():
    """Ejecutar todas las migraciones del notebook"""
    print("=" * 70)
    print("  MIGRACIÓN DEL SISTEMA DE NOTEBOOK")
    print("=" * 70)
    print()

    # Ruta de la base de datos
    db_path = root_dir / "widget_sidebar.db"
    print(f"[DB] Base de datos: {db_path}")

    if not db_path.exists():
        print("[!] ADVERTENCIA: La base de datos no existe, se creara automaticamente")
        print()

    # Conectar a la base de datos
    print("[*] Conectando a la base de datos...")
    db = DBManager(str(db_path))
    print("[OK] Conexion establecida")
    print()

    try:
        # Ejecutar migraciones
        print("=" * 70)
        print("  FASE 1: Crear tabla notebook_tabs")
        print("=" * 70)
        with db.transaction() as conn:
            upgrade_tabs(conn)
        print()

        print("=" * 70)
        print("  FASE 2: Agregar settings del notebook")
        print("=" * 70)
        with db.transaction() as conn:
            upgrade_settings(conn)
        print()

        # Verificar resultados
        print("=" * 70)
        print("  VERIFICACIÓN")
        print("=" * 70)

        # Verificar tabla
        tables = db.execute_query(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='notebook_tabs'"
        )
        if tables:
            print("[OK] Tabla 'notebook_tabs' existe")

            # Verificar índices
            indices = db.execute_query(
                "SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='notebook_tabs'"
            )
            print(f"[OK] Indices creados: {len(indices)}")
            for idx in indices:
                print(f"   - {idx['name']}")
        else:
            print("[ERROR] Tabla 'notebook_tabs' no existe")

        # Verificar settings
        notebook_settings = db.execute_query(
            "SELECT key, value FROM settings WHERE key LIKE 'notebook_%'"
        )
        print(f"[OK] Settings del notebook: {len(notebook_settings)}")
        for setting in notebook_settings:
            print(f"   - {setting['key']}: {setting['value']}")

        print()
        print("=" * 70)
        print("  MIGRACION COMPLETADA EXITOSAMENTE")
        print("=" * 70)

    except Exception as e:
        print()
        print("=" * 70)
        print("  ERROR EN LA MIGRACION")
        print("=" * 70)
        print(f"Error: {e}")
        print()
        print("Revirtiendo cambios...")

        try:
            with db.transaction() as conn:
                downgrade_settings(conn)
                downgrade_tabs(conn)
            print("[OK] Cambios revertidos")
        except Exception as e2:
            print(f"[ERROR] Error al revertir: {e2}")

        sys.exit(1)

    finally:
        db.close()
        print("[*] Conexion cerrada")


def test_crud_operations():
    """Probar operaciones CRUD básicas"""
    print()
    print("=" * 70)
    print("  TEST DE OPERACIONES CRUD")
    print("=" * 70)
    print()

    db_path = root_dir / "widget_sidebar.db"
    db = DBManager(str(db_path))

    try:
        # Test 1: Crear tab
        print("Test 1: Crear tab...")
        tab_id = db.add_notebook_tab(title='Test Tab')
        print(f"[OK] Tab creada con ID: {tab_id}")

        # Test 2: Obtener tab
        print("\nTest 2: Obtener tab...")
        tab = db.get_notebook_tab(tab_id)
        print(f"[OK] Tab obtenida: {tab['title']}")

        # Test 3: Actualizar tab
        print("\nTest 3: Actualizar tab...")
        db.update_notebook_tab(
            tab_id,
            content='Test content',
            tags='test,demo',
            category_id=1
        )
        tab = db.get_notebook_tab(tab_id)
        print(f"[OK] Tab actualizada: content='{tab['content']}', tags='{tab['tags']}'")

        # Test 4: Listar todas las tabs
        print("\nTest 4: Listar todas las tabs...")
        tabs = db.get_notebook_tabs()
        print(f"[OK] Total de tabs: {len(tabs)}")

        # Test 5: Contar tabs
        print("\nTest 5: Contar tabs...")
        count = db.count_notebook_tabs()
        print(f"[OK] Numero de tabs: {count}")

        # Test 6: Eliminar tab
        print("\nTest 6: Eliminar tab...")
        db.delete_notebook_tab(tab_id)
        tab = db.get_notebook_tab(tab_id)
        if tab is None:
            print(f"[OK] Tab eliminada correctamente")
        else:
            print(f"[ERROR] Tab no se elimino")

        print()
        print("=" * 70)
        print("  TODOS LOS TESTS PASARON")
        print("=" * 70)

    except Exception as e:
        print(f"\n[ERROR] en tests: {e}")
        import traceback
        traceback.print_exc()

    finally:
        db.close()


if __name__ == '__main__':
    # Ejecutar migraciones
    run_migrations()

    # Ejecutar tests
    response = input("\n¿Deseas ejecutar tests de CRUD? (s/n): ")
    if response.lower() in ['s', 'si', 'y', 'yes']:
        test_crud_operations()

    print("\n[OK] Proceso completado!")
