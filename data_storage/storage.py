from index import load_index
from main import Entity, State, CausalEdge, ENTITY_FILE, STATE_FILE, EDGE_FILE

def get_entity(entity_id: str):
    index = load_index("tgdb/index/entity.idx")
    offset = index.get(entity_id)
    if offset is None:
        return None
    with open(ENTITY_FILE, "rb") as f:
        f.seek(offset)
        return Entity.STRUCT.unpack(f.read(37))

def get_state(entity_id: str, timestamp: int):
    index = load_index("tgdb/index/state.idx")
    offset = index.get((entity_id, timestamp))
    if offset is None:
        return None
    with open(STATE_FILE, "rb") as f:
        f.seek(offset)
        return State.STRUCT.unpack(f.read(164))

def get_edges_by_from(from_id: str):
    index = load_index("tgdb/index/edge.idx")
    offsets = index.get("from", {}).get(from_id, [])
    edges = []
    with open(EDGE_FILE, "rb") as f:
        for off in offsets:
            f.seek(off)
            edges.append(CausalEdge.STRUCT.unpack(f.read(120)))
    return edges
