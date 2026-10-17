"""
Enhanced Cognitive Universe Module
-----------------
Inherits from CognitiveUniverse, adds EmergenceDetectorFixed for real-time emergence detection,
and supports building networks with a specified number of concepts.
"""

from typing import Dict, Any, Optional
import random

from emergence.universe import CognitiveUniverse
from emergence.detector_fixed import EmergenceDetectorFixed


random.seed(42)

class CognitiveUniverseEnhanced(CognitiveUniverse):
    """Enhanced cognitive universe that uses EmergenceDetectorFixed to detect emergence during evolution."""

    def __init__(self, individual_params: Optional[Dict[str, Any]] = None,
                 network_seed: int = 42, num_concepts: Optional[int] = None):
        """
        :param individual_params: Individual parameters
        :param network_seed: Random seed
        :param num_concepts: Number of concepts to use when building the semantic network
        """
        super().__init__(individual_params, network_seed)
        self.emergence_detector = EmergenceDetectorFixed()
        self.observations = {
            'natural_compressions': [],
            'natural_migrations': [],
            'energy_convergence_phases': []
        }
        self.num_concepts = num_concepts

    def initialize_semantic_network(self) -> None:
        """Initialize semantic network, supporting a specified number of concepts."""
        from core.semantic_network import SemanticConceptNetwork

        semantic_net = SemanticConceptNetwork()
        semantic_net.build_comprehensive_network(num_concepts=self.num_concepts)

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

    def evolve_with_emergence_detection(self, iterations: int = 1000,
                                        detection_interval: int = 200) -> Dict[str, list]:
        """Evolution process with emergence detection.

        :param iterations: Number of iterations
        :param detection_interval: Interval for emergence detection
        :return: Dictionary of observed emergence events
        """
        print(f"Starting enhanced evolution: {iterations} iterations, detection interval: {detection_interval}")

        initial_energy = self.calculate_network_energy()
        self.energy_history = [initial_energy]

        for i in range(iterations):
            self.iteration_count += 1

            self.basic_energy_optimization()

            if random.random() < 0.3:
                self._random_traversal()

            if i % 10 == 0:
                self.apply_basic_forgetting()

            current_energy = self.calculate_network_energy()
            self.energy_history.append(current_energy)

            if i % detection_interval == 0 and i > 200:
                self._detect_emergence(i)

            if i % 500 == 0:
                improvement = ((initial_energy - current_energy) / initial_energy * 100) if initial_energy > 0 else 0
                print(f"Iteration {i}: energy = {current_energy:.3f} (improvement: {improvement:.1f}%)")
                print(f"  Detected compressions: {len(self.observations['natural_compressions'])}")
                print(f"  Detected migrations: {len(self.observations['natural_migrations'])}")

        return self.observations

    def _detect_emergence(self, iteration: int) -> None:
        """Perform emergence detection and record new events."""
        # Detect concept compression
        compressions = self.emergence_detector.detect_spontaneous_compression(
            self.G, self.energy_history, self.traversal_history
        )

        for compression in compressions:
            if not self._is_duplicate_compression(compression):
                compression['detection_iteration'] = iteration
                self.observations['natural_compressions'].append(compression)
                print(f"🎯 Iteration {iteration}: Natural concept compression discovered!")
                print(f"   Center: {compression['center']}, cluster size: {compression['cluster_size']}")
                print(f"   Strength: {compression['emergence_strength']:.3f}")

        # Detect principle migration
        migrations = self.emergence_detector.detect_emergent_migration(
            self.G, self.traversal_history, iteration
        )

        for migration in migrations:
            if not self._is_duplicate_migration(migration):
                migration['detection_iteration'] = iteration
                self.observations['natural_migrations'].append(migration)
                print(f"🌉 Iteration {iteration}: Natural principle migration discovered!")
                print(f"   Principle: {migration['principle_node']}")
                print(f"   Path: {migration['from_node']} -> {migration['to_node']}")
                print(f"   Efficiency: {migration['efficiency_gain']:.3f}")

    def _is_duplicate_compression(self, new_compression: Dict) -> bool:
        """Check if the same compression event has already been recorded."""
        for existing in self.observations['natural_compressions']:
            if (existing['center'] == new_compression['center'] and
                    set(existing['related_nodes']) == set(new_compression['related_nodes'])):
                return True
        return False

    def _is_duplicate_migration(self, new_migration: Dict) -> bool:
        """Enhanced duplicate migration check, including reverse paths and recent frequency."""
        principle_node = new_migration['principle_node']
        from_node = new_migration['from_node']
        to_node = new_migration['to_node']

        # Exact same migration
        for existing in self.observations['natural_migrations']:
            if (existing['principle_node'] == principle_node and
                    existing['from_node'] == from_node and
                    existing['to_node'] == to_node):
                return True

        # Reverse direction migration
        for existing in self.observations['natural_migrations']:
            if (existing['principle_node'] == principle_node and
                    existing['from_node'] == to_node and
                    existing['to_node'] == from_node):
                return True

        # Same principle node appears too frequently recently
        recent_count = 0
        for existing in self.observations['natural_migrations'][-10:]:
            if existing['principle_node'] == principle_node:
                recent_count += 1
                if recent_count >= 3:
                    return True

        return False


if __name__ == "__main__":
    enhanced = CognitiveUniverseEnhanced(num_concepts=51)
    enhanced.initialize_semantic_network()
    enhanced.evolve_with_emergence_detection(iterations=10000)
    print("CognitiveUniverseEnhanced test completed")