# Widget Sidebar - Database Schema

**Database:** `widget_sidebar.db`

**Total Tables:** 16

---

## Table: `bookmarks`

**Rows:** 2

| Column        | Type      | Not Null | Default           | Primary Key |
| ------------- | --------- | -------- | ----------------- | ----------- |
| `id`          | INTEGER   |          |                   | ✓           |
| `title`       | TEXT      | ✓        |                   |             |
| `url`         | TEXT      | ✓        |                   |             |
| `folder`      | TEXT      |          | NULL              |             |
| `icon`        | TEXT      |          | NULL              |             |
| `created_at`  | TIMESTAMP |          | CURRENT_TIMESTAMP |             |
| `order_index` | INTEGER   |          | 0                 |             |

**CREATE Statement:**

```sql
CREATE TABLE bookmarks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                url TEXT NOT NULL,
                folder TEXT DEFAULT NULL,
                icon TEXT DEFAULT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                order_index INTEGER DEFAULT 0
            )
```

**Indexes:**

```sql
CREATE INDEX idx_bookmarks_order ON bookmarks(order_index)

```

```sql
CREATE INDEX idx_bookmarks_url ON bookmarks(url)

```

---

## Table: `browser_config`

**Rows:** 1

| Column       | Type      | Not Null | Default                  | Primary Key |
| ------------ | --------- | -------- | ------------------------ | ----------- |
| `id`         | INTEGER   |          |                          | ✓           |
| `home_url`   | TEXT      |          | 'https://www.google.com' |             |
| `is_visible` | BOOLEAN   |          | 0                        |             |
| `width`      | INTEGER   |          | 500                      |             |
| `height`     | INTEGER   |          | 700                      |             |
| `created_at` | TIMESTAMP |          | CURRENT_TIMESTAMP        |             |
| `updated_at` | TIMESTAMP |          | CURRENT_TIMESTAMP        |             |

**CREATE Statement:**

```sql
CREATE TABLE browser_config (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                home_url TEXT DEFAULT 'https://www.google.com',
                is_visible BOOLEAN DEFAULT 0,
                width INTEGER DEFAULT 500,
                height INTEGER DEFAULT 700,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
```

---

## Table: `browser_profiles`

**Rows:** 2

| Column         | Type      | Not Null | Default           | Primary Key |
| -------------- | --------- | -------- | ----------------- | ----------- |
| `id`           | INTEGER   |          |                   | ✓           |
| `name`         | TEXT      | ✓        |                   |             |
| `storage_path` | TEXT      | ✓        |                   |             |
| `is_default`   | BOOLEAN   |          | 0                 |             |
| `created_at`   | TIMESTAMP |          | CURRENT_TIMESTAMP |             |
| `last_used`    | TIMESTAMP |          | CURRENT_TIMESTAMP |             |

**CREATE Statement:**

```sql
CREATE TABLE browser_profiles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                storage_path TEXT NOT NULL,
                is_default BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_used TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
```

---

## Table: `browser_sessions`

**Rows:** 2

| Column         | Type      | Not Null | Default           | Primary Key |
| -------------- | --------- | -------- | ----------------- | ----------- |
| `id`           | INTEGER   |          |                   | ✓           |
| `name`         | TEXT      | ✓        |                   |             |
| `is_auto_save` | BOOLEAN   |          | 0                 |             |
| `created_at`   | TIMESTAMP |          | CURRENT_TIMESTAMP |             |
| `updated_at`   | TIMESTAMP |          | CURRENT_TIMESTAMP |             |

**CREATE Statement:**

```sql
CREATE TABLE browser_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                is_auto_save BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
```

---

## Table: `categories`

**Rows:** 24

| Column          | Type      | Not Null | Default           | Primary Key |
| --------------- | --------- | -------- | ----------------- | ----------- |
| `id`            | INTEGER   |          |                   | ✓           |
| `name`          | TEXT      | ✓        |                   |             |
| `icon`          | TEXT      |          |                   |             |
| `order_index`   | INTEGER   | ✓        |                   |             |
| `is_active`     | BOOLEAN   |          | 1                 |             |
| `is_predefined` | BOOLEAN   |          | 0                 |             |
| `created_at`    | TIMESTAMP |          | CURRENT_TIMESTAMP |             |
| `updated_at`    | TIMESTAMP |          | CURRENT_TIMESTAMP |             |
| `color`         | TEXT      |          |                   |             |
| `badge`         | TEXT      |          |                   |             |
| `item_count`    | INTEGER   |          | 0                 |             |
| `total_uses`    | INTEGER   |          | 0                 |             |
| `last_accessed` | TIMESTAMP |          |                   |             |
| `access_count`  | INTEGER   |          | 0                 |             |
| `is_pinned`     | BOOLEAN   |          | 0                 |             |
| `pinned_order`  | INTEGER   |          | 0                 |             |

