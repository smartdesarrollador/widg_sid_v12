"""
Migración: Agregar tabla notebook_tabs para pestañas persistentes
Fecha: 2025-11-03
Versión: 1.0

Esta migración crea la tabla notebook_tabs que almacena las pestañas
del bloc de notas de forma persistente. Las pestañas funcionan como
borradores temporales que pueden convertirse en items definitivos.
"""


def upgrade(conn):
    """Crear tabla notebook_tabs"""
    print("[*] Creando tabla notebook_tabs...")

    conn.execute("""
        CREATE TABLE IF NOT EXISTS notebook_tabs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL DEFAULT 'Sin titulo',
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

    print("[*] Creando indices para optimizar consultas...")

    # Índices para optimizar consultas
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_notebook_tabs_position
        ON notebook_tabs(position)
    """)

    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_notebook_tabs_category
        ON notebook_tabs(category_id)
    """)

    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_notebook_tabs_updated
        ON notebook_tabs(updated_at)
    """)

    print("[OK] Tabla notebook_tabs creada exitosamente")
    print("[OK] Indices creados exitosamente")


def downgrade(conn):
    """Revertir migración"""
    print("[!] Eliminando tabla notebook_tabs...")

    # Eliminar índices primero
    conn.execute("DROP INDEX IF EXISTS idx_notebook_tabs_position")
    conn.execute("DROP INDEX IF EXISTS idx_notebook_tabs_category")
    conn.execute("DROP INDEX IF EXISTS idx_notebook_tabs_updated")

    # Eliminar tabla
    conn.execute("DROP TABLE IF EXISTS notebook_tabs")

    print("[OK] Tabla notebook_tabs eliminada")
