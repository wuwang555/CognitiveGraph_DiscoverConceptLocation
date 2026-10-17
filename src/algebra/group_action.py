# algebra/group_action.py
"""
Group Action Module

According to Section 4.3 of the paper, the cognitive symmetry group acts on the cognitive state space.
This module implements group actions, orbit and stabilizer calculation, and verifies the orbit-stabilizer theorem.
"""

import networkx as nx
import numpy as np
from typing import List, Dict, Set, Tuple


class GroupActionOnCognitiveSpace:
    """Group action on cognitive state space.

    This class encapsulates the action of the symmetry group on the cognitive network, including
    computing orbits, stabilizers, and verifying the orbit-stabilizer theorem (Theorem 4.3.3).

    Attributes:
        group (CognitiveSymmetryGroup): The associated cognitive symmetry group.
        orbits_cache (dict): Cache for computed orbits, keyed by network hash.
        stabilizers_cache (dict): Cache for computed stabilizers.
    """

    def __init__(self, symmetry_group: 'CognitiveSymmetryGroup'):
        """
        Args:
            symmetry_group: An instance of the cognitive symmetry group.
        """
        self.group = symmetry_group
        self.orbits_cache = {}
        self.stabilizers_cache = {}

    def apply_group_element(self, network: nx.Graph,
                            permutation: Dict) -> nx.Graph:
        """Apply a group element (node permutation) to the cognitive network.

        Args:
            network (nx.Graph): Original network.
            permutation (Dict): Permutation mapping, e.g., {old node: new node}.

        Returns:
            nx.Graph: New network after permutation.
        """
        new_network = nx.Graph()
        # Add nodes (using permuted names)
        for node in network.nodes():
            new_node = permutation.get(node, node)
            new_network.add_node(new_node)
        # Add edges (preserve weights)
        for u, v, data in network.edges(data=True):
            new_u = permutation.get(u, u)
            new_v = permutation.get(v, v)
            # Deep copy edge data to avoid reference
            new_data = data.copy()
            new_network.add_edge(new_u, new_v, **new_data)
        return new_network

    def compute_orbit(self, network: nx.Graph) -> List[nx.Graph]:
        """Compute the orbit of a cognitive state (all images under the group action).

        The orbit is defined as { g·network | g ∈ group }.

        Args:
            network (nx.Graph): Initial network.

        Returns:
            List[nx.Graph]: List of networks in the orbit (deduplicated).
        """
        network_hash = self._network_hash(network)
        if network_hash in self.orbits_cache:
            return self.orbits_cache[network_hash]

        orbit_set = set()  # Store hashes to avoid duplicates
        orbit_networks = []
        for g in self.group.automorphisms:
            transformed = self.apply_group_element(network, g)
            h = self._network_hash(transformed)
            if h not in orbit_set:
                orbit_set.add(h)
                orbit_networks.append(transformed)

        self.orbits_cache[network_hash] = orbit_networks
        return orbit_networks

    def compute_stabilizer(self, network: nx.Graph) -> List[Dict]:
        """Compute the stabilizer subgroup of a cognitive state (group elements that leave the network unchanged).

        The stabilizer is defined as { g ∈ group | g·network = network }.

        Args:
            network (nx.Graph): Initial network.

        Returns:
            List[Dict]: List of automorphisms in the stabilizer.
        """
        network_hash = self._network_hash(network)
        if network_hash in self.stabilizers_cache:
            return self.stabilizers_cache[network_hash]

        stabilizer = []
        for g in self.group.automorphisms:
            transformed = self.apply_group_element(network, g)
            if self._networks_equal(network, transformed):
                stabilizer.append(g)

        self.stabilizers_cache[network_hash] = stabilizer
        return stabilizer

    def verify_orbit_stabilizer_theorem(self, network: nx.Graph) -> bool:
        """Verify the orbit-stabilizer theorem: |Orbit| = |Group| / |Stabilizer|.

        Theorem 4.3.3: For finite group actions, |O_G| = |G| / |Stab(G)|.

        Args:
            network (nx.Graph): Initial network.

        Returns:
            bool: Whether the theorem holds (in integer sense).

        Raises:
            ValueError: If the group is empty or stabilizer is empty (should at least contain identity).
        """
        if len(self.group.automorphisms) == 0:
            raise ValueError("Group is empty, cannot verify theorem")
        stabilizer = self.compute_stabilizer(network)
        if len(stabilizer) == 0:
            # In theory, identity should always be present; if not, implementation error
            raise ValueError("Stabilizer is empty; automorphism detection may have missed identity")
        orbit = self.compute_orbit(network)
        expected = len(self.group.automorphisms) / len(stabilizer)
        # Expected value should be integer (by Lagrange's theorem)
        if not expected.is_integer():
            return False
        return len(orbit) == int(expected)

    def _network_hash(self, network: nx.Graph) -> str:
        """Generate a simple hash representation of the network (for caching and deduplication).

        Args:
            network (nx.Graph): Network.

        Returns:
            str: String representation based on sorted edge weights.
        """
        edges = sorted([(u, v, network[u][v]['weight'])
                        for u, v in network.edges()])
        return str(edges)

    def _networks_equal(self, G1: nx.Graph, G2: nx.Graph, rtol: float = 1e-5) -> bool:
        """Compare two networks for equality (considering nodes, edges, and weights).

        Args:
            G1 (nx.Graph): First network.
            G2 (nx.Graph): Second network.

        Returns:
            bool: True if network structures and weights are identical.
        """
        if set(G1.nodes()) != set(G2.nodes()):
            return False
        if G1.number_of_edges() != G2.number_of_edges():
            return False

        # Compare edges and weights
        for u, v in G1.edges():
            if not G2.has_edge(u, v):
                return False
            w1 = G1[u][v].get('weight', 0.0)
            w2 = G2[u][v].get('weight', 0.0)
            if not np.isclose(w1, w2, rtol=rtol):
                return False
        return True


# Simple test
if __name__ == "__main__":
    from algebra.cognitive_symmetry import CognitiveSymmetryGroup

    G = nx.Graph()
    nodes = ["A", "B"]
    G.add_nodes_from(nodes)
    G.add_edge("A", "B", weight=1.0)

    sym_group = CognitiveSymmetryGroup(G)
    sym_group.automorphisms = [{"A": "A", "B": "B"}, {"A": "B", "B": "A"}]  # Manually set

    action = GroupActionOnCognitiveSpace(sym_group)
    orbit = action.compute_orbit(G)
    stabilizer = action.compute_stabilizer(G)
    print(f"Orbit size: {len(orbit)}")
    print(f"Stabilizer size: {len(stabilizer)}")
    print(f"Theorem holds: {action.verify_orbit_stabilizer_theorem(G)}")