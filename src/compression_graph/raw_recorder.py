# -*- coding: utf-8 -*-
"""
Record raw (pre-deduplication) compression events.

The original emergence detector deduplicates compression events,
so observations['natural_compressions'] holds only unique patterns.
We run a non-deduplicating detector in parallel to obtain real
co-occurrence frequencies, while leaving original behavior intact.
"""

import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_PROJ = os.path.dirname(_HERE)
for _p in (_HERE, _PROJ):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from src.emergence.universe_enhanced import CognitiveUniverseEnhanced
from src.emergence.detector_fixed import EmergenceDetectorFixed


class NonDeduplicatingDetector(EmergenceDetectorFixed):
    """Detector variant that never suppresses repeated detections."""

    def _is_duplicate_compression(self, center, neighbors):
        return False


class RawRecordingUniverseEnhanced(CognitiveUniverseEnhanced):
    """Extends CognitiveUniverseEnhanced to also record every raw detection."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.raw_compressions = []
        self.raw_migrations = []
        self._raw_detector = NonDeduplicatingDetector(
            detection_thresholds=self.emergence_detector.thresholds
        )

    def _detect_emergence(self, iteration: int) -> None:
        # Raw recording: no deduplication
        raw_comps = self._raw_detector.detect_spontaneous_compression(
            self.G, self.energy_history, self.traversal_history
        )
        for c in raw_comps:
            c = dict(c)
            c["detection_iteration"] = iteration
            self.raw_compressions.append(c)

        raw_migs = self._raw_detector.detect_emergent_migration(
            self.G, self.traversal_history, iteration
        )
        for m in raw_migs:
            m = dict(m)
            m["detection_iteration"] = iteration
            self.raw_migrations.append(m)

        # Original deduplicated behavior
        super()._detect_emergence(iteration)