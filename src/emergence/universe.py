"""
Cognitive Universe Module (Based on Two Postulates)
-----------------------------
Define PureEnergyDynamics and CognitiveUniverse classes, relying only on the energy minimization postulate and forgetting mechanism,
to observe natural emergence phenomena.
"""

import networkx as nx
import numpy as np
import random
import math
from typing import Dict, Any, List, Optional

from config import BASE_PARAMETERS

np.random.seed(42)
random.seed(42)

class PureEnergyDynamics:
    """Pure energy dynamics, implementing only the two postulates: global energy calculation and local change attempts."""

    def __init__(self, individual_params: Dict[str, Any]):
        """
        :param individual_params: Individual parameters, including forgetting_rate, etc.
        """
        self.individual_params = individual_params
        self.energy_state = {}
        self.global_energy_history = []
        self.local_energy_changes = []
        self.forgetting_rate = individual_params.get('forgetting_rate', 0.002)

    def compute_global_energy(self, network: nx.Graph) -> float:
        """Compute global network energy (average edge weight)."""
        if network.number_of_edges() == 0:
            return 0
        energies = [network[u][v]['weight'] for u, v in network.edges()]
        return np.mean(energies)

    def compute_local_energy(self, node: str, network: nx.Graph) -> float:
        """Compute local energy of a node (mean weight of incident edges)."""
        if node not in network:
            return 0
        neighbors = list(network.neighbors(node))
        if not neighbors:
            return 0
        local_energy = 0
        for neighbor in neighbors:
            local_energy += network[node][neighbor]['weight']
        return local_energy / len(neighbors)

    def generate_random_changes(self, network: nx.Graph, num_changes: int = 5) -> List[Dict]:
        """Generate random change attempts, including edge weight adjustments, node activation, local optimization."""
        changes = []
        nodes = list(network.nodes())

        if len(nodes) < 2:
            return changes

        for _ in range(num_changes):
            change_type = random.choice([
                'edge_weight_adjustment',
                'node_activation',
                'local_optimization'
            ])

            if change_type == 'edge_weight_adjustment':
                if network.number_of_edges() > 0:
                    u, v = random.choice(list(network.edges()))
                    current_weight = network[u][v]['weight']
                    new_weight = max(0.05, current_weight * random.uniform(0.8, 1.2))
                    changes.append({
                        'type': 'edge_weight_adjustment',
                        'edge': (u, v),
                        'old_weight': current_weight,
                        'new_weight': new_weight
                    })

            elif change_type == 'node_activation':
                node = random.choice(nodes)
                changes.append({
                    'type': 'node_activation',
                    'node': node,
                    'effect': random.uniform(0.9, 1.1)
                })

            elif change_type == 'local_optimization':
                if len(nodes) >= 3:
                    center = random.choice(nodes)
                    neighbors = list(network.neighbors(center))[:3]
                    if len(neighbors) >= 2:
                        changes.append({
                            'type': 'local_optimization',
                            'center': center,
                            'neighbors': neighbors,
                            'optimization_strength': random.uniform(0.7, 0.95)
                        })

        return changes

    def apply_change_and_compute(self, network: nx.Graph, change: Dict) -> float:
        """Apply change and compute new energy (without permanently retaining change)."""
        original_state = {}

        if change['type'] == 'edge_weight_adjustment':
            u, v = change['edge']
            original_state[(u, v)] = network[u][v]['weight']
            network[u][v]['weight'] = change['new_weight']

        elif change['type'] == 'node_activation':
            node = change['node']
            for neighbor in network.neighbors(node):
                original_state[(node, neighbor)] = network[node][neighbor]['weight']
                network[node][neighbor]['weight'] *= change['effect']

        elif change['type'] == 'local_optimization':
            center = change['center']
            for neighbor in change['neighbors']:
                if network.has_edge(center, neighbor):
                    original_state[(center, neighbor)] = network[center][neighbor]['weight']
                    network[center][neighbor]['weight'] *= change['optimization_strength']

        new_energy = self.compute_global_energy(network)

        # Restore original state
        for key, value in original_state.items():
            if isinstance(key, tuple) and len(key) == 2:
                u, v = key
                if network.has_edge(u, v):
                    network[u][v]['weight'] = value

        return new_energy

    def keep_change(self, network: nx.Graph, change: Dict) -> None:
        """Permanently keep change (update network)."""
        if change['type'] == 'edge_weight_adjustment':
            u, v = change['edge']
            network[u][v]['weight'] = change['new_weight']

        elif change['type'] == 'node_activation':
            node = change['node']
            for neighbor in network.neighbors(node):
                network[node][neighbor]['weight'] *= change['effect']

        elif change['type'] == 'local_optimization':
            center = change['center']
            for neighbor in change['neighbors']:
                if network.has_edge(center, neighbor):
                    network[center][neighbor]['weight'] *= change['optimization_strength']


