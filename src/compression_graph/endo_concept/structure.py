# -*- coding: utf-8 -*-
"""
Generation of the structured definition form  CONCEPT_STRUCTURE.

A "description" in this framework is NOT an action of the system --
it is a property of the definition form itself. Once definitions are
structures, the description exists automatically.

Structure fields:
    core     : fixpoint cluster members
    boundary : concepts that point into the core
    logic    : edge weight (frequency) from boundary to core
    energy   : energy gradient (average co-occurrence count)
    sources  : IDs of the compression events supporting this structure
"""

from typing import List, Dict, Any, FrozenSet


def _name_for(core: List[str]) -> str:
    """Human-readable name for a fixpoint cluster."""
    if len(core) == 1:
        return core[0]
    return "·".join(core)


def build_concept_structure(fixpoints: List[Dict[str, Any]],
                            logic_result: List[Dict[str, Any]],
                            events: List[Dict[str, Any]],
                            graph=None) -> Dict[str, Dict[str, Any]]:
    """
    fixpoints    : list of {core, support, count, stability, method}
    logic_result : list of {core, boundary, logic, n_containing}
    events       : raw compression events
    graph        : optional UndirectedCompressionGraph, for energy gradient
    """
    # Index logic by frozen core
    logic_by_core: Dict[FrozenSet[str], Dict[str, Any]] = {}
    for rec in logic_result:
        logic_by_core[frozenset(rec["core"])] = rec

    structure: Dict[str, Dict[str, Any]] = {}

    for fp in fixpoints:
        core = sorted(fp["core"])
        core_set = frozenset(core)

        logic_rec = logic_by_core.get(core_set, {})
        boundary = list(logic_rec.get("boundary", []))
        logic = dict(logic_rec.get("logic", {}))

        # ---- sources: event IDs containing the core ----
        sources: List[int] = []
        for idx, e in enumerate(events):
            center = e.get("center")
            if not center:
                continue
            members = e.get("related_nodes") or []
            txn = frozenset([center] + [m for m in members if m])
            if core_set.issubset(txn):
                eid = e.get("event_id", idx)
                try:
                    sources.append(int(eid))
                except Exception:
                    sources.append(idx)

        # ---- energy gradient: mean co-occurrence between core and boundary ----
        energy: Dict[str, float] = {}
        for b in boundary:
            counts = []
            if graph is not None:
                for c in core:
                    if b in graph.G and c in graph.G and graph.G.has_edge(b, c):
                        counts.append(float(graph.G[b][c].get("count", 0)))
            energy[b] = float(sum(counts) / len(counts)) if counts else 0.0

        # ---- unique name ----
        name = _name_for(core)
        base = name
        i = 2
        while name in structure:
            name = f"{base}#{i}"
            i += 1

        structure[name] = {
            "core": core,
            "boundary": boundary,
            "logic": {k: round(float(v), 6) for k, v in logic.items()},
            "energy": {k: round(float(v), 6) for k, v in energy.items()},
            "sources": sources,
        }

    return structure