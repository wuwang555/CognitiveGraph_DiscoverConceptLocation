# -*- coding: utf-8 -*-
"""
Configuration for the compression-graph observation layer.

Kept minimal on purpose. Every threshold is absolute, not relative,
so scales remain comparable.
"""

COMPRESSION_GRAPH_CONFIG = {
    # ---------- Input ----------
    # True : use raw events before deduplication (real frequencies)
    # False: use deduplicated 'natural_compressions'
    "use_raw_events": True,

    # ---------- Graph construction ----------
    # 'clique': every unordered pair inside the cluster gets +1
    # 'star'  : only (center, member) pairs get +1
    "edge_mode": "clique",

    # ---------- Migration detection ----------
    "min_path_nodes": 2,
    "max_path_nodes": 10,
    "n_hard_walks": 500,           # number of hard traversal seeds
    "n_soft_walks": 500,           # number of soft traversal attempts
    "migration_threshold": 50,     # absolute: avg co-occurrence of a path

    # ---------- Compression detection ----------
    "min_cluster_size": 3,
    "max_cluster_size": 8,
    "compression_threshold": 1.5,  # absolute: Phi = internal / external

    # ---------- Output ----------
    "output_dir": "../../results/compression_graph",
    "random_seed": 42,
    "verbose": True,
}