"""
Cognitive Graph Experiment Platform Main Entry.

Provides an experiment management class that supports running different cognitive models
(random network, Q-learning, preset algorithms, natural emergence) and comparative analysis.
"""

import sys
import os
from experiments.emergence_study_fixed import EmergenceStudyFixed
from core.semantic_network import SemanticConceptNetwork
from experiments.population_study import run_semantic_enhanced_experiment, demo_semantic_network
from utils.visualization import *

# Import baseline models
from models.random_network import RandomNetworkModel
from models.qlearning_enhanced import EnhancedQLearningCognitiveGraph

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))


class CognitiveGraphExperimentManager:
    """
    Cognitive graph experiment manager.

    Responsible for running different types of cognitive model experiments, including:
        - Random network model (non-intelligent baseline)
        - Enhanced Q-learning model (traditional AI approach)
        - Preset algorithm model (simulating traditional cognitive computing paradigm)
        - Natural emergence model (new paradigm based on energy minimization)

    Also provides comparative analysis functionality.
    """

    def __init__(self):
        """Initialize the experiment manager, creating an empty results dictionary."""
        self.experiment_results = {}

    def run_random_network_model(self, num_nodes=51, max_iterations=10000):
        """
        Run the random network baseline model.

        Parameters
        ----------
        num_nodes : int, optional
            Number of network nodes, default 51.
        max_iterations : int, optional
            Maximum number of iterations, default 10000.

        Returns
        -------
        dict
            Experiment result dictionary containing 'improvement' and other keys.
        """
        print("\n" + "=" * 50)
        print("Random Network Baseline Model (Non-Intelligent Mechanism)")
        print("=" * 50)

        base_params = {
            'forgetting_rate': 0.002,
            'base_learning_rate': 0.85,
            'hard_traversal_bias': 0.0,
            'soft_traversal_bias': 0.0,
            'compression_bias': 0.0,
            'migration_bias': 0.0,
            'learning_rate_variation': 0.1
        }

        random_model = RandomNetworkModel(base_params)
        result = random_model.run_experiment(num_nodes=num_nodes, max_iterations=max_iterations)

        random_model.visualize_graph("Random Network Model")

        self.experiment_results['random_network'] = result
        return result

    def run_qlearning_model(self, num_nodes=51, max_iterations=10000):
        """
        Run the enhanced Q-learning baseline model.

        Parameters
        ----------
        num_nodes : int, optional
            Number of network nodes, default 51.
        max_iterations : int, optional
            Maximum number of iterations, default 10000.

        Returns
        -------
        dict
            Experiment result dictionary containing 'improvement', 'q_table_stats', and other keys.
        """
        print("\n" + "=" * 50)
        print("Enhanced Q-learning Baseline Model (Traditional RL + Improvements)")
        print("=" * 50)

        base_params = {
            'forgetting_rate': 0.002,
            'base_learning_rate': 0.85,
            'hard_traversal_bias': 0.0,
            'soft_traversal_bias': 0.0,
            'compression_bias': 0.0,
            'migration_bias': 0.0,
            'learning_rate_variation': 0.1
        }

        qlearning_model = EnhancedQLearningCognitiveGraph(base_params)
        result = qlearning_model.run_experiment(num_nodes=num_nodes, max_iterations=max_iterations)

        qlearning_model.visualize_graph("Enhanced Q-learning Model")

        if num_nodes >= 5 and 'path_examples' in result and result['path_examples']:
            print("\nOptimal path examples:")
            for i, example in enumerate(result['path_examples'][:2]):
                print(f"  Example {i + 1}: {example['start']} -> {example['end']}")
                print(f"    Path: {example['path']}")
                print(f"    Cumulative Q-value: {example['q_value']:.3f}")

        if 'q_table_stats' in result:
            q_stats = result['q_table_stats']
            print(f"\nQ-table statistics:")
            print(f"  Size: {q_stats['size']}")
            print(f"  Sparsity: {q_stats['sparsity']:.3f}")
            print(f"  Non-zero entries: {q_stats['non_zero_entries']}")
            print(f"  Mean: {q_stats['mean']:.3f}")
            print(f"  Positive ratio: {q_stats['positive_ratio']:.3f}")

        self.experiment_results['qlearning'] = result
        return result

    def run_preset_algorithm_model(self, num_concepts=None):
        """
        Run the traditional mechanism design model (preset algorithm).

        Parameters
        ----------
        num_concepts : int, optional
            Number of concepts; if None, use default scale.

        Returns
        -------
        list
            List of experiment results for each individual.
        """
        print("\n" + "=" * 50)
        print("Traditional Mechanism Design Model (Preset Algorithm)")
        if num_concepts:
            print(f"Using {num_concepts} concepts")
        print("=" * 50)

        results = run_semantic_enhanced_experiment(
            num_individuals=2,
            max_iterations=10000,
            num_concepts=num_concepts
        )

        if results and len(results) > 0:
            first_individual = results[0]
            if 'graph' in first_individual:
                first_individual['graph'].visualize_graph("Traditional Mechanism Model")

        self.experiment_results['traditional'] = results
        return results

    def run_natural_emergence_model(self, num_individuals=2, max_iterations=10000, num_concepts=None):
        """
        Run the pure energy model to observe natural emergence phenomena.

        Parameters
        ----------
        num_individuals : int, optional
            Number of individuals, default 2.
        max_iterations : int, optional
            Maximum number of iterations, default 10000.
        num_concepts : int, optional
            Number of concepts; if None, use default scale.

        Returns
        -------
        list
            List of experiment results for each individual.
        """
        print("\n" + "=" * 50)
        print("Pure Energy Model - Natural Emergence Observation")
        if num_concepts:
            print(f"Using {num_concepts} concepts")
        print("=" * 50)

        study = EmergenceStudyFixed()
        results = study.run_pure_emergence_experiment(
            num_individuals=num_individuals,
            max_iterations=max_iterations,
            num_concepts=num_concepts
        )

        study.visualize_emergence_results()

        self.experiment_results['pure_emergence'] = results
        return results

    def run_benchmark_comparison(self, num_nodes=51, max_iterations=10000, num_concepts=None):
        """
        Run all baseline model comparison experiments.

        Parameters
        ----------
        num_nodes : int, optional
            Number of network nodes for random and Q-learning models, default 51.
        max_iterations : int, optional
            Maximum number of iterations, default 10000.
        num_concepts : int, optional
            Number of concepts for semantic models; if None, use default scale.

        Returns
        -------
        dict
            Dictionary containing results for each model, keyed by model name.
        """
        print("\n" + "=" * 60)
        print("Baseline Model Comparison Experiment")
        if num_concepts:
            print(f"Semantic models using {num_concepts} concepts")
        print("=" * 60)

        results = {}

        print("\n1. Running random network model...")
        random_result = self.run_random_network_model(num_nodes, max_iterations)
        results['random'] = random_result

        print("\n2. Running enhanced Q-learning model...")
        qlearning_result = self.run_qlearning_model(num_nodes, max_iterations)
        results['qlearning'] = qlearning_result

        print("\n3. Running traditional mechanism model...")
        from experiments.population_study import run_semantic_enhanced_experiment
        traditional_results = run_semantic_enhanced_experiment(
            num_individuals=1,
            max_iterations=max_iterations,
            num_concepts=num_concepts
        )
        if traditional_results:
            results['traditional'] = traditional_results[0]

        print("\n4. Running natural emergence model...")
        study = EmergenceStudyFixed()
        emergence_results = study.run_pure_emergence_experiment(
            num_individuals=1,
            max_iterations=max_iterations,
            num_concepts=num_concepts
        )
        if emergence_results:
            results['emergence'] = emergence_results[0]

        self._compare_benchmark_results(results)
        self.experiment_results['benchmark_comparison'] = results
        return results

    def _compare_benchmark_results(self, results):
        """
        Internal method: print baseline model performance comparison table and generate comparison charts.

        Parameters
        ----------
        results : dict
            Dictionary of results for each model.
        """
        print("\n" + "=" * 60)
        print("Baseline Model Performance Comparison")
        print("=" * 60)

        print(f"{'Model Type':<20} {'Energy Reduction (%)':<15} {'Iterations':<12} {'Nodes':<10}")
        print("-" * 60)

        for model_type, result in results.items():
            if isinstance(result, dict) and 'improvement' in result:
                improvement = result['improvement']
                iterations = result.get('iterations', 'N/A')
                nodes = result.get('num_nodes', 'N/A')
                print(f"{model_type:<20} {improvement:<15.1f} {iterations:<12} {nodes:<10}")
            elif isinstance(result, list) and len(result) > 0 and 'improvement' in result[0]:
                improvement = result[0]['improvement']
                print(f"{model_type:<20} {improvement:<15.1f} {'N/A':<12} {'N/A':<10}")

        print("-" * 60)
        self._plot_benchmark_comparison(results)

    def _plot_benchmark_comparison(self, results):
        """
        Internal method: draw a bar chart comparing baseline model performance.

        Parameters
        ----------
        results : dict
            Dictionary of results for each model.
        """
        try:
            import matplotlib.pyplot as plt

            model_names = []
            improvements = []
            colors = []

            color_map = {
                'random': 'gray',
                'qlearning': 'blue',
                'traditional': 'green',
                'emergence': 'red'
            }

            for model_type, result in results.items():
                if model_type in color_map:
                    if isinstance(result, dict) and 'improvement' in result:
                        model_names.append(model_type)
                        improvements.append(result['improvement'])
                        colors.append(color_map[model_type])
                    elif isinstance(result, list) and len(result) > 0 and 'improvement' in result[0]:
                        model_names.append(model_type)
                        improvements.append(result[0]['improvement'])
                        colors.append(color_map[model_type])

            if not model_names:
                return

            plt.figure(figsize=(10, 6))
            bars = plt.bar(model_names, improvements, color=colors, alpha=0.7)

            for bar, improvement in zip(bars, improvements):
                plt.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.5,
                         f'{improvement:.1f}%', ha='center', va='bottom')

            plt.xlabel('Model Type')
            plt.ylabel('Energy Reduction (%)')
            plt.title('Baseline Model Performance Comparison')
            plt.ylim(0, max(improvements) * 1.2 if improvements else 50)
            plt.grid(True, alpha=0.3)

            from matplotlib.patches import Patch
            legend_elements = [Patch(facecolor=color, label=name, alpha=0.7)
                               for name, color in color_map.items() if name in model_names]
            plt.legend(handles=legend_elements, loc='upper right')

            plt.tight_layout()
            plt.show()

            os.makedirs('results/comparison', exist_ok=True)
            plt.savefig('results/comparison/benchmark_comparison.png', dpi=300, bbox_inches='tight')
            print(f"Comparison chart saved to: results/comparison/benchmark_comparison.png")

        except Exception as e:
            print(f"Error drawing comparison chart: {e}")

    def run_complete_study(self, num_concepts=None):
        """
        Run a complete study, including benchmark comparison and main model comparison.

        Parameters
        ----------
        num_concepts : int, optional
            Number of concepts.

        Returns
        -------
        tuple
            Result lists for traditional and emergence models.
        """
        print("\n" + "=" * 50)
        print("Complete Cognitive Graph Study")
        if num_concepts:
            print(f"Using {num_concepts} concepts")
        print("=" * 50)

        print("Phase 1: Baseline Model Comparison")
        benchmark_results = self.run_benchmark_comparison(num_nodes=51, max_iterations=10000, num_concepts=num_concepts)

        print("\nPhase 2: Main Model Comparison")
        traditional_results = self.run_preset_algorithm_model(num_concepts=num_concepts)
        emergence_results = self.run_natural_emergence_model(num_concepts=num_concepts)

        self._compare_results(traditional_results, emergence_results)
        return traditional_results, emergence_results

    def _compare_results(self, traditional, emergence):
        """
        Internal method: simple comparison of traditional and emergence model results.

        Parameters
        ----------
        traditional : list
            List of traditional model results.
        emergence : list
            List of emergence model results.
        """
        print("\n" + "=" * 50)
        print("Model Comparison Results")
        print("=" * 50)

        if traditional and emergence:
            trad_improve = sum(r['improvement'] for r in traditional) / len(traditional)
            emerge_improve = sum(r.get('energy_improvement', 0) for r in emergence) / len(emergence)

            print(f"Traditional model average improvement: {trad_improve:.1f}%")
            print(f"Emergence model average improvement: {emerge_improve:.1f}%")

    def quick_demo(self, num_concepts=None):
        """
        Quick demo mode: run a semantic network demonstration and a small emergence experiment.

        Parameters
        ----------
        num_concepts : int, optional
            Number of concepts.

        Returns
        -------
        list
            Emergence model experiment results.
        """
        print("\n" + "=" * 50)
        print("Quick Demo Mode")
        if num_concepts:
            print(f"Using {num_concepts} concepts")
        print("=" * 50)

        demo_semantic_network(num_concepts=num_concepts)

        return self.run_natural_emergence_model(
            num_individuals=1,
            max_iterations=2000,
            num_concepts=num_concepts
        )

    def show_summary(self):
        """
        Display summary information of experiments that have been run.
        """
        print("\n" + "=" * 50)
        print("Experiment Summary")
        print("=" * 50)

        for exp_type, results in self.experiment_results.items():
            if results:
                if isinstance(results, dict):
                    print(f"{exp_type}: 1 experiment")
                    if 'improvement' in results:
                        print(f"  Energy improvement: {results['improvement']:.1f}%")
                elif isinstance(results, list):
                    print(f"{exp_type}: {len(results)} experiments")
                else:
                    print(f"{exp_type}: result data")


