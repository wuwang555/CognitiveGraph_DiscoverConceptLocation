"""
Cognitive Graph Base Module
----------------
Define the BaseCognitiveGraph class, implementing the dynamic evolution of the cognitive network, including traversal,
forgetting, compression, migration and other core operations, and integrating a cognitive state manager to simulate
subjective energy changes.
"""

import networkx as nx
import numpy as np
import random
import math
from collections import defaultdict
from typing import Dict, Any, List, Optional, Tuple

from core.cognitive_states import CognitiveState, CognitiveStateManager

np.random.seed(42)
random.seed(42)

class BaseCognitiveGraph:
    """Base cognitive graph class, implementing energy dynamics-driven cognitive network evolution.

    This class encapsulates the core data structure (undirected graph) and operation methods of the cognitive graph.
    Edge weights represent cognitive energy. Through operations such as traversal, forgetting, compression, and migration,
    global energy minimization is achieved. It also integrates a cognitive state manager to simulate the influence of
    subjective cognitive states (focus, exploration, fatigue, inspiration) on behavioral strategies.

    :param individual_params: Dictionary of individual parameters, including forgetting rate, learning rate, biases, etc.
    :param network_seed: Random seed for reproducibility.
    """

    def __init__(self, individual_params: Dict[str, Any], network_seed: int = 42):
        self.G = nx.Graph()
        self.traversal_history = []          # Record traversal paths and types
        self.concept_centers = {}             # Record compressed concept centers
        self.iteration_count = 0
        self.energy_history = []              # Network average energy history

        # State management
        self.state_manager = CognitiveStateManager()

        # Individual parameters
        self.individual_params = individual_params
        self._setup_parameters(individual_params)

        self.last_activation_time = {}        # Record last activation time for each edge
        self.network_seed = network_seed

    def _setup_parameters(self, individual_params: Dict[str, Any]) -> None:
        """Parse individual cognitive parameters from the parameter dictionary.

        :param individual_params: Dictionary containing the following keys:
            - forgetting_rate: Forgetting rate
            - base_learning_rate: Base learning rate
            - hard_traversal_bias: Hard traversal bias
            - soft_traversal_bias: Soft traversal bias
            - compression_bias: Compression bias
            - migration_bias: Migration bias
            - learning_rate_variation: Learning rate variation coefficient
        """
        self.forgetting_rate = individual_params.get('forgetting_rate', 0.002)
        self.base_learning_rate = individual_params.get('base_learning_rate', 0.85)
        self.hard_traversal_bias = individual_params.get('hard_traversal_bias', 0.0)
        self.soft_traversal_bias = individual_params.get('soft_traversal_bias', 0.0)
        self.compression_bias = individual_params.get('compression_bias', 0.0)
        self.migration_bias = individual_params.get('migration_bias', 0.0)
        self.learning_rate_variation = individual_params.get('learning_rate_variation', 0.1)

        # Energy allocation strategy for hard and soft traversal
        self.hard_traversal_energy_ratio = 0.6
        self.soft_traversal_energy_ratio = 0.4

    @property
    def current_state(self) -> CognitiveState:
        """Current cognitive state (enum value)."""
        return self.state_manager.current_state

    @property
    def subjective_energy(self) -> float:
        """Subjective cognitive energy, reflecting the individual's current cognitive resource level."""
        return self.state_manager.subjective_energy

    @property
    def cognitive_energy_history(self) -> List[Dict]:
        """History of cognitive state changes."""
        return self.state_manager.cognitive_energy_history

    def update_cognitive_state(self) -> None:
        """Update cognitive state according to the transition matrix and record history."""
        self.state_manager.update_cognitive_state()

    def _update_subjective_energy(self) -> None:
        """Update subjective energy value based on current state."""
        self.state_manager._update_subjective_energy()

    def can_traverse_edge(self, edge_energy: float, traversal_type: str) -> Tuple[bool, float]:
        """Determine whether an edge can be traversed given the current subjective energy.

        :param edge_energy: Current energy (weight) of the edge
        :param traversal_type: Traversal type, 'hard' or 'soft'
        :return: (whether traversable, remaining energy balance)
        """
        if traversal_type == "hard":
            required_energy = edge_energy * 0.8
            available_energy = self.subjective_energy * self.hard_traversal_energy_ratio
        else:
            required_energy = edge_energy * 0.6
            available_energy = self.subjective_energy * self.soft_traversal_energy_ratio

        return available_energy >= required_energy, available_energy - required_energy

    def traverse_path(self, path: List[str], traversal_type: str = "hard") -> None:
        """Traverse along the specified path, update edge weights (learning effect), and record history.

        Traversal reduces the energy of edges along the path; the learning rate is influenced by traversal type,
        node similarity, and individual differences. After traversal, adjust cognitive state based on energy balance.

        :param path: List of nodes representing the traversal path
        :param traversal_type: Traversal type, 'hard' or 'soft'
        """
        # Randomly update cognitive state
        if random.random() < 0.1:
            self.update_cognitive_state()

        total_required_energy = 0
        for i in range(len(path) - 1):
            u, v = path[i], path[i + 1]
            if self.G.has_edge(u, v):
                total_required_energy += self.G[u][v]['weight']

        can_traverse, energy_balance = self.can_traverse_edge(total_required_energy, traversal_type)

        # Small chance to force traversal (simulating cognitive resource overdraft)
        if not can_traverse:
            if random.random() < 0.2 and self.current_state != CognitiveState.FATIGUED:
                can_traverse = True
                energy_balance = -0.5

        if not can_traverse:
            if random.random() < 0.3:
                self.state_manager.current_state = CognitiveState.FATIGUED
                self._update_subjective_energy()
            return

        self.traversal_history.append((path, traversal_type, self.iteration_count))
        current_time = self.iteration_count

        for i in range(len(path) - 1):
            u, v = path[i], path[i + 1]
            if self.G.has_edge(u, v):
                self.last_activation_time[(u, v)] = current_time
                if 'traversal_count' not in self.G[u][v]:
                    self.G[u][v]['traversal_count'] = 0
                self.G[u][v]['traversal_count'] += 1

                similarity = 0.5   # Default similarity; actual should be provided by semantic network
                base_rate = self.base_learning_rate

                individual_learning_variation = np.random.uniform(
                    1 - self.learning_rate_variation,
                    1 + self.learning_rate_variation
                )

                if traversal_type == "hard":
                    learning_rate = base_rate * (0.7 + 0.3 * similarity) * individual_learning_variation
                else:
                    learning_rate = base_rate * 0.9 * individual_learning_variation

                current_weight = self.G[u][v]['weight']
                learning_effect = learning_rate * (current_weight / 2.0)

                new_weight = max(0.05, current_weight * (1 - learning_effect))
                self.G[u][v]['weight'] = new_weight

        self._post_traversal_state_update(traversal_type, energy_balance)

    def _post_traversal_state_update(self, traversal_type: str, energy_balance: float) -> None:
        """Update cognitive state after traversal based on energy balance.

        :param traversal_type: Traversal type
        :param energy_balance: Remaining energy after traversal (can be positive or negative)
        """
        if energy_balance > 0.3:
            if traversal_type == "hard" and random.random() < 0.4:
                self.state_manager.current_state = CognitiveState.FOCUSED
            elif traversal_type == "soft" and random.random() < 0.3:
                self.state_manager.current_state = CognitiveState.EXPLORATORY
        elif energy_balance < -0.2:
            if random.random() < 0.5:
                self.state_manager.current_state = CognitiveState.FATIGUED

        self._update_subjective_energy()

    def _apply_forgetting(self) -> None:
        """Apply forgetting mechanism, increase energy of edges inactive for a long time (return to original weight)."""
        current_time = self.iteration_count

        for u, v in self.G.edges():
            time_since_last_activation = current_time - self.last_activation_time.get((u, v), 0)
            if time_since_last_activation > 0:
                current_energy = self.G[u][v]['weight']
                similarity = 0.5

                forget_factor = self.forgetting_function(
                    current_time,
                    self.last_activation_time.get((u, v), 0),
                    current_energy,
                    similarity
                )

                new_weight = self.G[u][v]['weight'] * (1 + forget_factor)
                original = self.G[u][v].get('original_weight', 2.0)
                self.G[u][v]['weight'] = min(new_weight, original)

    def forgetting_function(self, current_time: int, last_activation_time: int,
                            current_energy: float, similarity: float) -> float:
        """Calculate forgetting factor based on an exponential decay model.

        .. math::
            forget\_factor = (1 - e^{-\\Delta t / 500}) \\times
            (0.5 + 0.5 \\cdot \\frac{E}{2.0}) \\times (1 - 0.5 \\cdot sim) \\times forgetting\_rate

        :param current_time: Current iteration count
        :param last_activation_time: Last activation time
        :param current_energy: Current edge energy
        :param similarity: Semantic similarity of the two endpoint nodes
        :return: Forgetting factor (between 0 and 0.1)
        """
        time_gap = current_time - last_activation_time

        base_forgetting = 1 - math.exp(-time_gap / 500)
        energy_factor = 0.5 + 0.5 * (current_energy / 2.0)
        similarity_protection = 1 - (similarity * 0.5)

        forgetting_factor = (base_forgetting * energy_factor *
                             similarity_protection * self.forgetting_rate)

        return min(forgetting_factor, 0.1)

    def monte_carlo_iteration(self, max_iterations: int = 10000) -> None:
        """Perform Monte Carlo simulation, iteratively evolving the cognitive network.

        Each iteration includes:
            1. Periodic cognitive state update
            2. Apply forgetting mechanism
            3. Select operation (hard traversal, soft traversal, compression, migration) based on current state
            4. Record network energy history

        :param max_iterations: Maximum number of iterations
        """
        print(f"Initial cognitive state: {self.current_state.value}, subjective energy: {self.subjective_energy:.2f}")

        for iteration in range(max_iterations):
            self.iteration_count += 1

            if iteration % 100 == 0:
                self.update_cognitive_state()

            self._apply_forgetting()

            current_avg_energy = self.calculate_network_energy()
            self.energy_history.append(current_avg_energy)

            operation = self._select_operation_based_on_state()

            if operation == "hard_traversal":
                self._state_based_hard_traversal()
            elif operation == "soft_traversal":
                self._state_based_soft_traversal()
            elif operation == "compression":
                self._random_compression()
            elif operation == "migration":
                self._random_migration()

            if iteration % 500 == 0:
                stats = self.get_network_stats()
                print(f"Iteration {iteration}, State: {self.current_state.value}, "
                      f"Subjective energy: {self.subjective_energy:.2f}, Network energy: {current_avg_energy:.3f}")

    def _select_operation_based_on_state(self) -> str:
        """Select the next operation type based on the current cognitive state.

        State-operation probability mapping is defined by a predefined dictionary, with different probabilities
        for each operation under different states.

        :return: Operation name string
        """
        state_operations = {
            CognitiveState.FOCUSED: {
                "hard_traversal": 0.5,
                "soft_traversal": 0.3,
                "compression": 0.1,
                "migration": 0.1
            },
            CognitiveState.EXPLORATORY: {
                "hard_traversal": 0.3,
                "soft_traversal": 0.4,
                "compression": 0.1,
                "migration": 0.2
            },
            CognitiveState.FATIGUED: {
                "hard_traversal": 0.2,
                "soft_traversal": 0.4,
                "compression": 0.2,
                "migration": 0.2
            },
            CognitiveState.INSPIRED: {
                "hard_traversal": 0.3,
                "soft_traversal": 0.4,
                "compression": 0.1,
                "migration": 0.2
            }
        }

        probs = state_operations[self.current_state]
        rand_val = random.random()
        cumulative = 0
        for op, prob in probs.items():
            cumulative += prob
            if rand_val <= cumulative:
                return op
        return "hard_traversal"

    def _state_based_hard_traversal(self) -> None:
        """Initiate hard traversal based on current state: find and traverse a low-energy path."""
        available_nodes = list(self.G.nodes())
        if not available_nodes:
            return
        start_node = random.choice(available_nodes)
        path = self._find_hard_traversal_path(start_node, 3)
        if path and len(path) >= 2:
            self.traverse_path(path, "hard")

    def _state_based_soft_traversal(self) -> None:
        """Initiate soft traversal based on current state: random walk to explore new paths."""
        available_nodes = list(self.G.nodes())
        if not available_nodes:
            return
        start_node = random.choice(available_nodes)
        path = self._find_soft_traversal_path(start_node, 2)
        if path and len(path) >= 2:
            self.traverse_path(path, "soft")

    def _find_hard_traversal_path(self, start_node: str, max_length: int) -> Optional[List[str]]:
        """Find a hard traversal path: prioritize edges with lower energy, ensuring energy allowance.

        :param start_node: Starting node
        :param max_length: Maximum path length (number of nodes)
        :return: List of nodes (path) or None
        """
        path = [start_node]
        current_node = start_node

        for _ in range(max_length - 1):
            neighbors = list(self.G.neighbors(current_node))
            if not neighbors:
                break

            # Sort by energy ascending (low energy first)
            neighbors.sort(key=lambda n: self.G[current_node][n]['weight'])

            found_next = False
            for neighbor in neighbors[:3]:
                if neighbor not in path:
                    edge_energy = self.G[current_node][neighbor]['weight']
                    can_traverse, _ = self.can_traverse_edge(edge_energy, "hard")
                    if can_traverse:
                        path.append(neighbor)
                        current_node = neighbor
                        found_next = True
                        break

            if not found_next:
                break

        return path if len(path) >= 2 else None

    def _find_soft_traversal_path(self, start_node: str, max_length: int) -> Optional[List[str]]:
        """Find a soft traversal path: randomly select neighbors, subject to energy constraints.

        :param start_node: Starting node
        :param max_length: Maximum path length
        :return: List of nodes (path) or None
        """
        path = [start_node]
        current_node = start_node

        for _ in range(max_length - 1):
            neighbors = list(self.G.neighbors(current_node))
            if not neighbors:
                break

            random.shuffle(neighbors)

            found_next = False
            for neighbor in neighbors:
                if neighbor not in path:
                    edge_energy = self.G[current_node][neighbor]['weight']
                    can_traverse, _ = self.can_traverse_edge(edge_energy, "soft")
                    if can_traverse:
                        path.append(neighbor)
                        current_node = neighbor
                        found_next = True
                        break

            if not found_next:
                break

        return path if len(path) >= 2 else None

    def _random_compression(self) -> None:
        """Randomly attempt concept compression: select a center node; if it has enough strong connections, compress."""
        available_nodes = list(self.G.nodes())
        if len(available_nodes) < 3:
            return

        # Low probability trigger
        if random.random() > 0.10:
            return

        if self.iteration_count < 2000:
            return

        center_candidate = random.choice(available_nodes)

        good_neighbors = []
        for neighbor in self.G.neighbors(center_candidate):
            if (self.G[center_candidate][neighbor]['weight'] < 1.0 and
                self.calculate_semantic_similarity(center_candidate, neighbor) > 0.4):
                good_neighbors.append(neighbor)

        if len(good_neighbors) >= 3:
            num_to_compress = random.randint(2, min(3, len(good_neighbors)))
            nodes_to_compress = random.sample(good_neighbors, num_to_compress)

            compression_strength = random.uniform(0.4, 0.6)
            self.conceptual_compression(center_candidate, nodes_to_compress, compression_strength)

    def conceptual_compression(self, center_node: str, related_nodes: List[str],
                               compression_strength: float = 0.5) -> bool:
        """Execute concept compression: strengthen connections between center node and related nodes (reduce energy),
        encapsulating the microstructure.

        After compression, the edges between center node and related nodes have reduced energy, forming a macro-concept
        node, with internal structure encapsulated.

        :param center_node: Compression center node
        :param related_nodes: List of related nodes
        :param compression_strength: Compression strength factor (0~1); smaller means stronger compression
        :return: Whether compression was successfully performed
        """
        if len(related_nodes) < 2:
            return False

        for node in related_nodes:
            if self.G.has_edge(center_node, node):
                current_energy = self.G[center_node][node]['weight']
                compressed_energy = max(0.05, current_energy * compression_strength)
                self.G[center_node][node]['weight'] = compressed_energy

        self.concept_centers[center_node] = {
            'related_nodes': related_nodes,
            'compression_strength': compression_strength,
            'iteration': self.iteration_count
        }

        return True

    def _random_migration(self) -> None:
        """Randomly attempt first-principles migration: find a low-energy path between two nodes via principle nodes."""
        available_nodes = list(self.G.nodes())
        if len(available_nodes) < 4:
            return

        if random.random() > 0.05:
            return

        start_node, end_node = random.sample(available_nodes, 2)

        principle_candidates = [n for n in available_nodes
                                if n not in [start_node, end_node]]

        if not principle_candidates:
            return

        num_principles = random.randint(1, min(2, len(principle_candidates)))
        selected_principles = random.sample(principle_candidates, num_principles)

        exploration_bonus = random.uniform(0.05, 0.15)
        self.first_principles_migration(start_node, end_node, selected_principles, exploration_bonus)

    def first_principles_migration(self, start_node: str, end_node: str,
                                   principle_nodes: List[str], exploration_bonus: float = 0.1) -> Optional[List[str]]:
        """First-principles migration: find an indirect path through principle nodes that is more energy-efficient
        than the direct connection.

        Migration occurs only if the total energy of the new path is lower than the direct connection by at least
        improvement_threshold.

        :param start_node: Starting node
        :param end_node: Target node
        :param principle_nodes: List of candidate principle nodes
        :param exploration_bonus: Exploration bonus, reduces path energy to encourage new discoveries
        :return: Migration path (including principle nodes) or None
        """
        best_path = None
        best_energy = float('inf')

        # Direct connection energy
        direct_energy = float('inf')
        if self.G.has_edge(start_node, end_node):
            direct_energy = self.G[start_node][end_node]['weight']
            best_path = [start_node, end_node]
            best_energy = direct_energy

        # Try through each principle node
        for principle in principle_nodes:
            if (self.G.has_edge(start_node, principle) and
                    self.G.has_edge(principle, end_node)):

                path_energy = (self.G[start_node][principle]['weight'] +
                               self.G[principle][end_node]['weight'])

                # Apply exploration bonus
                adjusted_energy = path_energy - exploration_bonus

                if adjusted_energy < best_energy:
                    best_energy = adjusted_energy
                    best_path = [start_node, principle, end_node]

        # Require new path to be significantly better than direct path
        improvement_threshold = 0.2
        if (best_path and len(best_path) > 2 and
                best_energy < direct_energy * (1 - improvement_threshold)):

            # Strengthen connections along the migration path
            for i in range(len(best_path) - 1):
                u, v = best_path[i], best_path[i + 1]
                current = self.G[u][v]['weight']
                new_energy = max(0.05, current * random.uniform(0.6, 0.8))
                self.G[u][v]['weight'] = new_energy

            # Record migration relationship
            principle_node = best_path[1]
            if 'migration_bridges' not in self.G.nodes[principle_node]:
                self.G.nodes[principle_node]['migration_bridges'] = []

            self.G.nodes[principle_node]['migration_bridges'].append({
                'from': start_node,
                'to': end_node,
                'energy_saving': direct_energy - best_energy,
                'iteration': self.iteration_count
            })

            # Simulate traversing this newly discovered optimized path
            self.traverse_path(best_path, traversal_type="soft")

            return best_path

        return None

    def get_network_stats(self) -> Dict[str, Any]:
        """Get statistical information of the current network.

        :return: Dictionary containing node count, edge count, iteration count, average energy, compression centers count, migration bridges count
        """
        stats = {
            'nodes': self.G.number_of_nodes(),
            'edges': self.G.number_of_edges(),
            'iterations': self.iteration_count,
            'avg_energy': self.calculate_network_energy(),
            'compression_centers': len(self.concept_centers),
            'migration_bridges': 0
        }

        for node in self.G.nodes():
            if 'migration_bridges' in self.G.nodes[node]:
                stats['migration_bridges'] += len(self.G.nodes[node]['migration_bridges'])

        return stats

    def calculate_network_energy(self) -> float:
        """Calculate the average energy of the current network (mean of all edge weights)."""
        if self.G.number_of_edges() == 0:
            return 0
        energies = [self.G[u][v]['weight'] for u, v in self.G.edges()]
        return np.mean(energies)

    def calculate_semantic_similarity(self, node1: str, node2: str) -> float:
        """Calculate the semantic similarity between two nodes; default returns 0.5, subclasses should override to use real semantic information."""
        return 0.5

    def visualize_energy_convergence(self) -> None:
        """Visualize the energy convergence process (requires matplotlib and appropriate implementation)."""
        from utils.visualization import visualize_energy_convergence
        visualize_energy_convergence(self.energy_history, self.concept_centers)

    def visualize_cognitive_states(self) -> None:
        """Visualize cognitive state change history."""
        from utils.visualization import visualize_cognitive_states
        for i, entry in enumerate(self.cognitive_energy_history):
            if 'iteration' not in entry:
                entry['iteration'] = i
        visualize_cognitive_states(self.cognitive_energy_history, self.energy_history)

    def visualize_graph(self, title: str = "Cognitive Graph", figsize: Tuple[int, int] = (12, 8)) -> None:
        """Visualize the current cognitive graph structure."""
        from utils.visualization import visualize_graph
        visualize_graph(self.G, self.concept_centers, title, figsize)


if __name__ == "__main__":
    params = {
        'forgetting_rate': 0.002,
        'base_learning_rate': 0.85,
        'hard_traversal_bias': 0.1,
        'soft_traversal_bias': 0.1,
        'compression_bias': 0.05,
        'migration_bias': 0.05,
        'learning_rate_variation': 0.1
    }
    cg = BaseCognitiveGraph(params)
    # Additional test logic can be added...
    print("BaseCognitiveGraph initialized successfully")