**CREATE Statement:**

```sql
CREATE TABLE categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                icon TEXT,
                order_index INTEGER NOT NULL,
                is_active BOOLEAN DEFAULT 1,
                is_predefined BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            , color TEXT, badge TEXT, item_count INTEGER DEFAULT 0, total_uses INTEGER DEFAULT 0, last_accessed TIMESTAMP, access_count INTEGER DEFAULT 0, is_pinned BOOLEAN DEFAULT 0, pinned_order INTEGER DEFAULT 0)
```

**Indexes:**

```sql
CREATE INDEX idx_categories_order ON categories(order_index)
```

---

## Table: `clipboard_history`

**Rows:** 0

| Column      | Type      | Not Null | Default           | Primary Key |
| ----------- | --------- | -------- | ----------------- | ----------- |
| `id`        | INTEGER   |          |                   | ✓           |
| `item_id`   | INTEGER   |          |                   |             |
| `content`   | TEXT      | ✓        |                   |             |
| `copied_at` | TIMESTAMP |          | CURRENT_TIMESTAMP |             |

**CREATE Statement:**

```sql
CREATE TABLE clipboard_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_id INTEGER,
                content TEXT NOT NULL,
                copied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (item_id) REFERENCES items(id) ON DELETE SET NULL
            )
```

**Indexes:**

```sql
CREATE INDEX idx_clipboard_history_date ON clipboard_history(copied_at DESC)
```

---

## Table: `item_usage_history`

**Rows:** 4

| Column              | Type    | Not Null | Default         | Primary Key |
| ------------------- | ------- | -------- | --------------- | ----------- |
| `id`                | INTEGER |          |                 | ✓           |
| `item_id`           | INTEGER | ✓        |                 |             |
| `used_at`           | TEXT    | ✓        | datetime('now') |             |
| `execution_time_ms` | INTEGER |          | 0               |             |
| `success`           | INTEGER |          | 1               |             |
| `error_message`     | TEXT    |          |                 |             |

**CREATE Statement:**

```sql
CREATE TABLE item_usage_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_id INTEGER NOT NULL,
                used_at TEXT NOT NULL DEFAULT (datetime('now')),
                execution_time_ms INTEGER DEFAULT 0,
                success INTEGER DEFAULT 1,
                error_message TEXT,
                FOREIGN KEY (item_id) REFERENCES items(id) ON DELETE CASCADE
            )
```

**Indexes:**

```sql
CREATE INDEX idx_usage_item_id ON item_usage_history(item_id)
```

```sql
CREATE INDEX idx_usage_date ON item_usage_history(used_at)
```

---

## Table: `items`

**Rows:** 120

| Column              | Type         | Not Null | Default           | Primary Key |
| ------------------- | ------------ | -------- | ----------------- | ----------- |
| `id`                | INTEGER      |          |                   | ✓           |
| `category_id`       | INTEGER      | ✓        |                   |             |
| `label`             | TEXT         | ✓        |                   |             |
| `content`           | TEXT         | ✓        |                   |             |
| `type`              | TEXT         |          | 'TEXT'            |             |
| `icon`              | TEXT         |          |                   |             |
| `is_sensitive`      | BOOLEAN      |          | 0                 |             |
| `tags`              | TEXT         |          |                   |             |
| `created_at`        | TIMESTAMP    |          | CURRENT_TIMESTAMP |             |
| `updated_at`        | TIMESTAMP    |          | CURRENT_TIMESTAMP |             |
| `last_used`         | TIMESTAMP    |          |                   |             |
| `is_favorite`       | INTEGER      |          | 0                 |             |
| `favorite_order`    | INTEGER      |          | 0                 |             |
| `use_count`         | INTEGER      |          | 0                 |             |
| `color`             | TEXT         |          |                   |             |
| `badge`             | TEXT         |          |                   |             |
| `description`       | TEXT         |          |                   |             |
| `shortcut`          | TEXT         |          |                   |             |
| `working_dir`       | TEXT         |          |                   |             |
| `is_active`         | BOOLEAN      |          | 1                 |             |
| `is_archived`       | BOOLEAN      |          | 0                 |             |
| `is_list`           | BOOLEAN      |          | 0                 |             |
| `list_group`        | TEXT         |          | NULL              |             |
| `orden_lista`       | INTEGER      |          | 0                 |             |
| `file_size`         | INTEGER      |          | NULL              |             |
| `file_type`         | VARCHAR(50)  |          | NULL              |             |
| `file_extension`    | VARCHAR(10)  |          | NULL              |             |
| `original_filename` | VARCHAR(255) |          | NULL              |             |
| `file_hash`         | VARCHAR(64)  |          | NULL              |             |

