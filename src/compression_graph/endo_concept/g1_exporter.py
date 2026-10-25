# -*- coding: utf-8 -*-
"""
g1_exporter.py -- Export G1 (energy-graph) data for six-quadrant validation.

G1 in the original paper is a fully-connected (or near-fully-connected)
weighted energy graph. Node "importance" does NOT come from degree, but
from how much the node's incident edges have been energy-minimized:

  - mean edge weight  (lower  = more learned)
  - minimum edge weight (low  = at least one strong path)
  - weight drop       (original - current, larger = more learning)
  - traversal frequency (higher = more activation)

This exporter runs the original emergence model once per (config_method,
scale) and writes G1 to CSV.

Compatibility note
------------------
CognitiveUniverseEnhanced overrides `observations` and drops keys that
the parent's evolve() expects. We re-add them before calling evolve().
No change is made to the original paper code.

Usage
-----
    # from endo_concept/ directory
    python g1_exporter.py --config A

    # or orchestrated via run_validation.py
"""
import argparse
import os
import sys

# ---- 1. Parse args BEFORE importing config (CONFIG_METHOD must be set first) ----
_parser = argparse.ArgumentParser()
_parser.add_argument("--config", choices=["A", "B", "C"], default="A")
_parser.add_argument("--scales", nargs="+", type=int, default=[51, 71, 91, 111])
_parser.add_argument("--iterations", type=int, default=10000)
_parser.add_argument("--out_root", default=None,
                     help="Default: <project_root>/results/g1_export")
_args = _parser.parse_args()

os.environ["CONFIG_METHOD"] = _args.config

# ---- 2. Path setup ----
_HERE = os.path.dirname(os.path.abspath(__file__))
_CG   = os.path.dirname(_HERE)
_SRC  = os.path.dirname(_CG)
_PROJ = os.path.dirname(_SRC)
for _p in (_HERE, _CG, _SRC, _PROJ):
    if _p not in sys.path:
        sys.path.insert(0, _p)

# ---- 3. Now import config and packages ----
import numpy as np
import pandas as pd
from pathlib import Path
from collections import Counter, defaultdict

from src.emergence.universe_enhanced import CognitiveUniverseEnhanced
from src.utils.individual_variation import (
    IndividualVariation,
    create_enhanced_individual_params,
)
from config import BASE_PARAMETERS, VARIATION_RANGES


# ===================================================================== #
def _patch_observations(universe):
    """Re-add keys that CognitiveUniverseEnhanced dropped from the
    parent's observations dict. Required by CognitiveUniverse.evolve()."""
    for key in (
        'spontaneous_compressions',
        'emergent_migrations',
        'traversal_patterns',
        'energy_minimization_traces',
        'network_evolution_snapshots',
    ):
        universe.observations.setdefault(key, [])


# ===================================================================== #
def export_g1(universe, scale, config, out_root):
    """Write G1 data (edges, nodes, energy_history, traversal_freq) to CSV."""
    out_dir = Path(out_root) / f"config_{config}" / f"scale{scale}"
    out_dir.mkdir(parents=True, exist_ok=True)
    G = universe.G

    # ---- edges ----
    edge_rows = []
    for u, v, d in G.edges(data=True):
        edge_rows.append({
            "concept_a": u,
            "concept_b": v,
            "weight": float(d["weight"]),
            "original_weight": float(d.get("original_weight", d["weight"])),
            "traversal_count": int(d.get("traversal_count", 0)),
            "similarity": float(d.get("similarity", 0.0)),
        })
    pd.DataFrame(edge_rows).to_csv(out_dir / "g1_edges.csv",
                                   index=False, encoding="utf-8-sig")

    # ---- nodes (aggregate) ----
    node_weights = defaultdict(list)
    node_drops = defaultdict(list)
    node_sims = defaultdict(list)
    for u, v, d in G.edges(data=True):
        w = d["weight"]
        ow = d.get("original_weight", w)
        sim = d.get("similarity", 0.0)
        for node in (u, v):
            node_weights[node].append(w)
            node_drops[node].append(ow - w)
            node_sims[node].append(sim)

    traversal_freq = Counter()
    for t in universe.traversal_history:
        path = None
        if isinstance(t, dict):
            path = t.get("path")
        elif isinstance(t, (list, tuple)):
            path = t[0] if (t and isinstance(t[0], list)) else list(t)
        if path:
            for node in path:
                traversal_freq[node] += 1

    node_rows = []
    for c in set(node_weights.keys()) | set(traversal_freq.keys()):
        ws = node_weights.get(c, [])
        ds = node_drops.get(c, [])
        ss = node_sims.get(c, [])
        node_rows.append({
            "concept": c,
            "mean_weight": float(np.mean(ws)) if ws else None,
            "min_weight": float(np.min(ws)) if ws else None,
            "weight_drop": float(np.mean(ds)) if ds else 0.0,
            "mean_similarity": float(np.mean(ss)) if ss else 0.0,
            "traversal_freq": int(traversal_freq.get(c, 0)),
        })
    pd.DataFrame(node_rows).to_csv(out_dir / "g1_nodes.csv",
                                   index=False, encoding="utf-8-sig")

    # ---- energy_history ----
    pd.DataFrame({
        "iteration": list(range(len(universe.energy_history))),
        "energy": [float(e) for e in universe.energy_history],
    }).to_csv(out_dir / "energy_history.csv",
              index=False, encoding="utf-8-sig")

    # ---- traversal_freq (standalone) ----
    pd.DataFrame([
        {"concept": c, "freq": n}
        for c, n in sorted(traversal_freq.items(), key=lambda x: -x[1])
    ]).to_csv(out_dir / "traversal_freq.csv",
              index=False, encoding="utf-8-sig")

    print(f"  [saved] {out_dir}  "
          f"({len(edge_rows)} edges, {len(node_rows)} nodes, "
          f"{len(universe.energy_history)} energy points)")


# ===================================================================== #
def main():
    default_root = Path(_PROJ) / "results" / "g1_export"
    out_root = (Path(_PROJ) / "results" / "g1_export").resolve()
    out_root.mkdir(parents=True, exist_ok=True)

    print("=" * 68)
    print(f"G1 exporter -- config={_args.config}, scales={_args.scales}")
    print("=" * 68)

    for scale in _args.scales:
        print(f"\n[scale={scale}] initializing ...")

        var_sim = IndividualVariation(BASE_PARAMETERS, VARIATION_RANGES)
        base_params = var_sim.generate_individual(f"g1_{_args.config}_{scale}")
        ind_params = create_enhanced_individual_params(base_params)

        universe = CognitiveUniverseEnhanced(
            individual_params=ind_params,
            network_seed=42,
            num_concepts=scale,
        )
        universe.initialize_semantic_network()

        # ★ 修复 KeyError：补全子类覆盖后丢失的 observations 键
        _patch_observations(universe)

        # ★ 用父类的 evolve() —— 与 universe.py 完全一致的一阶演化，
        #    不掺 emergence detection 的开销；G1 只需要图 + history。
        universe.evolve(
            iterations=_args.iterations,
            observation_interval=100,
        )

        export_g1(universe, scale, _args.config, out_root)

    print("\nDone.  G1 export at:", out_root)


if __name__ == "__main__":
    main()