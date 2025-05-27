import os
import json
import pickle
import torch
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

# ========== Чтение всех рёбер ==========
def read_all_edges():
    edges = []
    for file in os.listdir(EDGE_DIR):
        if file.endswith(".bin"):
            with open(os.path.join(EDGE_DIR, file), "r", encoding="utf-8") as f:
                for line in f:
                    try:
                        edge = json.loads(line)
                        edges.append(edge)
                    except json.JSONDecodeError:
                        continue
    return edges

def iter_user_events(user_name: str, direction: str = "out"):
    """
    Ленивая выдача всех событий пользователя в хронологическом порядке.
    direction: "out" (u→*), "in" (*→u)
    """
    key = (user_name, direction)
    if key not in EDGE_DIR_TREE:
        return
    # intervaltree.overlap возвращает несортированный набор – отсортируем по t
    events = sorted(EDGE_DIR_TREE[key], key=lambda iv: iv.begin)
    for iv in events:
        edge = EDGE_HASH[iv.data]
        yield (edge["from_name"],
               edge["to_name"],
               edge["timestamp_start"],
               edge["data"].get("label", 0))

def sliding_user_windows(user_names, k=20):
    """Возвращает последовательности длиной k: (u,v,t,features,label)."""
    for u in user_names:
        seq = []
        for iv in sorted(EDGE_DIR_TREE[(u, "out")], key=lambda iv: iv.begin):
            e = EDGE_HASH[iv.data]
            seq.append((
                e["from_name"], e["to_name"], e["timestamp_start"],
                torch.tensor(e["data"]["features"], dtype=torch.float32),
                e["data"]["label"]
            ))
        if not seq:
            continue
        seq = seq[-k:]
        if len(seq) < k:
            seq = [seq[0]] * (k - len(seq)) + seq
        yield seq

# ========== Пример использования ==========
if __name__ == "__main__":
    print("\n▶ Примеры узлов:")
    for node_id, node in list(NODE_HASH.items())[:5]:
        print(f"- {node['name']} [{node['timestamp_start']} – {node['timestamp_end']}]")

    print("\n▶ Примеры рёбер:")
    for edge_id, edge in list(EDGE_HASH.items())[:5]:
        print(f"- {edge['from_name']} → {edge['to_name']} @ {edge['timestamp_start']}")
        print(f"  Тип: {edge['data'].get('type', 'unknown')}, Метка: {edge['data'].get('label')}, Фичи: {edge['data'].get('features', [])[:3]}")
