# -*- coding: utf-8 -*-
"""
Run all objective metrics end-to-end:

  1. Run the universe (raw-recording) once per scale.
  2. Build the compression graph.
  3. Compute:
       - energy-decline power-law fit
       - edge-cooccurrence Zipf
       - center-frequency Zipf
       - total-node-frequency Zipf
       - compression-potential Phi distribution
       - migration threshold scan
       - compression threshold scan
  4. Save CSV tables under results/compression_graph/objective_metrics/
"""

import os
import sys
from pathlib import Path

_HERE = os.path.dirname(os.path.abspath(__file__))
_CG = os.path.dirname(_HERE)
_PROJ = os.path.dirname(_CG)
for _p in (_HERE, _CG, _PROJ):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import pandas as pd

from src.compression_graph.config_compression import COMPRESSION_GRAPH_CONFIG
from src.compression_graph.raw_recorder import RawRecordingUniverseEnhanced
from src.compression_graph.cg_core import UndirectedCompressionGraph
from src.compression_graph.detector import CompressionGraphDetector

from zipf import edge_zipf, center_zipf, node_total_zipf
from power_law import fit_energy_curve
from potential import potential_stats
from threshold_scan import (
    scan_migration_threshold,
    scan_compression_threshold,
)

from src.utils.individual_variation import (
    IndividualVariation,
    create_enhanced_individual_params,
)
from config import BASE_PARAMETERS, VARIATION_RANGES


def run_universe(scale, max_iterations=10000, detection_interval=100):
    var_sim = IndividualVariation(BASE_PARAMETERS, VARIATION_RANGES)
    base_params = var_sim.generate_individual(f"scale{scale}_obj")
    ind_params = create_enhanced_individual_params(base_params)

    universe = RawRecordingUniverseEnhanced(
        individual_params=ind_params,
        network_seed=42,
        num_concepts=scale,
    )
    universe.initialize_semantic_network()
    universe.evolve_with_emergence_detection(
        iterations=max_iterations,
        detection_interval=detection_interval,
    )
    return universe


def main():
    cfg = COMPRESSION_GRAPH_CONFIG
    scales = [51, 71, 91, 111]

    out_dir = (Path(_HERE) / "../../../results/objective_metrics").resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    power_rows = []
    edge_zipf_rows = []
    center_zipf_rows = []
    node_total_zipf_rows = []
    potential_rows = []
    mig_scan_rows = []
    comp_scan_rows = []

    mig_thresholds = [20, 30, 40, 50, 60, 70, 80, 90, 100]
    comp_thresholds = [1.0, 1.25, 1.5, 1.75, 2.0, 2.25, 2.5, 3.0]

    for scale in scales:
        print(f"\n{'#' * 60}")
        print(f"# Objective metrics, scale = {scale}")
        print(f"{'#' * 60}")

        universe = run_universe(scale)

        # --- Energy power law ---
        fit = fit_energy_curve(universe.energy_history)
        if fit:
            power_rows.append({
                "scale": scale,
                "model": fit["model"],
                "a": fit["a"],
                "b": fit["b"],
                "c": fit["c"],
                "r2": fit["r2"],
                "rmse": fit["rmse"],
                "n_iterations": len(universe.energy_history),
            })
            print(f"  Power law: model={fit['model']}, "
                  f"b={fit['b']:.4f}, R2={fit['r2']:.4f}, "
                  f"RMSE={fit['rmse']:.4f}")

        # --- Build graph ---
        compressions = universe.raw_compressions
        seed_nodes = list(universe.G.nodes())
        graph = UndirectedCompressionGraph(edge_mode=cfg["edge_mode"])
        graph.add_compressions(compressions)
        graph.build(seed_nodes=seed_nodes)

        # --- Zipf: edges ---
        ez = edge_zipf(graph)
        if ez:
            edge_zipf_rows.append({"scale": scale, **ez})
            print(f"  Edge Zipf: slope={ez['slope']:.3f}, "
                  f"R2={ez['r2']:.3f}, n_edges={ez['n']}")

        # --- Zipf: centers ---
        cz = center_zipf(compressions)
        if cz:
            center_zipf_rows.append({"scale": scale, **cz})
            print(f"  Center Zipf: slope={cz['slope']:.3f}, "
                  f"R2={cz['r2']:.3f}, n_centers={cz['n']}")

        # --- Zipf: node totals ---
        nz = node_total_zipf(compressions)
        if nz:
            node_total_zipf_rows.append({"scale": scale, **nz})
            print(f"  Node-total Zipf: slope={nz['slope']:.3f}, "
                  f"R2={nz['r2']:.3f}, n_nodes={nz['n']}")

        # --- Compression potential ---
        detector = CompressionGraphDetector(graph, cfg)
        clusters = detector.detect_compression()
        phi_values = [c["phi"] for c in clusters]
        ps = potential_stats(phi_values)
        if ps:
            potential_rows.append({"scale": scale, **ps})
            print(f"  Phi: mean={ps['mean']:.3f}, std={ps['std']:.3f}, "
                  f"min={ps['min']:.3f}, max={ps['max']:.3f}, n={ps['count']}")

        # --- Migration threshold scan ---
        mig_scan = scan_migration_threshold(graph, cfg, mig_thresholds)
        for t, n in mig_scan.items():
            mig_scan_rows.append({
                "scale": scale, "threshold": t, "n_migrations": n,
            })
        print(f"  Migration scan: "
              f"{ {t: n for t, n in sorted(mig_scan.items())} }")

        # --- Compression threshold scan ---
        comp_scan = scan_compression_threshold(graph, cfg, comp_thresholds)
        for t, n in comp_scan.items():
            comp_scan_rows.append({
                "scale": scale, "threshold": t, "n_compressions": n,
            })
        print(f"  Compression scan: "
              f"{ {t: n for t, n in sorted(comp_scan.items())} }")

    # --- Save all CSV tables ---
    def save(rows, name):
        if not rows:
            print(f"[skip] {name}.csv (no rows)")
            return
        path = out_dir / f"{name}.csv"
        pd.DataFrame(rows).to_csv(path, index=False, encoding="utf-8-sig")
        print(f"Saved: {path}")

    print(f"\n{'=' * 60}")
    print("Saving objective-metric tables...")
    print(f"{'=' * 60}")

    save(power_rows, "power_law")
    save(edge_zipf_rows, "zipf_edges")
    save(center_zipf_rows, "zipf_centers")
    save(node_total_zipf_rows, "zipf_node_totals")
    save(potential_rows, "potential")
    save(mig_scan_rows, "threshold_scan_migration")
    save(comp_scan_rows, "threshold_scan_compression")

    # --- Print final summary ---
    print(f"\n{'=' * 60}")
    print("Summary")
    print(f"{'=' * 60}")

    if power_rows:
        print("\n[Power law]")
        print(pd.DataFrame(power_rows).to_string(index=False))

    if edge_zipf_rows:
        print("\n[Edge Zipf]")
        print(pd.DataFrame(edge_zipf_rows).to_string(index=False))

    if center_zipf_rows:
        print("\n[Center Zipf]")
        print(pd.DataFrame(center_zipf_rows).to_string(index=False))

    if potential_rows:
        print("\n[Compression potential]")
        print(pd.DataFrame(potential_rows).to_string(index=False))


if __name__ == "__main__":
    main()