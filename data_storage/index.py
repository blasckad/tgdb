import os
import pickle
from collections import defaultdict

INDEX_DIR = "tgdb/index/"
os.makedirs(INDEX_DIR, exist_ok=True)

ENTITY_INDEX_FILE = os.path.join(INDEX_DIR, "entity.idx")
STATE_INDEX_FILE = os.path.join(INDEX_DIR, "state.idx")
EDGE_INDEX_FILE = os.path.join(INDEX_DIR, "edge.idx")

def load_index(file_path):
    if os.path.exists(file_path):
        with open(file_path, "rb") as f:
            return pickle.load(f)
    return {}

def save_index(index, file_path):
    with open(file_path, "wb") as f:
        pickle.dump(index, f)

def update_entity_index(entity_id, offset):
    index = load_index(ENTITY_INDEX_FILE)
    index[entity_id] = offset
    save_index(index, ENTITY_INDEX_FILE)

def update_state_index(entity_id, timestamp, offset):
    index = load_index(STATE_INDEX_FILE)
    index[(entity_id, timestamp)] = offset
    save_index(index, STATE_INDEX_FILE)

def update_edge_index(from_id, to_id, offset):
    index = load_index(EDGE_INDEX_FILE)
    if not index:
        index = {"from": defaultdict(list), "to": defaultdict(list)}
    index["from"][from_id].append(offset)
    index["to"][to_id].append(offset)
    save_index(index, EDGE_INDEX_FILE)
