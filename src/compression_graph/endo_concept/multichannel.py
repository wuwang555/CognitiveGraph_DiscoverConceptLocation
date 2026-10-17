# -*- coding: utf-8 -*-
"""
Multi-channel initialization of edge weights.

Original formula (single channel, sim only):
    E_ij = α (1 - sim_ij) + β / (1 + H_ij) + γ · div_ij

Extended multi-channel formula:
    E_ij^(0) = w1 · (1 - sim_ij)
             + w2 · (1 - logic_ij)
             + w3 · energy_ij

Defaults: w1 = 0.4, w2 = 0.4, w3 = 0.2.

    sim_ij    : semantic similarity
    logic_ij  : directed logic strength (from CONCEPT_STRUCTURE)
    energy_ij : energy gradient (from CONCEPT_STRUCTURE)
"""

import math
from typing import Dict, Any, Optional, Callable, Tuple


# ---------------------------------------------------------------------- #
def _lookup_logic(structure: Dict[str, Any], ci: str, cj: str) -> float:
    """Logic strength of ci -> cj (or cj -> ci if the reverse exists)."""
    if ci in structure:
        v = structure[ci].get("logic", {}).get(cj)
        if v is not None:
            return float(v)
    if cj in structure:
        v = structure[cj].get("logic", {}).get(ci)
        if v is not None:
            return float(v)
    return 0.0


def _lookup_energy(structure: Dict[str, Any], ci: str, cj: str) -> float:
    """Energy gradient between ci and cj, whichever direction is stored."""
    if ci in structure:
        v = structure[ci].get("energy", {}).get(cj)
        if v is not None:
            return float(v)
    if cj in structure:
        v = structure[cj].get("energy", {}).get(ci)
        if v is not None:
            return float(v)
    return 0.0


# ---------------------------------------------------------------------- #
def compute_initial_energy(concept_i: str,
                           concept_j: str,
                           structures: Dict[str, Any],
                           semantic_similarity: Optional[float] = None,
                           weights: Tuple[float, float, float] = (0.4, 0.4, 0.2)) -> float:
    """
    Multi-channel initial edge weight.

    :param semantic_similarity: optional externally supplied similarity
                                (e.g. from SemanticConceptNetwork).
                                If None, the sim channel contributes 0.
    """
    w1, w2, w3 = weights

    sim = float(semantic_similarity) if semantic_similarity is not None else 0.0
    sim = max(0.0, min(1.0, sim))

    logic = _lookup_logic(structures, concept_i, concept_j)
    logic = max(0.0, min(1.0, logic))

    energy = _lookup_energy(structures, concept_i, concept_j)
    # Soft saturation: energy is a raw co-occurrence count (0 .. ~500+).
    energy_norm = energy / (1.0 + energy) if energy > 0 else 0.0

    return (w1 * (1.0 - sim)
            + w2 * (1.0 - logic)
            + w3 * energy_norm)


# ---------------------------------------------------------------------- #
def rebuild_edges_with_multichannel(graph,
                                    structures: Dict[str, Any],
                                    semantic_similarity_fn: Optional[Callable[[str, str], float]] = None,
                                    weights: Tuple[float, float, float] = (0.4, 0.4, 0.2)) -> None:
    """
    Recompute all edge weights in `graph` using the multi-channel formula.

    The original co-occurrence count is preserved in the attribute
    ``weight_old``; the new value is written into ``weight``.
    """
    G = graph.G
    for u, v, d in G.edges(data=True):
        sim = 0.0
        if semantic_similarity_fn is not None:
            try:
                sim = float(semantic_similarity_fn(u, v))
            except Exception:
                sim = 0.0
        d["weight_old"] = d.get("weight_old", d.get("count", 0))
        d["weight"] = compute_initial_energy(u, v, structures, sim, weights)