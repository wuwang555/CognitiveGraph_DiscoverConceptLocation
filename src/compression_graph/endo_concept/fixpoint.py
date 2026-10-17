# -*- coding: utf-8 -*-
"""
Fixpoint detection for compression events.

A "fixpoint" is a stable cluster of concepts -- a set that co-occurs
in compression events more often than chance, cannot be decomposed
into smaller stable units, and whose members maintain a consistent
role across events.

Detection methods (switchable via config["fixpoint_method"]):

    "A"   - frequent itemset mining (Apriori-style enumeration)
    "B"   - containment lattice (lower-bound elements)
    "C"   - role-consistency analysis
    "ABC" - union of the above

Joint criteria (see the task report, §5.3):
    1. support > θ_s
    2. lower-bound in the containment lattice (optional)
    3. mean role-consistency > θ_role

Role consistency replaces the original positional stability
S(x) = 1 - std(rank) / mean(rank). The original formula is
numerically unstable when mean(rank) → 0 (any concept that is
occasionally a member gets an S near 0, killing its whole cluster).
The new formula is bounded in [0.5, 1.0] and symmetric:

    role(x) = max(n_center(x), n_member(x)) / (n_center(x) + n_member(x))

All thresholds are absolute so scales remain comparable.
"""

import math
from collections import Counter, defaultdict
from itertools import combinations
from typing import List, Dict, Any, FrozenSet

import numpy as np


# ====================================================================== #
# Helpers
# ====================================================================== #
def events_to_transactions(events: List[Dict[str, Any]]) -> List[FrozenSet[str]]:
    """Convert compression events into transaction sets.

    A compression event (center, members) yields the transaction
    {center} ∪ members. Empty transactions are dropped. Single-node
    transactions are KEPT so that fp_min_itemset_size = 1 can see them.
    """
    transactions: List[FrozenSet[str]] = []
    for e in events:
        center = e.get("center")
        if not center:
            continue
        members = e.get("related_nodes") or []
        txn = frozenset([center] + [m for m in members if m and m != center])
        if len(txn) >= 1:
            transactions.append(txn)
    return transactions


def position_ranks(events: List[Dict[str, Any]]) -> Dict[str, List[int]]:
    """Positional rank of each concept across events (kept for reference).

    Rank per event:
        0 - concept is the center
        1 - concept is a member
    Concepts absent from an event are simply not recorded.
    """
    ranks: Dict[str, List[int]] = defaultdict(list)
    for e in events:
        center = e.get("center")
        members = e.get("related_nodes") or []
        if center:
            ranks[center].append(0)
        for m in members:
            if m and m != center:
                ranks[m].append(1)
    return dict(ranks)


def stability_scores(events: List[Dict[str, Any]]) -> Dict[str, float]:
    """Role consistency in [0.5, 1.0].

        role(x) = max(n_center(x), n_member(x)) / (n_center(x) + n_member(x))

    Properties:
        - always the center       -> 1.0
        - always a member         -> 1.0
        - 50/50 mix               -> 0.5
        - symmetric, bounded, no numerical blow-up
        - concepts with zero participations never appear

    This replaces the original S(x) = 1 - std(rank)/mean(rank), which
    collapses to 0 when mean(rank) is small.
    """
    n_center: Counter = Counter()
    n_member: Counter = Counter()

    for e in events:
        center = e.get("center")
        members = e.get("related_nodes") or []
        if center:
            n_center[center] += 1
        for m in members:
            if m and m != center:
                n_member[m] += 1

    scores: Dict[str, float] = {}
    for concept in set(n_center) | set(n_member):
        c = n_center.get(concept, 0)
        m = n_member.get(concept, 0)
        total = c + m
        if total <= 0:
            continue
        scores[concept] = max(c, m) / total
    return scores


