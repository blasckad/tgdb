class Node:
    def __init__(self, id, name, data=None):
        self.id = id
        self.name = name
        self.data = data or {}

class Edge:
    def __init__(self, from_node, to_node, data=None):
        self.from_node = from_node
        self.to_node = to_node
        self.data = data or {}
