"""
Cognitive Graph Results Analysis Module.

Provides statistical analysis of experimental results and network metric calculation functions.
"""

import numpy as np


def analyze_population_results(results):
    """
    Analyze population experiment results, compute and print statistics.

    Parameters
    ----------
    results : list of dict
        List of experimental results for each individual, each dictionary should contain the following keys:
            - 'improvement' : float  # Energy improvement percentage
            - 'compression_centers' : list  # List of concept compression centers
            - 'migration_bridges' : list  # List of migration bridges

    Returns
    -------
    dict
        Dictionary containing the following statistical metrics:
            - 'mean_improvement' : float   # Average energy improvement
            - 'std_improvement' : float    # Standard deviation of energy improvement
            - 'mean_compressions' : float  # Average number of concept compressions
            - 'mean_migrations' : float    # Average number of migrations
    """
    print(f"\n=== Population Statistics Results ===")

    improvements = [r['improvement'] for r in results]
    compressions = [r['compression_centers'] for r in results]
    migrations = [r['migration_bridges'] for r in results]

    print(f"Energy reduction statistics:")
    print(f"  Mean: {np.mean(improvements):.1f}%")
    print(f"  Std Dev: {np.std(improvements):.1f}%")
    print(f"  Range: {min(improvements):.1f}% - {max(improvements):.1f}%")

    print(f"Concept compression statistics:")
    print(f"  Mean: {np.mean(compressions):.1f}")
    print(f"  Range: {min(compressions)} - {max(compressions)}")

    print(f"Migration bridge statistics:")
    print(f"  Mean: {np.mean(migrations):.1f}")
    print(f"  Range: {min(migrations)} - {max(migrations)}")

    print(f"\n=== Individual Difference Analysis ===")

    best_individual = max(results, key=lambda x: x['improvement'])
    worst_individual = min(results, key=lambda x: x['improvement'])

    print(f"Best individual: {best_individual['individual_id']} (energy reduction: {best_individual['improvement']:.1f}%)")
    print(f"Worst individual: {worst_individual['individual_id']} (energy reduction: {worst_individual['improvement']:.1f}%)")

    return {
        'mean_improvement': np.mean(improvements),
        'std_improvement': np.std(improvements),
        'mean_compressions': np.mean(compressions),
        'mean_migrations': np.mean(migrations)
    }


def get_network_stats(G, iteration_count, concept_centers):
    """
    Get statistical information of the cognitive network.

    Parameters
    ----------
    G : networkx.Graph
        Cognitive network graph object.
    iteration_count : int
        Current iteration count.
    concept_centers : dict
        Dictionary of concept compression centers, keyed by node name with compression information.

    Returns
    -------
    dict
        Dictionary containing the following keys:
            - 'nodes' : int                     # Number of nodes
            - 'edges' : int                     # Number of edges
            - 'iterations' : int                # Iteration count
            - 'avg_energy' : float              # Average energy
            - 'compression_centers' : int       # Number of compression centers
            - 'migration_bridges' : int         # Total number of migration bridges
    """
    stats = {
        'nodes': G.number_of_nodes(),
        'edges': G.number_of_edges(),
        'iterations': iteration_count,
        'avg_energy': calculate_network_energy(G),
        'compression_centers': len(concept_centers),
        'migration_bridges': 0
    }

    for node in G.nodes():
        if 'migration_bridges' in G.nodes[node]:
            stats['migration_bridges'] += len(G.nodes[node]['migration_bridges'])

    return stats


def calculate_network_energy(G):
    """
    Calculate the average network energy.

    Parameters
    ----------
    G : networkx.Graph
        Cognitive network graph object, edges should have 'weight' attribute representing energy.

    Returns
    -------
    float
        Average energy across all edges; returns 0 if no edges.
    """
    if G.number_of_edges() == 0:
        return 0
    energies = [G[u][v]['weight'] for u, v in G.edges()]
    return np.mean(energies)


if __name__ == "__main__":
    # Simple test: create mock data and call analysis function
    mock_results = [
        {'individual_id': 'ind1', 'improvement': 23.5, 'compression_centers': [1, 2], 'migration_bridges': [1]},
        {'individual_id': 'ind2', 'improvement': 18.2, 'compression_centers': [3], 'migration_bridges': []},
    ]
    analyze_population_results(mock_results)