def check_dependencies():
    """
    Check whether necessary dependency libraries are installed.

    Returns
    -------
    bool
        True if all dependencies exist, otherwise False.
    """
    required_libs = ['jieba', 'networkx', 'matplotlib', 'numpy']
    missing_libs = []

    for lib in required_libs:
        try:
            __import__(lib)
        except ImportError:
            missing_libs.append(lib)

    if missing_libs:
        print(f"❌ Missing dependency libraries: {', '.join(missing_libs)}")
        print("Please install: pip install " + " ".join(missing_libs))
        return False

    print("✅ All dependencies loaded successfully")
    return True


def get_concept_count_input():
    """
    Interactively get the number of concepts chosen by the user.

    Returns
    -------
    int
        Number of concepts chosen by the user.
    """
    print("\nSelect number of concepts:")
    print("1. 51 concepts (default)")
    print("2. 71 concepts")
    print("3. 120 concepts (full)")
    print("4. Custom number of concepts")

    choice = input("Please choose (1-4, default 1): ").strip() or "1"

    if choice == "1":
        return 51
    elif choice == "2":
        return 71
    elif choice == "3":
        return 120
    elif choice == "4":
        custom_input = input("Enter custom number of concepts (1-120, default 51): ").strip()
        if custom_input == "":
            return 51
        try:
            num_concepts = int(custom_input)
            if num_concepts < 1:
                print("Number of concepts must be greater than 0, using default 51")
                return 51
            elif num_concepts > 120:
                print("Maximum number of concepts is 120, using 120")
                return 120
            return num_concepts
        except ValueError:
            print("Invalid input, using default 51")
            return 51
    else:
        print("Invalid input, using default 51")
        return 51


