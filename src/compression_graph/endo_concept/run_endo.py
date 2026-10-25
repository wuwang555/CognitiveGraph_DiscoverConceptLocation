# -*- coding: utf-8 -*-
"""
End-to-end entry point for the endo-concept generation module.

Pipeline per (scale, minsize, fixpoint_method):
    1. Load raw compression events.
    2. Detect fixpoints with the given method and min itemset size.
    3. Derive directed logic edges.
    4. Compute Φ (boundary potential) for each fixpoint.
    5. Build CONCEPT_STRUCTURE.
    6. Recompute edge weights with the multi-channel formula.
    7. Apply the high-order correction.

Output layout:
    endo_result/
        endo_summary.csv
        scale{N}/config_{X}/minsize_{M}/fixpoint_{method}/
            fixpoints.json
            logic_edges.csv
            concept_structure.json
            edge_weights.csv
            run_meta.json

Run:
    CONFIG_METHOD=B python run_endo.py
or via batch:
    python batch_run.py
"""

import os
import sys
import json
import random
import traceback
from pathlib import Path

import numpy as np

# ---------- Reproducibility ----------
random.seed(42)
np.random.seed(42)
os.environ.setdefault("PYTHONHASHSEED", "0")

_HERE = os.path.dirname(os.path.abspath(__file__))   # .../endo_concept
_CG = os.path.dirname(_HERE)                         # .../compression_graph
_PROJ = os.path.dirname(_CG)                         # project root
for _p in (_HERE, _CG, _PROJ):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import pandas as pd

from config_endo import ENDO_CONCEPT_CONFIG
from fixpoint import FixpointDetector
from logic_derive import LogicDeriver
from boundary import compute_phi, boundary_summary
from structure import build_concept_structure
from multichannel import rebuild_edges_with_multichannel
from high_order import apply_high_order_correction

from src.compression_graph.cg_core import UndirectedCompressionGraph


# ====================================================================== #
def _config_method():
    return os.environ.get("CONFIG_METHOD", "B").upper()


def _resolve_raw_csv(cfg):
    """Resolve the raw compression events CSV."""
    env = os.environ.get("ENDO_RAW_CSV")
    if env:
        p = Path(env)
        if p.exists():
            return p

    raw_csv = Path(cfg["raw_events_path"])
    if raw_csv.exists():
        return raw_csv

    alt = Path("../results/compression_graph/raw_compression_events.csv")
    if alt.exists():
        return alt

    return raw_csv


# ====================================================================== #
def load_events(csv_path, scale):
    df = pd.read_csv(csv_path)
    if "scale" in df.columns:
        df = df[df["scale"] == scale]

    events = []
    for _, row in df.iterrows():
        related_raw = row.get("related_nodes", "")
        if pd.isna(related_raw):
            related = []
        else:
            related = [r.strip() for r in str(related_raw).split("|")
                       if r and r != "nan"]

        center = row.get("center", None)
        if pd.isna(center):
            continue

        events.append({
            "event_id": int(row.get("event_id", len(events))),
            "detection_iteration": int(row["detection_iteration"])
                if "detection_iteration" in row and pd.notna(row["detection_iteration"])
                else -1,
            "center": str(center),
            "related_nodes": related,
            "emergence_strength": float(row["emergence_strength"])
                if "emergence_strength" in row and pd.notna(row["emergence_strength"])
                else None,
        })
    return events