class CognitiveUniverse:
    """Cognitive universe, based on two postulates: cognitive spacetime and energy dynamics, observing natural emergence.

    Main mechanisms:
        - Learning: reduce edge weights through traversal
        - Forgetting: edges not activated for a long time return to original weight
        - Random traversal: explore the network
    Does not include any preset compression or migration algorithms, only records observed emergence phenomena.
    """

    def __init__(self, individual_params: Optional[Dict[str, Any]] = None, network_seed: int = 42):
        """
        :param individual_params: Individual parameters, default uses BASE_PARAMETERS
        :param network_seed: Random seed
        """
        if individual_params is None:
            individual_params = BASE_PARAMETERS.copy()

        self.G = nx.Graph()
        self.individual_params = individual_params
        self.network_seed = network_seed
        self.iteration_count = 0

        self.energy_dynamics = PureEnergyDynamics(individual_params)

        self.state_history = []
        self.current_energy_level = 1.0

        self.energy_history = []

        self.traversal_history = []

        self.last_activation_time = {}

        self.observations = {
            'spontaneous_compressions': [],
            'emergent_migrations': [],
            'traversal_patterns': [],
            'energy_minimization_traces': [],
            'network_evolution_snapshots': []
        }

        self.learning_rate = individual_params.get('base_learning_rate', 0.85)
        self.forgetting_rate = individual_params.get('forgetting_rate', 0.002)
        self.base_forgetting_strength = 0.002

        random.seed(network_seed)
        np.random.seed(network_seed)
        print("Cognitive universe initialized: forgetting mechanism activated")

    def initialize_semantic_network(self) -> None:
        """Initialize semantic network, building nodes and edges from SemanticConceptNetwork."""
        from core.semantic_network import SemanticConceptNetwork

        semantic_net = SemanticConceptNetwork()
        semantic_net.build_comprehensive_network()

        nodes = list(semantic_net.concept_definitions.keys())
        self.G.add_nodes_from(nodes)

        initial_edges = []
        for i, node1 in enumerate(nodes):
            for j, node2 in enumerate(nodes[i + 1:], i + 1):
                similarity = semantic_net.calculate_semantic_similarity(node1, node2)

                if similarity > 0.1:
                    energy = 2.0 - similarity * 1.5
                    energy = max(0.3, min(2.0, energy))

                    initial_edges.append((node1, node2, {
                        'weight': energy,
                        'traversal_count': 0,
                        'original_weight': energy,
                        'similarity': similarity
                    }))
                    self.last_activation_time[(node1, node2)] = 0

        for u, v, attr in initial_edges:
            self.G.add_edge(u, v, **attr)

        print(f"Semantic network initialization: {len(nodes)} nodes, {len(initial_edges)} edges")
        print(f"Initial global energy: {self.calculate_network_energy():.3f}")

    def calculate_network_energy(self) -> float:
        """Calculate current network average energy."""
        if self.G.number_of_edges() == 0:
            return 0
        energies = [self.G[u][v]['weight'] for u, v in self.G.edges()]
        return np.mean(energies)

    def basic_energy_optimization(self) -> bool:
        """Basic energy optimization: randomly select an edge for learning (reduce energy), possibly propagate to neighbors."""
        if self.G.number_of_edges() == 0:
            return False

        edges = list(self.G.edges())
        u, v = random.choice(edges)

        self.record_edge_activation(u, v)

        if random.random() < 0.5:
            neighbors = list(self.G.neighbors(u))
            if neighbors:
                neighbor = random.choice(neighbors)
                if self.G.has_edge(u, neighbor):
                    self.record_edge_activation(u, neighbor)

        return True

    def record_edge_activation(self, u: str, v: str) -> None:
        """Record edge activation, update activation time and apply learning effect (reduce weight)."""
        self.last_activation_time[(u, v)] = self.iteration_count

        current_energy = self.G[u][v]['weight']
        learning_rate = 0.1
        new_energy = current_energy * (1 - learning_rate)
        self.G[u][v]['weight'] = max(0.05, new_energy)

    def apply_basic_forgetting(self) -> None:
        """Apply basic forgetting mechanism: edges not activated for a long time return to original energy."""
        current_time = self.iteration_count

        for u, v in self.G.edges():
            time_since_activation = current_time - self.last_activation_time.get((u, v), 0)

            if time_since_activation > 0:
                current_energy = self.G[u][v]['weight']
                original_energy = self.G[u][v].get('original_weight', 2.0)

                forget_factor = self._compute_forget_factor(time_since_activation)

                new_energy = current_energy + (original_energy - current_energy) * forget_factor
                new_energy = min(new_energy, original_energy)

                self.G[u][v]['weight'] = max(0.1, new_energy)

    def _compute_forget_factor(self, time_gap: int) -> float:
        """Compute forgetting factor based on exponential decay."""
        base_rate = self.forgetting_rate
        time_factor = 1 - math.exp(-time_gap / 800)
        forget_factor = base_rate * time_factor
        return min(forget_factor, 0.15)

    def _random_traversal(self) -> None:
        """Random traversal: start from a random node and perform a random walk of 2-4 steps, record path and activate edges."""
        nodes = list(self.G.nodes())
        if len(nodes) < 2:
            return

        start_node = random.choice(nodes)
        path = [start_node]
        current_node = start_node
        path_length = random.randint(2, 4)

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

        if len(path) >= 2:
            self.traversal_history.append({
                'path': path.copy(),
                'iteration': self.iteration_count,
                'type': 'random_traversal'
            })

            current_time = self.iteration_count
            for i in range(len(path) - 1):
                u, v = path[i], path[i + 1]
                if self.G.has_edge(u, v):
                    self.record_edge_activation(u, v)

    def evolve(self, iterations: int = 1000, observation_interval: int = 100) -> Dict[str, List]:
        """Let the universe evolve naturally, observing emergence phenomena.

        :param iterations: Number of iterations
        :param observation_interval: Interval for taking network snapshots
        :return: observations dictionary
        """
        print(f"Starting cognitive universe evolution: {iterations} iterations")
        print("Executing only basic energy optimization, observing natural emergence...")

        initial_energy = self.calculate_network_energy()
        self.energy_history.append(initial_energy)
        print(f"Initial global energy: {initial_energy:.3f}")

        for i in range(iterations):
            self.iteration_count += 1

            self.basic_energy_optimization()

            if random.random() < 0.3:
                self._random_traversal()

            if i % 10 == 0:
                self.apply_basic_forgetting()

            current_energy = self.calculate_network_energy()
            self.energy_history.append(current_energy)

            if i % observation_interval == 0:
                self._take_network_snapshot()

            if i % 500 == 0:
                current_energy = self.calculate_network_energy()
                improvement = ((initial_energy - current_energy) / initial_energy * 100) if initial_energy > 0 else 0
                print(f"Iteration {i}: global energy = {current_energy:.3f} (improvement: {improvement:.1f}%)")

        final_energy = self.calculate_network_energy()
        total_improvement = ((initial_energy - final_energy) / initial_energy * 100) if initial_energy > 0 else 0

        print(f"\nEvolution completed!")
        print(f"Final global energy: {final_energy:.3f}")
        print(f"Total improvement: {total_improvement:.1f}%")
        print(f"Network size: {self.G.number_of_nodes()} nodes, {self.G.number_of_edges()} edges")
        print(f"Number of traversals: {len(self.traversal_history)}")

        return self.observations

    def _take_network_snapshot(self) -> None:
        """Record current network snapshot (statistics)."""
        snapshot = {
            'iteration': self.iteration_count,
            'global_energy': self.calculate_network_energy(),
            'node_count': self.G.number_of_nodes(),
            'edge_count': self.G.number_of_edges(),
            'average_degree': np.mean([d for n, d in self.G.degree()]) if self.G.number_of_nodes() > 0 else 0,
            'clustering_coefficient': nx.average_clustering(self.G) if self.G.number_of_nodes() > 0 else 0
        }
        self.observations['network_evolution_snapshots'].append(snapshot)

    def get_emergence_metrics(self) -> Dict[str, float]:
        """Get quantitative metrics of emergence phenomena."""
        metrics = {
            'energy_minimization_efficiency': 0,
            'structural_emergence_index': 0,
            'cognitive_complexity': 0,
            'adaptation_rate': 0
        }

        if len(self.energy_dynamics.global_energy_history) > 1:
            initial_energy = self.energy_dynamics.global_energy_history[0]
            final_energy = self.energy_dynamics.global_energy_history[-1]
            metrics['energy_minimization_efficiency'] = (
                initial_energy - final_energy) / initial_energy if initial_energy > 0 else 0

            energy_changes = np.diff(self.energy_dynamics.global_energy_history)
            negative_changes = [change for change in energy_changes if change < 0]
            metrics['adaptation_rate'] = len(negative_changes) / len(energy_changes) if energy_changes else 0

        if len(self.observations['network_evolution_snapshots']) > 1:
            initial_clustering = self.observations['network_evolution_snapshots'][0]['clustering_coefficient']
            final_clustering = self.observations['network_evolution_snapshots'][-1]['clustering_coefficient']
            metrics['structural_emergence_index'] = final_clustering - initial_clustering

            density = self.G.number_of_edges() / (self.G.number_of_nodes() *
                                                  (self.G.number_of_nodes() - 1) / 2) if self.G.number_of_nodes() > 1 else 0
            metrics['cognitive_complexity'] = density * final_clustering

        return metrics

    def report_emergence_findings(self) -> Dict[str, float]:
        """Print and return emergence observation report."""
        print("\n" + "=" * 60)
        print("Pure Emergence Observation Report")
        print("=" * 60)

        metrics = self.get_emergence_metrics()

        print(f"Energy minimization efficiency: {metrics['energy_minimization_efficiency']:.3f}")
        print(f"Structural emergence index: {metrics['structural_emergence_index']:.3f}")
        print(f"Cognitive complexity: {metrics['cognitive_complexity']:.3f}")
        print(f"Adaptation rate: {metrics['adaptation_rate']:.3f}")

        print(f"\nNetwork evolution snapshots: {len(self.observations['network_evolution_snapshots'])} records")
        print(f"Traversal patterns: {len(self.traversal_history)} traversals")

        if self.energy_dynamics.global_energy_history:
            energy_reduction = self.energy_dynamics.global_energy_history[0] - \
                               self.energy_dynamics.global_energy_history[-1]
            print(f"Total energy reduction: {energy_reduction:.3f}")

        print(f"\nObservation conclusions:")
        if metrics['energy_minimization_efficiency'] > 0.1:
            print("✓ Significant energy minimization trend observed")
        if metrics['structural_emergence_index'] > 0:
            print("✓ Self-organization of network structure observed")
        if metrics['adaptation_rate'] > 0.3:
            print("✓ Good environmental adaptability observed")

        return metrics

    def get_network_stats(self) -> Dict[str, Any]:
        """Return current network statistics."""
        return {
            'nodes': self.G.number_of_nodes(),
            'edges': self.G.number_of_edges(),
            'iterations': self.iteration_count,
            'global_energy': self.calculate_network_energy(),
            'traversal_count': len(self.traversal_history),
            'snapshots_count': len(self.observations['network_evolution_snapshots'])
        }


if __name__ == "__main__":
    universe = CognitiveUniverse()
    universe.initialize_semantic_network()
    universe.evolve(iterations=10000)
    print("CognitiveUniverse evolution test completed")