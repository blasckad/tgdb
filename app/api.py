from flask import Blueprint, request, jsonify
from app.db import ArangoDB

db = ArangoDB(db_name="TemporalGraphDB", username="root", password="my_password")
nodes = db.get_collection("Nodes")
edges = db.get_collection("Edges", edge=True)

api_blueprint = Blueprint('api', __name__)

@api_blueprint.route('/nodes', methods=['POST'])
def create_node():
    data = request.json
    node = {
        "id": data["id"],
        "name": data["name"],
        "data": data.get("data", {})
    }
    nodes.insert(node, overwrite=True)
    return jsonify({"message": "Node created", "node": node}), 201

@api_blueprint.route('/edges', methods=['POST'])
def create_edge():
    data = request.json
    edge = {
        "_from": f"Nodes/{data['from']}",
        "_to": f"Nodes/{data['to']}",
        "data": data.get("data", {})
    }
    edges.insert(edge, overwrite=True)
    return jsonify({"message": "Edge created", "edge": edge}), 201

@api_blueprint.route('/nodes/<node_id>', methods=['GET'])
def get_node(node_id):
    node = nodes.get({"id": node_id})
    if not node:
        return jsonify({"error": "Node not found"}), 404
    return jsonify(node), 200

@api_blueprint.route('/edges', methods=['GET'])
def get_edges():
    result = [edge for edge in edges.all()]
    return jsonify(result), 200