**File Management Fields (Added for PATH items):**
- `file_size`: File size in bytes
- `file_type`: MIME type of the file (e.g., "image/jpeg", "application/pdf")
- `file_extension`: File extension without dot (e.g., "jpg", "pdf", "txt")
- `original_filename`: Original name of the file before storage
- `file_hash`: SHA256 hash of the file for integrity verification

**CREATE Statement:**

```sql
CREATE TABLE items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category_id INTEGER NOT NULL,
                label TEXT NOT NULL,
                content TEXT NOT NULL,
                type TEXT CHECK(type IN ('TEXT', 'URL', 'CODE', 'PATH')) DEFAULT 'TEXT',
                icon TEXT,
                is_sensitive BOOLEAN DEFAULT 0,
                tags TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_used TIMESTAMP,
                is_favorite INTEGER DEFAULT 0,
                favorite_order INTEGER DEFAULT 0,
                use_count INTEGER DEFAULT 0,
                color TEXT,
                badge TEXT,
                description TEXT,
                shortcut TEXT,
                working_dir TEXT,
                is_active BOOLEAN DEFAULT 1,
                is_archived BOOLEAN DEFAULT 0,
                is_list BOOLEAN DEFAULT 0,
                list_group TEXT DEFAULT NULL,
                orden_lista INTEGER DEFAULT 0,
                file_size INTEGER DEFAULT NULL,
                file_type VARCHAR(50) DEFAULT NULL,
                file_extension VARCHAR(10) DEFAULT NULL,
                original_filename VARCHAR(255) DEFAULT NULL,
                file_hash VARCHAR(64) DEFAULT NULL,
                FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE CASCADE
            )
```

**Indexes:**

```sql
CREATE INDEX idx_items_category ON items(category_id)
```

```sql
CREATE INDEX idx_items_last_used ON items(last_used DESC)
```

```sql
CREATE INDEX idx_items_is_list ON items(is_list) WHERE is_list = 1
```

```sql
CREATE INDEX idx_items_list_group ON items(list_group) WHERE list_group IS NOT NULL
```

```sql
CREATE INDEX idx_items_orden_lista ON items(category_id, list_group, orden_lista) WHERE is_list = 1
```

---

## Table: `notebook_tabs`

**Rows:** 3

| Column         | Type      | Not Null | Default           | Primary Key |
| -------------- | --------- | -------- | ----------------- | ----------- |
| `id`           | INTEGER   |          |                   | ✓           |
| `title`        | TEXT      | ✓        | 'Sin titulo'      |             |
| `content`      | TEXT      |          | ''                |             |
| `category_id`  | INTEGER   |          |                   |             |
| `item_type`    | TEXT      |          | 'TEXT'            |             |
| `tags`         | TEXT      |          | ''                |             |
| `description`  | TEXT      |          | ''                |             |
| `is_sensitive` | INTEGER   |          | 0                 |             |
| `is_active`    | INTEGER   |          | 1                 |             |
| `is_archived`  | INTEGER   |          | 0                 |             |
| `position`     | INTEGER   | ✓        |                   |             |
| `created_at`   | TIMESTAMP |          | CURRENT_TIMESTAMP |             |
| `updated_at`   | TIMESTAMP |          | CURRENT_TIMESTAMP |             |

**CREATE Statement:**

```sql
CREATE TABLE notebook_tabs (
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
```

**Indexes:**

```sql
CREATE INDEX idx_notebook_tabs_position
        ON notebook_tabs(position)

```

```sql
CREATE INDEX idx_notebook_tabs_category
        ON notebook_tabs(category_id)

```

```sql
CREATE INDEX idx_notebook_tabs_updated
        ON notebook_tabs(updated_at)

```

---

## Table: `pinned_panels`

**Rows:** 0

