#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Cognitive Graph Objective Metrics Analysis Script (Central Nodes + Total Node Frequency Zipf)

Functionality:
1. Run emergence experiments, save energy history, compression events, migration events.
2. Metric 1: Power-law/exponential fitting of energy decline curve, compute decay exponent and R².
3. Metric 2: Zipf test (power-law fit) for occurrence frequency of central concepts, plot log-log graph.
4. Metric 3: Zipf test for total occurrence frequency of concept nodes in compression clusters (center + members).
Output directory: results/analysis/objective_metrics/
"""

import os
import sys
import json
import time
import csv
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
from pathlib import Path
from scipy.optimize import curve_fit
from scipy import stats
from collections import Counter

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from emergence.universe_enhanced import CognitiveUniverseEnhanced
from utils.individual_variation import IndividualVariation, create_enhanced_individual_params
from config import BASE_PARAMETERS, VARIATION_RANGES

# Set Chinese font (if available)
plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False


class ObjectiveMetricsAnalysis:
    """
    Cognitive Graph Objective Metrics Analysis Class (Central Nodes + Total Node Frequency Zipf)
    """

    def __init__(self, output_dir="../../results/analysis/objective_metrics"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.fig_dir = self.output_dir / "figures"
        self.fig_dir.mkdir(exist_ok=True)
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.summary_data = []                 # Summary for each individual
        self.center_counter = Counter()         # Occurrence count of central nodes
        self.node_total_counter = Counter()     # Total occurrence count of nodes in compression events (deduplicated)

    # ---------- Fitting function definitions ----------
    @staticmethod
    def power_law(x, a, b, c):
        """Power-law function a * x^(-b) + Cognitive_Map_Animation_Visual_Elements_Description.md"""
        return a * np.power(x, -b) + c

    @staticmethod
    def exp_decay(x, a, b, c):
        """Exponential decay a * exp(-b * x) + Cognitive_Map_Animation_Visual_Elements_Description.md"""
        return a * np.exp(-b * x) + c

    def fit_energy_curve(self, x, y):
        """
        Fit the energy history with two models, return the best model's parameters and metrics.
        Returns dictionary: {'model': 'power'/'exp', 'params': [a,b,Cognitive_Map_Animation_Visual_Elements_Description.md], 'r2': float, 'rmse': float, 'fluctuation': float}
        """
        # Power-law fit
        try:
            popt_power, _ = curve_fit(self.power_law, x, y, maxfev=5000,
                                      p0=[y[0]-y[-1], 0.5, y[-1]])
            residuals_power = y - self.power_law(x, *popt_power)
            ss_res = np.sum(residuals_power**2)
            ss_tot = np.sum((y - np.mean(y))**2)
            r2_power = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0
            rmse_power = np.sqrt(np.mean(residuals_power**2))
            fluctuation_power = np.mean(np.abs(residuals_power))
        except:
            r2_power = -np.inf
            rmse_power = np.inf
            fluctuation_power = np.inf
            popt_power = None

        # Exponential fit
        try:
            popt_exp, _ = curve_fit(self.exp_decay, x, y, maxfev=5000,
                                    p0=[y[0]-y[-1], 0.001, y[-1]])
            residuals_exp = y - self.exp_decay(x, *popt_exp)
            ss_res = np.sum(residuals_exp**2)
            ss_tot = np.sum((y - np.mean(y))**2)
            r2_exp = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0
            rmse_exp = np.sqrt(np.mean(residuals_exp**2))
            fluctuation_exp = np.mean(np.abs(residuals_exp))
        except:
            r2_exp = -np.inf
            rmse_exp = np.inf
            fluctuation_exp = np.inf
            popt_exp = None

        # Choose model with higher R²
        if r2_power > r2_exp and popt_power is not None:
            return {
                'model': 'power',
                'params': popt_power.tolist(),
                'r2': r2_power,
                'rmse': rmse_power,
                'fluctuation': fluctuation_power
            }
        elif r2_exp > r2_power and popt_exp is not None:
            return {
                'model': 'exp',
                'params': popt_exp.tolist(),
                'r2': r2_exp,
                'rmse': rmse_exp,
                'fluctuation': fluctuation_exp
            }
        else:
            # Both failed or equal, return None
            return None

    # ---------- Experiment execution ----------
    def run_experiments(self, scales=None, num_individuals=3, max_iterations=10000,
                        detection_interval=100, window=100):
        """
        Run emergence experiments for given scales and number of individuals, save raw data and compute objective metrics.
        """
        if scales is None:
            scales = [51, 71, 91, 111]

        print("=" * 60)
        print("Cognitive Graph Objective Metrics Analysis Experiment (Central Nodes + Total Node Frequency Zipf)")
        print("=" * 60)
        print(f"Scales: {scales}")
        print(f"Number of individuals: {num_individuals}")
        print(f"Iterations: {max_iterations}")
        print(f"Detection interval: {detection_interval}")
        print(f"Output directory: {self.output_dir}")
        print("=" * 60)

        variation_simulator = IndividualVariation(BASE_PARAMETERS, VARIATION_RANGES)

        for scale in scales:
            print(f"\n--- Processing scale {scale} concepts ---")
            for ind in range(num_individuals):
                ind_id = f"ind{ind}"
                print(f"  Individual {ind_id} ...")

                # Generate individual parameters
                base_params = variation_simulator.generate_individual(f"scale{scale}_{ind_id}")
                individual_params = create_enhanced_individual_params(base_params)

                # Create universe instance
                universe = CognitiveUniverseEnhanced(individual_params,
                                                     network_seed=42+ind,
                                                     num_concepts=scale)

                # Initialize network
                universe.initialize_semantic_network()

                # Run evolution with emergence detection
                start_time = time.time()
                observations = universe.evolve_with_emergence_detection(
                    iterations=max_iterations,
                    detection_interval=detection_interval
                )
                elapsed = time.time() - start_time

                # Get energy history
                energy_history = universe.energy_history

                # Extract compression and migration events
                compressions = observations.get('natural_compressions', [])
                migrations = observations.get('natural_migrations', [])

                # --- Save raw data ---
                self._save_energy_history(scale, ind, energy_history)
                self._save_compressions(scale, ind, compressions)
                self._save_migrations(scale, ind, migrations)

                # --- Metric 1: Energy curve fitting ---
                x = np.arange(len(energy_history))
                y = np.array(energy_history)
                fit_result = self.fit_energy_curve(x, y)

                # --- Basic statistics ---
                initial_energy = energy_history[0]
                final_energy = energy_history[-1]
                energy_improvement = (initial_energy - final_energy) / initial_energy * 100

                # --- Collect node frequencies from compression events ---
                for comp in compressions:
                    center = comp.get('center')
                    related = comp.get('related_nodes', [])
                    if center:
                        # Count central node
                        self.center_counter[center] += 1
                        # Total node frequency: all involved nodes (deduplicated)
                        nodes_in_event = set([center] + related)
                        for node in nodes_in_event:
                            self.node_total_counter[node] += 1

                # --- Individual summary data ---
                entry = {
                    'scale': scale,
                    'individual': ind,
                    'initial_energy': initial_energy,
                    'final_energy': final_energy,
                    'energy_improvement': energy_improvement,
                    'total_compressions': len(compressions),
                    'total_migrations': len(migrations),
                    'elapsed_time': elapsed,
                }
                if fit_result:
                    entry.update({
                        'fit_model': fit_result['model'],
                        'fit_r2': fit_result['r2'],
                        'fit_rmse': fit_result['rmse'],
                        'fit_fluctuation': fit_result['fluctuation'],
                        'fit_params': json.dumps(fit_result['params'])  # Convert to string for storage
                    })
                else:
                    entry.update({
                        'fit_model': 'none',
                        'fit_r2': None,
                        'fit_rmse': None,
                        'fit_fluctuation': None,
                        'fit_params': None
                    })

                self.summary_data.append(entry)

                print(f"      Energy improvement: {energy_improvement:.2f}%")
                print(f"      Fitted model: {entry.get('fit_model', 'none')}, R²: {entry.get('fit_r2', 0):.3f}")
                print(f"      Compression events: {len(compressions)}")
                print(f"      Migration events: {len(migrations)}")
                print(f"      Time elapsed: {elapsed:.1f}s")

                # --- Plot individual energy decline rate (optional, simplified) ---
                self.plot_energy_rate(scale, ind, energy_history, fit_result, window)

        # Save summary results
        self._save_summary()

        # --- Metric 2: Zipf analysis of central node occurrence frequencies ---
        self.zipf_center_analysis()

        # --- Metric 3: Zipf analysis of total node frequencies ---
        self.zipf_node_total_analysis()

    def plot_energy_rate(self, scale, ind, energy_history, fit_result, window=100):
        """Plot energy decline rate, overlay theoretical rate from fitted curve (dashed line)"""
        rates = []
        indices = []
        for i in range(0, len(energy_history) - window, window):
            rates.append(energy_history[i] - energy_history[i + window])
            indices.append(i)

        plt.figure(figsize=(8, 5))
        # Actual rate curve
        plt.plot(indices, rates, 'b-', linewidth=1.5, label='Actual decline rate')

        # If fit result exists, add theoretical rate dashed line
        if fit_result and fit_result['model'] != 'none':
            model = fit_result['model']
            params = fit_result['params']
            # Compute theoretical energy values (at each time point)
            x_full = np.arange(len(energy_history))
            if model == 'power':
                y_fit = self.power_law(x_full, *params)
            else:  # exp
                y_fit = self.exp_decay(x_full, *params)
            # Compute theoretical rate (with same window step)
            fit_rates = []
            for i in indices:
                if i + window < len(y_fit):
                    fit_rates.append(y_fit[i] - y_fit[i + window])
                else:
                    fit_rates.append(0)
            plt.plot(indices, fit_rates, 'r--', linewidth=1.5, label=f'Theoretical rate ({model})')

        plt.xlabel('Iteration')
        plt.ylabel('Energy decline rate')
        plt.title(f'Scale {scale} Individual {ind}: Energy decline rate and fitted curve')
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        fig_path = self.fig_dir / f"energy_rate_scale{scale}_ind{ind}_{self.timestamp}.png"
        plt.savefig(fig_path, dpi=150)
        plt.close()

    def zipf_center_analysis(self):
        """
        Perform power-law fitting (Zipf test) for central node occurrence frequencies, plot log-log graph.
        """
        if not self.center_counter:
            print("Warning: No compression events, cannot perform center node Zipf analysis")
            return

        # Sort by frequency descending
        items = sorted(self.center_counter.items(), key=lambda x: x[1], reverse=True)
        centers = [item[0] for item in items]
        freqs = [item[1] for item in items]

        # Convert to log coordinates
        log_ranks = np.log(np.arange(1, len(freqs)+1))
        log_freqs = np.log(freqs)

        # Linear fit (power-law)
        slope, intercept, r_value, p_value, std_err = stats.linregress(log_ranks, log_freqs)
        r2 = r_value**2

        print("\n" + "=" * 60)
        print("Metric 2: Zipf distribution test for central node occurrence frequencies")
        print("=" * 60)
        print(f"Power-law exponent (slope): {slope:.3f}")
        print(f"R²: {r2:.3f}")
        print(f"p-value: {p_value:.3e}")
        print(f"Total compression events: {sum(freqs)}")
        print(f"Number of distinct center nodes: {len(centers)}")
        print("=" * 60)

        # Plot log-log graph
        plt.figure(figsize=(8, 6))
        plt.scatter(log_ranks, log_freqs, alpha=0.7, label='Observed data')
        x_fit = np.linspace(min(log_ranks), max(log_ranks), 100)
        y_fit = slope * x_fit + intercept
        plt.plot(x_fit, y_fit, 'r--', label=f'Fitted line (slope={slope:.2f})')
        plt.xlabel('log(rank)')
        plt.ylabel('log(frequency of center nodes)')
        plt.title('Power-law test for center node frequencies (Zipf)')
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        fig_path = self.fig_dir / f"zipf_center_{self.timestamp}.png"
        plt.savefig(fig_path, dpi=150)
        plt.close()
        print(f"Center node Zipf plot saved: {fig_path}")

        # Save Zipf result to JSON
        zipf_result = {
            'slope': slope,
            'intercept': intercept,
            'r2': r2,
            'p_value': p_value,
            'total_events': sum(freqs),
            'unique_centers': len(centers),
            'top_centers': {centers[i]: freqs[i] for i in range(min(10, len(centers)))}
        }
        with open(self.output_dir / f"zipf_center_result_{self.timestamp}.json", 'w', encoding='utf-8') as f:
            json.dump(zipf_result, f, ensure_ascii=False, indent=2)

    def zipf_node_total_analysis(self):
        """
        Perform power-law fitting (Zipf test) for total occurrence frequencies of nodes in compression events
        (center + members, deduplicated), plot log-log graph.
        """
        if not self.node_total_counter:
            print("Warning: No compression events, cannot perform node total frequency Zipf analysis")
            return

        # Sort by frequency descending
        items = sorted(self.node_total_counter.items(), key=lambda x: x[1], reverse=True)
        nodes = [item[0] for item in items]
        freqs = [item[1] for item in items]

        # Convert to log coordinates
        log_ranks = np.log(np.arange(1, len(freqs)+1))
        log_freqs = np.log(freqs)

        # Linear fit (power-law)
        slope, intercept, r_value, p_value, std_err = stats.linregress(log_ranks, log_freqs)
        r2 = r_value**2

        print("\n" + "=" * 60)
        print("Metric 3: Zipf distribution test for total node occurrence frequencies in compressions")
        print("=" * 60)
        print(f"Power-law exponent (slope): {slope:.3f}")
        print(f"R²: {r2:.3f}")
        print(f"p-value: {p_value:.3e}")
        print(f"Total occurrences: {sum(freqs)}")
        print(f"Number of distinct nodes: {len(nodes)}")
        print("=" * 60)

        # Plot log-log graph
        plt.figure(figsize=(8, 6))
        plt.scatter(log_ranks, log_freqs, alpha=0.7, label='Observed data')
        x_fit = np.linspace(min(log_ranks), max(log_ranks), 100)
        y_fit = slope * x_fit + intercept
        plt.plot(x_fit, y_fit, 'r--', label=f'Fitted line (slope={slope:.2f})')
        plt.xlabel('log(rank)')
        plt.ylabel('log(total frequency of nodes)')
        plt.title('Power-law test for total node frequencies in compressions (Zipf)')
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        fig_path = self.fig_dir / f"zipf_node_total_{self.timestamp}.png"
        plt.savefig(fig_path, dpi=150)
        plt.close()
        print(f"Node total frequency Zipf plot saved: {fig_path}")

        # Save Zipf result to JSON
        zipf_result = {
            'slope': slope,
            'intercept': intercept,
            'r2': r2,
            'p_value': p_value,
            'total_occurrences': sum(freqs),
            'unique_nodes': len(nodes),
            'top_nodes': {nodes[i]: freqs[i] for i in range(min(10, len(nodes)))}
        }
        with open(self.output_dir / f"zipf_node_total_result_{self.timestamp}.json", 'w', encoding='utf-8') as f:
            json.dump(zipf_result, f, ensure_ascii=False, indent=2)

    # ---------- Data saving helper functions ----------
    def _save_energy_history(self, scale, ind, energy_history):
        filename = self.output_dir / f"energy_history_scale{scale}_ind{ind}_{self.timestamp}.csv"
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['iteration', 'energy'])
            for it, e in enumerate(energy_history):
                writer.writerow([it, e])

    def _save_compressions(self, scale, ind, compressions):
        if not compressions:
            return
        filename = self.output_dir / f"compressions_scale{scale}_ind{ind}_{self.timestamp}.csv"
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            fieldnames = ['detection_iteration', 'center', 'related_nodes', 'cluster_size',
                          'energy_synergy', 'cohesion', 'emergence_strength']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for c in compressions:
                row = {k: c.get(k, '') for k in fieldnames}
                if 'related_nodes' in row and isinstance(row['related_nodes'], list):
                    row['related_nodes'] = '|'.join(row['related_nodes'])
                writer.writerow(row)

    def _save_migrations(self, scale, ind, migrations):
        if not migrations:
            return
        filename = self.output_dir / f"migrations_scale{scale}_ind{ind}_{self.timestamp}.csv"
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            fieldnames = ['detection_iteration', 'principle_node', 'from_node', 'to_node',
                          'efficiency_gain', 'domain_span', 'path']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for m in migrations:
                row = {k: m.get(k, '') for k in fieldnames}
                if 'path' in row and isinstance(row['path'], list):
                    row['path'] = ' -> '.join(row['path'])
                writer.writerow(row)

    def _save_summary(self):
        """Save individual summary data to CSV and JSON"""
        df = pd.DataFrame(self.summary_data)
        csv_path = self.output_dir / f"individual_summary_{self.timestamp}.csv"
        df.to_csv(csv_path, index=False, encoding='utf-8-sig')

        json_path = self.output_dir / f"individual_summary_{self.timestamp}.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(self.summary_data, f, ensure_ascii=False, indent=2)

        print(f"\nSummary files saved:")
        print(f"  CSV: {csv_path}")
        print(f"  JSON: {json_path}")

        # Print average fitting metrics by scale
        print("\nAverage fitting metrics by scale:")
        grouped = df.groupby('scale').agg({
            'energy_improvement': 'mean',
            'fit_r2': 'mean',
            'fit_rmse': 'mean',
            'fit_fluctuation': 'mean',
            'total_compressions': 'mean',
            'total_migrations': 'mean'
        }).round(3)
        print(grouped.to_string())


if __name__ == "__main__":
    analyzer = ObjectiveMetricsAnalysis()
    analyzer.run_experiments(
        scales=[51, 71, 91, 111],
        num_individuals=3,
        max_iterations=10000,
        detection_interval=100,
        window=100
    )
    print("\nAll experiments completed, data saved.")