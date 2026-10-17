#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
compare_time.py

Compare runtime between pure postulate evolution (no detection) and full evolution (with detection).
"""

import sys
import os
import time
import random
import numpy as np
from pathlib import Path
from datetime import datetime

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from emergence.universe import CognitiveUniverse
from emergence.universe_enhanced import CognitiveUniverseEnhanced
from utils.individual_variation import IndividualVariation, create_enhanced_individual_params
from config import BASE_PARAMETERS, VARIATION_RANGES

random.seed(42)
np.random.seed(42)


# ============================================================
# 1. Pure postulate mode (no detection)
# ============================================================
class CoreOnlyUniverse(CognitiveUniverse):
    """
    Keep only spacetime graph and energy minimization, remove all observations, logging, and detection.
    """

    def __init__(self, individual_params=None, network_seed=42, num_concepts=None):
        super().__init__(individual_params, network_seed)
        self.num_concepts = num_concepts

    def evolve_core_only(self, iterations=10000):
        """
        Execute pure postulate evolution, no observations recorded.
        """
        # Initialize network (important!)
        self.initialize_semantic_network()

        for i in range(iterations):
            self.iteration_count += 1

            # Energy optimization (learning)
            self.basic_energy_optimization()

            # Random traversal
            if random.random() < 0.3:
                self._random_traversal()

            # Forgetting (every 10 steps)
            if i % 10 == 0:
                self.apply_basic_forgetting()

    def initialize_semantic_network(self):
        from core.semantic_network import SemanticConceptNetwork

        semantic_net = SemanticConceptNetwork()
        semantic_net.build_comprehensive_network(num_concepts=self.num_concepts)

        nodes = list(semantic_net.concept_definitions.keys())
        self.G.add_nodes_from(nodes)

        for i, node1 in enumerate(nodes):
            for j, node2 in enumerate(nodes[i+1:], i+1):
                similarity = semantic_net.calculate_semantic_similarity(node1, node2)
                if similarity > 0.1:
                    energy = 2.0 - similarity * 1.5
                    energy = max(0.3, min(2.0, energy))
                    self.G.add_edge(node1, node2,
                                    weight=energy,
                                    traversal_count=0,
                                    original_weight=energy,
                                    similarity=similarity)
                    self.last_activation_time[(node1, node2)] = 0


def run_core_only_benchmark(scales, num_individuals=3, iterations=10000):
    """
    Run pure postulate mode, return list of results.
    """
    results = []
    for scale in scales:
        for ind in range(num_individuals):
            var_sim = IndividualVariation(BASE_PARAMETERS, VARIATION_RANGES)
            base_params = var_sim.generate_individual(f"scale{scale}_ind{ind}")
            ind_params = create_enhanced_individual_params(base_params)

            universe = CoreOnlyUniverse(
                individual_params=ind_params,
                network_seed=42 + ind,
                num_concepts=scale
            )

            start = time.time()
            universe.evolve_core_only(iterations=iterations)
            elapsed = time.time() - start

            results.append({
                'mode': 'core_only',
                'scale': scale,
                'individual': ind,
                'time_sec': elapsed
            })

            print(f"[core_only] Scale {scale} Individual {ind+1} completed, time: {elapsed:.2f} seconds")
    return results


# ============================================================
# 2. Full mode (with detection)
# ============================================================
def run_full_benchmark(scales, num_individuals=3, iterations=10000):
    """
    Run full mode (CognitiveUniverseEnhanced + detection), return list of results.
    """
    results = []
    for scale in scales:
        for ind in range(num_individuals):
            var_sim = IndividualVariation(BASE_PARAMETERS, VARIATION_RANGES)
            base_params = var_sim.generate_individual(f"scale{scale}_ind{ind}")
            ind_params = create_enhanced_individual_params(base_params)

            universe = CognitiveUniverseEnhanced(
                individual_params=ind_params,
                network_seed=42 + ind,
                num_concepts=scale
            )

            # Important: initialize network (full mode does not auto-initialize)
            universe.initialize_semantic_network()

            start = time.time()
            universe.evolve_with_emergence_detection(
                iterations=iterations,
                detection_interval=100
            )
            elapsed = time.time() - start

            results.append({
                'mode': 'full_with_detection',
                'scale': scale,
                'individual': ind,
                'time_sec': elapsed
            })

            print(f"[full] Scale {scale} Individual {ind+1} completed, time: {elapsed:.2f} seconds")
    return results


# ============================================================
# 3. Main: run sequentially and output comparison
# ============================================================
def main():
    scales = [51, 71, 91, 111]
    num_individuals = 3
    iterations = 10000

    print("=" * 70)
    print("Time Comparison Experiment: Pure Postulate vs Full Detection")
    print(f"Scales: {scales}")
    print(f"Individuals per scale: {num_individuals}")
    print(f"Iterations: {iterations}")
    print("=" * 70)

    # 1. Run pure postulate mode
    print("\n--- Starting pure postulate mode (no detection) ---")
    core_results = run_core_only_benchmark(scales, num_individuals, iterations)

    # 2. Run full mode
    print("\n--- Starting full mode (with detection) ---")
    full_results = run_full_benchmark(scales, num_individuals, iterations)

    # 3. Aggregate statistics
    core_by_scale = {}
    full_by_scale = {}
    for r in core_results:
        s = r['scale']
        core_by_scale.setdefault(s, []).append(r['time_sec'])
    for r in full_results:
        s = r['scale']
        full_by_scale.setdefault(s, []).append(r['time_sec'])

    print("\n" + "=" * 70)
    print("Average time per scale (seconds)")
    print(f"{'Scale':>6} {'Pure Postulate':>12} {'Full Detection':>12} {'Difference':>12} {'Ratio':>10}")
    print("-" * 70)
    for scale in scales:
        core_avg = np.mean(core_by_scale[scale])
        full_avg = np.mean(full_by_scale[scale])
        diff = full_avg - core_avg
        ratio = full_avg / core_avg if core_avg > 0 else float('inf')
        print(f"{scale:>6} {core_avg:>12.2f} {full_avg:>12.2f} {diff:>+12.2f} {ratio:>9.2f}x")

    total_core = sum(r['time_sec'] for r in core_results)
    total_full = sum(r['time_sec'] for r in full_results)
    print("-" * 70)
    print(f"{'Total':>6} {total_core:>12.2f} {total_full:>12.2f} {total_full - total_core:>+12.2f} {total_full/total_core:>9.2f}x")

    # 4. Save results to CSV
    import pandas as pd
    df = pd.DataFrame(core_results + full_results)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_file = f"../../results/analysis/time/time_comparison_{timestamp}.csv"
    df.to_csv(out_file, index=False)
    print(f"\nDetailed results saved to {out_file}")


if __name__ == "__main__":
    main()