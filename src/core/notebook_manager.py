"""
NotebookManager - Gestión de pestañas del notebook
Capa de lógica de negocio para operaciones de notebook tabs
"""

from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class NotebookManager:
    """Manager para operaciones de notebook tabs"""

    def __init__(self, db_manager):
        """
        Inicializar NotebookManager

        Args:
            db_manager: Instancia de DBManager
        """
        self.db = db_manager
        logger.info("NotebookManager initialized")

    def get_all_tabs(self):
        """
        Obtener todas las pestañas ordenadas por posición

        Returns:
            List[Dict]: Lista de pestañas
        """
        tabs = self.db.get_notebook_tabs(order_by='position')
        logger.debug(f"Retrieved {len(tabs)} tabs")
        return tabs

    def get_tab(self, tab_id):
        """
        Obtener una pestaña específica

        Args:
            tab_id: ID de la pestaña

        Returns:
            Optional[Dict]: Datos de la pestaña o None
        """
        tab = self.db.get_notebook_tab(tab_id)
        if tab:
            logger.debug(f"Retrieved tab {tab_id}: {tab.get('title', 'Untitled')}")
        else:
            logger.warning(f"Tab {tab_id} not found")
        return tab

    def create_tab(self, title='Sin titulo'):
        """
        Crear nueva pestaña vacía

        Args:
            title: Título de la pestaña (default: 'Sin titulo')

        Returns:
            int: ID de la pestaña creada
        """
        tab_id = self.db.add_notebook_tab(title=title)
        logger.info(f"Created new tab: {title} (ID: {tab_id})")
        return tab_id

    def update_tab(self, tab_id, **fields):
        """
        Actualizar campos de una pestaña

        Args:
            tab_id: ID de la pestaña
            **fields: Campos a actualizar

        Returns:
            bool: True si se actualizó correctamente
        """
        success = self.db.update_notebook_tab(tab_id, **fields)

        if success:
            logger.debug(f"Updated tab {tab_id}")
        else:
            logger.warning(f"Failed to update tab {tab_id}")

        return success

    def delete_tab(self, tab_id):
        """
        Eliminar una pestaña

        Args:
            tab_id: ID de la pestaña

        Returns:
            bool: True si se eliminó correctamente
        """
        success = self.db.delete_notebook_tab(tab_id)

        if success:
            logger.info(f"Deleted tab {tab_id}")
        else:
            logger.warning(f"Failed to delete tab {tab_id}")

        return success

    def reorder_tabs(self, tab_ids_in_order):
        """
        Reordenar pestañas según lista de IDs

        Args:
            tab_ids_in_order: Lista de IDs en el orden deseado

        Returns:
            bool: True si se reordenó correctamente
        """
        success = self.db.reorder_notebook_tabs(tab_ids_in_order)

        if success:
            logger.info(f"Reordered {len(tab_ids_in_order)} tabs")
        else:
            logger.warning("Failed to reorder tabs")

        return success

    def get_tab_count(self):
        """
        Obtener número de pestañas

        Returns:
            int: Número de pestañas
        """
        count = self.db.count_notebook_tabs()
        logger.debug(f"Tab count: {count}")
        return count

    def convert_tab_to_item(self, tab_id, delete_after=False):
        """
        Convertir una pestaña en un item definitivo

        Args:
            tab_id: ID de la pestaña
            delete_after: Si True, elimina la pestaña después de convertir

        Returns:
            int: ID del item creado

        Raises:
            ValueError: Si la pestaña no existe o falta información requerida
        """
        tab_data = self.get_tab(tab_id)

        if not tab_data:
            raise ValueError(f"Tab {tab_id} not found")

        # Validar datos requeridos
        if not tab_data.get('title') or not tab_data.get('content'):
            raise ValueError("Tab must have title and content")

        if not tab_data.get('category_id'):
            raise ValueError("Tab must have a category")

        # Crear item
        try:
            # Parsear tags si es string
            tags = tab_data.get('tags', '')
            if isinstance(tags, str):
                tags = [t.strip() for t in tags.split(',') if t.strip()]

            item_id = self.db.add_item(
                category_id=tab_data['category_id'],
                label=tab_data['title'],
                content=tab_data['content'],
                item_type=tab_data.get('item_type', 'TEXT'),
                tags=tags,
                description=tab_data.get('description', ''),
                is_sensitive=bool(tab_data.get('is_sensitive', 0)),
                is_active=bool(tab_data.get('is_active', 1)),
                is_archived=bool(tab_data.get('is_archived', 0))
            )

            logger.info(f"Converted tab {tab_id} to item {item_id}")

            # Eliminar pestaña si se solicita
            if delete_after:
                self.delete_tab(tab_id)
                logger.debug(f"Deleted tab {tab_id} after conversion")

            return item_id

        except Exception as e:
            logger.error(f"Error converting tab {tab_id} to item: {e}", exc_info=True)
            raise

    def clear_empty_tabs(self):
        """
        Eliminar pestañas vacías (sin título ni contenido)

        Returns:
            int: Número de pestañas eliminadas
        """
        tabs = self.get_all_tabs()
        deleted_count = 0

        for tab in tabs:
            if not tab.get('title') and not tab.get('content'):
                self.delete_tab(tab['id'])
                deleted_count += 1

        if deleted_count > 0:
            logger.info(f"Cleared {deleted_count} empty tabs")

        return deleted_count

    def get_tabs_by_category(self, category_id):
        """
        Obtener pestañas que pertenecen a una categoría específica

        Args:
            category_id: ID de la categoría

        Returns:
            List[Dict]: Lista de pestañas de esa categoría
        """
        all_tabs = self.get_all_tabs()
        category_tabs = [
            tab for tab in all_tabs
            if tab.get('category_id') == category_id
        ]

        logger.debug(f"Found {len(category_tabs)} tabs for category {category_id}")
        return category_tabs
