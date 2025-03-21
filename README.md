## 1. Хранение данных

### 1.1 Узлы (`nodes.bin`)
- Файлы хранятся в бинарном формате, разделенные по месяцам.
- **Структура данных:**
  - `node_id (UUID)`: уникальный идентификатор узла.
  - `name (str)`: имя объекта.
  - `timestamp (int)`: время создания версии объекта.
  - `active (bool)`: актуален ли объект (`True` – активен, `False` – устарел).
  - `data (JSON)`: дополнительные данные объекта.

#### Пример:
| node_id | name  | timestamp  | active | data           |
|---------|-------|------------|--------|----------------|
| n1      | Alice | 1708400000 | True   | { "age": 25 }  |
| n2      | Alice | 1708500000 | True   | { "age": 26 }  |
| n3      | Alice | 1710000000 | False  | {}             |

### 1.2 Рёбра (`edges.bin`)
- Хранятся аналогично узлам, разделенные по месяцам.
- **Структура данных:**
  - `edge_id (UUID)`: уникальный идентификатор ребра.
  - `from_name (str)`: имя начального узла.
  - `to_name (str)`: имя конечного узла.
  - `timestamp_start (int)`: время начала существования связи.
  - `active (bool)`: активно ли ребро.
  - `data (JSON)`: информация о связи.

#### Пример:
| edge_id | from_name | to_name | timestamp_start | active | data               |
|---------|----------|--------|-----------------|--------|--------------------|
| e1      | Alice    | Bob    | 1708400000      | True   | { "type": "friend" } |
| e2      | Alice    | Bob    | 1710000000      | False  | {}                 |

### 1.3 Индексация входящих и исходящих рёбер (`edges_index.bin`)
- Позволяет быстро находить связи для узлов.
- **Структура данных:**
  - `node_name (str)`: имя узла.
  - `direction (str)`: `"in"` (входящие) или `"out"` (исходящие).
  - `edge_id (UUID)`: ссылка на `edges.bin`.
  - `timestamp (int)`: момент создания связи.

#### Пример:
| node_name | direction | edge_id | timestamp  |
|-----------|----------|---------|------------|
| Alice     | out      | e1      | 1708400000 |
| Bob       | in       | e1      | 1708400000 |

---

## 2. Индексация

### 2.1 Индексация узлов
✔ **B-Tree**: `(name, timestamp) → node_id`  
✔ **Hash Index**: `node_id → данные`

### 2.2 Индексация рёбер
✔ **B-Tree**: `(from_name, to_name, timestamp_start) → edge_id`  
✔ **Hash Index**: `edge_id → данные`

### 2.3 Индексация входящих и исходящих рёбер
✔ **B-Tree**: `(node_name, direction, timestamp) → edge_id`

---

## 3. Партиционирование данных
✔ **Файлы разделены по месяцам** (например, `nodes_2024_01.bin`, `edges_2024_01.bin`).  
✔ **Запросы загружают только нужные файлы**.  
✔ **Объединение данных без конфликтов индексов при межмесячных запросах**.  

---

## 4. Оптимизация поиска путей
✔ **Поиск путей с временными ограничениями**.  
✔ **Кэширование часто запрашиваемых связей**.  
✔ **Дополнительные структуры для быстрого доступа к "живым" объектам**.  

---

## 5. Оценка сложности запросов

| Запрос | Используемый индекс | Оценка сложности (Big-O) |
|--------|---------------------|--------------------------|
| Найти все версии объекта `"Alice"` | B-Tree (по `name`) | `O(log N)` |
| Найти `"Alice"` в момент `T` | B-Tree (по `name, timestamp`) | `O(log N)` |
| Найти все связи `"Alice"` | B-Tree (по `node_name`) | `O(log M)` |
| Найти связи `"Alice"` в диапазоне `[T1, T2]` | B-Tree (по `timestamp`) | `O(log M)` |
| Найти все актуальные связи `"Alice"` | B-Tree + фильтр по `active` | `O(log M)` |
| Поиск пути `"Alice" → "Bob"` с учетом времени | B-Tree (по `from_name, to_name, timestamp_start`) | `O(log M) + O(P)` |

Где:  
- `N` – количество узлов.  
- `M` – количество рёбер.  
- `P` – длина найденного пути.
