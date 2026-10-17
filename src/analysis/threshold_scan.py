#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
threshold_scan.py
Concept compression threshold scanning experiment script (fixed np.savez error)
For the natural emergence model with 91 concepts, scan detection threshold (compression_synergy) from 0.5 to 0.9,
record the number of compressions detected at each threshold, and plot the curve.
"""

import sys
import os
import json
import numpy as np
import matplotlib.pyplot as plt
from tqdm import tqdm

# Add project root to path (adjust according to actual project structure)
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from emergence.universe_enhanced import CognitiveUniverseEnhanced


def run_threshold_scan(
    thresholds: list,
    num_concepts: int = 91,
    iterations: int = 10000,
    network_seed: int = 42,
    detection_interval: int = 200,
    temp_save: bool = True
) -> dict:
    """
    Execute scan experiment over the given list of thresholds.

    Args:
        thresholds (list): List of thresholds to scan.
        num_concepts (int): Number of concept nodes.
        iterations (int): Number of evolution iterations.
        network_seed (int): Random seed.
        detection_interval (int): Emergence detection interval.
        temp_save (bool): Whether to save temporary results after each iteration (to prevent data loss on interruption).

    Returns:
        dict: Threshold -> number of compressions mapping.
    """
    results = {}

    for i, thresh in enumerate(tqdm(thresholds, desc="Threshold scan progress")):
        # Create universe instance (reinitialize each time to ensure consistent random sequence)
        universe = CognitiveUniverseEnhanced(
            individual_params=None,
            network_seed=network_seed,
            num_concepts=num_concepts
        )

        # Modify the detector's compression synergy threshold
        universe.emergence_detector.thresholds['compression_synergy'] = thresh

        # Initialize semantic network (nodes and edges generated based on semantic similarity)
        universe.initialize_semantic_network()

        # Run evolution with emergence detection
        observations = universe.evolve_with_emergence_detection(
            iterations=iterations,
            detection_interval=detection_interval
        )

        # Record number of compression events
        comp_count = len(observations.get('natural_compressions', []))
        results[thresh] = comp_count

        # Optional: save temporary results to JSON file (overwrite latest state)
        if temp_save:
            # Convert float keys to strings for JSON serialization
            str_key_results = {str(k): v for k, v in results.items()}
            with open('threshold_scan_temp.json', 'w', encoding='utf-8') as f:
                json.dump(str_key_results, f, indent=2)

    return results


def plot_scan_results(results: dict, save_path: str = None):
    """
    Plot threshold vs number of compressions curve.

    Args:
        results (dict): Threshold -> number of compressions mapping (keys are floats).
        save_path (str, optional): Path to save the figure.
    """
    thresholds = sorted(results.keys())
    counts = [results[t] for t in thresholds]

    plt.figure(figsize=(10, 6))
    plt.plot(thresholds, counts, marker='o', linestyle='-', linewidth=2, markersize=8)
    plt.xlabel('Compression Synergy Threshold', fontsize=12)
    plt.ylabel('Number of Detected Compressions', fontsize=12)
    plt.title('Effect of Detection Threshold on Observed Compression Events\n(91 Concepts, 10,000 Iterations)', fontsize=14)
    plt.grid(True, alpha=0.3)
    plt.xticks(thresholds)

    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"Figure saved to: {save_path}")
    plt.show()


if __name__ == "__main__":
    # Define threshold scan range (0.5 to 0.9, step 0.05)
    scan_thresholds = np.arange(0.5, 0.91, 0.05).round(2).tolist()
    print(f"Will scan thresholds: {scan_thresholds}")

    # Run scan experiment
    results = run_threshold_scan(
        thresholds=scan_thresholds,
        num_concepts=91,
        iterations=10000,
        network_seed=42,
        detection_interval=200,
        temp_save=True
    )

    # Print results
    print("\nThreshold scan results:")
    for thresh in sorted(results.keys()):
        print(f"  Threshold {thresh:.2f} -> Compressions {results[thresh]}")

    # Save results to JSON file (convert keys to strings)
    str_key_results = {str(k): v for k, v in results.items()}
    with open('../../results/analysis/add_scan/threshold_scan_results.json', 'w', encoding='utf-8') as f:
        json.dump(str_key_results, f, indent=2)
    print("Results saved to threshold_scan_results.json")

    # Plot curve
    plot_scan_results(results, save_path='../../results/analysis/add_scan/threshold_scan_plot.png')