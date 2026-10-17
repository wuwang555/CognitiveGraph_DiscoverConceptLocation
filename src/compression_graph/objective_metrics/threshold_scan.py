# -*- coding: utf-8 -*-
"""
Threshold scan for migration and compression detection.

Mirrors the original paper's threshold_scan.py, adapted to the
compression graph.
"""

import os
import sys
from typing import List, Dict

_HERE = os.path.dirname(os.path.abspath(__file__))
_CG = os.path.dirname(_HERE)
if _CG not in sys.path:
    sys.path.insert(0, _CG)

from src.compression_graph.detector import CompressionGraphDetector


def scan_migration_threshold(graph, base_config,
                             thresholds: List[float]) -> Dict[float, int]:
    results = {}
    for t in thresholds:
        cfg = dict(base_config)
        cfg["migration_threshold"] = t
        detector = CompressionGraphDetector(graph, cfg)
        migrations = detector.detect_migration()
        results[float(t)] = len(migrations)
    return results


def scan_compression_threshold(graph, base_config,
                               thresholds: List[float]) -> Dict[float, int]:
    results = {}
    for t in thresholds:
        cfg = dict(base_config)
        cfg["compression_threshold"] = t
        detector = CompressionGraphDetector(graph, cfg)
        clusters = detector.detect_compression()
        results[float(t)] = len(clusters)
    return results