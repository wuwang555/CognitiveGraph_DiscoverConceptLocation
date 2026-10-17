"""
Compression Graph — second-order observation layer.

Detects compression and migration on an undirected compression
co-occurrence graph. Results are statistical candidates, not
validated concepts.
"""

__all__ = [
    "config_compression",
    "raw_recorder",
    "cg_core",
    "detector",
    "table_export",
    "pipeline",
    "visualize",
]