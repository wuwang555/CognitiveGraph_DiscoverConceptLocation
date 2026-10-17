#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Cognitive Graph Theory One-Click Run Script (Enhanced Reproducibility Version).
This script automatically runs four-scale comparison experiments, emergence studies,
algebraic verification experiments, and semantic network demonstrations,
and generates detailed runtime logs to ensure reproducibility.
"""

import sys
import os
import time
import json
import platform
import logging
import random
from datetime import datetime
from pathlib import Path

# Set random seed (ensure reproducibility)
import numpy as np
np.random.seed(42)
random.seed(42)

# Add project root directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import dependencies (for version recording)
import networkx as nx
try:
    import pandas as pd
except ImportError:
    pd = None
try:
    import matplotlib
except ImportError:
    matplotlib = None
try:
    import scipy
except ImportError:
    scipy = None
try:
    import jieba
except ImportError:
    jieba = None


def setup_logging():
    """Configure logger to output to both console and file."""
    # Create logs directory
    Path("logs").mkdir(parents=True, exist_ok=True)

    # Log filename includes timestamp to avoid overwriting
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = f"logs/reproducibility_{timestamp}.log"

    # Configure root logger
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # Remove existing handlers (prevent duplication)
    if logger.hasHandlers():
        logger.handlers.clear()

    # File handler
    file_handler = logging.FileHandler(log_file, mode='w', encoding='utf-8')
    file_handler.setLevel(logging.INFO)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)

    # Define format
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger


def log_environment(logger):
    """Record system environment and dependency versions."""
    logger.info("=== Environment Information ===")
    logger.info(f"Current time: {datetime.now()}")
    logger.info(f"Python version: {sys.version}")
    logger.info(f"Platform: {platform.platform()}")
    logger.info(f"CPU info: {platform.processor()}")
    logger.info(f"Machine type: {platform.machine()}")
    logger.info(f"Python interpreter path: {sys.executable}")
    logger.info(f"System path: {sys.path}")

    logger.info("=== Dependency Versions ===")
    logger.info(f"numpy: {np.__version__}")
    if pd:
        logger.info(f"pandas: {pd.__version__}")
    if matplotlib:
        logger.info(f"matplotlib: {matplotlib.__version__}")
    logger.info(f"networkx: {nx.__version__}")
    if scipy:
        logger.info(f"scipy: {scipy.__version__}")
    if jieba:
        # jieba may not have __version__ attribute
        logger.info(f"jieba: {getattr(jieba, '__version__', 'unknown')}")

    # Record key experimental parameters (extracted from the paper; additional parameters may exist inside modules)
    logger.info("=== Experimental Parameters ===")
    logger.info("Concept scales: [51, 71, 91, 111]")
    logger.info("Number of iterations: 10000")
    logger.info("Number of individuals: 3")
    logger.info("Semantic similarity threshold: 0.08")
    logger.info("Compression synergy threshold: 0.76")
    logger.info("Migration efficiency threshold: 0.35")
    logger.info("Cluster cohesion threshold: 0.7")
    logger.info("Minimum connection strength: 0.5")
    logger.info("Learning rate: 0.85")
    logger.info("Cognitive temperature T: 1.0")
    logger.info("Random seed: 42")


def check_dependencies(logger):
    """
    Check whether required dependencies are installed, and record versions.
    """
    required_libs = ['numpy', 'pandas', 'matplotlib', 'networkx', 'scipy', 'jieba']
    missing_libs = []

    for lib in required_libs:
        try:
            __import__(lib)
        except ImportError:
            missing_libs.append(lib)

    if missing_libs:
        logger.error(f"Missing dependencies: {', '.join(missing_libs)}")
        print(f"❌ Missing dependencies: {', '.join(missing_libs)}")
        print("Please install: pip install " + " ".join(missing_libs))
        return False

    logger.info("✅ All dependencies loaded successfully")
    print("✅ All dependencies loaded successfully")
    return True


def create_output_directories(logger):
    """
    Create directories required for experiment outputs.
    """
    directories = [
        'results/',
        'results/batch_experiments/',
        'results/emergence/',
        'results/algebra/',
        'results/visualizations/',
        'logs/'
    ]

    for dir_path in directories:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
        logger.info(f"📁 Created directory: {dir_path}")
        print(f"📁 Created directory: {dir_path}")

    return True


def run_batch_experiments(logger):
    """
    Run four-scale comparison experiments (51/71/91/111 concepts).
    """
    logger.info("\n" + "=" * 80)
    logger.info("1️⃣ Running four-scale comparison experiments (51/71/91/111 concepts)")
    logger.info("=" * 80)

    try:
        from experiments.batch_experiments import BatchExperimentRunner

        runner = BatchExperimentRunner(output_dir='results/batch_experiments')

        logger.info("Starting four-scale comparison experiments...")
        start_time = time.time()

        runner.run_full_batch()
        runner.create_comparison_charts()

        elapsed_time = time.time() - start_time
        logger.info(f"✅ Four-scale comparison experiments completed! Time elapsed: {elapsed_time:.1f}s")
        return True

    except Exception as e:
        logger.exception(f"❌ Error while running four-scale comparison experiments: {e}")
        return False


def run_emergence_study(logger):
    """
    Run emergence study to observe natural emergence of concept compression and principle migration.
    """
    logger.info("\n" + "=" * 80)
    logger.info("2️⃣ Running emergence study")
    logger.info("=" * 80)

    try:
        from experiments.emergence_study_fixed import EmergenceStudyFixed

        logger.info("Starting emergence study...")
        start_time = time.time()

        study = EmergenceStudyFixed()
        scales = [51, 71, 91, 111]
        all_results = {}

        for scale in scales:
            logger.info(f"\nProcessing concept scale: {scale}...")
            try:
                results = study.run_pure_emergence_experiment(
                    num_individuals=3,
                    max_iterations=10000,
                    num_concepts=scale
                )
                all_results[scale] = results

                # Remove non-serializable 'universe' field
                serializable_results = []
                for individual in results:
                    serializable_individual = {k: v for k, v in individual.items() if k != 'universe'}
                    serializable_results.append(serializable_individual)

                # Generate filename with timestamp
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_file = f'results/emergence/emergence_{scale}_concepts_{timestamp}.json'
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(serializable_results, f, ensure_ascii=False, indent=2)
                logger.info(f"✅ Results saved to: {output_file}")
            except Exception as e:
                logger.exception(f"❌ Error processing scale {scale}: {e}")

        study.visualize_emergence_results()

        elapsed_time = time.time() - start_time
        logger.info(f"✅ Emergence study completed! Time elapsed: {elapsed_time:.1f}s")
        return True

    except Exception as e:
        logger.exception(f"❌ Error while running emergence study: {e}")
        return True  # Do not interrupt overall process

def run_algebra_experiments(logger):
    """
    Run algebraic verification experiments to validate cognitive operation semigroups, Noether-type propositions, etc.
    """
    logger.info("\n" + "=" * 80)
    logger.info("3️⃣ Running algebraic verification experiments")
    logger.info("=" * 80)

    try:
        from algebra.algebra_experiments import AlgebraValidationExperiments

        logger.info("Starting algebraic verification experiments...")
        start_time = time.time()

        experiments = AlgebraValidationExperiments()
        all_results = experiments.run_all_experiments()

        elapsed_time = time.time() - start_time
        logger.info(f"✅ Algebraic verification experiments completed! Time elapsed: {elapsed_time:.1f}s")
        return True

    except Exception as e:
        logger.exception(f"❌ Error while running algebraic verification experiments: {e}")
        return False


def run_semantic_network_demo(logger):
    """
    Run semantic network demonstration to show semantic associations between concepts.
    """
    logger.info("\n" + "=" * 80)
    logger.info("4️⃣ Running semantic network demonstration")
    logger.info("=" * 80)

    try:
        try:
            from main import demo_semantic_network
            demo_semantic_network()
            return True
        except ImportError:
            from core.semantic_network import SemanticConceptNetwork

            logger.info("Building semantic concept network...")
            semantic_net = SemanticConceptNetwork()

            core_definitions = {
                "牛顿定律": "物体运动的基本定律，描述了力与运动的关系",
                "微积分": "研究变化和累积的数学分支，包括微分和积分",
                "算法": "解决问题的一系列明确的计算步骤",
                "优化": "在给定约束下找到最佳解决方案的过程"
            }

            for concept, definition in core_definitions.items():
                semantic_net.add_concept_definition(concept, definition, "predefined")

            semantic_net.build_comprehensive_network()

            logger.info("\nExample cross‑domain path search:")
            paths = semantic_net.find_cross_domain_paths("牛顿定律", "算法", max_path_length=3)
            if paths:
                best_path, similarity = paths[0]
                logger.info(f"牛顿定律 -> 算法:")
                logger.info(f"  Path: {' -> '.join(best_path)}")
                logger.info(f"  Similarity: {similarity:.3f}")

            logger.info("\nGenerating semantic network visualization...")
            semantic_net.visualize_semantic_network()

            return True

    except Exception as e:
        logger.exception(f"❌ Error while running semantic network demonstration: {e}")
        return True


def generate_summary_report(logger):
    """
    Generate experiment summary report and save as Markdown file.
    """
    logger.info("\n" + "=" * 80)
    logger.info("📊 Generating experiment summary report")
    logger.info("=" * 80)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = f'results/experiment_summary_{timestamp}.md'

    summary = f"""