def main():
    """
    Main function: provides an interactive menu to run the selected experiment.
    """
    if not check_dependencies():
        return

    print("\n=== Cognitive Graph Model Experiment Platform ===")
    print("Select run mode:")
    print("1. Random Network Baseline Model (Non-Intelligent)")
    print("2. Enhanced Q-learning Baseline Model (Traditional RL + Improvements)")
    print("3. Traditional Mechanism Design Model (Preset Algorithm)")
    print("4. Pure Energy Emergence Model (Natural Emergence)")
    print("5. Baseline Model Comparison Experiment")
    print("6. Complete Comparative Study")
    print("7. Semantic Network Demonstration")
    print("8. Quick Demo")
    print("9. Experiment Summary")

    manager = CognitiveGraphExperimentManager()

    try:
        choice = input("\nSelect mode (1-9): ").strip()

        if choice == "1":
            num_nodes = input("Number of network nodes (default 51): ").strip() or "51"
            max_iterations = input("Number of iterations (default 3000): ").strip() or "3000"
            manager.run_random_network_model(
                num_nodes=int(num_nodes),
                max_iterations=int(max_iterations)
            )
        elif choice == "2":
            num_nodes = input("Number of network nodes (default 51): ").strip() or "51"
            max_iterations = input("Number of iterations (default 5000): ").strip() or "5000"
            manager.run_qlearning_model(
                num_nodes=int(num_nodes),
                max_iterations=int(max_iterations)
            )
        elif choice == "3":
            num_concepts = get_concept_count_input()
            manager.run_preset_algorithm_model(num_concepts=num_concepts)
        elif choice == "4":
            num_individuals = input("Number of individuals (default 2): ").strip() or "2"
            max_iterations = input("Number of iterations (default 8000): ").strip() or "8000"
            num_concepts = get_concept_count_input()
            manager.run_natural_emergence_model(
                num_individuals=int(num_individuals),
                max_iterations=int(max_iterations),
                num_concepts=num_concepts
            )
        elif choice == "5":
            num_nodes = input("Number of network nodes (default 51): ").strip() or "51"
            max_iterations = input("Number of iterations (default 3000): ").strip() or "3000"
            print("\nSemantic model concept count setting (random and Q-learning models are not affected):")
            num_concepts = get_concept_count_input()
            manager.run_benchmark_comparison(
                num_nodes=int(num_nodes),
                max_iterations=int(max_iterations),
                num_concepts=num_concepts
            )
        elif choice == "6":
            num_concepts = get_concept_count_input()
            manager.run_complete_study(num_concepts=num_concepts)
        elif choice == "7":
            num_concepts = get_concept_count_input()
            demo_semantic_network(num_concepts=num_concepts)
        elif choice == "8":
            num_concepts = get_concept_count_input()
            manager.quick_demo(num_concepts=num_concepts)
        elif choice == "9":
            manager.show_summary()
        else:
            print("Invalid choice, running baseline model comparison")
            manager.run_benchmark_comparison()

    except KeyboardInterrupt:
        print("\n\nProgram interrupted by user")
    except Exception as e:
        print(f"\nProgram error: {e}")


if __name__ == "__main__":
    main()