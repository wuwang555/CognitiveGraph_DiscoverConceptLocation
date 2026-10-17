# -*- coding: utf-8 -*-
"""
Undirected compression co-occurrence graph.

Nodes   : concepts
Edges   : "these two concepts were compressed together at least once"
Weights : co-occurrence count (raw count, no mapping)
"""

from collections import defaultdict
from typing import List, Dict, Any, Optional

import networkx as nx
import numpy as np


class UndirectedCompressionGraph:
    def __init__(self, edge_mode: str = "clique"):
        if edge_mode not in ("clique", "star"):
            raise ValueError(f"Unknown edge_mode: {edge_mode}")
        self.edge_mode = edge_mode
        self.G = nx.Graph()
        self.raw_counts = defaultdict(int)
        self.n_events = 0

    # ------------------------------------------------------------------ #
    # Building
    # ------------------------------------------------------------------ #
    def add_compression(self, center: str, related: List[str]) -> None:
        if not center:
            return
        related = [r for r in (related or []) if r and r != center]
        if not related:
            return

        self.n_events += 1
        nodes = [center] + related
        nodes = list(dict.fromkeys(nodes))

        if self.edge_mode == "clique":
            for i in range(len(nodes)):
                for j in range(i + 1, len(nodes)):
                    key = tuple(sorted([nodes[i], nodes[j]]))
                    self.raw_counts[key] += 1
        else:  # 'star'
            for m in related:
                key = tuple(sorted([center, m]))
                self.raw_counts[key] += 1

    def add_compressions(self, compressions: List[Dict[str, Any]]) -> None:
        for comp in compressions:
            self.add_compression(
                comp.get("center"),
                comp.get("related_nodes", []) or [],
            )

    def build(self, seed_nodes: Optional[List[str]] = None) -> nx.Graph:
        self.G.clear()
        if seed_nodes:
            self.G.add_nodes_from(seed_nodes)
        for (u, v), c in self.raw_counts.items():
            self.G.add_edge(u, v, weight=int(c), count=int(c))
        return self.G

    # ------------------------------------------------------------------ #
    # Stats
    # ------------------------------------------------------------------ #
    def stats(self) -> Dict[str, Any]:
        n_nodes = self.G.number_of_nodes()
        n_edges = self.G.number_of_edges()
        if n_edges == 0:
            return {
                "nodes": n_nodes, "edges": 0, "n_events": self.n_events,
                "count_min": 0, "count_max": 0,
                "count_mean": 0.0, "count_median": 0.0,
            }
        counts = np.array([d["count"] for _, _, d in self.G.edges(data=True)])
        return {
            "nodes": n_nodes,
            "edges": n_edges,
            "n_events": self.n_events,
            "count_min": int(counts.min()),
            "count_max": int(counts.max()),
            "count_mean": float(counts.mean()),
            "count_median": float(np.median(counts)),
        }