"""
Enhanced Cognitive Graph Model Module
Includes semantic-based cognitive graph and energy-optimized cognitive graph.
"""

from core.cognitive_graph import BaseCognitiveGraph
from core.semantic_network import EnhancedSemanticConceptNetwork
from typing import Dict, Any, List


class SemanticEnhancedCognitiveGraph(BaseCognitiveGraph):
    """Semantically Enhanced Cognitive Graph - Simplified Version

    Initialize the network based on semantic similarity and provide semantic-based concept compression functionality.
    """

    def __init__(self, individual_params: Dict[str, Any], network_seed: int = 42, num_concepts: int = None):
        """Initialize semantically enhanced cognitive graph.

        Args:
            individual_params (Dict[str, Any]): Individual parameters.
            network_seed (int): Random seed.
            num_concepts (int, optional): Number of concept nodes. If None, use default count.
        """
        super().__init__(individual_params, network_seed)
        self.semantic_network = EnhancedSemanticConceptNetwork(num_concepts=num_concepts)
        self.semantic_network.build_comprehensive_network()

    def calculate_semantic_similarity(self, node1: str, node2: str) -> float:
        """Calculate semantic similarity between two nodes.

        According to formula (3) in the paper, sim(v_i, v_j) is used for the energy function.

        Args:
            node1 (str): First node name.
            node2 (str): Second node name.

        Returns:
            float: Semantic similarity, range [0,1].
        """
        return self.semantic_network.calculate_enhanced_similarity(node1, node2, "adaptive")

    def initialize_semantic_graph(self):
        """Initialize cognitive graph based on semantics.

        Create edges based on semantic similarity, with initial edge weights set to 2.0 - similarity * 1.5,
        simulating the initial state of the energy function E_ij = α(1-sim) + ... from the paper.
        """
        nodes = list(self.semantic_network.concept_definitions.keys())
        self.G.add_nodes_from(nodes)

        edge_count = 0
        for i, node1 in enumerate(nodes):
            for j, node2 in enumerate(nodes[i + 1:], i + 1):
                similarity = self.calculate_semantic_similarity(node1, node2)
                if similarity > 0.1:
                    energy = 2.0 - similarity * 1.5
                    energy = max(0.3, min(2.0, energy))

                    self.G.add_edge(node1, node2, weight=energy,
                                    original_weight=energy, traversal_count=0)
                    self.last_activation_time[(node1, node2)] = 0
                    edge_count += 1

        print(f"Semantic initialization: {len(nodes)} nodes, {edge_count} edges")

    def conceptual_compression_based_on_semantics(self, compression_threshold: float = 0.3):
        """Concept compression based on semantics.

        According to the triggering condition for concept compression (Equation 4) in the paper,
        find semantically similar node clusters and compress them.

        Args:
            compression_threshold (float): Similarity threshold; above this is considered similar.

        Returns:
            list: List of compressed groups, each element is (center, related_nodes).
        """
        compressed_groups = []
        processed_nodes = set()

        for node in self.G.nodes():
            if node in processed_nodes:
                continue

            # Find semantically similar nodes
            similar_nodes = [node]
            for other_node in self.G.nodes():
                if (other_node != node and other_node not in processed_nodes and
                        self.calculate_semantic_similarity(node, other_node) > compression_threshold):
                    similar_nodes.append(other_node)

            if len(similar_nodes) > 1:
                # Select center node
                center = self._select_compression_center(similar_nodes)
                if center:
                    related_nodes = [n for n in similar_nodes if n != center]
                    compressed_groups.append((center, related_nodes))
                    processed_nodes.update(similar_nodes)

                    # Perform compression
                    self.conceptual_compression(center, related_nodes, 0.4)
                    print(f"Semantic compression: {center} <- {related_nodes}")

        return compressed_groups

    def _select_compression_center(self, nodes: List[str]) -> str:
        """Select compression center node, i.e., the node with the highest average similarity to others.

        Args:
            nodes (List[str]): List of candidate nodes.

        Returns:
            str: Center node name.
        """
        best_center = None
        best_avg_similarity = 0

        for candidate in nodes:
            total_similarity = 0
            count = 0

            for other in nodes:
                if candidate != other:
                    similarity = self.calculate_semantic_similarity(candidate, other)
                    total_similarity += similarity
                    count += 1

            if count > 0:
                avg_similarity = total_similarity / count
                if avg_similarity > best_avg_similarity:
                    best_avg_similarity = avg_similarity
                    best_center = candidate

        return best_center


