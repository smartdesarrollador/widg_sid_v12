"""
Migración: Agregar configuraciones del notebook
Fecha: 2025-11-03
Versión: 1.0

Esta migración agrega las configuraciones necesarias para el funcionamiento
del bloc de notas en la tabla settings.
"""


def upgrade(conn):
    """Agregar configuraciones del notebook"""
    print("[*] Agregando settings del notebook...")

    settings = [
        ('notebook_width', '450', 'Ancho de la ventana del notebook en pixeles'),
        ('notebook_autosave_interval', '5000', 'Intervalo de auto-guardado en milisegundos'),
        ('notebook_reserve_workspace', 'false', 'Reservar espacio en el escritorio de Windows'),
        ('notebook_last_active_tab', '0', 'Indice de la ultima pestana activa'),
        ('notebook_position', 'left', 'Posicion del notebook: left o right'),
        ('notebook_show_on_startup', 'false', 'Mostrar notebook al iniciar aplicacion'),
        ('notebook_max_tabs', '10', 'Numero maximo de pestanas permitidas'),
        ('notebook_tab_height', '600', 'Altura minima de la ventana del notebook'),
    ]

    # Verificar si la tabla settings tiene columna description
    cursor = conn.execute("PRAGMA table_info(settings)")
    columns = [row[1] for row in cursor.fetchall()]
    has_description = 'description' in columns

    for setting in settings:
        if has_description:
            key, value, description = setting
            conn.execute("""
                INSERT OR IGNORE INTO settings (key, value, description)
                VALUES (?, ?, ?)
            """, (key, value, description))
        else:
            key, value = setting[0], setting[1]
            conn.execute("""
                INSERT OR IGNORE INTO settings (key, value)
                VALUES (?, ?)
            """, (key, value))

    print("[OK] Settings del notebook agregadas:")
    for setting in settings:
        print(f"   - {setting[0]}: {setting[1]}")


def downgrade(conn):
    """Eliminar configuraciones del notebook"""
    print("[!] Eliminando settings del notebook...")

    setting_keys = [
        'notebook_width',
        'notebook_autosave_interval',
        'notebook_reserve_workspace',
        'notebook_last_active_tab',
        'notebook_position',
        'notebook_show_on_startup',
        'notebook_max_tabs',
        'notebook_tab_height',
    ]

    for key in setting_keys:
        conn.execute("DELETE FROM settings WHERE key = ?", (key,))

    print("[OK] Settings del notebook eliminadas")
