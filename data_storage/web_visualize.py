import streamlit as st
from pyvis.network import Network
import os
import json
import uuid
import tempfile
from read import read_all_nodes
from read import read_all_edges

st.set_page_config(page_title="TGDB Graph Visualizer", layout="wide")
st.title("TGDB: Визуализация графа сущностей и связей")

# Фильтры
timestamp_filter = st.slider("Фильтрация по timestamp", 0, 2000000000, 2000000000, step=1)
only_active = st.checkbox("Только активные узлы и связи", value=True)

# Создание графа
net = Network(height="750px", width="100%", directed=True)
net.force_atlas_2based()

# Загрузка и отображение узлов
node_ids = set()
for node in read_all_nodes():
    if only_active and not node.get("active"):
        continue
    if node["timestamp"] > timestamp_filter:
        continue

    node_id = node["node_id"]  # Уникальный ID для графа
    label = f"{node['name']} [{node['timestamp']}]"
    tooltip = f"Имя: {node['name']}<br>Timestamp: {node['timestamp']}<br>Active: {node['active']}<br>Данные: {json.dumps(node['data'], ensure_ascii=False)}"

    net.add_node(node_id, label=label, title=tooltip)
    node_ids.add(node_id)

# Загрузка и отображение рёбер
for edge in read_all_edges():
    if only_active and not edge.get("active"):
        continue
    if edge["timestamp_start"] > timestamp_filter:
        continue

    edge_id = edge["edge_id"]
    from_node_id = edge["from_id"]
    to_node_id = edge["to_id"]

    if from_node_id not in node_ids or to_node_id not in node_ids:
        continue

    label = edge["data"].get("type", "связь")
    tooltip = f"Тип: {label}<br>Timestamp: {edge['timestamp_start']}<br>Данные: {json.dumps(edge['data'], ensure_ascii=False)}"

    net.add_edge(from_node_id, to_node_id, label=label, title=tooltip)

# Отображение графа
with tempfile.NamedTemporaryFile(delete=False, suffix=".html") as tmp_file:
    net.save_graph(tmp_file.name)
    html_path = tmp_file.name

st.components.v1.html(open(html_path, 'r', encoding='utf-8').read(), height=800, scrolling=True)
