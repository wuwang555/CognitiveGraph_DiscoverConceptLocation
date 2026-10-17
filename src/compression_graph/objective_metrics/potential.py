# -*- coding: utf-8 -*-
"""
Compression-potential Phi distribution.

Phi = internal_avg / external_avg, as defined in the original paper.
"""

import numpy as np
from typing import List, Dict, Optional


def potential_stats(phi_values: List[float]) -> Optional[Dict[str, float]]:
    if not phi_values:
        return None
    arr = np.array(phi_values, dtype=float)
    return {
        "count": int(len(arr)),
        "mean": float(arr.mean()),
        "std": float(arr.std()),
        "min": float(arr.min()),
        "max": float(arr.max()),
        "median": float(np.median(arr)),
        "q25": float(np.percentile(arr, 25)),
        "q75": float(np.percentile(arr, 75)),
    }