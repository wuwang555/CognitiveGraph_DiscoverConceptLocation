# -*- coding: utf-8 -*-
"""
Directed logic derivation from fixpoints.

Once a fixpoint cluster C is identified, directionality emerges
automatically from the stability asymmetry between C and the
surrounding concepts:

    x -> C  iff  P(C ⊆ cluster(x)) > θ

i.e. if x participates in the majority of compression events that
contain C, we draw a directed edge x -> C. Its weight is the
empirical frequency.

No external directionality is imposed. The rule is derived purely
from compression statistics, consistent with the two postulates.
"""

from collections import Counter
from typing import List, Dict, Any, FrozenSet


class LogicDeriver:
    def __init__(self, config: Dict[str, Any]):
        self.cfg = config

    # ------------------------------------------------------------------ #
    def derive(self, fixpoints: List[Dict[str, Any]],
               events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        threshold = float(self.cfg.get("logic_threshold", 0.5))
        output = []

        for fp in fixpoints:
            core = frozenset(fp["core"])

            # All compression events whose transaction contains C
            containing = []
            for e in events:
                center = e.get("center")
                if not center:
                    continue
                members = e.get("related_nodes") or []
                txn = frozenset([center] + [m for m in members if m])
                if core.issubset(txn):
                    containing.append(txn)

            n_containing = len(containing)
            if n_containing == 0:
                continue

            # Frequency of each edge concept x inside containing events
            x_counts: Counter = Counter()
            for ev in containing:
                for x in ev:
                    if x not in core:
                        x_counts[x] += 1

            logic_edges: Dict[str, float] = {}
            for x, cnt in x_counts.items():
                freq = cnt / n_containing
                if freq > threshold:
                    logic_edges[x] = freq

            if not logic_edges:
                continue

            output.append({
                "core": sorted(core),
                "n_containing": n_containing,
                "logic": logic_edges,
                "boundary": sorted(logic_edges.keys()),
            })

        return output