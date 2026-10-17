"""
Population Cognitive Experiment Script
Used to run semantic-enhanced population experiments, simulating cognitive evolution of multiple individuals.
"""

import os
import csv
from utils.individual_variation import IndividualVariation, create_enhanced_individual_params
from models.enhanced_model import SemanticEnhancedCognitiveGraph, EnergyOptimizedCognitiveGraph
from utils.analysis import *
from core.cognitive_states import *
from utils.visualization import *


def run_semantic_enhanced_experiment(num_individuals=3, max_iterations=10000, num_concepts=None):
    """Run semantic-enhanced population experiment.

    Generate random parameters for multiple individuals, run cognitive evolution separately, and save energy history
    and analysis results.

    Args:
        num_individuals (int): Number of individuals.
        max_iterations (int): Maximum iterations.
        num_concepts (int, optional): Number of concept nodes.

    Returns:
        list: List of result dictionaries for each individual.
    """
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    population_results = []
    base_parameters = {
        'forgetting_rate': 0.002,
        'base_learning_rate': 0.85,
        'hard_traversal_bias': 0.0,
        'soft_traversal_bias': 0.0,
        'compression_bias': 0.0,
        'migration_bias': 0.0,
        'learning_rate_variation': 0.1
    }

    variation_ranges = {
        'forgetting_rate': 0.2,
        'base_learning_rate': 0.1,
        'hard_traversal_bias': (-0.1, 0.1),
        'soft_traversal_bias': (-0.1, 0.1),
        'compression_bias': (-0.03, 0.03),
        'migration_bias': (-0.05, 0.05),
        'learning_rate_variation': (0.05, 0.15)
    }

    variation_simulator = IndividualVariation(base_parameters, variation_ranges)
    population_results = []

    print(f"=== Starting semantic-enhanced population experiment: {num_individuals} individuals ===")
    if num_concepts:
        print(f"Number of concepts: {num_concepts}")

    for i in range(num_individuals):
        individual_id = f"Individual_{i + 1}"
        print(f"\n--- Simulating {individual_id} ---")

        base_individual_params = variation_simulator.generate_individual(individual_id)
        individual_params = create_enhanced_individual_params(base_individual_params)

        # Create cognitive graph, passing num_concepts parameter
        individual_graph = SemanticEnhancedCognitiveGraph(individual_params, num_concepts=num_concepts)
        individual_graph.initialize_semantic_graph()

        # Use get_network_stats() to obtain initial statistics
        initial_stats = individual_graph.get_network_stats()
        initial_energy = initial_stats['avg_energy']

        individual_graph.monte_carlo_iteration(max_iterations=max_iterations)

        # Save energy history
        energy_history = individual_graph.cognitive_energy_history
        energy_file = os.path.join("results/population", f"energy_history_{individual_id}_{timestamp}.csv")
        os.makedirs("results/population", exist_ok=True)
        with open(energy_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['iteration', 'energy'])
            for idx, e in enumerate(energy_history):
                writer.writerow([idx, e])
        print(f"Energy history saved: {energy_file}")

        # Use get_network_stats() to obtain final statistics
        final_stats = individual_graph.get_network_stats()
        improvement = ((initial_energy - final_stats['avg_energy']) / initial_energy * 100)

        result = {
            'individual_id': individual_id,
            'parameters': individual_params,
            'initial_energy': initial_energy,
            'final_energy': final_stats['avg_energy'],
            'improvement': improvement,
            'compression_centers': final_stats['compression_centers'],
            'migration_bridges': final_stats['migration_bridges'],
            'concept_centers': list(individual_graph.concept_centers.keys()),
            'cognitive_states': individual_graph.cognitive_energy_history
        }

        population_results.append(result)

        print(f"{individual_id} results:")
        print(f"  Energy reduction: {improvement:.1f}%")
        print(f"  Compression centers: {result['compression_centers']}")
        print(f"  Migration bridges: {result['migration_bridges']}")

        individual_graph.visualize_cognitive_states()

    analyze_population_results(population_results)

    return population_results


