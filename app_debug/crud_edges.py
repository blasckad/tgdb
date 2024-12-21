from config import get_database

db = get_database()
edges = db.collection('Edges')

def create_edge(from_node, from_level, to_node, to_level, additional_info=None):
    """Создаёт новое ребро."""
    edge_data = {
        "_from": f"Nodes/{from_node}",
        "_to": f"Nodes/{to_node}",
        "from_level": from_level,
        "to_level": to_level,
        "additional_info": additional_info or {}
    }
    edges.insert(edge_data, overwrite=True)

def read_edge(edge_id):
    """Возвращает данные ребра по его ID."""
    return edges.get(edge_id)

def update_edge(edge_id, new_data):
    """Обновляет данные ребра."""
    edge = edges.get(edge_id)
    if not edge:
        raise ValueError(f"Ребро с ID {edge_id} не найдено.")
    edge.update(new_data)
    edges.update(edge)

def delete_edge(edge_id):
    """Удаляет ребро по его ID."""
    edges.delete(edge_id)
