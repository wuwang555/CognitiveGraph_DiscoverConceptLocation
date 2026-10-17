"""
batch_experiments.py
Batch experiment script for cognitive graph models
Runs comparison experiments across different concept scales for all models systematically
"""

import sys
import os
import time
import json
from datetime import datetime
import pandas as pd
from pathlib import Path
# Import experiment manager
try:
    from main import CognitiveGraphExperimentManager
    print("✅ Successfully imported experiment manager")
except ImportError as e:
    print(f"❌ Failed to import experiment manager: {e}")
    sys.exit(1)


class BatchExperimentRunner:
    """Batch experiment runner, manages comparison experiments across multiple scales and models.

    This class is responsible for configuring, running, and saving experimental data for all models,
    and generating comparison charts.

    Attributes:
        manager (CognitiveGraphExperimentManager): Experiment manager instance.
        output_dir (Path): Output directory for results.
        config (dict): Experiment configuration parameters.
        results (list): List of all experimental results.
        summary (dict): Summary of results grouped by scale.
    """

    def __init__(self, output_dir="../../results/batch_experiments"):
        """Initialize batch runner.

        Args:
            output_dir (str): Directory to save results, default is "../../results/batch_experiments".
        """
        self.manager = CognitiveGraphExperimentManager()
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Experiment configuration
        self.config = {
            "iterations": 10000,  # Iterations per run
            "repetitions": 1,  # Repetitions per configuration (reduced randomness)
            "models": ["random", "qlearning", "traditional", "emergence"],
            "scales": [51, 71, 91, 111],  # Concept scales
            "timestamp": datetime.now().strftime("%Y%m%d_%H%M%S")
        }

        # Result storage
        self.results = []
        self.summary = {}

    def run_single_experiment(self, model_type, scale):
        """Run a single experiment.

        Args:
            model_type (str): Model type, one of "random", "qlearning", "traditional", "emergence".
            scale (int): Concept scale (number of nodes).

        Returns:
            dict or None: Dictionary of experimental metrics, None if failed.
        """
        print(f"\n{'=' * 60}")
        print(f"Running experiment: {model_type.upper()} model | Concept scale: {scale}")
        print('=' * 60)

        start_time = time.time()

        try:
            if model_type == "random":
                result = self.manager.run_random_network_model(
                    num_nodes=scale,
                    max_iterations=self.config["iterations"]
                )
            elif model_type == "qlearning":
                result = self.manager.run_qlearning_model(
                    num_nodes=scale,
                    max_iterations=self.config["iterations"]
                )
            elif model_type == "traditional":
                result = self.manager.run_preset_algorithm_model(
                    num_concepts=scale
                )
                # Handle list format results
                if isinstance(result, list) and len(result) > 0:
                    result = result[0]
            elif model_type == "emergence":
                result = self.manager.run_natural_emergence_model(
                    num_individuals=1,  # For speed, run only 1 individual
                    max_iterations=self.config["iterations"],
                    num_concepts=scale
                )
                # Handle list format results
                if isinstance(result, list) and len(result) > 0:
                    result = result[0]
            else:
                print(f"❌ Unknown model type: {model_type}")
                return None

            elapsed_time = time.time() - start_time

            # Extract key metrics
            metrics = self._extract_metrics(model_type, result, scale, elapsed_time)

            print(f"✅ Experiment completed | Time: {elapsed_time:.1f}s | Energy improvement: {metrics.get('improvement', 'N/A')}%")

            return metrics

        except Exception as e:
            print(f"❌ Experiment failed: {e}")
            import traceback
            traceback.print_exc()
            return None

    def _extract_metrics(self, model_type, result, scale, elapsed_time):
        """Extract key metrics from result.

        Args:
            model_type (str): Model type.
            result (dict): Result dictionary returned by experiment.
            scale (int): Concept scale.
            elapsed_time (float): Elapsed time (seconds).

        Returns:
            dict: Extracted metrics dictionary.
        """
        metrics = {
            "model": model_type,
            "scale": scale,
            "elapsed_time": elapsed_time,
            "iterations": self.config["iterations"]
        }

        if not result:
            return metrics

        # Common metric extraction
        if isinstance(result, dict):
            # Energy improvement metrics
            if 'improvement' in result:
                metrics["improvement"] = result['improvement']
            elif 'energy_improvement' in result:
                metrics["improvement"] = result['energy_improvement']
            elif 'improvement_percent' in result:
                metrics["improvement"] = result['improvement_percent']

            # Concept compression
            if 'compression_centers' in result:
                metrics["compression_centers"] = result['compression_centers']
            elif 'compression_count' in result:
                metrics["compression_centers"] = result['compression_count']

            # Principle migration
            if 'migration_bridges' in result:
                metrics["migration_bridges"] = result['migration_bridges']
            elif 'migration_count' in result:
                metrics["migration_bridges"] = result['migration_count']

            # Network statistics
            if 'network_stats' in result:
                stats = result['network_stats']
                metrics.update({
                    "num_nodes": stats.get('num_nodes', scale),
                    "num_edges": stats.get('num_edges', 0),
                    "avg_energy": stats.get('avg_energy', 0)
                })

        # Model-specific metrics
        if model_type == "qlearning" and isinstance(result, dict):
            if 'q_table_stats' in result:
                q_stats = result['q_table_stats']
                metrics.update({
                    "q_table_sparsity": q_stats.get('sparsity', 0),
                    "q_table_non_zero": q_stats.get('non_zero_entries', 0)
                })
        elif model_type == "traditional" and isinstance(result, dict):
            # Traditional model may have cognitive state statistics
            if 'state_stats' in result:
                state_stats = result['state_stats']
                metrics["exploration_ratio"] = state_stats.get('exploration', 0)
                metrics["inspiration_ratio"] = state_stats.get('inspiration', 0)
        elif model_type == "emergence" and isinstance(result, dict):
            # Emergence model specific metrics
            metrics.update({
                "compression_frequency": result.get('compression_frequency', 0),
                "migration_frequency": result.get('migration_frequency', 0)
            })

        return metrics

    def run_full_batch(self):
        """Run full batch experiment (all scales × all models)."""
        print("\n" + "=" * 80)
        print("Starting full batch experiment")
        print(f"Configuration: {self.config['scales']} scales × {self.config['models']} models")
        print(f"Iterations: {self.config['iterations']}")
        print("=" * 80)

        total_experiments = len(self.config["scales"]) * len(self.config["models"])
        completed = 0

        for scale in self.config["scales"]:
            scale_results = {}

            for model in self.config["models"]:
                # Run experiment
                metrics = self.run_single_experiment(model, scale)

                if metrics:
                    # Save result
                    self.results.append(metrics)
                    scale_results[model] = metrics

                    # Update progress
                    completed += 1
                    progress = (completed / total_experiments) * 100
                    print(f"\n📊 Progress: {completed}/{total_experiments} ({progress:.1f}%)")

            # Save summary for this scale
            self.summary[scale] = scale_results

        # Save all results
        self.save_results()

        print("\n" + "=" * 80)
        print("🎉 All batch experiments completed!")
        print("=" * 80)

        # Display summary
        self.display_summary()

    def save_results(self):
        """Save experiment results to CSV and JSON files."""
        timestamp = self.config["timestamp"]

        # Save detailed results to CSV
        df_results = pd.DataFrame(self.results)
        csv_path = self.output_dir / f"detailed_results_{timestamp}.csv"
        df_results.to_csv(csv_path, index=False, encoding='utf-8-sig')

        # Save summary to JSON
        summary_path = self.output_dir / f"summary_{timestamp}.json"
        with open(summary_path, 'w', encoding='utf-8') as f:
            # Convert non-serializable objects
            json_ready = {}
            for scale, models in self.summary.items():
                json_ready[str(scale)] = {}
                for model, metrics in models.items():
                    json_ready[str(scale)][model] = {
                        k: (float(v) if isinstance(v, (int, float)) else str(v))
                        for k, v in metrics.items()
                    }

            json.dump(json_ready, f, ensure_ascii=False, indent=2)

        # Save configuration
        config_path = self.output_dir / f"config_{timestamp}.json"
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, ensure_ascii=False, indent=2)

        print(f"\n📁 Results saved:")
        print(f"  Detailed results: {csv_path}")
        print(f"  Experiment summary: {summary_path}")
        print(f"  Configuration: {config_path}")

        return csv_path, summary_path

    def display_summary(self):
        """Display experiment results summary table in console."""
        print("\n" + "=" * 80)
        print("Experiment Results Summary")
        print("=" * 80)

        # Create summary table
        summary_data = []

        for scale in self.config["scales"]:
            scale_row = {"Concept Scale": scale}

            if scale in self.summary:
                for model in self.config["models"]:
                    if model in self.summary[scale]:
                        metrics = self.summary[scale][model]
                        improvement = metrics.get('improvement', 0)

                        # Add performance metrics
                        scale_row[f"{model} Energy Improvement (%)"] = f"{improvement:.1f}%" if isinstance(improvement, (int, float)) else improvement

                        # Add special metrics
                        if model == "emergence":
                            compression = metrics.get('compression_centers', 0)
                            migration = metrics.get('migration_bridges', 0)
                            scale_row["Emergence Compressions"] = compression
                            scale_row["Emergence Migrations"] = migration

            summary_data.append(scale_row)

        # Display table
        df_summary = pd.DataFrame(summary_data)
        print(df_summary.to_string(index=False))

        # Calculate statistics
        print("\n" + "=" * 80)
        print("Key Statistics")
        print("=" * 80)

        # 1. Average performance of each model across scales
        print("\n📈 Model performance:")
        for model in self.config["models"]:
            improvements = []
            for scale in self.config["scales"]:
                if scale in self.summary and model in self.summary[scale]:
                    imp = self.summary[scale][model].get('improvement', 0)
                    if isinstance(imp, (int, float)):
                        improvements.append(imp)

            if improvements:
                avg_imp = sum(improvements) / len(improvements)
                print(f"  {model:15s}: average improvement {avg_imp:.1f}% (range: {min(improvements):.1f}%-{max(improvements):.1f}%)")

        # 2. Scale effect analysis
        print("\n📊 Scale effect analysis:")
        for model in ["traditional", "emergence"]:
            improvements_by_scale = {}
            for scale in self.config["scales"]:
                if scale in self.summary and model in self.summary[scale]:
                    imp = self.summary[scale][model].get('improvement', 0)
                    if isinstance(imp, (int, float)):
                        improvements_by_scale[scale] = imp

            if improvements_by_scale:
                print(f"  {model} model:")
                for scale, imp in sorted(improvements_by_scale.items()):
                    print(f"    {scale} concepts: {imp:.1f}%")

    def create_comparison_charts(self):
        """Create performance comparison and scale effect charts (using matplotlib)."""
        try:
            import matplotlib.pyplot as plt
            import numpy as np

            print("\n📊 Generating comparison charts...")

            # Prepare data
            scales = self.config["scales"]
            models = self.config["models"]

            # Performance comparison bar chart
            fig1, ax1 = plt.subplots(figsize=(12, 8))

            bar_width = 0.2
            x = np.arange(len(scales))

            model_colors = {
                "random": "#999999",
                "qlearning": "#4C72B0",
                "traditional": "#55A868",
                "emergence": "#C44E52"
            }

            model_labels = {
                "random": "Random Network",
                "qlearning": "Enhanced Q-learning",
                "traditional": "Traditional Mechanism Design",
                "emergence": "Natural Emergence"
            }

            for i, model in enumerate(models):
                improvements = []
                for scale in scales:
                    if scale in self.summary and model in self.summary[scale]:
                        imp = self.summary[scale][model].get('improvement', 0)
                        improvements.append(float(imp) if isinstance(imp, (int, float)) else 0)
                    else:
                        improvements.append(0)

                ax1.bar(x + i * bar_width, improvements, bar_width,
                        label=model_labels[model], color=model_colors[model], alpha=0.8)

            ax1.set_xlabel('Concept Scale', fontsize=12)
            ax1.set_ylabel('Energy Improvement (%)', fontsize=12)
            ax1.set_title('Performance Comparison of Different Models at Various Concept Scales', fontsize=14,
                          fontweight='bold')
            ax1.set_xticks(x + bar_width * 1.5)
            ax1.set_xticklabels([f"Scale {s}" for s in scales])
            ax1.legend()
            ax1.grid(True, alpha=0.3)

            plt.tight_layout()
            chart_path1 = self.output_dir / f"performance_comparison_{self.config['timestamp']}.png"
            plt.savefig(chart_path1, dpi=300)
            print(f"✅ Performance comparison chart saved: {chart_path1}")

            # Scale effect line chart
            fig2, ax2 = plt.subplots(figsize=(10, 6))

            for model in ["traditional", "emergence"]:
                scales_list = []
                improvements_list = []

                for scale in scales:
                    if scale in self.summary and model in self.summary[scale]:
                        imp = self.summary[scale][model].get('improvement', 0)
                        if isinstance(imp, (int, float)):
                            scales_list.append(scale)
                            improvements_list.append(imp)

                if scales_list and improvements_list:
                    ax2.plot(scales_list, improvements_list,
                             marker='o', linewidth=2, markersize=8,
                             label=model_labels[model])

            ax2.set_xlabel('Concept Scale', fontsize=12)
            ax2.set_ylabel('Energy Improvement (%)', fontsize=12)
            ax2.set_title('Scale Effect Analysis of Cognitive Models', fontsize=14, fontweight='bold')
            ax2.legend()
            ax2.grid(True, alpha=0.3)

            plt.tight_layout()
            chart_path2 = self.output_dir / f"scale_effect_{self.config['timestamp']}.png"
            plt.savefig(chart_path2, dpi=300)
            print(f"✅ Scale effect chart saved: {chart_path2}")

            plt.show()

        except ImportError:
            print("⚠️  Matplotlib not installed, skipping chart generation")
            print("   Please run: pip install matplotlib")
        except Exception as e:
            print(f"❌ Error generating charts: {e}")

    def create_comparison_charts_zh(self):
        """Create performance comparison and scale effect charts (using matplotlib) with Chinese labels."""
        try:
            import matplotlib.pyplot as plt
            import numpy as np

            print("\n📊 Generating comparison charts...")

            # Prepare data
            scales = self.config["scales"]
            models = self.config["models"]

            # Performance comparison bar chart
            fig1, ax1 = plt.subplots(figsize=(12, 8))

            bar_width = 0.2
            x = np.arange(len(scales))

            model_colors = {
                "random": "#999999",
                "qlearning": "#4C72B0",
                "traditional": "#55A868",
                "emergence": "#C44E52"
            }

            model_labels = {
                "random": "Random Network",
                "qlearning": "Enhanced Q-learning",
                "traditional": "Traditional Mechanism Design",
                "emergence": "Natural Emergence"
            }

            for i, model in enumerate(models):
                improvements = []
                for scale in scales:
                    if scale in self.summary and model in self.summary[scale]:
                        imp = self.summary[scale][model].get('improvement', 0)
                        improvements.append(float(imp) if isinstance(imp, (int, float)) else 0)
                    else:
                        improvements.append(0)

                ax1.bar(x + i * bar_width, improvements, bar_width,
                        label=model_labels[model], color=model_colors[model], alpha=0.8)

            ax1.set_xlabel('Concept Scale', fontsize=12)
            ax1.set_ylabel('Energy Improvement (%)', fontsize=12)
            ax1.set_title('Performance Comparison of Different Models at Various Concept Scales', fontsize=14,
                          fontweight='bold')
            ax1.set_xticks(x + bar_width * 1.5)
            ax1.set_xticklabels([f"Scale {s}" for s in scales])
            ax1.legend()
            ax1.grid(True, alpha=0.3)

            plt.tight_layout()
            chart_path1 = self.output_dir / f"performance_comparison_{self.config['timestamp']}.png"
            plt.savefig(chart_path1, dpi=300)
            print(f"✅ Performance comparison chart saved: {chart_path1}")

            # Scale effect line chart
            fig2, ax2 = plt.subplots(figsize=(10, 6))

            for model in ["traditional", "emergence"]:
                scales_list = []
                improvements_list = []

                for scale in scales:
                    if scale in self.summary and model in self.summary[scale]:
                        imp = self.summary[scale][model].get('improvement', 0)
                        if isinstance(imp, (int, float)):
                            scales_list.append(scale)
                            improvements_list.append(imp)

                if scales_list and improvements_list:
                    ax2.plot(scales_list, improvements_list,
                             marker='o', linewidth=2, markersize=8,
                             label=model_labels[model])

            ax2.set_xlabel('Concept Scale', fontsize=12)
            ax2.set_ylabel('Energy Improvement (%)', fontsize=12)
            ax2.set_title('Scale Effect Analysis of Cognitive Models', fontsize=14, fontweight='bold')
            ax2.legend()
            ax2.grid(True, alpha=0.3)

            plt.tight_layout()
            chart_path2 = self.output_dir / f"scale_effect_{self.config['timestamp']}.png"
            plt.savefig(chart_path2, dpi=300)
            print(f"✅ Scale effect chart saved: {chart_path2}")

            plt.show()

        except ImportError:
            print("⚠️  Matplotlib not installed, skipping chart generation")
            print("   Please run: pip install matplotlib")
        except Exception as e:
            print(f"❌ Error generating charts: {e}")

