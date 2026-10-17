# -*- coding: utf-8 -*-
"""
End-to-end entry point for the endo-concept generation module.

Pipeline:
    1. Load raw compression events produced by the first-order system.
    2. Detect fixpoints with the configured method (A / B / C / ABC).
    3. Derive directed logic edges.
    4. Compute Φ (boundary potential) for each fixpoint.
    5. Build CONCEPT_STRUCTURE.
    6. Recompute edge weights with the multi-channel formula.
    7. Apply the high-order correction.

Run (from the `compression_graph/` directory):
    python endo_concept/run_endo.py

Or (from project root):
    python compression_graph/endo_concept/run_endo.py
"""

import os
import sys
import json
from pathlib import Path

_HERE = os.path.dirname(os.path.abspath(__file__))   # .../compression_graph/endo_concept
_CG = os.path.dirname(_HERE)                          # .../compression_graph
_PROJ = os.path.dirname(_CG)                          # project root
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
def _resolve_paths(cfg):
    """Find raw_compression_events.csv whether the script is run from
    compression_graph/ or from the project root."""
    raw_csv = Path(cfg["raw_events_path"])
    out_dir = Path(cfg["output_dir"])
    if raw_csv.exists():
        return raw_csv, out_dir

    alt_raw = Path("../results/compression_graph/"
                   "raw_compression_events.csv")
    alt_out = Path("compression_graph/results/compression_graph/endo_concept")
    if alt_raw.exists():
        return alt_raw, alt_out

    return raw_csv, out_dir


# ====================================================================== #
def load_events(csv_path: str, scale: int):
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
def run_one_scale(scale: int,
                  events,
                  cfg,
                  out_dir: Path):
    print(f"\n{'=' * 62}")
    print(f"# Endo-concept generation, scale = {scale}")
    print(f"# Fixpoint method = {cfg['fixpoint_method']}")
    print(f"{'=' * 62}")
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

    # ---- 3. Build compression graph (needed for energy gradient + Φ) ----
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
              f"std={phi_stats['std']:.3f}  "
              f"n={phi_stats['count']}")

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

    # ---- Save outputs ----
    scale_dir = out_dir / f"scale{scale}"
    scale_dir.mkdir(parents=True, exist_ok=True)

    with open(scale_dir / "fixpoints.json", "w", encoding="utf-8") as f:
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
            scale_dir / "logic_edges.csv", index=False, encoding="utf-8-sig"
        )

    with open(scale_dir / "concept_structure.json", "w", encoding="utf-8") as f:
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
            scale_dir / "edge_weights.csv", index=False, encoding="utf-8-sig"
        )

    print(f"[Saved] {scale_dir}")

    return {
        "scale": scale,
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
    raw_csv, out_dir = _resolve_paths(cfg)
    out_dir.mkdir(parents=True, exist_ok=True)

    if not raw_csv.exists():
        print(f"[ERROR] raw events CSV not found: {raw_csv}")
        print("        Run `python run_static.py` first to produce it.")
        return

    print(f"Using raw events CSV: {raw_csv}")
    print(f"Output directory:     {out_dir}")

    summary_rows = []
    for scale in cfg.get("scales", [51, 71, 91, 111]):
        try:
            events = load_events(str(raw_csv), scale)
        except Exception as exc:
            print(f"[skip] scale {scale}: {exc}")
            continue
        if not events:
            print(f"[skip] scale {scale}: no events")
            continue
        row = run_one_scale(scale, events, cfg, out_dir)
        summary_rows.append(row)

    if summary_rows:
        path = out_dir / "endo_summary.csv"
        pd.DataFrame(summary_rows).to_csv(path, index=False, encoding="utf-8-sig")
        print(f"\n{'=' * 62}")
        print(f"Saved summary: {path}")
        print(pd.DataFrame(summary_rows).to_string(index=False))


if __name__ == "__main__":
    main()