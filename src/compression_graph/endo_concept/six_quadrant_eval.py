# -*- coding: utf-8 -*-
"""
six_quadrant_eval.py -- Six-quadrant validation.

Uses:
  - G1 (energy graph) from g1_exporter
  - G2 (compression co-occurrence graph) from endo_result/raw_events_*/
  - B/C fixpoints from endo_result/scale*/config_*/...

Classification table (6 quadrants):

    G1  G2  B/C          ->  label
    +   +   silent       ->  meta-concept / meta-layer
    +   +   B+ C-        ->  general / interface / adsorbed core
    +   +   B+ C+        ->  specialist / core atom
    +   -   silent       ->  background path
    -   +   B+           ->  compression product
    -   -   silent       ->  background / directory

"+" / "-" split by z-score sign of G1/G2 composites.
"""
import argparse
import json
import os
import sys
from collections import Counter, defaultdict
from pathlib import Path

_parser = argparse.ArgumentParser()
_parser.add_argument("--config", choices=["A", "B", "C"], default="A")
_parser.add_argument("--scales", nargs="+", type=int, default=[51, 71, 91, 111])
_parser.add_argument("--g1_root", default=None)
_parser.add_argument("--endo_root", default=None)
_parser.add_argument("--out_dir", default=None)
_args = _parser.parse_args()

_HERE = os.path.dirname(os.path.abspath(__file__))
_CG = os.path.dirname(_HERE)
_SRC = os.path.dirname(_CG)
_PROJ = os.path.dirname(_SRC)
for _p in (_HERE, _CG, _SRC, _PROJ):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import numpy as np
import pandas as pd
import networkx as nx


if _args.g1_root is None:
    _args.g1_root = str(Path(_HERE) / "g1_export")
if _args.endo_root is None:
    _args.endo_root = str(Path(_HERE) / "endo_result")
if _args.out_dir is None:
    _args.out_dir = str(Path(_HERE) / "six_quadrant_results")


# ===================================================================== #
# Load
# ===================================================================== #
def load_g1_nodes(config, scale, g1_root):
    p = Path(g1_root) / f"config_{config}" / f"scale{scale}" / "g1_nodes.csv"
    if not p.exists():
        return None
    return pd.read_csv(p)


def load_g2_graph(config, scale, endo_root):
    """Build compression co-occurrence graph from raw events."""
    candidates = [
        Path(endo_root) / f"raw_events_{config}" / "raw_compression_events.csv",
        Path(endo_root) / f"raw_events_{config.lower()}" / "raw_compression_events.csv",
    ]
    src = None
    for p in candidates:
        if p.exists():
            src = p
            break
    if src is None:
        return None

    df = pd.read_csv(src)
    if "scale" in df.columns:
        df = df[df["scale"] == scale]
    if df.empty:
        return None

    G = nx.Graph()
    counts = Counter()
    for _, row in df.iterrows():
        center = row.get("center")
        if pd.isna(center):
            continue
        center = str(center)
        raw_rel = row.get("related_nodes", "")
        rel = [] if pd.isna(raw_rel) else [x.strip() for x in str(raw_rel).split("|") if x.strip()]
        nodes = list(dict.fromkeys([center] + rel))
        for i in range(len(nodes)):
            for j in range(i + 1, len(nodes)):
                key = tuple(sorted([nodes[i], nodes[j]]))
                counts[key] += 1

    for (u, v), c in counts.items():
        G.add_edge(u, v, count=int(c), weight=int(c))
    return G


def load_bc(config, scale, endo_root):
    base = Path(endo_root) / f"scale{scale}" / f"config_{config}" / "minsize_1"
    out = {"B": [], "C": []}
    for m in ("B", "C"):
        p = base / f"fixpoint_{m}" / "fixpoints.json"
        if p.exists():
            with open(p, "r", encoding="utf-8") as f:
                out[m] = json.load(f)
    return out


# ===================================================================== #
# Score functions
# ===================================================================== #
def _z(arr):
    arr = np.asarray(arr, dtype=float)
    m = arr.mean()
    s = arr.std()
    if s == 0 or np.isnan(s):
        return np.zeros_like(arr)
    return (arr - m) / s


def compute_g1_scores(g1_df):
    """G1 = energy graph. Positive = high energy-minimization activity.

    composite = -z(mean_weight) + z(weight_drop) + z(traversal_freq)

    Lower mean weight → higher score (more learned).
    Larger drop → higher score (more learning applied).
    Higher traversal freq → higher score (more activated).
    """
    df = g1_df.copy()
    for col in ("mean_weight", "min_weight", "weight_drop", "traversal_freq"):
        if col in df.columns:
            df[col] = df[col].fillna(df[col].median())

    score = (
        0.40 * _z(-df["mean_weight"].values)
        + 0.30 * _z(df["weight_drop"].values)
        + 0.30 * _z(df["traversal_freq"].values)
    )
    return dict(zip(df["concept"], score))