def run_specific_combination():
    """Run a specific combination experiment (for debugging)."""
    runner = BatchExperimentRunner()

    # Test single combination
    print("Testing single experiment combination...")
    metrics = runner.run_single_experiment("emergence", 91)

    if metrics:
        print("\nTest results:")
        for key, value in metrics.items():
            print(f"  {key}: {value}")


def main():
    """Main function, provides interactive menu for selecting run mode."""
    print("\n" + "=" * 80)
    print("Cognitive Graph Model Batch Experiment Platform")
    print("=" * 80)

    print("\nSelect run mode:")
    print("1. Run full batch experiment (all scales × all models)")
    print("2. Run specific scale experiment")
    print("3. Run specific model experiment")
    print("4. Run only emergence model across scales")
    print("5. Test single experiment combination")

    choice = input("\nSelect mode (1-5): ").strip()

    runner = BatchExperimentRunner()

    if choice == "1":
        # Full batch
        runner.run_full_batch()
        runner.create_comparison_charts()

    elif choice == "2":
        # Specific scale
        print("\nSelect concept scale:")
        print("Available scales: 51, 71, 91, 111")
        scale_input = input("Enter scales (comma separated, e.g., 51,91): ").strip()

        try:
            scales = [int(s.strip()) for s in scale_input.split(",")]
            runner.config["scales"] = scales
            runner.run_full_batch()
            runner.create_comparison_charts()
        except ValueError:
            print("❌ Invalid input, please use numbers")

    elif choice == "3":
        # Specific model
        print("\nSelect model:")
        print("1. Random Network")
        print("2. Enhanced Q-learning")
        print("3. Traditional Mechanism Design")
        print("4. Natural Emergence")
        print("5. All models")

        model_choice = input("Select (1-5): ").strip()

        model_map = {
            "1": ["random"],
            "2": ["qlearning"],
            "3": ["traditional"],
            "4": ["emergence"],
            "5": ["random", "qlearning", "traditional", "emergence"]
        }

        if model_choice in model_map:
            runner.config["models"] = model_map[model_choice]
            runner.run_full_batch()
            runner.create_comparison_charts()
        else:
            print("❌ Invalid selection")

    elif choice == "4":
        # Run only emergence model across scales
        runner.config["models"] = ["emergence"]
        runner.run_full_batch()
        runner.create_comparison_charts()

    elif choice == "5":
        # Test single combination
        run_specific_combination()

    else:
        print("⚠️  Invalid selection, running full batch")
        runner.run_full_batch()
        runner.create_comparison_charts()

    print("\n" + "=" * 80)
    print("Batch experiment completed!")
    print("=" * 80)


if __name__ == "__main__":
    main()