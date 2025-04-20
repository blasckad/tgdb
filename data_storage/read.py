import os
import json
import pickle
from datetime import datetime
from intervaltree import IntervalTree

# ========== Папки и пути ==========
BASE_DIR = "tgdb"
NODE_DIR = os.path.join(BASE_DIR, "nodes")
EDGE_DIR = os.path.join(BASE_DIR, "edges")
INDEX_DIR = os.path.join(BASE_DIR, "index")

NODE_TREE_PATH = os.path.join(INDEX_DIR, "node_tree.pkl")
NODE_HASH_PATH = os.path.join(INDEX_DIR, "node_hash.pkl")

EDGE_TREE_PATH = os.path.join(INDEX_DIR, "edge_tree.pkl")
EDGE_HASH_PATH = os.path.join(INDEX_DIR, "edge_hash.pkl")

EDGE_DIR_TREE_PATH = os.path.join(INDEX_DIR, "edge_dir_tree.pkl")

# ========== Загрузка ==========
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

# ========== Узлы ==========

def read_node_by_id(node_id):
    return NODE_HASH.get(node_id)

def read_node_by_name_at_time(name, timestamp):
    if name not in NODE_TREE:
        return None
    intervals = NODE_TREE[name][timestamp]
    if not intervals:
        return None
    # Берем самый поздний start_ts из подходящих
    best = max(intervals, key=lambda i: i.begin)
    return NODE_HASH.get(best.data)

def read_nodes_by_name_range(name, start, end):
    if name not in NODE_TREE:
        return []
    return [NODE_HASH[i.data] for i in NODE_TREE[name].overlap(start, end)]

# ========== Рёбра ==========

def read_edge_by_id(edge_id):
    return EDGE_HASH.get(edge_id)

def read_edge_by_pair_at_time(from_name, to_name, timestamp):
    key = (from_name, to_name)
    if key not in EDGE_TREE:
        return None
    intervals = EDGE_TREE[key][timestamp]
    if not intervals:
        return None
    best = max(intervals, key=lambda i: i.begin)
    return EDGE_HASH.get(best.data)

def read_edges_by_pair_range(from_name, to_name, start, end):
    key = (from_name, to_name)
    if key not in EDGE_TREE:
        return []
    return [EDGE_HASH[i.data] for i in EDGE_TREE[key].overlap(start, end)]

# ========== Направления рёбер ==========

def read_edges_by_direction(node_name, direction, start, end):
    key = (node_name, direction)
    if key not in EDGE_DIR_TREE:
        return []
    return [EDGE_HASH[i.data] for i in EDGE_DIR_TREE[key].overlap(start, end)]

# ========== Пример использования ==========
if __name__ == "__main__":
    ts = 1708500000
    ts_range = (1700000000, 1710000000)

    print("\n▶ Актуальный узел Alice:")
    print(read_node_by_name_at_time("Alice", ts))

    print("\n▶ Все версии Alice:")
    for node in read_nodes_by_name_range("Alice", *ts_range):
        print(node)

    print("\n▶ Актуальное ребро Alice → Bob:")
    print(read_edge_by_pair_at_time("Alice", "Bob", ts))

    print("\n▶ Входящие в Bob:")
    for edge in read_edges_by_direction("Bob", "in", *ts_range):
        print(edge)

    print("\n▶ Исходящие от Alice:")
    for edge in read_edges_by_direction("Alice", "out", *ts_range):
        print(edge)
