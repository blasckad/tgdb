def show_node_changes(node):
    """Показывает изменения узла по уровням."""
    if not node:
        print("Узел не найден.")
        return

    print(f"\nИзменения узла с ID {node['_key']} по уровням:")
    for level in sorted(node.get("level_data", []), key=lambda x: x["level_id"]):
        print(f"Уровень: {level['level_id']}")
        print(f"  Данные: {level['data']}")
        print("-" * 40)