def compute_g2_scores(g2_graph):
    """G2 = sparse co-occurrence graph. Positive = high centrality."""
    if g2_graph is None or g2_graph.number_of_nodes() == 0:
        return {}

    weighted_deg = dict(g2_graph.degree(weight="count"))
    try:
        betweenness = nx.betweenness_centrality(g2_graph)
    except Exception:
        betweenness = {n: 0.0 for n in g2_graph.nodes()}

    nodes = list(g2_graph.nodes())
    wd = np.array([weighted_deg.get(n, 0) for n in nodes], dtype=float)
    bt = np.array([betweenness.get(n, 0) for n in nodes], dtype=float)

    score = 0.6 * _z(wd) + 0.4 * _z(bt)
    return dict(zip(nodes, score))


# ===================================================================== #
# Classify
# ===================================================================== #
def classify(g1_scores, g2_scores, bc, candidate_set):
    b_members = set()
    for fp in bc["B"]:
        for m in fp.get("core", []):
            b_members.add(m)

    c_members = set()
    for fp in bc["C"]:
        for m in fp.get("core", []):
            c_members.add(m)

    rows = []
    for concept in candidate_set:
        g1 = float(g1_scores.get(concept, 0.0))
        g2 = float(g2_scores.get(concept, 0.0))
        in_b = concept in b_members
        in_c = concept in c_members

        g1p = g1 > 0
        g2p = g2 > 0

        if g1p and g2p:
            if not in_b:
                label = "元概念/元层"
            elif in_b and not in_c:
                label = "一般层/接口"
            elif in_b and in_c:
                label = "专家层/核心原子"
            else:
                label = "未分类"
        elif g1p and not g2p:
            label = "背景路径" if not in_b else "未分类"
        elif not g1p and g2p:
            label = "压缩产物" if in_b else "未分类"
        else:  # not g1p and not g2p
            label = "背景/目录" if not in_b else "未分类"

        rows.append({
            "concept": concept,
            "g1_score": round(g1, 4),
            "g2_score": round(g2, 4),
            "in_B": in_b,
            "in_C": in_c,
            "quadrant": label,
        })
    return pd.DataFrame(rows)


# ===================================================================== #
# Main
# ===================================================================== #
def main():
    out_dir = Path(_args.out_dir) / f"config_{_args.config}"
    out_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 68)
    print(f"Six-quadrant evaluation -- config={_args.config}")
    print(f"  G1 root: {_args.g1_root}")
    print(f"  endo root: {_args.endo_root}")
    print(f"  out dir: {out_dir}")
    print("=" * 68)

    summary_rows = []

    for scale in _args.scales:
        print(f"\n[scale={scale}]")

        g1_df = load_g1_nodes(_args.config, scale, _args.g1_root)
        if g1_df is None:
            print(f"  [skip] G1 export not found at "
                  f"{_args.g1_root}/config_{_args.config}/scale{scale}/g1_nodes.csv")
            continue

        g2_graph = load_g2_graph(_args.config, scale, _args.endo_root)
        if g2_graph is None:
            print("  [warn] G2 source missing; G2 scores will be 0")

        bc = load_bc(_args.config, scale, _args.endo_root)
        print(f"  B fixpoints = {len(bc['B'])}, C fixpoints = {len(bc['C'])}")

        g1_scores = compute_g1_scores(g1_df)
        g2_scores = compute_g2_scores(g2_graph)
        df = classify(g1_scores, g2_scores, bc,
                      candidate_set=set(g1_scores.keys()))
        df["scale"] = scale
        df["config"] = _args.config

        out_csv = out_dir / f"six_quadrant_scale{scale}.csv"
        df.to_csv(out_csv, index=False, encoding="utf-8-sig")

        counts = df["quadrant"].value_counts().to_dict()
        print("  distribution:")
        for lab, n in sorted(counts.items(), key=lambda x: -x[1]):
            print(f"    {lab:20s} : {n}")

        row = {"scale": scale, "config": _args.config}
        for lab, n in counts.items():
            row[lab] = n
        summary_rows.append(row)

    if summary_rows:
        sdf = pd.DataFrame(summary_rows).fillna(0)
        sdf.to_csv(out_dir / "summary.csv",
                   index=False, encoding="utf-8-sig")
        print(f"\n[saved] {out_dir / 'summary.csv'}")


if __name__ == "__main__":
    main()