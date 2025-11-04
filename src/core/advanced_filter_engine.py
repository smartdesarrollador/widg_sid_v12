"""
Advanced Filter Engine
Motor de filtrado avanzado para items
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from models.item import Item, ItemType


class AdvancedFilterEngine:
    """
    Motor para aplicar filtros complejos a listas de items

    Soporta múltiples criterios de filtrado que se pueden combinar:
    - Tipo de item (TEXT, URL, CODE, PATH)
    - Estado (favorito, sensible, con/sin tags)
    - Uso y popularidad (use_count, last_used)
    - Tags (multi-selección con AND/OR)
    - Fechas (created_at, last_used)
    """

    def __init__(self):
        """Inicializar el motor de filtrado"""
        self.cache = {}  # Caché para resultados de filtros (optimización futura)

    def apply_filters(self, items: List[Item], filters: Dict[str, Any]) -> List[Item]:
        """
        Aplicar todos los filtros a la lista de items

        Args:
            items: Lista de items a filtrar
            filters: Diccionario con los criterios de filtrado

        Returns:
            Lista de items que cumplen todos los criterios

        Ejemplo de filters:
            {
                "type": ["TEXT", "URL"],
                "is_favorite": True,
                "tags": {"values": ["git"], "mode": "AND"},
                "use_count": {"operator": ">", "value": 5}
            }
        """
        import logging
        logger = logging.getLogger(__name__)

        logger.debug(f"apply_filters called with {len(items)} items and filters: {filters}")

        if not filters:
            return items

        filtered = items.copy()

        # Aplicar cada filtro secuencialmente
        if 'type' in filters and filters['type']:
            filtered = self._filter_by_type(filtered, filters['type'])

        if 'is_favorite' in filters and filters['is_favorite'] is not None:
            filtered = self._filter_by_favorite(filtered, filters['is_favorite'])

        if 'is_sensitive' in filters and filters['is_sensitive'] is not None:
            filtered = self._filter_by_sensitive(filtered, filters['is_sensitive'])

        if 'has_tags' in filters and filters['has_tags'] is not None:
            filtered = self._filter_by_has_tags(filtered, filters['has_tags'])

        if 'is_list' in filters and filters['is_list'] is not None:
            filtered = self._filter_by_is_list(filtered, filters['is_list'])

        if 'tags' in filters and filters['tags']:
            filtered = self._filter_by_tags(filtered, filters['tags'])

        if 'use_count' in filters and filters['use_count']:
            filtered = self._filter_by_use_count(filtered, filters['use_count'])

        if 'last_used' in filters and filters['last_used']:
            filtered = self._filter_by_last_used(filtered, filters['last_used'])

        if 'created_at' in filters and filters['created_at']:
            logger.debug(f"Applying created_at filter: {filters['created_at']}")
            before_count = len(filtered)
            filtered = self._filter_by_created_date(filtered, filters['created_at'])
            logger.debug(f"After created_at filter: {len(filtered)} items (was {before_count})")

        # Aplicar ordenamiento si se especifica
        if 'sort_by' in filters and filters['sort_by']:
            filtered = self._sort_items(filtered, filters['sort_by'])

        # Limitar a top N si se especifica
        if 'top_n' in filters and filters['top_n']:
            filtered = filtered[:filters['top_n']]

        return filtered

    def _filter_by_type(self, items: List[Item], types: List[str]) -> List[Item]:
        """
        Filtrar por tipo de item

        Args:
            items: Lista de items
            types: Lista de tipos permitidos (ej: ["TEXT", "URL"])

        Returns:
            Items que son de alguno de los tipos especificados
        """
        if not types:
            return items

        return [
            item for item in items
            if item.type.value.upper() in [t.upper() for t in types]
        ]

    def _filter_by_favorite(self, items: List[Item], is_favorite: bool) -> List[Item]:
        """
        Filtrar por items favoritos

        Args:
            items: Lista de items
            is_favorite: True para solo favoritos, False para solo no favoritos

        Returns:
            Items filtrados
        """
        import logging
        logger = logging.getLogger(__name__)
        logger.debug(f"_filter_by_favorite called with {len(items)} items, is_favorite={is_favorite}")

        filtered = [
            item for item in items
            if hasattr(item, 'is_favorite') and item.is_favorite == is_favorite
        ]

        logger.debug(f"_filter_by_favorite returning {len(filtered)} items")
        for item in items[:3]:  # Log first 3 items for debugging
            has_attr = hasattr(item, 'is_favorite')
            value = getattr(item, 'is_favorite', None) if has_attr else None
            logger.debug(f"  Item '{item.label}': has_is_favorite={has_attr}, value={value}")

        return filtered

    def _filter_by_sensitive(self, items: List[Item], is_sensitive: bool) -> List[Item]:
        """
        Filtrar por items sensibles

        Args:
            items: Lista de items
            is_sensitive: True para solo sensibles, False para solo no sensibles

        Returns:
            Items filtrados
        """
        return [
            item for item in items
            if item.is_sensitive == is_sensitive
        ]

    def _filter_by_has_tags(self, items: List[Item], has_tags: bool) -> List[Item]:
        """
        Filtrar por items con/sin tags

        Args:
            items: Lista de items
            has_tags: True para items con tags, False para items sin tags

        Returns:
            Items filtrados
        """
        if has_tags:
            return [item for item in items if item.tags and len(item.tags) > 0]
        else:
            return [item for item in items if not item.tags or len(item.tags) == 0]

    def _filter_by_is_list(self, items: List[Item], is_list: bool) -> List[Item]:
        """
        Filtrar por items que son listas

        Args:
            items: Lista de items
            is_list: True para solo listas, False para solo items normales

        Returns:
            Items filtrados
        """
        return [
            item for item in items
            if hasattr(item, 'is_list_item') and item.is_list_item() == is_list
        ]

    def _filter_by_tags(self, items: List[Item], tag_filter: Dict[str, Any]) -> List[Item]:
        """
        Filtrar por tags específicos

        Args:
            items: Lista de items
            tag_filter: Dict con "values" (lista de tags) y "mode" (AND/OR)

        Returns:
            Items filtrados

        Ejemplo:
            tag_filter = {"values": ["git", "docker"], "mode": "OR"}
        """
        if not tag_filter or 'values' not in tag_filter:
            return items

        target_tags = tag_filter['values']
        mode = tag_filter.get('mode', 'OR').upper()

        if mode == 'AND':
            # Item debe tener TODOS los tags
            return [
                item for item in items
                if item.tags and all(tag in item.tags for tag in target_tags)
            ]
        else:  # OR
            # Item debe tener AL MENOS UN tag
            return [
                item for item in items
                if item.tags and any(tag in item.tags for tag in target_tags)
            ]

    def _filter_by_use_count(self, items: List[Item], count_filter: Dict[str, Any]) -> List[Item]:
        """
        Filtrar por número de usos

        Args:
            items: Lista de items
            count_filter: Dict con "operator" y "value"

        Returns:
            Items filtrados

        Ejemplo:
            count_filter = {"operator": ">", "value": 5}
        """
        if not count_filter:
            return items

        operator = count_filter.get('operator', '>')
        value = count_filter.get('value', 0)

        filtered = []
        for item in items:
            use_count = getattr(item, 'use_count', 0)

            if operator == '>':
                if use_count > value:
                    filtered.append(item)
            elif operator == '>=':
                if use_count >= value:
                    filtered.append(item)
            elif operator == '<':
                if use_count < value:
                    filtered.append(item)
            elif operator == '<=':
                if use_count <= value:
                    filtered.append(item)
            elif operator == '=':
                if use_count == value:
                    filtered.append(item)

        return filtered

    def _filter_by_last_used(self, items: List[Item], date_filter: Dict[str, Any]) -> List[Item]:
        """
        Filtrar por fecha de último uso

        Args:
            items: Lista de items
            date_filter: Dict con preset o rango personalizado

        Returns:
            Items filtrados

        Ejemplo:
            date_filter = {"preset": "last_7_days"}
            date_filter = {"custom_from": datetime, "custom_to": datetime}
        """
        if not date_filter:
            return items

        now = datetime.now()

        # Usar preset si está disponible
        if 'preset' in date_filter:
            preset = date_filter['preset']

            if preset == 'today':
                start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
            elif preset == 'last_7_days':
                start_date = now - timedelta(days=7)
            elif preset == 'last_30_days':
                start_date = now - timedelta(days=30)
            elif preset == 'last_90_days':
                start_date = now - timedelta(days=90)
            elif preset == 'never':
                # Items nunca usados (use_count = 0)
                return [item for item in items if getattr(item, 'use_count', 0) == 0]
            else:
                return items

            return [
                item for item in items
                if hasattr(item, 'last_used') and item.last_used >= start_date
            ]

        # Usar rango personalizado
        if 'custom_from' in date_filter and 'custom_to' in date_filter:
            from_date = date_filter['custom_from']
            to_date = date_filter['custom_to']

            return [
                item for item in items
                if hasattr(item, 'last_used') and from_date <= item.last_used <= to_date
            ]

        return items

    def _filter_by_created_date(self, items: List[Item], date_filter: Dict[str, Any]) -> List[Item]:
        """
        Filtrar por fecha de creación

        Args:
            items: Lista de items
            date_filter: Dict con preset o rango personalizado

        Returns:
            Items filtrados
        """
        import logging
        logger = logging.getLogger(__name__)

        if not date_filter:
            return items

        now = datetime.now()

        # Usar preset si está disponible
        if 'preset' in date_filter:
            preset = date_filter['preset']

            if preset == 'today':
                start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
            elif preset == 'this_week':
                start_date = now - timedelta(days=now.weekday())
                start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
            elif preset == 'this_month':
                start_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            elif preset == 'last_7_days':
                start_date = now - timedelta(days=7)
            elif preset == 'last_30_days':
                start_date = now - timedelta(days=30)
            else:
                return items

            logger.debug(f"Date filter preset '{preset}': start_date={start_date}, now={now}")

            filtered = []
            for item in items:
                if hasattr(item, 'created_at') and item.created_at:
                    if item.created_at >= start_date:
                        filtered.append(item)
                        logger.debug(f"Item '{item.label}' included: created_at={item.created_at}")
                    else:
                        logger.debug(f"Item '{item.label}' excluded: created_at={item.created_at} < {start_date}")
                else:
                    logger.debug(f"Item '{item.label}' has no created_at attribute")

            return filtered

        # Usar rango personalizado
        if 'custom_from' in date_filter and 'custom_to' in date_filter:
            from_date = date_filter['custom_from']
            to_date = date_filter['custom_to']

            logger.debug(f"Date filter custom range: from={from_date}, to={to_date}")

            filtered = []
            for item in items:
                if hasattr(item, 'created_at') and item.created_at:
                    # Asegurar que created_at es datetime
                    item_date = item.created_at
                    if isinstance(item_date, str):
                        try:
                            item_date = datetime.fromisoformat(item_date.replace('Z', '+00:00'))
                        except:
                            try:
                                item_date = datetime.strptime(item_date, '%Y-%m-%d %H:%M:%S')
                            except:
                                logger.warning(f"Could not parse created_at for item '{item.label}': {item_date}")
                                continue

                    if from_date <= item_date <= to_date:
                        filtered.append(item)
                        logger.debug(f"Item '{item.label}' included: created_at={item_date}")
                    else:
                        logger.debug(f"Item '{item.label}' excluded: created_at={item_date} not in range [{from_date}, {to_date}]")
                else:
                    logger.debug(f"Item '{item.label}' has no created_at attribute")

            logger.debug(f"Filtered {len(filtered)} items out of {len(items)}")
            return filtered

        return items

    def _sort_items(self, items: List[Item], sort_by: str) -> List[Item]:
        """
        Ordenar items según criterio

        Args:
            items: Lista de items
            sort_by: Criterio de ordenamiento

        Returns:
            Items ordenados

        Opciones de sort_by:
            - use_count_desc: Más usados primero
            - use_count_asc: Menos usados primero
            - recent: Usados recientemente primero
            - oldest: Más antiguos primero
            - label_asc: Alfabético A-Z
            - label_desc: Alfabético Z-A
        """
        if sort_by == 'use_count_desc':
            return sorted(items, key=lambda x: getattr(x, 'use_count', 0), reverse=True)
        elif sort_by == 'use_count_asc':
            return sorted(items, key=lambda x: getattr(x, 'use_count', 0))
        elif sort_by == 'recent':
            return sorted(
                items,
                key=lambda x: getattr(x, 'last_used', datetime.min),
                reverse=True
            )
        elif sort_by == 'oldest':
            return sorted(
                items,
                key=lambda x: getattr(x, 'created_at', datetime.max)
            )
        elif sort_by == 'label_asc':
            return sorted(items, key=lambda x: x.label.lower())
        elif sort_by == 'label_desc':
            return sorted(items, key=lambda x: x.label.lower(), reverse=True)
        else:
            return items

    def get_available_tags(self, items: List[Item]) -> Dict[str, int]:
        """
        Obtener todos los tags únicos con su conteo de items

        Args:
            items: Lista de items

        Returns:
            Dict con tag como clave y conteo como valor

        Ejemplo:
            {"git": 15, "docker": 8, "python": 23}
        """
        tag_counts = {}

        for item in items:
            if item.tags:
                for tag in item.tags:
                    tag_counts[tag] = tag_counts.get(tag, 0) + 1

        # Ordenar por conteo descendente
        return dict(sorted(tag_counts.items(), key=lambda x: x[1], reverse=True))
