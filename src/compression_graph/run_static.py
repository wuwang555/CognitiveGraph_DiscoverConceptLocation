# -*- coding: utf-8 -*-
"""
Static entry point.

Run the original emergence experiment once per scale, then post-process
the raw compression events into the compression graph, detect
compression / migration candidates, and export CSV tables.
"""

import os
import sys
from pathlib import Path

_HERE = os.path.dirname(os.path.abspath(__file__))
_PROJ = os.path.dirname(_HERE)
for _p in (_HERE, _PROJ):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from config_compression import COMPRESSION_GRAPH_CONFIG
from raw_recorder import RawRecordingUniverseEnhanced
from cg_core import UndirectedCompressionGraph
from pipeline import CompressionGraphPipeline
from table_export import TableExporter
from visualize import (
    plot_compression_graph,
    plot_edge_count_distribution,
    plot_migration_paths,
)

from src.utils.individual_variation import (
    IndividualVariation,
    create_enhanced_individual_params,
)
from config import BASE_PARAMETERS, VARIATION_RANGES


def run_one(scale, individual_id=0, max_iterations=10000,
            detection_interval=100, use_raw=True):
    var_sim = IndividualVariation(BASE_PARAMETERS, VARIATION_RANGES)
    base_params = var_sim.generate_individual(
        f"scale{scale}_ind{individual_id}"
    )
    ind_params = create_enhanced_individual_params(base_params)

    universe = RawRecordingUniverseEnhanced(
        individual_params=ind_params,
        network_seed=42 + individual_id,
        num_concepts=scale,
    )
    universe.initialize_semantic_network()
    universe.evolve_with_emergence_detection(
        iterations=max_iterations,
        detection_interval=detection_interval,
    )

    if use_raw:
        compressions = universe.raw_compressions
    else:
        compressions = universe.observations["natural_compressions"]

    print(f"[scale={scale}] raw compression events: {len(compressions)}")
    seed_nodes = list(universe.G.nodes())
    return compressions, seed_nodes


def main():
    cfg = COMPRESSION_GRAPH_CONFIG
    scales = [51, 71, 91, 111]
    out_dir = Path(cfg["output_dir"])
    out_dir.mkdir(parents=True, exist_ok=True)

    exporter = TableExporter(out_dir)

    for scale in scales:
        print(f"\n{'#' * 60}")
        print(f"# Scale = {scale}")
        print(f"{'#' * 60}")

        compressions, seed_nodes = run_one(
            scale, use_raw=cfg["use_raw_events"]
        )

        pipeline = CompressionGraphPipeline(cfg, exporter=exporter)
        out = pipeline.run(
            compressions,
            tag=f"scale{scale}",
            seed_nodes=seed_nodes,
            scale=scale,
        )

        # Visualization
        g = UndirectedCompressionGraph(edge_mode=cfg["edge_mode"])
        g.add_compressions(compressions)
        g.build(seed_nodes=seed_nodes)

        plot_compression_graph(g, out_dir / f"graph_scale{scale}.png")
        plot_edge_count_distribution(g, out_dir / f"edge_dist_scale{scale}.png")
        if out["candidate_migrations"]:
            plot_migration_paths(
                g, out["candidate_migrations"][:10],
                out_dir / f"migrations_scale{scale}.png",
            )

    written = exporter.flush()
    print("\n=== CSV tables ===")
    for name, n, path in written:
        print(f"  {name}.csv  rows={n}  -> {path}")

    df = exporter.summary_df()
    if not df.empty:
        print("\n=== Summary ===")
        print(df.to_string(index=False))


if __name__ == "__main__":
    main()