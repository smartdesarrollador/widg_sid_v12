"""
Script para habilitar la reserva de espacio del Notebook
"""
import sqlite3
import sys
from pathlib import Path

# Agregar src al path
root_dir = Path(__file__).parent
sys.path.insert(0, str(root_dir / 'src'))

DB_PATH = root_dir / 'widget_sidebar.db'

def main():
    print("=" * 60)
    print("HABILITAR RESERVA DE ESPACIO DEL NOTEBOOK")
    print("=" * 60)

    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()

    # Verificar settings actuales del notebook
    print("\n[*] Verificando settings actuales...")
    cursor.execute("SELECT key, value FROM settings WHERE key LIKE '%notebook%'")
    settings = cursor.fetchall()

    if settings:
        print(f"\n[OK] Encontrados {len(settings)} settings del notebook:")
        for key, value in settings:
            print(f"  - {key}: {value}")
    else:
        print("\n[!] No se encontraron settings del notebook")

    # Verificar si existe notebook_reserve_workspace
    cursor.execute("SELECT value FROM settings WHERE key = 'notebook_reserve_workspace'")
    result = cursor.fetchone()

    if result:
        current_value = result[0]
        print(f"\n[*] Setting actual notebook_reserve_workspace: {current_value}")

        if current_value.lower() == 'true':
            print("[OK] El setting ya está habilitado")
        else:
            print("[*] Habilitando setting...")
            cursor.execute(
                "UPDATE settings SET value = 'true' WHERE key = 'notebook_reserve_workspace'"
            )
            conn.commit()
            print("[OK] Setting habilitado correctamente")
    else:
        print("\n[!] Setting notebook_reserve_workspace no existe")
        print("[*] Creando setting con valor 'true'...")
        cursor.execute(
            "INSERT INTO settings (key, value) VALUES ('notebook_reserve_workspace', 'true')"
        )
        conn.commit()
        print("[OK] Setting creado y habilitado")

    # Verificar resultado final
    cursor.execute("SELECT value FROM settings WHERE key = 'notebook_reserve_workspace'")
    final_value = cursor.fetchone()[0]

    print(f"\n[OK] Valor final de notebook_reserve_workspace: {final_value}")
    print("\n" + "=" * 60)
    print("CONFIGURACION COMPLETADA")
    print("=" * 60)
    print("\nAhora cuando abras el Notebook:")
    print("  1. Se reservará espacio en el escritorio (540px)")
    print("  2. Otras aplicaciones se moverán automáticamente")
    print("  3. Al cerrar el Notebook, el espacio se restaurará")
    print("\nPrueba abriendo el Notebook con el botón 📓 o Ctrl+Shift+N")

    conn.close()

if __name__ == '__main__':
    main()
