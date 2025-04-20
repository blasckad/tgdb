import os
import json
import uuid
import pickle
from datetime import datetime
from intervaltree import Interval, IntervalTree

# ========== Папки ==========
BASE_DIR = "tgdb"
NODE_DIR = os.path.join(BASE_DIR, "nodes")
EDGE_DIR = os.path.join(BASE_DIR, "edges")
INDEX_DIR = os.path.join(BASE_DIR, "index")

os.makedirs(NODE_DIR, exist_ok=True)
os.makedirs(EDGE_DIR, exist_ok=True)
os.makedirs(INDEX_DIR, exist_ok=True)

# ========== Пути к индексам ==========
NODE_TREE_PATH = os.path.join(INDEX_DIR, "node_tree.pkl")
NODE_HASH_PATH = os.path.join(INDEX_DIR, "node_hash.pkl")

EDGE_TREE_PATH = os.path.join(INDEX_DIR, "edge_tree.pkl")
EDGE_HASH_PATH = os.path.join(INDEX_DIR, "edge_hash.pkl")

EDGE_DIR_TREE_PATH = os.path.join(INDEX_DIR, "edge_dir_tree.pkl")

# ========== Загрузка индексов ==========
def load_pickle(path):
    if os.path.exists(path):
        with open(path, "rb") as f:
            return pickle.load(f)
    return {}

NODE_TREE = load_pickle(NODE_TREE_PATH)
NODE_HASH = load_pickle(NODE_HASH_PATH)

EDGE_TREE = load_pickle(EDGE_TREE_PATH)
EDGE_HASH = load_pickle(EDGE_HASH_PATH)

EDGE_DIR_TREE = load_pickle(EDGE_DIR_TREE_PATH)

# ========== Сохранение индексов ==========
def save_all_indexes():
    with open(NODE_TREE_PATH, "wb") as f: pickle.dump(NODE_TREE, f)
    with open(NODE_HASH_PATH, "wb") as f: pickle.dump(NODE_HASH, f)
    with open(EDGE_TREE_PATH, "wb") as f: pickle.dump(EDGE_TREE, f)
    with open(EDGE_HASH_PATH, "wb") as f: pickle.dump(EDGE_HASH, f)
    with open(EDGE_DIR_TREE_PATH, "wb") as f: pickle.dump(EDGE_DIR_TREE, f)

# ========== Хелперы ==========
def month_key(timestamp):
    dt = datetime.utcfromtimestamp(timestamp)
    return f"{dt.year}_{dt.month:02d}"

# ========== Запись узла ==========
def write_node(name: str, start_ts: int, end_ts: int, data: dict):
    node_id = str(uuid.uuid4())
    record = {
        "node_id": node_id,
        "name": name,
        "timestamp_start": start_ts,
        "timestamp_end": end_ts,
        "data": data
    }

    # 1. Запись в bin
    binfile = os.path.join(NODE_DIR, f"{month_key(start_ts)}_nodes.bin")
    with open(binfile, "ab") as f:
        f.write(json.dumps(record).encode('utf-8') + b"\n")

    # 2. Обновление индексов
    if name not in NODE_TREE:
        NODE_TREE[name] = IntervalTree()
    NODE_TREE[name].addi(start_ts, end_ts, node_id)
    NODE_HASH[node_id] = record

# ========== Запись ребра ==========
def write_edge(from_name: str, to_name: str, start_ts: int, end_ts: int, data: dict):
    edge_id = str(uuid.uuid4())
    record = {
        "edge_id": edge_id,
        "from_name": from_name,
        "to_name": to_name,
        "timestamp_start": start_ts,
        "timestamp_end": end_ts,
        "data": data
    }

    # 1. Запись в bin
    binfile = os.path.join(EDGE_DIR, f"{month_key(start_ts)}_edges.bin")
    with open(binfile, "ab") as f:
        f.write(json.dumps(record).encode('utf-8') + b"\n")

    # 2. Обновление основных индексов
    key = (from_name, to_name)
    if key not in EDGE_TREE:
        EDGE_TREE[key] = IntervalTree()
    EDGE_TREE[key].addi(start_ts, end_ts, edge_id)
    EDGE_HASH[edge_id] = record

    # 3. Обновление индекса направлений
    for direction, node in [("out", from_name), ("in", to_name)]:
        dir_key = (node, direction)
        if dir_key not in EDGE_DIR_TREE:
            EDGE_DIR_TREE[dir_key] = IntervalTree()
        EDGE_DIR_TREE[dir_key].addi(start_ts, end_ts, edge_id)

# ========== Пример использования ==========
if __name__ == "__main__":
    write_node("Alice", 1700000000, 1708000000, {"age": 25})
    write_node("Alice", 1708000001, 1710000000, {"age": 26})
    write_node("Bob", 1700000000, 1710000000, {"age": 30})

    write_edge("Alice", "Bob", 1701000000, 1709000000, {"type": "friend"})
    write_edge("Bob", "Alice", 1702000000, 1708000000, {"type": "reply"})

    save_all_indexes()
    print("✅ Узлы и рёбра записаны с индексами.")
