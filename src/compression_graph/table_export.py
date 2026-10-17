# -*- coding: utf-8 -*-
"""
Aggregate results into CSV tables.

Tables:
  - summary.csv
  - raw_compression_events.csv
  - compression_edges.csv
  - candidate_compressions.csv
  - candidate_migrations.csv
"""

from pathlib import Path
from typing import List, Dict, Any

import pandas as pd


class TableExporter:
    def __init__(self, output_dir):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self._rows = {
            "summary": [],
            "raw_compression_events": [],
            "compression_edges": [],
            "candidate_compressions": [],
            "candidate_migrations": [],
        }

    # ------------------------------------------------------------------ #
    def add_summary(self, scale, stats, n_raw, n_comp, n_mig):
        self._rows["summary"].append({
            "scale": scale,
            "n_raw_compression_events": n_raw,
            "n_graph_nodes": stats["nodes"],
            "n_graph_edges": stats["edges"],
            "edge_count_max": stats["count_max"],
            "edge_count_mean": round(stats["count_mean"], 4),
            "n_candidate_compressions": n_comp,
            "n_candidate_migrations": n_mig,
        })

    def add_raw_events(self, scale, compressions):
        for i, c in enumerate(compressions):
            related = c.get("related_nodes", []) or []
            self._rows["raw_compression_events"].append({
                "scale": scale,
                "event_id": i,
                "detection_iteration": c.get("detection_iteration", -1),
                "center": c.get("center", ""),
                "cluster_size": len(related),
                "related_nodes": "|".join(related),
                "emergence_strength": c.get("emergence_strength", None),
            })

    def add_edges(self, scale, graph):
        for u, v, d in graph.G.edges(data=True):
            self._rows["compression_edges"].append({
                "scale": scale,
                "concept_a": u,
                "concept_b": v,
                "count": int(d["count"]),
            })

    def add_candidate_compressions(self, scale, clusters):
        for rank, c in enumerate(clusters, 1):
            self._rows["candidate_compressions"].append({
                "scale": scale,
                "rank": rank,
                "center": c["center"],
                "cluster": "|".join(c["cluster"]),
                "size": c["size"],
                "phi": round(c["phi"], 6),
            })

    def add_candidate_migrations(self, scale, migrations):
        for rank, m in enumerate(migrations, 1):
            self._rows["candidate_migrations"].append({
                "scale": scale,
                "rank": rank,
                "length": m["length"],
                "start": m["start"],
                "end": m["end"],
                "path": " -> ".join(m["path"]),
                "score": round(m["score"], 4),
            })

    # ------------------------------------------------------------------ #
    def flush(self):
        written = []
        for name, rows in self._rows.items():
            if not rows:
                continue
            df = pd.DataFrame(rows)
            path = self.output_dir / f"{name}.csv"
            df.to_csv(path, index=False, encoding="utf-8-sig")
            written.append((name, len(rows), str(path)))
        return written

    def summary_df(self):
        if not self._rows["summary"]:
            return pd.DataFrame()
        return pd.DataFrame(self._rows["summary"])