class EnergyOptimizedCognitiveGraph(SemanticEnhancedCognitiveGraph):
    """Energy-Optimized Cognitive Graph - Simplified Version

    Builds on the semantic enhancement, adding energy-optimized traversal and intelligent concept compression.
    """

    def __init__(self, individual_params: Dict[str, Any], network_seed: int = 42, num_concepts: int = None):
        """Initialize energy-optimized cognitive graph.

        Args:
            individual_params (Dict[str, Any]): Individual parameters.
            network_seed (int): Random seed.
            num_concepts (int, optional): Number of concept nodes.
        """
        super().__init__(individual_params, network_seed, num_concepts)
        self.energy_optimization_threshold = 0.3

    def energy_efficient_traversal(self, start_node: str, target_node: str, max_depth: int = 3):
        """Energy-efficient traversal (hybrid implementation of soft/hard traversal).

        According to the energy minimization principle from the paper, prioritize low-energy paths.

        Args:
            start_node (str): Starting node.
            target_node (str): Target node.
            max_depth (int): Maximum search depth.

        Returns:
            tuple: (path list, total energy)
        """
        def find_path(current, target, path, current_energy, visited, depth):
            if depth > max_depth or current == target:
                return path, current_energy

            best_path, best_energy = None, float('inf')
            neighbors = list(self.G.neighbors(current))

            # Sort by energy, prioritize low-energy paths (hard traversal)
            neighbors.sort(key=lambda n: self.G[current][n]['weight'])

            for neighbor in neighbors[:4]:  # Consider top 4 low-energy neighbors
                if neighbor not in visited:
                    edge_energy = self.G[current][neighbor]['weight']
                    new_energy = current_energy + edge_energy

                    if new_energy < best_energy * 1.5:  # Pruning
                        visited.add(neighbor)
                        candidate_path, candidate_energy = find_path(
                            neighbor, target, path + [neighbor], new_energy, visited, depth + 1
                        )
                        visited.remove(neighbor)

                        if candidate_energy < best_energy:
                            best_energy = candidate_energy
                            best_path = candidate_path

            return best_path, best_energy

        visited = {start_node}
        return find_path(start_node, target_node, [start_node], 0, visited, 0)

    def smart_concept_compression(self, compression_threshold: float = 0.4):
        """Intelligent concept compression, decide whether to compress based on expected energy savings.

        Corresponds to the triggering condition for concept compression in the paper:
        execute compression when the expected energy reduction exceeds the threshold.

        Args:
            compression_threshold (float): Compression threshold.

        Returns:
            list: List of successfully compressed groups, each element is (center, nodes, expected_saving).
        """
        compressed_groups = []

        # Find high-energy clusters
        high_energy_clusters = self._find_high_energy_clusters()

        for center, nodes in high_energy_clusters:
            if len(nodes) >= 2:
                expected_saving = self._calculate_compression_saving(center, nodes)

                if expected_saving > self.energy_optimization_threshold:
                    success = self.conceptual_compression(center, nodes, 0.5)
                    if success:
                        compressed_groups.append((center, nodes, expected_saving))
                        print(f"Intelligent compression: {center}, expected saving: {expected_saving:.3f}")

        return compressed_groups

    def _find_high_energy_clusters(self):
        """Find high-energy clusters, i.e., sets of nodes where the center has edges with high energy to neighbors.

        Returns:
            list: Each element is a tuple (center, neighbors).
        """
        clusters = []
        processed = set()

        for node in self.G.nodes():
            if node in processed:
                continue

            high_energy_neighbors = []
            for neighbor in self.G.neighbors(node):
                energy = self.G[node][neighbor]['weight']
                if energy > 1.0:  # High energy threshold
                    high_energy_neighbors.append(neighbor)

            if len(high_energy_neighbors) >= 2:
                clusters.append((node, high_energy_neighbors))
                processed.update(high_energy_neighbors)
                processed.add(node)

        return clusters

    def _calculate_compression_saving(self, center: str, nodes: List[str]) -> float:
        """Calculate the expected energy saving percentage from compression.

        According to the formula: saving = (current total energy - compressed total energy) / current total energy.
        Here we assume compressed energy decreases by 40% as an approximation.

        Args:
            center (str): Center node.
            nodes (List[str]): List of related nodes.

        Returns:
            float: Expected saving ratio.
        """
        current_total = sum(self.G[center][n]['weight'] for n in nodes if self.G.has_edge(center, n))
        compressed_total = current_total * 0.6  # Assume 40% reduction after compression
        return (current_total - compressed_total) / current_total if current_total > 0 else 0


if __name__ == "__main__":
    # Simple test: create a small cognitive graph and run basic functionality
    print("Testing EnhancedCognitiveGraph module...")
    params = {
        'forgetting_rate': 0.002,
        'base_learning_rate': 0.85,
        'hard_traversal_bias': 0.0,
        'soft_traversal_bias': 0.0,
        'compression_bias': 0.0,
        'migration_bias': 0.0,
        'learning_rate_variation': 0.1
    }
    graph = EnergyOptimizedCognitiveGraph(params, num_concepts=51)
    graph.initialize_semantic_graph()
    print("Initialization complete. Node count:", len(graph.G.nodes()))
    print("Edge count:", len(graph.G.edges()))
    print("Test passed.")