# -*- coding: utf-8 -*-
"""
End-to-end static pipeline:

    raw compressions -> undirected compression graph
                    -> detect_compression (candidates)
                    -> detect_migration (candidates)
                    -> JSON + CSV tables
"""

import json
from pathlib import Path
from typing import List, Dict, Any, Optional

from cg_core import UndirectedCompressionGraph
from detector import CompressionGraphDetector


class CompressionGraphPipeline:
    def __init__(self, config, exporter=None):
        self.cfg = config
        self.out_dir = Path(config["output_dir"])
        self.out_dir.mkdir(parents=True, exist_ok=True)
        self.exporter = exporter

    def run(self, compressions, tag, seed_nodes=None, scale=None):
        if self.cfg.get("verbose", True):
            print(f"\n=== Pipeline [{tag}] ===")
            print(f"Raw compression events: {len(compressions)}")

        graph = UndirectedCompressionGraph(edge_mode=self.cfg["edge_mode"])
        graph.add_compressions(compressions)
        graph.build(seed_nodes=seed_nodes)
        stats = graph.stats()

        if self.cfg.get("verbose", True):
            print(f"Graph: nodes={stats['nodes']}, edges={stats['edges']}, "
                  f"count_max={stats['count_max']}, "
                  f"count_mean={stats['count_mean']:.2f}")

        detector = CompressionGraphDetector(graph, self.cfg)
        clusters = detector.detect_compression()
        migrations = detector.detect_migration()

        if self.cfg.get("verbose", True):
            print(f"Candidate compressions: {len(clusters)}")
            print(f"Candidate migrations: {len(migrations)}")

        out = {
            "tag": tag,
            "scale": scale,
            "graph_stats": stats,
            "candidate_compressions": clusters,
            "candidate_migrations": migrations,
        }
        out_path = self.out_dir / f"pipeline_{tag}.json"
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(out, f, ensure_ascii=False, indent=2, default=str)

        if self.cfg.get("verbose", True):
            print(f"Saved JSON: {out_path}")

        if self.exporter is not None and scale is not None:
            self.exporter.add_raw_events(scale, compressions)
            self.exporter.add_edges(scale, graph)
            self.exporter.add_candidate_compressions(scale, clusters)
            self.exporter.add_candidate_migrations(scale, migrations)
            self.exporter.add_summary(
                scale, stats,
                n_raw=len(compressions),
                n_comp=len(clusters),
                n_mig=len(migrations),
            )

        return out