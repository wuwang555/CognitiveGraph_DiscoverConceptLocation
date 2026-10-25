# -*- coding: utf-8 -*-
"""
Configuration for the endo-concept generation module.

All thresholds are absolute so scales remain comparable. The fixpoint
detection method is switchable via `fixpoint_method`:

    "A"  - frequent itemset mining (Apriori-style enumeration)
    "B"  - containment lattice (lower-bound elements)
    "C"  - role-consistency analysis
    "ABC"/"ALL" - union of A, B, C

`run_endo.py` iterates over `fixpoint_methods` and `min_itemset_sizes`
to produce a full grid of results.
"""

ENDO_CONCEPT_CONFIG = {
    # ---------- Fixpoint detection method selection ----------
    # Default single value (kept for backward compatibility);
    # run_endo.py will loop over `fixpoint_methods` and override this.
    "fixpoint_method": "B",        # "A" | "B" | "C" | "ABC"

    # ---------- Methods to iterate over in run_endo.py ----------
    "fixpoint_methods": ["A", "B", "C"],

    # ---------- fp_min_itemset_size values to iterate over ----------
    "min_itemset_sizes": [1, 2, 3],

    # ---------- Method A: frequent itemset mining ----------
    "fp_min_support": 0.02,
    "fp_max_itemset_size": 8,
    "fp_min_itemset_size": 1,      # default; overridden by min_itemset_sizes

    # ---------- Method B: containment lattice ----------
    "lattice_min_support": 0.02,
    "lattice_min_set_size": 1,
    "lattice_max_itemset_size": 8,

    # ---------- Method C: role-consistency ----------
    "role_min_stability": 0.7,     # role consistency in [0.5, 1.0]
    "role_min_support": 0.005,     # auxiliary: filter out 1-occurrence noise
    "role_min_set_size": 1,
    "role_max_itemset_size": 8,

    # ---------- Guards against combinatorial explosion ----------
    "max_candidates": 200000,
    "max_fixpoints": 1000,

    # ---------- Joint criteria ----------
    "use_joint_criteria": True,
    "joint_support_min": 0.02,
    "joint_stability_min": 0.6,
    "use_stability_hard_threshold": False,   # False = only sort, don't reject
    "use_lower_bound_filter": True,          # True = "minimal fixpoint"

    # ---------- Logic derivation ----------
    "logic_threshold": 0.5,

    # ---------- Multi-channel initialization ----------
    "w_sim": 0.4,
    "w_logic": 0.4,
    "w_energy": 0.2,

    # ---------- High-order term internalization ----------
    "enable_high_order": True,

    # ---------- IO ----------
    "raw_events_path":
        "results/compression_graph/raw_compression_events.csv",
    "output_dir":
        "endo_result",
    "scales": [51, 71, 91, 111],

    "verbose": True,
}