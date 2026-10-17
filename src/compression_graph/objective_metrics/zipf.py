# -*- coding: utf-8 -*-
"""
Zipf / power-law fit for:
  - edge co-occurrence counts in the compression graph
  - center-node frequencies in raw compression events

Mirrors the original paper's Zipf analysis (center-frequency Zipf).
"""

import numpy as np
from scipy import stats
from collections import Counter
from typing import List, Dict, Any, Optional


def zipf_fit(values: List[float]) -> Optional[Dict[str, float]]:
    """
    Fit f(r) = C * r^{-alpha} in log-log space.

    values: raw counts (unsorted).
    Returns slope (-alpha), R2, p_value, n, total.
    """
    if len(values) < 3:
        return None
    sorted_vals = sorted(values, reverse=True)
    ranks = np.arange(1, len(sorted_vals) + 1)
    log_ranks = np.log(ranks)
    log_vals = np.log(sorted_vals)
    slope, intercept, r_value, p_value, std_err = stats.linregress(
        log_ranks, log_vals
    )
    return {
        "slope": float(slope),
        "intercept": float(intercept),
        "r2": float(r_value ** 2),
        "p_value": float(p_value),
        "n": int(len(sorted_vals)),
        "total": int(sum(sorted_vals)),
    }


def edge_zipf(graph) -> Optional[Dict[str, float]]:
    """Zipf of edge co-occurrence counts in the compression graph."""
    counts = [d["count"] for _, _, d in graph.G.edges(data=True)]
    return zipf_fit(counts)


def center_zipf(compression_events: List[Dict[str, Any]]) -> Optional[Dict[str, float]]:
    """Zipf of center-node frequencies in raw compression events."""
    centers = [e.get("center") for e in compression_events if e.get("center")]
    if not centers:
        return None
    counter = Counter(centers)
    return zipf_fit(list(counter.values()))


def node_total_zipf(compression_events: List[Dict[str, Any]]) -> Optional[Dict[str, float]]:
    """Zipf of total node frequencies in compression events (center + members)."""
    counter = Counter()
    for e in compression_events:
        center = e.get("center")
        related = e.get("related_nodes", []) or []
        nodes = set([center] + related) if center else set(related)
        for n in nodes:
            if n:
                counter[n] += 1
    if not counter:
        return None
    return zipf_fit(list(counter.values()))