# ====================================================================== #
# Detector
# ====================================================================== #
class FixpointDetector:
    """Detect fixpoint clusters with a switchable method (A/B/C/ABC)."""

    def __init__(self, config: Dict[str, Any]):
        self.cfg = config

    # ------------------------------------------------------------------ #
    def detect(self, events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        method = str(self.cfg.get("fixpoint_method", "A")).upper()

        if method == "A":
            raw = self._method_A(events)
        elif method == "B":
            raw = self._method_B(events)
        elif method == "C":
            raw = self._method_C(events)
        elif method in ("ABC", "ALL", "A+B+C"):
            raw = self._merge(
                self._method_A(events),
                self._method_B(events),
                self._method_C(events),
            )
        else:
            raise ValueError(
                f"Unknown fixpoint_method: {method!r}. "
                f"Choose from 'A', 'B', 'C', 'ABC'."
            )

        if self.cfg.get("use_joint_criteria", True):
            raw = self._apply_joint(raw, events)

        raw.sort(key=lambda r: (r["support"], len(r["core"])), reverse=True)
        return raw

    # ================================================================== #
    # Method A: frequent itemset mining
    # ================================================================== #
    def _method_A(self, events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        transactions = events_to_transactions(events)
        N = len(transactions)
        if N == 0:
            return []

        min_support = float(self.cfg.get("fp_min_support", 0.02))
        max_size = int(self.cfg.get("fp_max_itemset_size", 8))
        min_size = int(self.cfg.get("fp_min_itemset_size", 3))
        min_count = max(1, int(math.ceil(min_support * N)))

        counter: Counter = Counter()
        for t in transactions:
            items = list(t)
            n = len(items)
            top = min(max_size, n)
            lower = max(1, min_size)
            for size in range(lower, top + 1):
                for combo in combinations(items, size):
                    counter[frozenset(combo)] += 1

        stab = stability_scores(events)
        out: List[Dict[str, Any]] = []
        for itemset, cnt in counter.items():
            if cnt < min_count:
                continue
            members = sorted(itemset)
            mean_stab = float(np.mean([stab.get(m, 0.5) for m in members]))
            out.append({
                "core": members,
                "support": cnt / N,
                "count": cnt,
                "stability": mean_stab,
                "method": "A",
            })
        return out

    # ================================================================== #
    # Method B: containment lattice
    # ================================================================== #
    def _method_B(self, events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        transactions = events_to_transactions(events)
        N = len(transactions)
        if N == 0:
            return []

        min_size = int(self.cfg.get(
            "fp_min_itemset_size",
            self.cfg.get("lattice_min_set_size", 3),
        ))
        min_support = float(self.cfg.get("joint_support_min", 0.02))
        min_count = max(1, int(math.ceil(min_support * N)))

        distinct = list(set(transactions))

        frequent_sets: List = []
        for s in distinct:
            if len(s) < min_size:
                continue
            cnt = sum(1 for t in transactions if s.issubset(t))
            if cnt < min_count:
                continue
            frequent_sets.append((s, cnt))

        set_list = [s for s, _ in frequent_sets]
        stab = stability_scores(events)

        lower_bounds: List[Dict[str, Any]] = []
        for s, cnt in frequent_sets:
            is_lower = True
            for s2 in set_list:
                if s2 == s:
                    continue
                if s2.issubset(s):
                    is_lower = False
                    break
            if not is_lower:
                continue
            members = sorted(s)
            mean_stab = float(np.mean([stab.get(m, 0.5) for m in members]))
            lower_bounds.append({
                "core": members,
                "support": cnt / N,
                "count": cnt,
                "stability": mean_stab,
                "method": "B",
            })
        return lower_bounds

    # ================================================================== #
    # Method C: role-consistency analysis
    # ================================================================== #
    def _method_C(self, events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        stab = stability_scores(events)
        stability_min = float(self.cfg.get("stability_min", 0.6))
        min_size = int(self.cfg.get(
            "fp_min_itemset_size",
            self.cfg.get("lattice_min_set_size", 3),
        ))

        bucket: Dict[FrozenSet[str], Dict[str, Any]] = {}
        for e in events:
            center = e.get("center")
            if not center:
                continue
            members = e.get("related_nodes") or []
            s = frozenset([center] + [m for m in members if m and m != center])
            if len(s) < min_size:
                continue
            mean_stab = float(np.mean([stab.get(m, 0.5) for m in s]))
            if mean_stab < stability_min:
                continue
            if s not in bucket:
                bucket[s] = {
                    "core": sorted(s),
                    "support": 0.0,
                    "count": 0,
                    "stability": mean_stab,
                    "method": "C",
                }
            bucket[s]["count"] += 1

        N = max(1, len(events))
        out: List[Dict[str, Any]] = []
        for rec in bucket.values():
            rec["support"] = rec["count"] / N
            out.append(rec)
        return out

    # ================================================================== #
    # Merge helper
    # ================================================================== #
    @staticmethod
    def _merge(*lists) -> List[Dict[str, Any]]:
        merged: Dict[FrozenSet[str], Dict[str, Any]] = {}
        for lst in lists:
            for c in lst:
                key = frozenset(c["core"])
                if key not in merged or merged[key]["support"] < c["support"]:
                    merged[key] = dict(c)
        return list(merged.values())

    # ================================================================== #
    # Joint criteria
    # ------------------------------------------------------------------ #
    # Stage 1: enrich with support + stability
    # Stage 2: support hard threshold; stability either hard or soft
    # Stage 3: lower-bound filter (optional, defines "minimal fixpoint")
    # ================================================================== #
    def _apply_joint(self,
                     candidates: List[Dict[str, Any]],
                     events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        if not candidates:
            return []

        transactions = events_to_transactions(events)
        N = max(1, len(transactions))
        min_support = float(self.cfg.get("joint_support_min", 0.02))
        min_stability = float(self.cfg.get("joint_stability_min", 0.6))
        use_stab_hard = bool(self.cfg.get("use_stability_hard_threshold", False))
        use_lower_bound = bool(self.cfg.get("use_lower_bound_filter", True))

        stab = stability_scores(events)

        # ---- Stage 1: enrich ----
        enriched: List[Dict[str, Any]] = []
        for c in candidates:
            s = frozenset(c["core"])
            cnt = sum(1 for t in transactions if s.issubset(t))
            support = cnt / N
            mean_stab = float(np.mean([stab.get(m, 0.5) for m in s]))
            enriched.append({
                "core": list(s),
                "support": support,
                "count": cnt,
                "stability": mean_stab,
                "method": c.get("method", "?"),
            })

        # ---- Stage 2: support (hard) + stability (hard or soft) ----
        if use_stab_hard:
            passing = [c for c in enriched
                       if c["support"] >= min_support
                       and c["stability"] >= min_stability]
        else:
            passing = [c for c in enriched if c["support"] >= min_support]

        # ---- Stage 3: lower-bound filter (optional) ----
        if not use_lower_bound:
            passing.sort(key=lambda c: (c["support"], c["stability"]),
                         reverse=True)
            return passing

        out: List[Dict[str, Any]] = []
        for c in passing:
            s = frozenset(c["core"])
            is_lower = True
            for other in passing:
                if other is c:
                    continue
                os_ = frozenset(other["core"])
                if os_ != s and os_.issubset(s):
                    is_lower = False
                    break
            if is_lower:
                out.append(c)
        return out