# ====================================================================== #
def run_one_scale(scale, events, cfg, out_dir):
    """Run the full endo-concept pipeline for one (scale, configB.md) combo.

    Results are written directly into `out_dir`.
    """
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    method = str(cfg.get("fixpoint_method", "A")).upper()
    minsize = int(cfg.get("fp_min_itemset_size", 1))
    config_method = _config_method()

    print(f"\n{'=' * 70}")
    print(f"# Endo-concept  scale={scale}  configB.md={config_method}  "
          f"minsize={minsize}  method={method}")
    print(f"{'=' * 70}")
    print(f"Loaded {len(events)} compression events")

    # ---- 1. Fixpoint detection ----
    detector = FixpointDetector(cfg)
    fixpoints = detector.detect(events)
    print(f"[Fixpoints] detected: {len(fixpoints)}")
    for fp in fixpoints[:10]:
        print(f"  core={fp['core']}  support={fp['support']:.3f}  "
              f"stability={fp['stability']:.3f}  method={fp['method']}")
    if len(fixpoints) > 10:
        print(f"  ... ({len(fixpoints) - 10} more)")

    # ---- 2. Logic derivation ----
    deriver = LogicDeriver(cfg)
    logic_result = deriver.derive(fixpoints, events)
    total_edges = sum(len(r["boundary"]) for r in logic_result)
    print(f"[Logic] derived {total_edges} boundary edges over "
          f"{len(logic_result)} clusters")

    # ---- 3. Build compression graph ----
    graph = UndirectedCompressionGraph(edge_mode="clique")
    graph.add_compressions(events)
    graph.build()
    print(f"[Graph] nodes={graph.G.number_of_nodes()} "
          f"edges={graph.G.number_of_edges()}")

    # ---- 4. Φ for each fixpoint ----
    phi_list = []
    for fp in fixpoints:
        phi = compute_phi(graph, fp["core"])
        fp["phi"] = float(phi) if phi is not None else None
        if phi is not None:
            phi_list.append(phi)
    phi_stats = boundary_summary(phi_list)
    if phi_stats:
        print(f"[Boundary Φ] mean={phi_stats['mean']:.3f}  "
              f"std={phi_stats['std']:.3f}  n={phi_stats['count']}")

    # ---- 5. Build concept structure ----
    structure = build_concept_structure(fixpoints, logic_result, events, graph)
    print(f"[Structure] generated {len(structure)} concept entries")

    # ---- 6. Multi-channel initialization ----
    rebuild_edges_with_multichannel(
        graph, structure,
        semantic_similarity_fn=None,
        weights=(cfg["w_sim"], cfg["w_logic"], cfg["w_energy"]),
    )
    print(f"[Multi-channel] recomputed {graph.G.number_of_edges()} edge weights")

    # ---- 7. High-order correction ----
    if cfg.get("enable_high_order", True):
        apply_high_order_correction(graph, fixpoints, events)
        print("[High-order] applied λ_C correction inside fixpoints")

    # ================= Save =================
    with open(out_dir / "fixpoints.json", "w", encoding="utf-8") as f:
        json.dump(fixpoints, f, ensure_ascii=False, indent=2, default=str)

    logic_rows = []
    for rec in logic_result:
        for b, w in rec["logic"].items():
            logic_rows.append({
                "scale": scale,
                "core": "|".join(rec["core"]),
                "boundary": b,
                "logic_strength": round(float(w), 6),
            })
    if logic_rows:
        pd.DataFrame(logic_rows).to_csv(
            out_dir / "logic_edges.csv", index=False, encoding="utf-8-sig"
        )

    with open(out_dir / "concept_structure.json", "w", encoding="utf-8") as f:
        json.dump(structure, f, ensure_ascii=False, indent=2)

    edge_rows = []
    for u, v, d in graph.G.edges(data=True):
        edge_rows.append({
            "scale": scale,
            "concept_a": u,
            "concept_b": v,
            "count": int(d.get("count", 0)),
            "weight_multichannel": round(float(d.get("weight", 0.0)), 6),
            "weight_high_order": round(
                float(d.get("weight_high_order", d.get("weight", 0.0))), 6),
        })
    if edge_rows:
        pd.DataFrame(edge_rows).to_csv(
            out_dir / "edge_weights.csv", index=False, encoding="utf-8-sig"
        )

    # ---- Run meta ----
    meta = {
        "scale": scale,
        "config_method": config_method,
        "minsize": minsize,
        "fixpoint_method": method,
        "n_events": len(events),
        "n_fixpoints": len(fixpoints),
        "n_logic_edges": total_edges,
        "n_structure_entries": len(structure),
        "phi_mean": phi_stats.get("mean"),
        "phi_std": phi_stats.get("std"),
    }
    with open(out_dir / "run_meta.json", "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

    print(f"[Saved] {out_dir}")

    return {
        "n_events": len(events),
        "n_fixpoints": len(fixpoints),
        "n_logic_edges": total_edges,
        "n_structure_entries": len(structure),
        "phi_mean": phi_stats.get("mean"),
        "phi_std": phi_stats.get("std"),
    }


# ====================================================================== #
def main():
    cfg = ENDO_CONCEPT_CONFIG
    config_method = _config_method()

    output_root = Path(os.environ.get("ENDO_OUTPUT_DIR", cfg["output_dir"]))
    output_root.mkdir(parents=True, exist_ok=True)

    raw_csv = _resolve_raw_csv(cfg)
    if not raw_csv.exists():
        print(f"[ERROR] raw events CSV not found: {raw_csv}")
        print("        Run `python run_static.py` first to produce it.")
        return

    print(f"CONFIG_METHOD   = {config_method}")
    print(f"Raw events CSV  = {raw_csv}")
    print(f"Output root     = {output_root.resolve()}")

    methods = cfg.get("fixpoint_methods", ["A", "B", "C", "ABC"])
    min_sizes = cfg.get("min_itemset_sizes", [1, 2, 3])
    scales = cfg.get("scales", [51, 71, 91, 111])

    summary_rows = []

    for scale in scales:
        events = load_events(str(raw_csv), scale)
        if not events:
            print(f"[skip] scale {scale}: no events")
            continue

        for minsize in min_sizes:
            for method in methods:
                c = dict(cfg)
                c["fp_min_itemset_size"] = minsize
                c["fixpoint_method"] = method

                out_dir = (
                    output_root
                    / f"scale{scale}"
                    / f"config_{config_method}"
                    / f"minsize_{minsize}"
                    / f"fixpoint_{method}"
                )

                try:
                    row = run_one_scale(scale, events, c, out_dir)
                except Exception as exc:
                    print(f"[ERROR] scale={scale} minsize={minsize} "
                          f"method={method}: {exc}")
                    traceback.print_exc()
                    continue

                row.update({
                    "scale": scale,
                    "config_method": config_method,
                    "minsize": minsize,
                    "fixpoint_method": method,
                })
                summary_rows.append(row)

    # ---- Merge summary ----
    if summary_rows:
        summary_path = output_root / "endo_summary.csv"
        df = pd.DataFrame(summary_rows)
        if summary_path.exists():
            old = pd.read_csv(summary_path)
            df = pd.concat([old, df], ignore_index=True)
            df = df.drop_duplicates(
                subset=["scale", "config_method", "minsize", "fixpoint_method"],
                keep="last",
            )

        # Column order
        cols = [
            "scale", "config_method", "minsize", "fixpoint_method",
            "n_events", "n_fixpoints", "n_logic_edges",
            "n_structure_entries", "phi_mean", "phi_std",
        ]
        cols = [c for c in cols if c in df.columns]
        df = df[cols]
        df.to_csv(summary_path, index=False, encoding="utf-8-sig")

        print(f"\n{'=' * 70}")
        print(f"Saved summary: {summary_path}")
        print(df.to_string(index=False))


if __name__ == "__main__":
    main()