| Column              | Type      | Not Null | Default           | Primary Key |
| ------------------- | --------- | -------- | ----------------- | ----------- |
| `id`                | INTEGER   |          |                   | ✓           |
| `category_id`       | INTEGER   | ✓        |                   |             |
| `custom_name`       | TEXT      |          |                   |             |
| `custom_color`      | TEXT      |          |                   |             |
| `x_position`        | INTEGER   | ✓        |                   |             |
| `y_position`        | INTEGER   | ✓        |                   |             |
| `width`             | INTEGER   | ✓        | 350               |             |
| `height`            | INTEGER   | ✓        | 500               |             |
| `is_minimized`      | BOOLEAN   |          | 0                 |             |
| `created_at`        | TIMESTAMP |          | CURRENT_TIMESTAMP |             |
| `last_opened`       | TIMESTAMP |          | CURRENT_TIMESTAMP |             |
| `open_count`        | INTEGER   |          | 0                 |             |
| `is_active`         | BOOLEAN   |          | 1                 |             |
| `filter_config`     | TEXT      |          |                   |             |
| `keyboard_shortcut` | TEXT      |          |                   |             |

**CREATE Statement:**

```sql
CREATE TABLE pinned_panels (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category_id INTEGER NOT NULL,
                custom_name TEXT,
                custom_color TEXT,
                x_position INTEGER NOT NULL,
                y_position INTEGER NOT NULL,
                width INTEGER NOT NULL DEFAULT 350,
                height INTEGER NOT NULL DEFAULT 500,
                is_minimized BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_opened TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                open_count INTEGER DEFAULT 0,
                is_active BOOLEAN DEFAULT 1, filter_config TEXT, keyboard_shortcut TEXT,
                FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE CASCADE
            )
```

**Indexes:**

```sql
CREATE INDEX idx_pinned_category
            ON pinned_panels(category_id)

```

```sql
CREATE INDEX idx_pinned_last_opened
            ON pinned_panels(last_opened DESC)

```

```sql
CREATE INDEX idx_pinned_active
            ON pinned_panels(is_active)

```

---

## Table: `session_tabs`

**Rows:** 6

| Column       | Type      | Not Null | Default           | Primary Key |
| ------------ | --------- | -------- | ----------------- | ----------- |
| `id`         | INTEGER   |          |                   | ✓           |
| `session_id` | INTEGER   | ✓        |                   |             |
| `url`        | TEXT      | ✓        |                   |             |
| `title`      | TEXT      |          | 'Nueva pestaña'   |             |
| `position`   | INTEGER   |          | 0                 |             |
| `is_active`  | BOOLEAN   |          | 0                 |             |
| `created_at` | TIMESTAMP |          | CURRENT_TIMESTAMP |             |

**CREATE Statement:**

```sql
CREATE TABLE session_tabs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER NOT NULL,
                url TEXT NOT NULL,
                title TEXT DEFAULT 'Nueva pestaña',
                position INTEGER DEFAULT 0,
                is_active BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES browser_sessions(id) ON DELETE CASCADE
            )
```

**Indexes:**

```sql
CREATE INDEX idx_session_tabs_session_id ON session_tabs(session_id)

```

```sql
CREATE INDEX idx_session_tabs_position ON session_tabs(position)

```

---

## Table: `settings`

**Rows:** 13

| Column       | Type      | Not Null | Default           | Primary Key |
| ------------ | --------- | -------- | ----------------- | ----------- |
| `id`         | INTEGER   |          |                   | ✓           |
| `key`        | TEXT      | ✓        |                   |             |
| `value`      | TEXT      | ✓        |                   |             |
| `created_at` | TIMESTAMP |          | CURRENT_TIMESTAMP |             |
| `updated_at` | TIMESTAMP |          | CURRENT_TIMESTAMP |             |

**CREATE Statement:**

```sql
CREATE TABLE settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key TEXT UNIQUE NOT NULL,
                value TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
```

---

## Table: `smart_collections`

**Rows:** 4

| Column               | Type      | Not Null | Default           | Primary Key |
| -------------------- | --------- | -------- | ----------------- | ----------- |
| `id`                 | INTEGER   |          |                   | ✓           |
| `name`               | TEXT      | ✓        |                   |             |
| `description`        | TEXT      |          |                   |             |
| `icon`               | TEXT      |          | '🔍'              |             |
| `color`              | TEXT      |          | '#00d4ff'         |             |
| `tags_include`       | TEXT      |          |                   |             |
| `tags_exclude`       | TEXT      |          |                   |             |
| `category_id`        | INTEGER   |          |                   |             |
| `item_type`          | TEXT      |          |                   |             |
| `is_favorite`        | BOOLEAN   |          |                   |             |
| `is_sensitive`       | BOOLEAN   |          |                   |             |
| `is_active_filter`   | BOOLEAN   |          |                   |             |
| `is_archived_filter` | BOOLEAN   |          |                   |             |
| `search_text`        | TEXT      |          |                   |             |
| `date_from`          | TEXT      |          |                   |             |
| `date_to`            | TEXT      |          |                   |             |
| `created_at`         | TIMESTAMP |          | CURRENT_TIMESTAMP |             |
| `updated_at`         | TIMESTAMP |          | CURRENT_TIMESTAMP |             |
| `is_active`          | BOOLEAN   |          | 1                 |             |

