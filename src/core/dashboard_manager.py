"""
Dashboard Manager
Manages business logic for the Structure Dashboard
"""

from typing import Dict, List, Tuple
import logging

logger = logging.getLogger(__name__)


class DashboardManager:
    """Manager for dashboard data loading and processing"""

    def __init__(self, db_manager):
        """
        Initialize the dashboard manager

        Args:
            db_manager: DBManager instance for database operations
        """
        self.db = db_manager
        self._structure_cache = None
        self._statistics_cache = None
        logger.info("DashboardManager initialized")

    def get_full_structure(self, force_refresh: bool = False) -> Dict:
        """
        Get complete structure of categories and items

        Args:
            force_refresh: If True, force reload from database (default: False)

        Returns:
            Dict: Complete structure with categories and their items
                {
                    'categories': [
                        {
                            'id': int,
                            'name': str,
                            'icon': str,
                            'tags': List[str],
                            'items': [
                                {
                                    'id': int,
                                    'label': str,
                                    'content': str,
                                    'type': str,
                                    'tags': List[str],
                                    'is_favorite': bool,
                                    'is_sensitive': bool
                                },
                                ...
                            ]
                        },
                        ...
                    ]
                }
        """
        # Return cached if available and no force refresh
        if self._structure_cache and not force_refresh:
            logger.debug("Returning cached structure")
            return self._structure_cache

        logger.info("Loading full structure from database...")

        try:
            # Get all categories
            categories = self.db.get_categories()

            structure = {'categories': []}

            for category in categories:
                # Get items for this category
                items = self.db.get_items_by_category(category['id'])

                category_data = {
                    'id': category['id'],
                    'name': category['name'],
                    'icon': category.get('icon', '📁'),
                    'tags': self._parse_tags(category.get('tags', '')),
                    'is_predefined': category.get('is_predefined', False),
                    'is_active': category.get('is_active', 1),  # Agregar campo is_active
                    'items': []
                }

                # Process each item
                for item in items:
                    item_data = {
                        'id': item['id'],
                        'label': item['label'],
                        'content': item['content'],
                        'type': item['type'],
                        'tags': self._parse_tags(item.get('tags', '')),
                        'is_favorite': bool(item.get('is_favorite', 0)),
                        'is_sensitive': bool(item.get('is_sensitive', 0)),
                        'description': item.get('description', ''),
                        'is_list': bool(item.get('is_list', 0)),
                        'list_group': item.get('list_group', None),
                        'is_active': item.get('is_active', 1),  # Agregar campo is_active
                        'is_archived': bool(item.get('is_archived', 0)),  # Agregar campo is_archived
                        'use_count': item.get('use_count', 0),  # Agregar campo use_count para filtro "Más Usados"
                        'last_used': item.get('last_used', None)  # Agregar campo last_used para filtro "Recientes"
                    }
                    category_data['items'].append(item_data)

                structure['categories'].append(category_data)

            # Cache the structure
            self._structure_cache = structure

            logger.info(f"Loaded structure: {len(structure['categories'])} categories, "
                       f"{sum(len(c['items']) for c in structure['categories'])} total items")

            return structure

        except Exception as e:
            logger.error(f"Error loading full structure: {e}", exc_info=True)
            return {'categories': []}

    def calculate_statistics(self, structure: Dict = None) -> Dict:
        """
        Calculate statistics from the structure

        Args:
            structure: Optional structure dict (will load if not provided)

        Returns:
            Dict: Statistics about the data
                {
                    'total_categories': int,
                    'active_categories': int,
                    'total_items': int,
                    'total_favorites': int,
                    'total_sensitive': int,
                    'total_unique_tags': int,
                    'most_used_tag': str,
                    'avg_items_per_category': float,
                    'largest_category': Dict,
                    'type_distribution': Dict[str, int]
                }
        """
        # Return cached if available
        if self._statistics_cache and structure is None:
            logger.debug("Returning cached statistics")
            return self._statistics_cache

        if structure is None:
            structure = self.get_full_structure()

        logger.info("Calculating statistics...")

        try:
            categories = structure['categories']

            stats = {
                'total_categories': len(categories),
                'active_categories': len([c for c in categories if c['items']]),
                'total_items': 0,
                'total_favorites': 0,
                'total_sensitive': 0,
                'total_inactive': 0,  # Contador de desactivados
                'total_archived': 0,  # Contador de archivados
                'total_unique_tags': 0,
                'most_used_tag': '',
                'avg_items_per_category': 0.0,
                'largest_category': {},
                'type_distribution': {}
            }

            # Collect tags and count items
            all_tags = []
            largest_cat = None
            largest_count = 0

            type_counts = {}

            for category in categories:
                item_count = len(category['items'])
                stats['total_items'] += item_count

                # Track largest category
                if item_count > largest_count:
                    largest_count = item_count
                    largest_cat = {
                        'name': category['name'],
                        'item_count': item_count
                    }

                # Collect category tags
                all_tags.extend(category['tags'])

                for item in category['items']:
                    # Count favorites and sensitives
                    if item['is_favorite']:
                        stats['total_favorites'] += 1
                    if item['is_sensitive']:
                        stats['total_sensitive'] += 1

                    # Count inactive and archived
                    if not item.get('is_active', 1):  # Si is_active es 0 o False
                        stats['total_inactive'] += 1
                    if item.get('is_archived', False):  # Si is_archived es True
                        stats['total_archived'] += 1

                    # Collect item tags
                    all_tags.extend(item['tags'])

                    # Count item types
                    item_type = item['type']
                    type_counts[item_type] = type_counts.get(item_type, 0) + 1

            # Calculate unique tags
            unique_tags = set(all_tags)
            stats['total_unique_tags'] = len(unique_tags)

            # Find most used tag
            if all_tags:
                tag_counts = {}
                for tag in all_tags:
                    tag_counts[tag] = tag_counts.get(tag, 0) + 1
                stats['most_used_tag'] = max(tag_counts, key=tag_counts.get)

            # Average items per category
            if stats['total_categories'] > 0:
                stats['avg_items_per_category'] = round(
                    stats['total_items'] / stats['total_categories'], 1
                )

            # Largest category
            stats['largest_category'] = largest_cat or {'name': 'N/A', 'item_count': 0}

            # Type distribution
            stats['type_distribution'] = type_counts

            # Cache statistics
            self._statistics_cache = stats

            logger.info(f"Statistics calculated: {stats['total_items']} items, "
                       f"{stats['total_unique_tags']} unique tags")

            return stats

        except Exception as e:
            logger.error(f"Error calculating statistics: {e}", exc_info=True)
            return {}

    def _parse_tags(self, tags_str) -> List[str]:
        """
        Parse tags string or list into list

        Args:
            tags_str: Comma-separated tags string or list of tags

        Returns:
            List[str]: List of tag strings
        """
        if not tags_str:
            return []

        # If already a list, return it
        if isinstance(tags_str, list):
            return tags_str

        # If string, parse it
        if isinstance(tags_str, str):
            return [tag.strip() for tag in tags_str.split(',') if tag.strip()]

        return []

    def get_tag_cloud(self, structure: Dict = None) -> List[Tuple[str, int]]:
        """
        Get tag cloud data (tag name, count)

        Args:
            structure: Optional structure dict

        Returns:
            List[Tuple[str, int]]: List of (tag, count) tuples sorted by count desc
        """
        if structure is None:
            structure = self.get_full_structure()

        logger.info("Generating tag cloud...")

        try:
            tag_counts = {}

            for category in structure['categories']:
                # Count category tags
                for tag in category['tags']:
                    tag_counts[tag] = tag_counts.get(tag, 0) + 1

                # Count item tags
                for item in category['items']:
                    for tag in item['tags']:
                        tag_counts[tag] = tag_counts.get(tag, 0) + 1

            # Sort by count descending
            sorted_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)

            logger.info(f"Tag cloud generated with {len(sorted_tags)} unique tags")
            return sorted_tags

        except Exception as e:
            logger.error(f"Error generating tag cloud: {e}", exc_info=True)
            return []

    def invalidate_cache(self):
        """Invalidate all caches to force data reload"""
        self._structure_cache = None
        self._statistics_cache = None
        logger.info("Dashboard caches invalidated")

    def refresh_data(self) -> Dict:
        """
        Refresh all data from database

        Returns:
            Dict: Refreshed structure
        """
        self.invalidate_cache()
        return self.get_full_structure(force_refresh=True)

    def search(self, query: str, scope_filters: Dict, structure: Dict = None) -> List[Tuple[str, int, int]]:
        """
        Search for query in structure

        Args:
            query: Search query string
            scope_filters: Dict with boolean values for each scope
                {
                    'categories': bool,
                    'items': bool,
                    'tags': bool,
                    'content': bool
                }
            structure: Optional structure dict

        Returns:
            List[Tuple[str, int, int]]: List of (match_type, category_index, item_index)
                match_type can be: 'category', 'item', 'tag', 'content'
                item_index is -1 for category matches
        """
        if not query:
            return []

        if structure is None:
            structure = self.get_full_structure()

        logger.info(f"Searching for '{query}' with filters: {scope_filters}")

        query_lower = query.lower()
        matches = []

        categories = structure['categories']

        for cat_idx, category in enumerate(categories):
            # Search in category name
            if scope_filters.get('categories', True):
                if query_lower in category['name'].lower():
                    matches.append(('category', cat_idx, -1))
                    logger.debug(f"Category match: {category['name']}")

            # Search in category tags
            if scope_filters.get('tags', True):
                for tag in category['tags']:
                    if query_lower in tag.lower():
                        matches.append(('tag', cat_idx, -1))
                        logger.debug(f"Category tag match: {tag} in {category['name']}")
                        break  # Only count once per category

            # Search in items
            for item_idx, item in enumerate(category['items']):
                # Search in item label
                if scope_filters.get('items', True):
                    if query_lower in item['label'].lower():
                        matches.append(('item', cat_idx, item_idx))
                        logger.debug(f"Item match: {item['label']}")
                        continue  # Skip other checks for this item

                # Search in list_group (if is_list)
                if scope_filters.get('lists', True):
                    if item.get('is_list') and item.get('list_group'):
                        if query_lower in item['list_group'].lower():
                            matches.append(('list', cat_idx, item_idx))
                            logger.debug(f"List match: {item['list_group']} - {item['label']}")
                            continue

                # Search in item tags
                if scope_filters.get('tags', True):
                    for tag in item['tags']:
                        if query_lower in tag.lower():
                            matches.append(('tag', cat_idx, item_idx))
                            logger.debug(f"Item tag match: {tag} in {item['label']}")
                            break

                # Search in item content (if not sensitive)
                if scope_filters.get('content', True):
                    if not item['is_sensitive'] and item['content']:
                        if query_lower in item['content'].lower():
                            matches.append(('content', cat_idx, item_idx))
                            logger.debug(f"Content match in {item['label']}")

        logger.info(f"Search found {len(matches)} matches")
        return matches

    def filter_and_sort_structure(
        self,
        structure: Dict = None,
        type_filters: Dict = None,
        state_filters: Dict = None,
        sort_by: str = 'name_asc'
    ) -> Dict:
        """
        Filter and sort structure based on criteria

        Args:
            structure: Optional structure dict
            type_filters: Dict {'CODE': bool, 'URL': bool, 'PATH': bool, 'TEXT': bool}
            state_filters: Dict {'favorites': bool, 'sensitive': bool, 'normal': bool}
            sort_by: Sort order - 'name_asc', 'name_desc', 'items_desc', 'items_asc'

        Returns:
            Dict: Filtered and sorted structure
        """
        if structure is None:
            structure = self.get_full_structure()

        logger.info(f"Filtering structure - Types: {type_filters}, States: {state_filters}, Sort: {sort_by}")

        # Deep copy to avoid modifying original
        import copy
        filtered_structure = copy.deepcopy(structure)

        # Apply filters if provided
        if type_filters or state_filters:
            for category in filtered_structure['categories']:
                filtered_items = []

                for item in category['items']:
                    # Check type filter
                    if type_filters:
                        if not type_filters.get(item['type'], True):
                            continue

                    # Check state filter
                    if state_filters:
                        is_favorite = item['is_favorite']
                        is_sensitive = item['is_sensitive']
                        is_normal = not is_favorite and not is_sensitive

                        include = False
                        if state_filters.get('favorites', True) and is_favorite:
                            include = True
                        if state_filters.get('sensitive', True) and is_sensitive:
                            include = True
                        if state_filters.get('normal', True) and is_normal:
                            include = True

                        if not include:
                            continue

                    filtered_items.append(item)

                category['items'] = filtered_items

        # Sort categories
        if sort_by == 'name_asc':
            filtered_structure['categories'].sort(key=lambda c: c['name'].lower())
        elif sort_by == 'name_desc':
            filtered_structure['categories'].sort(key=lambda c: c['name'].lower(), reverse=True)
        elif sort_by == 'items_desc':
            filtered_structure['categories'].sort(key=lambda c: len(c['items']), reverse=True)
        elif sort_by == 'items_asc':
            filtered_structure['categories'].sort(key=lambda c: len(c['items']))

        logger.info(f"Filtering complete")
        return filtered_structure