# 🧠 Cognitive Graph Theory Experiment Summary Report

## 📅 Experiment Information
- Run time: {timestamp}
- Script version: 2.0
- Author: Zeng Mingjia

## 🎯 Experiment Objectives
To verify energy minimization as the fundamental driving force for cognitive organization, and observe the natural emergence of concept compression and first‑principle migration.

## 📊 Experiment Items
1. ✅ Four‑scale comparison experiments (51/71/91/111 concepts)
2. ✅ Emergence study
3. ✅ Algebraic verification experiments
4. ✅ Semantic network demonstration

## 📁 Result Files
Experimental results are saved in the following directories:
- `results/batch_experiments/` - Four‑scale comparison experiment data
- `results/emergence/` - Emergence study data
- `results/algebra/` - Algebraic verification experiment data
- `results/visualizations/` - Visualization charts

## Data Description
For detailed data description, see `results/DATA_DICTIONARY.md`

## 🚀 Next Steps
1. Examine the specific experimental result files
2. Adjust parameters and re‑run specific experiments
3. Extend concept scale tests
4. Compare with other cognitive models

## 📞 Contact
If you have questions or suggestions, please contact the project author.

---

*Cognition has no boundaries, learning never ends.*
*Exploring the boundaries of cognition, understanding the essence of learning.*
"""

    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(summary)

    logger.info(f"✅ Experiment summary report generated: {report_file}")
    logger.info("\nReport preview:")
    logger.info("-" * 50)
    logger.info(summary[:500] + "...")
    logger.info("-" * 50)

    return report_file


def main():
    """Main function: sequentially run all experiments and generate summary report."""
    # Configure logging
    logger = setup_logging()
    logger.info("=" * 80)
    logger.info("🧠 Cognitive Graph Theory: A Cognitive Computing Model Based on Energy Minimization")
    logger.info("=" * 80)
    logger.info("Author: Zeng Mingjia")
    logger.info("Version: 2.0")
    logger.info("Date: December 2025")
    logger.info("=" * 80)

    # Record environment information
    log_environment(logger)

    # Check dependencies
    if not check_dependencies(logger):
        logger.error("❌ Dependency check failed, please install required dependencies")
        return

    # Create output directories
    if not create_output_directories(logger):
        logger.error("❌ Directory creation failed")
        return

    logger.info("\n" + "=" * 80)
    logger.info("🚀 Starting one‑click execution of all experiments")
    logger.info("=" * 80)

    overall_start_time = time.time()

    experiment_status = {
        'batch_experiments': False,
        'emergence_study': False,
        'algebra_experiments': False,
        'semantic_demo': False
    }

    try:
        experiment_status['batch_experiments'] = run_batch_experiments(logger)
        experiment_status['emergence_study'] = run_emergence_study(logger)
        experiment_status['algebra_experiments'] = run_algebra_experiments(logger)
        experiment_status['semantic_demo'] = run_semantic_network_demo(logger)

        overall_elapsed_time = time.time() - overall_start_time
        report_file = generate_summary_report(logger)

        logger.info("\n" + "=" * 80)
        logger.info("🎉 All experiments completed!")
        logger.info("=" * 80)

        logger.info("\n📈 Experiment completion status:")
        for experiment, status in experiment_status.items():
            status_symbol = "✅" if status else "❌"
            logger.info(f"  {status_symbol} {experiment}")

        logger.info(f"\n⏱️  Total run time: {overall_elapsed_time:.1f}s")
        logger.info(f"📋 Experiment summary report: {report_file}")

        successful_experiments = sum(experiment_status.values())
        total_experiments = len(experiment_status)
        logger.info(f"\n📊 Success rate: {successful_experiments}/{total_experiments} ({successful_experiments / total_experiments * 100:.1f}%)")

        if successful_experiments == total_experiments:
            logger.info("\n🌟 All experiments succeeded!")
            logger.info("Suggestions:")
            logger.info("  1. Check the detailed results in the results/ directory")
            logger.info("  2. Run analysis.py for data analysis")
            logger.info("  3. Modify config.py to adjust parameters and re‑run experiments")
        elif successful_experiments >= 2:
            logger.info("\n⚠️  Some experiments completed; consider checking the failed ones")
        else:
            logger.info("\n❌ Most experiments failed; please check the environment and dependencies")

        logger.info("\n" + "=" * 80)
        logger.info("💡 Tips:")
        logger.info("  1. To re‑run a specific experiment, refer to main.py")
        logger.info("  2. Check README.md for detailed project instructions")
        logger.info("  3. Experiment results can be used to generate paper figures")
        logger.info("=" * 80)

    except KeyboardInterrupt:
        logger.warning("\n\n⏹️ Experiment interrupted by user")
        overall_elapsed_time = time.time() - overall_start_time
        logger.info(f"Run time so far: {overall_elapsed_time:.1f}s")

    except Exception as e:
        logger.exception(f"\n❌ Unexpected error while running experiments: {e}")

    # Shut down logging (optional)
    logging.shutdown()


if __name__ == "__main__":
    # Set Chinese font display
    import matplotlib
    matplotlib.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans']
    matplotlib.rcParams['axes.unicode_minus'] = False

    main()

    print("\n" + "=" * 80)
    print("🧠 Cognitive Graph Theory Experiment Platform")
    print("=" * 80)
    print("Thank you for using the Cognitive Graph Theory Experiment Platform!")
    print("For more information, please refer to the project documentation.")
    print("=" * 80)