def test_enhanced_features(num_concepts=None):
    """Test enhanced features such as similarity calculation, Monte Carlo iteration, and intelligent compression.

    Args:
        num_concepts (int, optional): Number of concept nodes.

    Returns:
        EnergyOptimizedCognitiveGraph: Evolved cognitive graph object.
    """
    print("=== Testing Enhanced Cognitive Graph Model ===")
    if num_concepts:
        print(f"Number of concepts: {num_concepts}")

    # Create individual parameters
    base_params = {
        'forgetting_rate': 0.002,
        'base_learning_rate': 0.85,
        'hard_traversal_bias': 0.0,
        'soft_traversal_bias': 0.0,
        'compression_bias': 0.0,
        'migration_bias': 0.0,
        'learning_rate_variation': 0.1
    }

    # Create energy-optimized cognitive graph, passing num_concepts parameter
    cognitive_graph = EnergyOptimizedCognitiveGraph(base_params, num_concepts=num_concepts)
    cognitive_graph.initialize_semantic_graph()

    print("Initial network statistics:")
    stats = cognitive_graph.get_network_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")

    # Test similarity calculation
    test_pairs = [("算法", "数据结构"), ("牛顿定律", "优化"), ("几何学", "拓扑学")]

    print("\n=== Similarity Calculation Test ===")
    for concept1, concept2 in test_pairs:
        similarity = cognitive_graph.calculate_semantic_similarity(concept1, concept2)
        print(f"{concept1} <-> {concept2}: {similarity:.3f}")

    # Run Monte Carlo simulation
    print("\n=== Starting Energy Optimization Simulation ===")
    cognitive_graph.monte_carlo_iteration(max_iterations=10000)

    # Intelligent concept compression
    print("\n=== Intelligent Concept Compression ===")
    compressed_groups = cognitive_graph.improved_smart_concept_compression(
        compression_threshold=0.3,
        max_group_size=6
    )
    print(f"Completed {len(compressed_groups)} intelligent compressions")

    # Final statistics
    final_stats = cognitive_graph.get_network_stats()
    improvement = ((stats['avg_energy'] - final_stats['avg_energy']) / stats['avg_energy'] * 100)

    print(f"\n=== Final Results ===")
    print(f"Energy reduction: {improvement:.1f}%")
    print(f"Compression centers: {final_stats['compression_centers']}")
    print(f"Migration bridges: {final_stats['migration_bridges']}")

    return cognitive_graph


def demo_semantic_network(num_concepts=None):
    """Demonstrate semantic network functionality, including cross-domain path finding.

    Args:
        num_concepts (int, optional): Number of concept nodes.
    """
    from core.semantic_network import SemanticConceptNetwork
    from utils.visualization import visualize_semantic_network

    semantic_net = SemanticConceptNetwork()
    # Build semantic network, passing num_concepts parameter
    semantic_net.build_comprehensive_network(num_concepts=num_concepts)

    print("\n=== Semantic Network Demonstration ===")
    if num_concepts:
        print(f"Number of concepts: {num_concepts}")

    # Show keywords for some concepts
    sample_concepts = ["牛顿定律", "微积分", "算法", "优化"]
    for concept in sample_concepts:
        if concept in semantic_net.concept_keywords:
            print(f"{concept}: {semantic_net.concept_keywords[concept]}")

    # Find cross-domain paths
    print("\n=== Cross-Domain Path Examples ===")
    domain_pairs = [
        ("牛顿定律", "算法"),
        ("微积分", "机器学习"),
        ("几何学", "计算机视觉")
    ]

    for start, end in domain_pairs:
        paths = semantic_net.find_cross_domain_paths(start, end)
        if paths:
            best_path, similarity = paths[0]
            print(f"{start} -> {end}:")
            print(f"  Path: {' -> '.join(best_path)}")
            print(f"  Semantic similarity: {similarity:.3f}")
        else:
            print(f"{start} -> {end}: No path found")

    # Visualize semantic network
    semantic_net.visualize_semantic_network()


if __name__ == "__main__":
    # Simple test: run a small-scale population experiment
    print("Running population experiment test (2 individuals, 500 iterations)")
    results = run_semantic_enhanced_experiment(num_individuals=2, max_iterations=10000, num_concepts=51)
    print("Test completed.")