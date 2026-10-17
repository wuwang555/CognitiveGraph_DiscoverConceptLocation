# emergence_study_fixed.py
"""
Emergence Phenomenon Study Experiment (Fixed Version)
Used to observe natural emergence of concept compression and principle migration from the two postulates
(cognitive spacetime and energy dynamics).
"""

import numpy as np
import time
import pandas as pd
from datetime import datetime
from emergence.universe_enhanced import CognitiveUniverseEnhanced
from emergence.observer import EmergenceObserver
from emergence.detector_fixed import EmergenceDetectorFixed
from utils.individual_variation import IndividualVariation, create_enhanced_individual_params
from config import *
import os
import csv
import networkx as nx


class EmergenceStudyFixed:
    """Fixed emergence phenomenon study experiment class.

    This class is responsible for running pure emergence experiments, recording concept compression and
    principle migration events, and saving results to Excel files.
    """

    def __init__(self):
        """Initialize study instance, create result containers and unified timestamp."""
        self.results = {}
        self.comparison_data = {}
        self.excel_data = {'compressions': [], 'migrations': []}
        from datetime import datetime
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")   # Unified timestamp

    def save_to_excel(self, filename=None):
        """Save emergence data to Excel file.

        Args:
            filename (str, optional): File name to save. If None, automatically generated.

        Returns:
            str: Saved file path.
        """
        if filename is None:
            # Ensure directory exists
            emergence_dir = "results/emergence"
            os.makedirs(emergence_dir, exist_ok=True)

            filename = os.path.join(emergence_dir, f"emergence_results_{self.timestamp}.xlsx")

        # Create DataFrames
        df_compressions = pd.DataFrame(self.excel_data['compressions'])
        df_migrations = pd.DataFrame(self.excel_data['migrations'])

        # Save to Excel
        with pd.ExcelWriter(filename, engine='openpyxl') as writer:
            df_compressions.to_excel(writer, sheet_name='Concept Compressions', index=False)
            df_migrations.to_excel(writer, sheet_name='First-Principles Migrations', index=False)

        print(f"Data saved to: {filename}")
        print(f"Concept compression records: {len(df_compressions)}")
        print(f"Principle migration records: {len(df_migrations)}")

        return filename

    def run_pure_emergence_experiment(self, num_individuals=3, max_iterations=None, num_concepts=None):
        """Run pure emergence observation experiment.

        Based on the two postulates (cognitive spacetime and energy dynamics), run universe evolution and observe
        natural emergence of concept compression and principle migration.

        Args:
            num_individuals (int): Number of individuals.
            max_iterations (int, optional): Maximum iterations per individual.
            num_concepts (int, optional): Number of concept nodes. If None, use default.

        Returns:
            list: List of result dictionaries for each individual.
        """
        if max_iterations is None:
            max_iterations = EXPERIMENT_CONFIG['default_iterations']

        print("=== Pure Emergence Observation Experiment ===")
        print("Goal: Observe natural emergence phenomena from the two postulates")
        print(f"Configuration: {num_individuals} individuals, {max_iterations} iterations")
        if num_concepts:
            print(f"Number of concepts: {num_concepts}")
        print("=" * 50)

        variation_simulator = IndividualVariation(BASE_PARAMETERS, VARIATION_RANGES)
        emergence_results = []

        for i in range(num_individuals):
            individual_id = f"Emergence_Individual_{i + 1}"
            print(f"\n--- Observing {individual_id} ---")

            # Generate individual parameters
            base_params = variation_simulator.generate_individual(individual_id)
            individual_params = create_enhanced_individual_params(base_params)

            # Directly create enhanced universe instance, passing num_concepts parameter
            universe_enhanced = CognitiveUniverseEnhanced(individual_params, num_concepts=num_concepts)
            observer = EmergenceObserver()
            detector = EmergenceDetectorFixed()

            # Initialize universe network
            self._initialize_universe_network(universe_enhanced)

            # Run universe evolution
            start_time = time.time()
            observations = universe_enhanced.evolve_with_emergence_detection(
                iterations=max_iterations,
                detection_interval=100
            )
            end_time = time.time()

            # Save energy history
            energy_history = universe_enhanced.energy_history
            energy_file = os.path.join("results/emergence", f"energy_history_{individual_id}_{self.timestamp}.csv")
            with open(energy_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['iteration', 'energy'])
                for idx, e in enumerate(energy_history):
                    writer.writerow([idx, e])
            print(f"Energy history saved: {energy_file}")

            # Optionally save final network structure (GraphML)
            graphml_file = os.path.join("results/emergence", f"network_{individual_id}_{self.timestamp}.graphml")
            nx.write_graphml(universe_enhanced.G, graphml_file)
            print(f"Network structure saved: {graphml_file}")

            # Record to Excel data structure
            self._record_excel_data(individual_id, observations, universe_enhanced)

            # Collect individual results
            individual_result = {
                'individual_id': individual_id,
                'parameters': individual_params,
                'observations': observations,  # Use returned observations
                'final_energy': universe_enhanced.calculate_network_energy(),
                'initial_energy': universe_enhanced.energy_history[0] if universe_enhanced.energy_history else 1.0,
                'energy_improvement': self._calculate_energy_improvement(universe_enhanced.energy_history),
                'compression_count': len(observations['natural_compressions']),
                'migration_count': len(observations['natural_migrations']),
                'computation_time': end_time - start_time,
                'universe': universe_enhanced  # Save universe object for later use
            }

            emergence_results.append(individual_result)

            print(f"{individual_id} completed:")
            print(f"  Computation time: {individual_result['computation_time']:.1f} seconds")
            print(f"  Energy improvement: {individual_result['energy_improvement']:.1f}%")
            print(f"  Compressions observed: {individual_result['compression_count']}")
            print(f"  Migrations observed: {individual_result['migration_count']}")

        self.results['pure_emergence'] = emergence_results
        self._analyze_emergence_results(emergence_results)
        excel_file = self.save_to_excel()
        return emergence_results

    def _record_excel_data(self, individual_id, observations, universe):
        """Record compression and migration data to excel_data container.

        Args:
            individual_id (str): Individual identifier.
            observations (dict): Observed emergence phenomena dictionary.
            universe (CognitiveUniverseEnhanced): Universe object.
        """
        # Record concept compressions
        for compression in observations['natural_compressions']:
            self.excel_data['compressions'].append({
                'Individual ID': individual_id,
                'Center Node': compression['center'],
                'Related Node Count': len(compression['related_nodes']),
                'Related Nodes': ', '.join(compression['related_nodes']),
                'Energy Synergy': compression.get('energy_synergy', 0),
                'Cluster Cohesion': compression.get('cohesion', 0),
                'Emergence Strength': compression.get('emergence_strength', 0),
                'Detection Iteration': compression.get('detection_iteration', 0),
                'Current Network Energy': universe.calculate_network_energy(),
                'Timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })

        # Record principle migrations
        for migration in observations['natural_migrations']:
            self.excel_data['migrations'].append({
                'Individual ID': individual_id,
                'Principle Node': migration['principle_node'],
                'Start Node': migration['from_node'],
                'Target Node': migration['to_node'],
                'Migration Path': ' -> '.join(migration.get('path', [])),
                'Efficiency Gain': migration.get('efficiency_gain', 0),
                'Domain Span': migration.get('domain_span', 0),
                'Detection Iteration': migration.get('detection_iteration', 0),
                'Current Network Energy': universe.calculate_network_energy(),
                'Timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })

    def _initialize_universe_network(self, universe):
        """Initialize universe network.

        Attempt to use semantic network initialization; fall back to test network on failure.

        Args:
            universe (CognitiveUniverseEnhanced): Universe object.
        """
        try:
            # Use enhanced semantic network initialization, supports num_concepts parameter
            universe.initialize_semantic_network()
        except Exception as e:
            print(f"Semantic network initialization failed: {e}, using test network")
            self._create_test_network(universe)

    def _create_test_network(self, universe):
        """Create test network for quick debugging.

        Args:
            universe (CognitiveUniverseEnhanced): Universe object.
        """
        test_nodes = ["算法", "数据结构", "优化", "递归", "迭代", "抽象", "模式识别",
                      "能量", "学习", "记忆", "思考", "创造", "理解", "应用"]
        universe.G.add_nodes_from(test_nodes)

        import random
        np.random.seed(42)
        random.seed(42)
        # Create more meaningful connections
        connections = [
            ("算法", "数据结构"), ("算法", "优化"), ("递归", "迭代"),
            ("抽象", "模式识别"), ("学习", "记忆"), ("思考", "创造"),
            ("理解", "应用"), ("能量", "优化"), ("算法", "递归")
        ]

        for u, v in connections:
            energy = random.uniform(0.5, 1.5)
            universe.G.add_edge(u, v, weight=energy)

        # Add some random connections
        for i in range(10):
            u, v = random.sample(test_nodes, 2)
            if not universe.G.has_edge(u, v):
                energy = random.uniform(0.8, 2.0)
                universe.G.add_edge(u, v, weight=energy)

        print(f"Test network: {len(test_nodes)} nodes, {universe.G.number_of_edges()} edges")

    def _calculate_energy_improvement(self, energy_history):
        """Calculate energy improvement percentage.

        Args:
            energy_history (list): List of energy history.

        Returns:
            float: Improvement percentage.
        """
        if len(energy_history) < 2:
            return 0.0
        initial = energy_history[0]
        final = energy_history[-1]
        if initial == 0:
            return 0.0
        return ((initial - final) / initial) * 100

    def _analyze_emergence_results(self, results):
        """Analyze emergence experiment results, print statistics.

        Args:
            results (list): List of individual results.
        """
        print("\n" + "=" * 50)
        print("Natural Emergence Experiment Results Analysis")
        print("=" * 50)

        # Basic statistics
        improvements = [r['energy_improvement'] for r in results]
        compressions = [r['compression_count'] for r in results]
        migrations = [r['migration_count'] for r in results]

        print(f"Energy improvement statistics:")
        print(f"  Mean: {np.mean(improvements):.1f}%")
        print(f"  Std Dev: {np.std(improvements):.1f}%")
        print(f"  Range: {min(improvements):.1f}% - {max(improvements):.1f}%")

        print(f"Concept compression emergence:")
        print(f"  Mean: {np.mean(compressions):.1f} events")
        print(f"  Total: {sum(compressions)} events")

        print(f"Principle migration emergence:")
        print(f"  Mean: {np.mean(migrations):.1f} events")
        print(f"  Total: {sum(migrations)} events")

    def visualize_emergence_results(self):
        """Visualize emergence experiment results, generating energy improvement and emergence quantity charts."""
        import matplotlib.pyplot as plt
        import numpy as np

        if 'pure_emergence' not in self.results:
            print("Please run the experiment first!")
            return

        results = self.results['pure_emergence']

        # Create comparison charts
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))

        # 1. Energy improvement comparison
        improvements = [r['energy_improvement'] for r in results]
        individuals = [r['individual_id'] for r in results]

        bars = ax1.bar(individuals, improvements, color=['skyblue', 'lightgreen', 'lightcoral'])
        ax1.set_title('Natural Emergence Group Energy Improvement Comparison')
        ax1.set_ylabel('Energy Improvement (%)')
        ax1.set_xlabel('Individual')

        # Add value labels on bars
        for bar, improvement in zip(bars, improvements):
            height = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width() / 2., height,
                     f'{improvement:.1f}%', ha='center', va='bottom')

        # 2. Emergence phenomenon counts
        compressions = [r['compression_count'] for r in results]
        migrations = [r['migration_count'] for r in results]

        x = np.arange(len(individuals))
        width = 0.35

        ax2.bar(x - width / 2, compressions, width, label='Concept Compression', color='orange')
        ax2.bar(x + width / 2, migrations, width, label='Principle Migration', color='purple')
        ax2.set_title('Emergence Phenomenon Count Comparison')
        ax2.set_ylabel('Number of Events')
        ax2.set_xlabel('Individual')
        ax2.set_xticks(x)
        ax2.set_xticklabels(individuals)
        ax2.legend()

        # 3. Energy convergence curve example
        if results and len(results) > 0 and hasattr(results[0]['universe'], 'energy_history'):
            sample_energy_history = results[0]['universe'].energy_history
            ax3.plot(sample_energy_history, 'b-', alpha=0.7)
            ax3.set_title('Typical Energy Convergence Process')
            ax3.set_xlabel('Iteration')
            ax3.set_ylabel('Average Cognitive Energy')
            ax3.grid(True, alpha=0.3)

        # 4. Network statistics
        if results and len(results) > 0:
            node_counts = [r['universe'].G.number_of_nodes() for r in results]
            edge_counts = [r['universe'].G.number_of_edges() for r in results]

            ax4.bar(individuals, node_counts, alpha=0.6, label='Node Count')
            ax4.bar(individuals, edge_counts, alpha=0.6, label='Edge Count')
            ax4.set_title('Network Scale Statistics')
            ax4.set_ylabel('Count')
            ax4.legend()

        plt.tight_layout()

        fig_dir = "results/emergence/figures"
        os.makedirs(fig_dir, exist_ok=True)
        plt.savefig(os.path.join(fig_dir, f"emergence_visualization_{self.timestamp}.png"),
                    dpi=300, bbox_inches='tight')
        plt.show()


def main_fixed():
    """Fixed version main function, run emergence experiment and visualize."""
    study = EmergenceStudyFixed()

    # Run pure emergence experiment
    emergence_results = study.run_pure_emergence_experiment(
        num_individuals=2,
        max_iterations=8000  # Reduce iterations for quick testing
    )

    # Visualize results
    study.visualize_emergence_results()

    return study


if __name__ == "__main__":
    main_fixed()