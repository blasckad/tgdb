import os
from create import write_node, write_edge, save_all_indexes

# Пути к файлам
ACTIONS_PATH = "../data/mooc_actions.tsv"
FEATURES_PATH = "../data/mooc_action_features.tsv"
LABELS_PATH = "../data/mooc_action_labels.tsv"

# ========== Загрузка данных ==========

# 1. Читаем метки
labels = {}
with open(LABELS_PATH, "r") as f:
    next(f)  # пропустить заголовок
    for line in f:
        action_id, label = line.strip().split()
        labels[action_id] = int(label)

# 2. Читаем признаки
features = {}
with open(FEATURES_PATH, "r") as f:
    next(f)
    for line in f:
        parts = line.strip().split()
        action_id = parts[0]
        feats = list(map(float, parts[1:]))
        features[action_id] = feats

# 3. Читаем действия и записываем в TGDB
LIMIT = 500_000  # можно увеличить

with open(ACTIONS_PATH, "r") as f:
    next(f)
    for i, line in enumerate(f):
        if i >= LIMIT:
            break

        action_id, user_id, target_id, ts = line.strip().split()
        timestamp = int(float(ts))
        user = f"user_{user_id}"
        target = f"item_{target_id}"
        start = timestamp
        end = start + 60  # минута как длительность действия

        # Признаки и метки
        feats = features.get(action_id, [])
        label = labels.get(action_id, 0)

        edge_data = {
            "action_id": action_id,
            "features": feats,
            "label": label
        }

        # Запись
        write_node(user, start, end, {})
        write_node(target, start, end, {})
        write_edge(user, target, start, end, edge_data)

# Финальное сохранение
save_all_indexes()
print("✅ ACT-MOOC записан в TGDB.")
