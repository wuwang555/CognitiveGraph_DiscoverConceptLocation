# -*- coding: utf-8 -*-
"""
Fixpoint detection for compression events.

Three independent methods, each with its own search space and filter:

    A: powerset + support      (all frequent itemsets)
    B: powerset + lower-bound  (minimal frequent itemsets)
    C: powerset + stability    (role-consistent itemsets)

All three share the same powerset enumeration routine. Independence
comes from two places:

    1. Each method has its own parameter set -- no leakage between methods.
    2. Each method applies its own filter after enumeration.

Guards against combinatorial explosion:
    - `max_candidates`: stops enumeration once the number of distinct
      itemsets exceeds the cap (per call).
    - `max_fixpoints`:   caps the returned list per method (sorted top-N).

Role consistency (replaces the unstable positional formula):

    role(x) = max(n_center, n_member) / (n_center + n_member)   in [0.5, 1.0]

The original S(x) = 1 - std(rank)/mean(rank) collapses to 0 when
mean(rank) is small, which killed whole clusters. The new metric is
bounded, symmetric, and directly interpretable.
"""

import math
from collections import Counter
from itertools import combinations
from typing import List, Dict, Any, FrozenSet, Tuple

import numpy as np


# ====================================================================== #
# Helpers
# ====================================================================== #
def events_to_transactions(events: List[Dict[str, Any]]) -> List[FrozenSet[str]]:
    """Convert compression events into transaction sets.

    A compression event (center, members) yields the transaction
    {center} ∪ members. Empty transactions are dropped.
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


def stability_scores(events: List[Dict[str, Any]]) -> Dict[str, float]:
    """Role consistency in [0.5, 1.0].

        role(x) = max(n_center(x), n_member(x)) / (n_center(x) + n_member(x))

    - always the center -> 1.0
    - always a member   -> 1.0
    - 50/50 mix         -> 0.5
    - bounded, symmetric, no numerical blow-up
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

        if self.cfg.get("use_joint_criteria", False):
            raw = self._apply_joint(raw, events)

        raw.sort(key=lambda r: (r["support"], len(r["core"])), reverse=True)
        return raw

    # ================================================================== #
    # Shared powerset enumeration (used by A, B, C)
    # ================================================================== #
    def _enumerate_powerset(self,
                            events: List[Dict[str, Any]],
                            min_size: int,
                            max_size: int,
                            max_candidates: int) -> Tuple[Counter, int]:
        """Enumerate all itemsets (subsets of transactions) up to max_size.

        Returns (counter, N) where counter maps frozenset -> raw count,
        and N is the number of transactions.

        Stops early when len(counter) exceeds max_candidates. The partial
        result is returned; the caller is responsible for treating the
        cap as a semantic cutoff (not silently truncating).
        """
        transactions = events_to_transactions(events)
        N = len(transactions)
        if N == 0:
            return Counter(), 0

        counter: Counter = Counter()
        lower = max(1, int(min_size))
        upper = max(lower, int(max_size))

        for t in transactions:
            items = list(t)
            n = len(items)
            top = min(upper, n)
            for size in range(lower, top + 1):
                for combo in combinations(items, size):
                    counter[frozenset(combo)] += 1
            if len(counter) > max_candidates:
                break

        return counter, N

    # ================================================================== #
    # Method A: powerset + support
    # ================================================================== #
    def _method_A(self, events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        min_size = int(self.cfg.get("fp_min_itemset_size", 1))
        max_size = int(self.cfg.get("fp_max_itemset_size", 8))
        min_support = float(self.cfg.get("fp_min_support", 0.02))
        max_cand = int(self.cfg.get("max_candidates", 200000))
        max_fp = int(self.cfg.get("max_fixpoints", 1000))

        counter, N = self._enumerate_powerset(events, min_size, max_size, max_cand)
        if N == 0:
            return []

        min_count = max(1, int(math.ceil(min_support * N)))
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

        out.sort(key=lambda r: (r["support"], len(r["core"])), reverse=True)
        return out[:max_fp]

    # ================================================================== #
    # Method B: powerset + lower-bound
    # ================================================================== #
    def _method_B(self, events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        min_size = int(self.cfg.get("lattice_min_set_size", 1))
        max_size = int(self.cfg.get("lattice_max_itemset_size", 8))
        min_support = float(self.cfg.get("lattice_min_support", 0.02))
        max_cand = int(self.cfg.get("max_candidates", 200000))
        max_fp = int(self.cfg.get("max_fixpoints", 1000))

        counter, N = self._enumerate_powerset(events, min_size, max_size, max_cand)
        if N == 0:
            return []

        min_count = max(1, int(math.ceil(min_support * N)))
        stab = stability_scores(events)

        # Step 1: frequent sets under support threshold
        frequent = {s: cnt for s, cnt in counter.items() if cnt >= min_count}
        frequent_set = set(frequent.keys())

        # Step 2: keep only lower-bound elements
        out: List[Dict[str, Any]] = []
        for s, cnt in frequent.items():
            if not self._is_lower_bound(s, frequent_set):
                continue
            members = sorted(s)
            mean_stab = float(np.mean([stab.get(m, 0.5) for m in members]))
            out.append({
                "core": members,
                "support": cnt / N,
                "count": cnt,
                "stability": mean_stab,
                "method": "B",
            })

        out.sort(key=lambda r: (r["support"], len(r["core"])), reverse=True)
        return out[:max_fp]

    @staticmethod
    def _is_lower_bound(s: FrozenSet[str],
                        frequent_set: set) -> bool:
        """True iff every proper subset of s of size |s|-1 is NOT frequent."""
        if len(s) <= 1:
            return True
        for sub in combinations(s, len(s) - 1):
            if frozenset(sub) in frequent_set:
                return False
        return True

    # ================================================================== #
    # Method C: powerset + stability
    # ================================================================== #
    def _method_C(self, events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        min_size = int(self.cfg.get("role_min_set_size", 1))
        max_size = int(self.cfg.get("role_max_itemset_size", 8))
        min_stability = float(self.cfg.get("role_min_stability", 0.7))
        min_support = float(self.cfg.get("role_min_support", 0.005))
        max_cand = int(self.cfg.get("max_candidates", 200000))
        max_fp = int(self.cfg.get("max_fixpoints", 1000))

        counter, N = self._enumerate_powerset(events, min_size, max_size, max_cand)
        if N == 0:
            return []

        min_count = max(1, int(math.ceil(min_support * N)))
        stab = stability_scores(events)

        out: List[Dict[str, Any]] = []
        for itemset, cnt in counter.items():
            if cnt < min_count:
                continue
            members = sorted(itemset)
            mean_stab = float(np.mean([stab.get(m, 0.5) for m in members]))
            if mean_stab < min_stability:
                continue
            out.append({
                "core": members,
                "support": cnt / N,
                "count": cnt,
                "stability": mean_stab,
                "method": "C",
            })

        out.sort(key=lambda r: (r["stability"], r["support"]), reverse=True)
        return out[:max_fp]

    # ================================================================== #
    # ABC union
    # ================================================================== #
    @staticmethod
    def _merge(*lists) -> List[Dict[str, Any]]:
        merged: Dict[FrozenSet[str], Dict[str, Any]] = {}
        for lst in lists:
            for c in lst:
                key = frozenset(c["core"])
                if key not in merged or merged[key]["support"] < c["support"]:
                    merged[key] = dict(c)
        max_fp = 1000  # will be re-truncated by detect()
        items = sorted(merged.values(),
                       key=lambda r: (r["support"], len(r["core"])),
                       reverse=True)
        return items[:max_fp]

    # ================================================================== #
    # Optional joint post-filter (default OFF)
    # ================================================================== #
    def _apply_joint(self,
                     candidates: List[Dict[str, Any]],
                     events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Optional post-filter: support + stability + lower-bound.

        Only runs when `use_joint_criteria` is True. Since each method
        already has its own filter, this should normally stay off.
        """
        if not candidates:
            return []

        min_support = float(self.cfg.get("joint_support_min", 0.02))
        min_stability = float(self.cfg.get("joint_stability_min", 0.6))
        use_stab_hard = bool(self.cfg.get("use_stability_hard_threshold", False))
        use_lower_bound = bool(self.cfg.get("use_lower_bound_filter", True))
        max_fp = int(self.cfg.get("max_fixpoints", 1000))

        if use_stab_hard:
            passing = [c for c in candidates
                       if c["support"] >= min_support
                       and c["stability"] >= min_stability]
        else:
            passing = [c for c in candidates if c["support"] >= min_support]

        if not use_lower_bound:
            passing.sort(key=lambda c: (c["support"], c["stability"]),
                         reverse=True)
            return passing[:max_fp]

        passing_set = set(frozenset(c["core"]) for c in passing)
        out: List[Dict[str, Any]] = []
        for c in passing:
            s = frozenset(c["core"])
            if self._is_lower_bound(s, passing_set):
                out.append(c)

        out.sort(key=lambda c: (c["support"], c["stability"]), reverse=True)
        return out[:max_fp]