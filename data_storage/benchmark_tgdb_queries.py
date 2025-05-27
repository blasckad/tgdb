from __future__ import annotations
import argparse, random, time
from collections import defaultdict
import matplotlib.pyplot as plt
import numpy as np
from tqdm import trange

from read import (
    read_nodes_by_name_range,
    read_node_by_name_at_time,
    read_edges_by_direction,
    NODE_TREE,
    EDGE_DIR_TREE,
)
# ─────────────────────────────────────────────────────────────────────────────

# ─── счётчики размеров индекса ───────────────────────────────────────────────
def n_ver(name): return len(NODE_TREE[name])
def m_edges(name): return len(EDGE_DIR_TREE.get((name, "in"), [])) + \
                           len(EDGE_DIR_TREE.get((name, "out"), []))

# ─── набор имён узлов ────────────────────────────────────────────────────────
NAMES = list(NODE_TREE.keys())

# ─── операции ────────────────────────────────────────────────────────────────
def q_all_versions(name, t1, t2):
    return read_nodes_by_name_range(name, t1, t2)

def q_state_at(name, t):
    return read_node_by_name_at_time(name, t)

def q_edges_all(name, t1, t2):
    res = []
    for d in ("in", "out"):
        res.extend(read_edges_by_direction(name, d, t1, t2))
    return res

def q_edges_now(name, t):
    res = []
    for d in ("in", "out"):
        res.extend(read_edges_by_direction(name, d, t, t))
    return res

# ─── служебные функции ───────────────────────────────────────────────────────
def rnd_ts():
    now = int(time.time())
    return now + random.randint(-365 * 24 * 3600, 365 * 24 * 3600)

def pick_node_by_size(size_fn, low, high):
    pool = [n for n in NAMES if low <= size_fn(n) <= high]
    return random.choice(pool) if pool else random.choice(NAMES)

# ─── эксперименты ────────────────────────────────────────────────────────────
def vary_k(fn_window, node_name, size_fn, runs):
    k_vals, t_vals = [], []
    idx_size = size_fn(node_name)

    for _ in trange(runs, desc="vary_k", leave=False):
        t1 = rnd_ts()
        t2 = t1 + random.randint(0, 180 * 24 * 3600)
        res = fn_window(node_name, t1, t2)
        k = len(res)
        t0 = time.perf_counter()
        _ = res
        ms = 1000 * (time.perf_counter() - t0)
        k_vals.append(k)
        t_vals.append(ms)
    return np.array(k_vals), np.array(t_vals), idx_size

def vary_idx(fn_point, size_fn, runs, kind):
    idx_vals, t_vals = [], []
    for _ in trange(runs, desc="vary_idx", leave=False):
        name = random.choice(NAMES)
        if kind == "v":     # узлы
            res = fn_point(name, rnd_ts())
        else:               # рёбра
            res = fn_point(name, rnd_ts())
        t0 = time.perf_counter()
        _ = res
        ms = 1000 * (time.perf_counter() - t0)
        idx_vals.append(size_fn(name))
        t_vals.append(ms)
    return np.array(idx_vals), np.array(t_vals)

# ─── отрисовка ───────────────────────────────────────────────────────────────
def plot_k(k, t, idx, title_ru):
    plt.figure(figsize=(6, 4))
    plt.scatter(k, t, s=10, alpha=.6, marker="x", color="#e69f00")
    plt.title(f"{title_ru}:  T vs k   (индекс = {idx})")
    plt.xlabel("k — размер результата")
    plt.ylabel("Время, мс")
    plt.grid(ls=":", alpha=.5)
    plt.tight_layout()
    plt.show()

def plot_idx(idx, t, axis_ru, title_ru):
    plt.figure(figsize=(6, 4))
    plt.scatter(idx, t, s=10, alpha=.6, marker="x", color="#0072B2")
    plt.title(f"{title_ru}:  T vs {axis_ru}")
    plt.xlabel(axis_ru)
    plt.ylabel("Время, мс")
    plt.grid(ls=":", alpha=.5)
    plt.tight_layout()
    plt.show()

# ─── основные сценарии ───────────────────────────────────────────────────────
def main(runs: int):
    # 1. Все версии узла
    rich = pick_node_by_size(n_ver, 30, 100)
    k, t, idx = vary_k(q_all_versions, rich, n_ver, runs)
    plot_k(k, t, idx, "Все версии узла")
    idx_v, t_v = vary_idx(q_state_at, n_ver, runs, "v")
    plot_idx(idx_v, t_v, "n — количество версий", "Все версии узла")

    # 2. Состояние узла (только лог-график)
    idx_v, t_v = vary_idx(q_state_at, n_ver, runs, "v")
    plot_idx(idx_v, t_v, "n — количество версий", "Состояние узла")

    # 3. Все рёбра узла
    rich = pick_node_by_size(m_edges, 30, 100)
    k, t, idx = vary_k(q_edges_all, rich, m_edges, runs)
    plot_k(k, t, idx, "Все рёбра узла")
    idx_m, t_m = vary_idx(q_edges_now, m_edges, runs, "e")
    plot_idx(idx_m, t_m, "m — количество рёбер", "Все рёбра узла")

    # 4. Рёбра узла в диапазоне
    rich = pick_node_by_size(m_edges, 30, 100)
    k, t, idx = vary_k(q_edges_all, rich, m_edges, runs)
    plot_k(k, t, idx, "Рёбра узла в диапазоне")
    idx_m, t_m = vary_idx(q_edges_now, m_edges, runs, "e")
    plot_idx(idx_m, t_m, "m — количество рёбер", "Рёбра узла в диапазоне")

    # 5. Актуальные рёбра
    rich = pick_node_by_size(m_edges, 30, 100)
    k, t, idx = vary_k(q_edges_all, rich, m_edges, runs)
    plot_k(k, t, idx, "Актуальные рёбра узла")
    idx_m, t_m = vary_idx(q_edges_now, m_edges, runs, "e")
    plot_idx(idx_m, t_m, "m — количество рёбер", "Актуальные рёбра узла")

# ─── CLI ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--runs", type=int, default=400,
                        help="Сколько точек на каждый график (default 400)")
    args = parser.parse_args()
    main(args.runs)
