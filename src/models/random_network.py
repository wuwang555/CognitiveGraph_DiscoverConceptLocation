"""
Random Network Model - Non-Intelligent Baseline Model
Randomly adjusts network edge weights with no optimization objective
Used to establish a baseline without intelligent mechanisms
"""

import networkx as nx
import numpy as np
import random
from typing import Dict, Any
from core.cognitive_graph import BaseCognitiveGraph

np.random.seed(42)
random.seed(42)

class RandomNetworkModel(BaseCognitiveGraph):
    """Random network model - non-intelligent baseline.

    This class completely randomly adjusts network weights with no optimization objective,
    used for comparison with other intelligent models.
    """

    def __init__(self, individual_params: Dict[str, Any], network_seed: int = 42):
        """Initialize random network model.

        Args:
            individual_params (Dict[str, Any]): Individual parameters (not actually used).
            network_seed (int): Random seed.
        """
        super().__init__(individual_params, network_seed)
        self.random_weight_std = 0.25  # Increase standard deviation for random weight adjustments
        self.random_activation_prob = 0.2  # Reduce random activation probability
        self.forgetting_enabled = False  # Disable forgetting mechanism to make it more "random"

    def initialize_random_network(self, num_nodes=51, connection_prob=0.2):
        """Initialize random network.

        Creates an Erdos-Renyi random graph and assigns random weights to edges.

        Args:
            num_nodes (int): Number of nodes.
            connection_prob (float): Edge connection probability.
        """
        # Create random graph
        self.G = nx.erdos_renyi_graph(num_nodes, connection_prob, seed=self.network_seed)

        # Assign random weights to edges
        for u, v in self.G.edges():
            weight = np.random.uniform(0.8, 2.0)  # Increase initial weight range
            self.G[u][v]['weight'] = weight
            self.G[u][v]['original_weight'] = weight
            self.G[u][v]['traversal_count'] = 0
            self.last_activation_time[(u, v)] = 0

        # Name nodes (using simple numbers)
        node_names = [f"Concept_{i}" for i in range(num_nodes)]
        mapping = {i: node_names[i] for i in range(num_nodes)}
        self.G = nx.relabel_nodes(self.G, mapping)

        print(f"Random network initialization: {num_nodes} nodes, {self.G.number_of_edges()} edges")
        print(f"Initial average energy: {self.calculate_network_energy():.3f}")

    def random_weight_adjustment(self):
        """Random weight adjustment - no intelligent mechanism.

        Randomly select an edge, increase or decrease its weight with 50% probability.
        """
        if self.G.number_of_edges() == 0:
            return

        # Randomly select an edge
        edges = list(self.G.edges())
        u, v = random.choice(edges)

        # Generate random change - increase randomness, not biased toward optimization
        current_weight = self.G[u][v]['weight']

        # 50% probability to increase, 50% to decrease
        if random.random() < 0.5:
            random_change = np.random.uniform(0, self.random_weight_std)
            new_weight = min(3.0, current_weight + random_change)  # Upper bound 3.0
        else:
            random_change = np.random.uniform(0, self.random_weight_std * 0.5)  # Smaller reduction magnitude
            new_weight = max(0.1, current_weight - random_change)  # Lower bound 0.1

        # Apply change (no optimization objective)
        self.G[u][v]['weight'] = new_weight

        # Randomly record activation time
        if random.random() < self.random_activation_prob:
            self.last_activation_time[(u, v)] = self.iteration_count

    def random_traversal(self):
        """Random traversal - no goal orientation.

        Randomly choose a starting point, perform a random walk of several steps, and possibly randomly adjust
        the weights of traversed edges.
        """
        nodes = list(self.G.nodes())
        if len(nodes) < 2:
            return

        # Random start node
        start_node = random.choice(nodes)
        path = [start_node]
        current_node = start_node

        # Random number of steps
        path_length = random.randint(1, 3)  # Reduce step count

        for step in range(path_length - 1):
            neighbors = list(self.G.neighbors(current_node))
            if not neighbors:
                break

            next_node = random.choice(neighbors)
            if next_node not in path:
                path.append(next_node)
                current_node = next_node
            else:
                break

        # Record traversal (but no purposeful adjustment of weights)
        if len(path) >= 2:
            self.traversal_history.append({
                'path': path.copy(),
                'iteration': self.iteration_count,
                'type': 'random_walk'
            })

            # Randomly decide whether to adjust weights of traversed edges
            if random.random() < 0.3:
                for i in range(len(path) - 1):
                    u, v = path[i], path[i + 1]
                    if self.G.has_edge(u, v):
                        # Randomly adjust weight
                        current = self.G[u][v]['weight']
                        adjustment = np.random.uniform(-0.2, 0.2)
                        new_weight = max(0.1, min(3.0, current + adjustment))
                        self.G[u][v]['weight'] = new_weight

    def random_forgetting(self):
        """Random forgetting - no pattern.

        Randomly select edges, with a certain probability regress toward original weight.
        """
        if not self.forgetting_enabled:
            return

        current_time = self.iteration_count

        for u, v in self.G.edges():
            # Randomly decide whether to apply forgetting
            if random.random() < 0.05:  # 5% probability to apply forgetting
                current_energy = self.G[u][v]['weight']
                original_energy = self.G[u][v].get('original_weight', 2.0)

                # Random forgetting factor, may increase or decrease
                forget_factor = random.uniform(-0.1, 0.1)
                new_energy = current_energy + (original_energy - current_energy) * forget_factor
                new_energy = max(0.1, min(3.0, new_energy))

                self.G[u][v]['weight'] = new_energy

    def random_monte_carlo_iteration(self, max_iterations=5000):
        """Random Monte Carlo simulation - no intelligent mechanism.

        Main loop, randomly selects operations (weight adjustment, traversal, forgetting) and executes.

        Args:
            max_iterations (int): Maximum number of iterations.

        Returns:
            float: Energy change percentage (may be negative).
        """
        print(f"Starting random network simulation: {max_iterations} iterations")
        print("Note: This is a non-intelligent baseline model, expected to perform poorly")

        initial_energy = self.calculate_network_energy()
        self.energy_history.append(initial_energy)

        for iteration in range(max_iterations):
            self.iteration_count += 1

            # Randomly select operation type
            operation_choice = random.random()

            if operation_choice < 0.7:  # 70% probability random weight adjustment
                self.random_weight_adjustment()
            elif operation_choice < 0.9:  # 20% probability random traversal
                self.random_traversal()
            else:  # 10% probability random forgetting
                self.random_forgetting()

            # Record energy history
            current_energy = self.calculate_network_energy()
            self.energy_history.append(current_energy)

            # Periodic reporting
            if iteration % 500 == 0:
                improvement = ((initial_energy - current_energy) / initial_energy * 100) if initial_energy > 0 else 0
                print(f"Iteration {iteration}: network energy = {current_energy:.3f} (change: {improvement:.1f}%)")

        final_energy = self.calculate_network_energy()
        total_improvement = ((initial_energy - final_energy) / initial_energy * 100) if initial_energy > 0 else 0

        print(f"\nRandom network simulation completed!")
        print(f"Initial energy: {initial_energy:.3f}, Final energy: {final_energy:.3f}")
        print(f"Total change: {total_improvement:.1f}%")
        print(f"Note: Positive values indicate energy reduction (improvement), negative values indicate energy increase (deterioration)")

        return total_improvement

    def run_experiment(self, num_nodes=51, max_iterations=5000):
        """Run a complete experiment.

        Args:
            num_nodes (int): Number of nodes.
            max_iterations (int): Maximum number of iterations.

        Returns:
            dict: Experiment results dictionary.
        """
        self.initialize_random_network(num_nodes)
        improvement = self.random_monte_carlo_iteration(max_iterations)

        stats = self.get_network_stats()

        return {
            'model_type': 'random_network',
            'num_nodes': num_nodes,
            'iterations': max_iterations,
            'initial_energy': self.energy_history[0] if self.energy_history else 0,
            'final_energy': self.calculate_network_energy(),
            'improvement': improvement,
            'network_stats': stats,
            'note': 'Non-intelligent baseline model, expected to perform poorly'
        }


if __name__ == "__main__":
    # Simple test: run a small random network
    print("Testing RandomNetworkModel...")
    params = {}
    model = RandomNetworkModel(params)
    result = model.run_experiment(num_nodes=51, max_iterations=8000)
    print("Test completed. Improvement rate:", result['improvement'])