**CREATE Statement:**

```sql
CREATE TABLE smart_collections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                description TEXT,
                icon TEXT DEFAULT '🔍',
                color TEXT DEFAULT '#00d4ff',

                -- Filtros
                tags_include TEXT,
                tags_exclude TEXT,
                category_id INTEGER,
                item_type TEXT CHECK(item_type IN ('TEXT', 'URL', 'CODE', 'PATH', NULL)),
                is_favorite BOOLEAN,
                is_sensitive BOOLEAN,
                is_active_filter BOOLEAN,
                is_archived_filter BOOLEAN,
                search_text TEXT,
                date_from TEXT,
                date_to TEXT,

                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT 1,

                FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE SET NULL
            )
```

**Indexes:**

```sql
CREATE INDEX idx_smart_collections_name
            ON smart_collections(name)

```

```sql
CREATE INDEX idx_smart_collections_active
            ON smart_collections(is_active)

```

```sql
CREATE INDEX idx_smart_collections_category
            ON smart_collections(category_id)

```

---

## Table: `speed_dials`

**Rows:** 4

| Column             | Type      | Not Null | Default           | Primary Key |
| ------------------ | --------- | -------- | ----------------- | ----------- |
| `id`               | INTEGER   |          |                   | ✓           |
| `title`            | TEXT      | ✓        |                   |             |
| `url`              | TEXT      | ✓        |                   |             |
| `thumbnail_path`   | TEXT      |          | NULL              |             |
| `background_color` | TEXT      |          | '#16213e'         |             |
| `icon`             | TEXT      |          | '🌐'              |             |
| `position`         | INTEGER   |          | 0                 |             |
| `created_at`       | TIMESTAMP |          | CURRENT_TIMESTAMP |             |
| `updated_at`       | TIMESTAMP |          | CURRENT_TIMESTAMP |             |

**CREATE Statement:**

```sql
CREATE TABLE speed_dials (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                url TEXT NOT NULL,
                thumbnail_path TEXT DEFAULT NULL,
                background_color TEXT DEFAULT '#16213e',
                icon TEXT DEFAULT '🌐',
                position INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
```

**Indexes:**

```sql
CREATE INDEX idx_speed_dials_position ON speed_dials(position)

```

---

## Table: `sqlite_sequence`

**Rows:** 14

| Column | Type | Not Null | Default | Primary Key |
| ------ | ---- | -------- | ------- | ----------- |
| `name` |      |          |         |             |
| `seq`  |      |          |         |             |

**CREATE Statement:**

```sql
CREATE TABLE sqlite_sequence(name,seq)
```

---

## Table: `tag_groups`

**Rows:** 8

| Column        | Type      | Not Null | Default           | Primary Key |
| ------------- | --------- | -------- | ----------------- | ----------- |
| `id`          | INTEGER   |          |                   | ✓           |
| `name`        | TEXT      | ✓        |                   |             |
| `description` | TEXT      |          |                   |             |
| `tags`        | TEXT      | ✓        |                   |             |
| `color`       | TEXT      |          | '#007acc'         |             |
| `icon`        | TEXT      |          | '🏷️'              |             |
| `created_at`  | TIMESTAMP |          | CURRENT_TIMESTAMP |             |
| `updated_at`  | TIMESTAMP |          | CURRENT_TIMESTAMP |             |
| `is_active`   | BOOLEAN   |          | 1                 |             |

**CREATE Statement:**

```sql
CREATE TABLE tag_groups (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                description TEXT,
                tags TEXT NOT NULL,
                color TEXT DEFAULT '#007acc',
                icon TEXT DEFAULT '🏷️',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT 1
            )
```

**Indexes:**

```sql
CREATE INDEX idx_tag_groups_name
            ON tag_groups(name)

```

```sql
CREATE INDEX idx_tag_groups_active
            ON tag_groups(is_active)

```

---
