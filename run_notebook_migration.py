"""
Script temporal para ejecutar la migración de notebook_tabs
"""
import sqlite3
import sys
from pathlib import Path

# Agregar el directorio src al path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

# Importar la migración
from database.migrations.add_notebook_tabs_table import upgrade

# Conectar a la base de datos
db_path = Path(__file__).parent / 'widget_sidebar.db'
print(f"Conectando a base de datos: {db_path}")

conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row

try:
    # Ejecutar la migración
    print("\n=== Ejecutando migración add_notebook_tabs_table ===\n")
    upgrade(conn)
    conn.commit()
    print("\n=== Migración completada exitosamente ===\n")
except Exception as e:
    print(f"\n[ERROR] Error al ejecutar migración: {e}")
    conn.rollback()
finally:
    conn.close()
    print("Conexión cerrada")
