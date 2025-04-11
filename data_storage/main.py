import os
import struct
from typing import List

DATA_DIR = "tgdb/files/"
os.makedirs(DATA_DIR, exist_ok=True)

ENTITY_FILE = os.path.join(DATA_DIR, "entities.dat")
STATE_FILE = os.path.join(DATA_DIR, "states.dat")
EDGE_FILE = os.path.join(DATA_DIR, "causal_edges.dat")

class Entity:
    STRUCT = struct.Struct('32s B I')

    def __init__(self, entity_id: str, typ: int, meta_offset: int = 0):
        self.entity_id = entity_id.encode("utf-8")[:32].ljust(32, b'\x00')
        self.typ = typ
        self.meta_offset = meta_offset

    def serialize(self):
        return self.STRUCT.pack(self.entity_id, self.typ, self.meta_offset)

class State:
    STRUCT = struct.Struct('32s Q 32f I')

    def __init__(self, entity_id: str, timestamp: int, features: List[float], context_offset: int = 0):
        assert len(features) == 32
        self.entity_id = entity_id.encode("utf-8")[:32].ljust(32, b'\x00')
        self.timestamp = timestamp
        self.features = features
        self.context_offset = context_offset

    def serialize(self):
        return self.STRUCT.pack(self.entity_id, self.timestamp, *self.features, self.context_offset)

class CausalEdge:
    STRUCT = struct.Struct('48s 48s f Q Q I')

    def __init__(self, from_id: str, to_id: str, F_ij: float, t_start: int, t_effect: int, context_offset: int = 0):
        self.from_id = from_id.encode("utf-8")[:48].ljust(48, b'\x00')
        self.to_id = to_id.encode("utf-8")[:48].ljust(48, b'\x00')
        self.F_ij = F_ij
        self.t_start = t_start
        self.t_effect = t_effect
        self.context_offset = context_offset

    def serialize(self):
        return self.STRUCT.pack(self.from_id, self.to_id, self.F_ij, self.t_start, self.t_effect, self.context_offset)

from index import update_entity_index, update_state_index, update_edge_index

def add_entity(entity_id: str, typ: int):
    e = Entity(entity_id, typ)
    with open(ENTITY_FILE, "ab") as f:
        offset = f.tell()
        f.write(e.serialize())
        update_entity_index(entity_id, offset)

def add_state(entity_id: str, timestamp: int, features: List[float]):
    s = State(entity_id, timestamp, features)
    with open(STATE_FILE, "ab") as f:
        offset = f.tell()
        f.write(s.serialize())
        update_state_index(entity_id, timestamp, offset)

def add_edge(from_id: str, to_id: str, F_ij: float, t1: int, t2: int):
    e = CausalEdge(from_id, to_id, F_ij, t1, t2)
    with open(EDGE_FILE, "ab") as f:
        offset = f.tell()
        f.write(e.serialize())
        update_edge_index(from_id, to_id, offset)