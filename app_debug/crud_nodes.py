from config import get_database

db = get_database()
nodes = db.collection('Nodes')

def create_node(node_id, name, level_data):
    """Создаёт новый узел."""
    node_data = {
        "_key": node_id,
        "name": name,
        "level_data": level_data  # Список данных для каждого уровня
    }
    nodes.insert(node_data, overwrite=True)

def read_node(node_id):
    """Возвращает данные узла по его ID."""
    return nodes.get(node_id)

def update_node(node_id, new_data):
    """Обновляет данные узла."""
    node = nodes.get(node_id)
    if not node:
        raise ValueError(f"Узел с ID {node_id} не найден.")
    node.update(new_data)
    nodes.update(node)

def delete_node(node_id):
    """Удаляет узел по его ID."""
    nodes.delete(node_id)
