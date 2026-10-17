# algebra/cognitive_symmetry.py
"""
Cognitive Symmetry Group Module

According to Section 4.2 of the paper, the cognitive symmetry group is the set of transformations that preserve
key properties of the cognitive network. This module implements concept isomorphism detection, conserved quantity
calculation, and verification of the Noether-type proposition.
"""

import networkx as nx
import numpy as np
from typing import List, Dict, Set, Tuple, Any
import itertools
from networkx.algorithms.isomorphism import GraphMatcher
import math
import random

np.random.seed(42)
random.seed(42)

class CognitiveSymmetryGroup:
    """Cognitive Symmetry Group Implementation.

    This class is responsible for detecting concept isomorphisms (node permutations that preserve edge weights),
    calculating conserved quantities (global energy, structural entropy, fractal dimension), and verifying
    the Noether-type proposition.

    Attributes:
        network (nx.Graph): Current cognitive network.
        automorphisms (List[Dict]): List of found automorphisms.
        conserved_quantities (Dict): Calculated conserved quantities.
    """

    def __init__(self, network: nx.Graph):
        """
        Args:
            network (nx.Graph): The cognitive network to analyze.
        """
        self.network = network
        self.automorphisms = []
        self.conserved_quantities = {}

    def find_concept_isomorphisms(self, max_samples=1000) -> List[Dict]:
        """Find concept isomorphisms (semantics-preserving node permutations).

        Since isomorphism detection is NP-hard, a random sampling approximation is used for large networks.
        Strategy description:
        - Node count ≤ 8: exhaustive enumeration of permutations, but limit to checking at most 1000 (may be less than total permutations).
        - Node count 9~12: use networkx's GraphMatcher for exact search.
        - Node count > 12: random sampling of permutations, fast degree sequence filtering followed by isomorphism verification.

        Args:
            max_samples (int): Maximum number of samples (for large networks).

        Returns:
            List[Dict]: Each dictionary represents an automorphism mapping {original node: mapped node}.
        """
        nodes = list(self.network.nodes())
        n = len(nodes)
        automorphisms = []

        # ---------- Strategy 1: Small networks (≤8), exhaustive enumeration ----------
        if n <= 8:
            permutations = itertools.permutations(range(n))
            total_perms = math.factorial(n)
            max_to_check = min(1000, total_perms)  # Check at most 1000
            checked = 0
            for perm in permutations:
                if checked >= max_to_check:
                    break
                checked += 1
                # Quick filter: degree sequence match
                if [self.network.degree(nodes[i]) for i in perm] != [self.network.degree(nodes[i]) for i in range(n)]:
                    continue
                if self._is_isomorphism(perm, nodes):
                    mapping = {nodes[i]: nodes[perm[i]] for i in range(n)}
                    automorphisms.append(mapping)
            # Add identity mapping after exhaustive search (just in case, exhaustive should find it)
            identity = {node: node for node in nodes}
            if identity not in automorphisms:
                automorphisms.append(identity)
            print(f"Exhaustively checked {checked} permutations, found {len(automorphisms)} automorphisms")
            return automorphisms

        # ---------- Strategy 2: Medium scale (9 ≤ n ≤ 12), use GraphMatcher exact search ----------
        if 9 <= n <= 12:
            try:
                # Define edge matching function: edge weights should be approximately equal
                def edge_match(e1_attr, e2_attr):
                    return np.isclose(e1_attr.get('weight', 0), e2_attr.get('weight', 0), rtol=0.2)

                GM = GraphMatcher(self.network, self.network,
                                  node_match=lambda n1, n2: True,  # No extra node attributes, always match
                                  edge_match=edge_match)

                for mapping in GM.isomorphisms_iter():
                    # mapping is already {original node: mapped node}, add directly
                    automorphisms.append(mapping)

            except Exception as e:
                print(f"GraphMatcher error: {e}, falling back to random sampling")
                automorphisms = self._random_sample_automorphisms(nodes, max_samples)

        # ---------- Strategy 3: Large networks (>12), random sampling + enforce identity ----------
        automorphisms = self._random_sample_automorphisms(nodes, max_samples)
        # Ensure identity mapping is included
        nodes = list(self.network.nodes())
        identity = {node: node for node in nodes}
        if identity not in automorphisms:
            automorphisms.append(identity)
            print("Forced addition of identity mapping (may be missed by random sampling)")

        # Store results in instance attribute
        self.automorphisms = automorphisms

        return automorphisms

    def _is_isomorphism(self, perm, nodes):
        """Check whether permutation perm preserves edges and weights (used for exhaustive and random sampling).

        Args:
            perm (tuple): Index permutation of nodes.
            nodes (list): List of nodes.

        Returns:
            bool: True if it is an automorphism.
        """
        # Sample some edges to speed up (identity mapping will always pass)
        edges_to_check = list(self.network.edges())
        if len(edges_to_check) > 20:
            edges_to_check = random.sample(edges_to_check, 20)
        for u, v in edges_to_check:
            i, j = nodes.index(u), nodes.index(v)
            v1, v2 = nodes[perm[i]], nodes[perm[j]]
            if not self.network.has_edge(v1, v2):
                return False
            w_orig = self.network[u][v]['weight']
            w_perm = self.network[v1][v2]['weight']
            if not np.isclose(w_orig, w_perm, rtol=0.2):
                return False
        return True

    def _random_sample_automorphisms(self, nodes, max_samples):
        """Randomly sample permutations to find automorphisms (excluding identity mapping, as probability is low).

        Args:
            nodes (list): List of nodes.
            max_samples (int): Maximum number of samples.

        Returns:
            list: List of found automorphism mappings.
        """
        n = len(nodes)
        automorphisms = []
        degree_seq = [self.network.degree(node) for node in nodes]
        for _ in range(max_samples):
            perm = list(range(n))
            random.shuffle(perm)
            # Quick degree sequence filter
            if [degree_seq[i] for i in perm] != degree_seq:
                continue
            if self._is_isomorphism(perm, nodes):
                mapping = {nodes[i]: nodes[perm[i]] for i in range(n)}
                automorphisms.append(mapping)
        return automorphisms

    def compute_conserved_quantities(self) -> Dict[str, float]:
        """Compute conserved quantities of the cognitive system.

        According to the Noether-type proposition, symmetries correspond to conserved quantities. Here we compute:
        - Global cognitive energy (total weight) – corresponds to time translation symmetry
        - Structural entropy (degree distribution entropy) – corresponds to concept permutation symmetry
        - Fractal dimension (clustering coefficient / average shortest path) – corresponds to scale transformation symmetry

        Returns:
            Dict[str, float]: Mapping from conserved quantity name to value.
        """
        conserved = {}

        # 1. Global energy conservation (time translation symmetry)
        total_energy = sum(self.network[u][v]['weight']
                           for u, v in self.network.edges())
        conserved['total_energy'] = total_energy

        # 2. Structural entropy conservation (concept permutation symmetry)
        degrees = [d for _, d in self.network.degree()]
        if degrees:
            degree_dist = np.histogram(degrees, bins=min(10, len(set(degrees))))[0]
            degree_dist = degree_dist / np.sum(degree_dist)
            entropy = -np.sum(degree_dist * np.log(degree_dist + 1e-10))
            conserved['structural_entropy'] = entropy
        else:
            conserved['structural_entropy'] = 0.0

        # 3. Fractal dimension conservation (scale transformation symmetry)
        # Use weighted network
        try:
            # Use reciprocal of weight as distance (higher energy → farther distance)
            weighted_network = self.network.copy()
            for u, v in weighted_network.edges():
                weight = weighted_network[u][v]['weight']
                # Avoid division by zero
                if weight > 0:
                    weighted_network[u][v]['distance'] = 1.0 / weight
                else:
                    weighted_network[u][v]['distance'] = 100.0  # Very large distance

            # Compute weighted clustering coefficient
            if nx.is_connected(weighted_network):
                # Use networkx's weighted clustering coefficient
                clustering = nx.average_clustering(weighted_network, weight='distance')

                # Compute weighted average shortest path
                try:
                    # Use Floyd-Warshall algorithm to compute all-pairs shortest paths
                    import itertools
                    path_lengths = []
                    nodes = list(weighted_network.nodes())

                    for i, src in enumerate(nodes):
                        for dst in nodes[i + 1:]:
                            try:
                                # Use Dijkstra's algorithm to compute shortest path
                                length = nx.dijkstra_path_length(weighted_network, src, dst, weight='distance')
                                path_lengths.append(length)
                            except nx.NetworkXNoPath:
                                # Skip if no path
                                continue

                    if path_lengths:
                        avg_path_length = np.mean(path_lengths)
                        fractal_dim = clustering / (avg_path_length + 1e-8)
                        conserved['fractal_dimension'] = fractal_dim
                    else:
                        conserved['fractal_dimension'] = 0.0

                except Exception as e:
                    print(f"Error computing average shortest path: {e}")
                    conserved['fractal_dimension'] = 0.0
            else:
                conserved['fractal_dimension'] = 0.0

        except Exception as e:
            print(f"Error computing fractal dimension: {e}")
            conserved['fractal_dimension'] = 0.0

        self.conserved_quantities = conserved
        return conserved

    def verify_noether_theorem(self, before_network: nx.Graph, after_network: nx.Graph,
                               transformation_type: str,
                               tolerance: float = 0.2) -> Tuple[bool, Dict]:
        """Verify the Noether-type proposition: whether conserved quantities remain unchanged under symmetry transformations.

        Args:
            before_network (nx.Graph): Network before transformation.
            after_network (nx.Graph): Network after transformation.
            transformation_type (str): Type of transformation (only used for logging).
            tolerance (float): Allowed relative change threshold.

        Returns:
            Tuple[bool, Dict]: First element indicates whether all conserved quantities are preserved;
                second element provides detailed change information for each conserved quantity, including before, after, relative_change, and conserved.
        """
        before_group = CognitiveSymmetryGroup(before_network)
        after_group = CognitiveSymmetryGroup(after_network)

        before_conserved = before_group.compute_conserved_quantities()
        after_conserved = after_group.compute_conserved_quantities()

        all_conserved = True
        conservation_details = {}

        for key in before_conserved.keys():
            if key in after_conserved:
                before_val = before_conserved[key]
                after_val = after_conserved[key]

                # Handle cases where before_val may be zero
                if abs(before_val) < 1e-10 and abs(after_val) < 1e-10:
                    is_conserved = True
                elif abs(before_val) < 1e-10:
                    is_conserved = False
                else:
                    relative_change = abs(before_val - after_val) / abs(before_val)
                    is_conserved = relative_change < tolerance

                conservation_details[key] = {
                    'before': before_val,
                    'after': after_val,
                    'relative_change': relative_change if abs(before_val) > 1e-10 else float('inf'),
                    'conserved': is_conserved
                }

                if not is_conserved:
                    all_conserved = False
                    print(f"Conserved quantity {key} changed beyond threshold {tolerance * 100:.0f}%: "
                          f"{before_val:.3f} -> {after_val:.3f} "
                          f"(change: {relative_change * 100:.1f}%)")

        return all_conserved, conservation_details


# Simple test
if __name__ == "__main__":
    G = nx.Graph()
    nodes = ["A", "B", "C"]
    G.add_nodes_from(nodes)
    G.add_edge("A", "B", weight=1.0)
    G.add_edge("B", "C", weight=1.0)
    G.add_edge("A", "C", weight=1.0)

    sym = CognitiveSymmetryGroup(G)
    autos = sym.find_concept_isomorphisms()
    conserved = sym.compute_conserved_quantities()
    print(f"Found {len(autos)} automorphisms")
    print(f"Conserved quantities: {conserved}")