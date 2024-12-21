from db_setup import setup_collections
from crud_nodes import create_node, read_node, update_node, delete_node
from crud_edges import create_edge, read_edge, update_edge, delete_edge
from utils import show_node_changes

def main():
    db = setup_collections()

    # Пример работы с узлами
    create_node("1", "Alice", [
        {"level_id": "L1", "data": {"role": "Engineer"}},
        {"level_id": "L2", "data": {"role": "Senior Engineer"}}
    ])
    node = read_node("1")
    show_node_changes(node)

    # Пример работы с рёбрами
    create_edge("1", "L1", "2", "L2", {"relationship": "colleague"})

if __name__ == "__main__":
    main()
