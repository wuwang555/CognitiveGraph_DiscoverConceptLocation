# -*- coding: utf-8 -*-
"""
High-order term internalization.

The second-order observation layer discovers fixpoints; we write their
effect back into the first-order energy formula as a higher-order
correction:

    E_ij^new = E_ij - Σ_C λ_C · δ_C(i, j)

with

    λ_C = (1 / |C|²) · Σ_{i,j ∈ C} c̄_ij
    δ_C(i, j) = 1 iff i, j ∈ C

This is the standard form of an effective action in the
renormalization group: the system modifies its own energy formula by
internalizing its own observed structure. No new assumption is added.
"""

from typing import List, Dict, Any, FrozenSet
import numpy as np


# ---------------------------------------------------------------------- #
def compute_lambdas(fixpoints: List[Dict[str, Any]],
                    events: List[Dict[str, Any]]) -> Dict[FrozenSet[str], float]:
    """Return λ_C for each fixpoint cluster C."""
    lambdas: Dict[FrozenSet[str], float] = {}

    for fp in fixpoints:
        core = frozenset(fp["core"])
        if len(core) < 2:
            lambdas[core] = 0.0
            continue

        # Count pairwise co-occurrences inside events containing C
        pair_counts: Dict[FrozenSet[str], int] = {}
        n_events = 0
        for e in events:
            center = e.get("center")
            if not center:
                continue
            members = e.get("related_nodes") or []
            txn = frozenset([center] + [m for m in members if m])
            if not core.issubset(txn):
                continue
            n_events += 1
            members_sorted = sorted(core)
            for i in range(len(members_sorted)):
                for j in range(i + 1, len(members_sorted)):
                    key = frozenset([members_sorted[i], members_sorted[j]])
                    pair_counts[key] = pair_counts.get(key, 0) + 1

        if n_events == 0 or not pair_counts:
            lambdas[core] = 0.0
            continue

        # Mean normalized co-occurrence c̄_ij
        c_values = [v / n_events for v in pair_counts.values()]
        mean_c = float(np.mean(c_values))
        lambdas[core] = mean_c / (len(core) ** 2)

    return lambdas


# ---------------------------------------------------------------------- #
def apply_high_order_correction(graph,
                                fixpoints: List[Dict[str, Any]],
                                events: List[Dict[str, Any]]) -> None:
    """
    Subtract λ_C from each internal edge of every fixpoint cluster.

    The new value is stored under ``weight_high_order``; the original
    ``weight`` attribute is left intact.
    """
    lambdas = compute_lambdas(fixpoints, events)
    G = graph.G

    corrections: Dict[tuple, float] = {}
    for core, lam in lambdas.items():
        if lam == 0.0:
            continue
        members = sorted(core)
        for i in range(len(members)):
            for j in range(i + 1, len(members)):
                u, v = members[i], members[j]
                if not G.has_edge(u, v):
                    continue
                key = tuple(sorted((u, v)))
                corrections[key] = corrections.get(key, 0.0) + lam

    for (u, v), lam in corrections.items():
        d = G[u][v]
        base = d.get("weight", d.get("count", 0.0))
        d["weight_high_order"] = float(base) - lam