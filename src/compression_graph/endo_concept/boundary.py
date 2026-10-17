# -*- coding: utf-8 -*-
"""
Boundary characterization.

In the one-order cognitive graph, boundaries are the fuzzy-relation
regions around fixpoint clusters. The width of a boundary is measured
by the compression potential:

    Φ(C) = mean(internal co-occurrence) / mean(external co-occurrence)

Φ small  ->  tight cluster, sharp boundary
Φ large  ->  loose cluster, blurred boundary
"""

from typing import List, Dict, Optional
import numpy as np


def compute_phi(graph, cluster: List[str]) -> Optional[float]:
    """Φ of an arbitrary cluster on the compression graph."""
    G = graph.G
    S = set(cluster)
    internal: List[float] = []
    external: List[float] = []
    seen = set()

    for u in S:
        if u not in G:
            continue
        for v in G.neighbors(u):
            key = tuple(sorted((u, v)))
            if key in seen:
                continue
            seen.add(key)
            c = float(G[u][v].get("count", 0))
            if v in S:
                internal.append(c)
            else:
                external.append(c)

    if not internal or not external:
        return None
    avg_in = sum(internal) / len(internal)
    avg_ex = sum(external) / len(external)
    if avg_ex == 0.0:
        return None
    return avg_in / avg_ex


def boundary_summary(phis: List[float]) -> Dict[str, float]:
    """Descriptive statistics over a set of Φ values."""
    if not phis:
        return {}
    arr = np.asarray(phis, dtype=float)
    return {
        "count": int(len(arr)),
        "mean": float(arr.mean()),
        "std": float(arr.std()),
        "min": float(arr.min()),
        "max": float(arr.max()),
        "median": float(np.median(arr)),
        "q25": float(np.percentile(arr, 25)),
        "q75": float(np.percentile(arr, 75)),
    }