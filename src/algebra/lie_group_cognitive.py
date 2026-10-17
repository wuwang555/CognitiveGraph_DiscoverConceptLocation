# algebra/lie_group_cognitive.py
"""
Lie Group Description of Cognitive Evolution Module

According to Section 4.4 of the paper, continuous-time cognitive evolution can be described by the Lie group equation
dG/dt = A(t)G(t). This module implements Lie algebra generators (basic cognitive operations) and the evolution process
based on the exponential map.
"""

import numpy as np
import networkx as nx
from typing import List, Tuple, Dict
from scipy.linalg import expm

np.random.seed(42)

class LieAlgebraGenerator:
    """Lie algebra generator, corresponding to basic cognitive operations.

    Attributes:
        name (str): Generator name (e.g., "E" for energy optimization).
        matrix (np.ndarray): Effect matrix, representing the operation's influence on the network.
    """

    def __init__(self, name: str, effect_matrix: np.ndarray):
        """
        Args:
            name (str): Generator name.
            effect_matrix (np.ndarray): Matrix of shape (n, n) acting on the adjacency matrix.
        """
        self.name = name
        self.matrix = effect_matrix  # Operation effect matrix

    def __repr__(self):
        return f"LieAlgebraGenerator('{self.name}', shape={self.matrix.shape})"


class CognitiveLieGroup:
    """Lie group description of cognitive evolution.

    This class manages Lie algebra generators (energy optimization operator E, concept compression operator C,
    principle migration operator M) and provides an evolution method: via the exponential map exp(tA) to evolve the
    initial network along a specified direction.

    Attributes:
        network_size (int): Number of nodes in the network.
        generators (Dict[str, LieAlgebraGenerator]): Dictionary of generators.
    """

    def __init__(self, network_size: int):
        """
        Args:
            network_size (int): Number of nodes in the cognitive network, used to generate matrices of appropriate size.
        """
        self.network_size = network_size
        self.generators = {}

        # Define basic generators
        self._initialize_generators()

    def _initialize_generators(self):
        """Initialize Lie algebra generators: energy optimization (E), concept compression (C), principle migration (M)."""
        n = self.network_size

        # 1. Energy optimization operator E - reduces matrix elements (negative direction change)
        E_matrix = np.random.uniform(-0.1, -0.01, (n, n))
        np.fill_diagonal(E_matrix, 0)  # Diagonal zero
        self.generators['E'] = LieAlgebraGenerator('Energy Optimization', E_matrix)

        # 2. Concept compression operator C - increases correlation (makes some elements closer)
        C_matrix = np.zeros((n, n))
        for i in range(n):
            for j in range(n):
                if i != j:
                    # Compression effect: makes similar nodes closer
                    C_matrix[i, j] = np.random.uniform(-0.05, 0.05)
        self.generators['C'] = LieAlgebraGenerator('Concept Compression', C_matrix)

        # 3. Principle migration operator M - establishes new connections
        M_matrix = np.zeros((n, n))
        for i in range(n):
            for j in range(n):
                if i != j:
                    # Migration effect: moderate change
                    M_matrix[i, j] = np.random.uniform(-0.08, 0.08)
        self.generators['M'] = LieAlgebraGenerator('Principle Migration', M_matrix)

    def evolve_network(self, initial_network: nx.Graph,
                       time_steps: int = 10,
                       generator_coeffs: Dict[str, float] = None) -> List[nx.Graph]:
        """Evolve the cognitive network using Lie group.

        According to the evolution equation dG/dt = A(t)G(t), where A(t) is the linear combination of generators.
        Use the exponential map for discrete-time evolution: G(t+Δt) = exp(Δt * A) G(t).
        Here Δt is fixed at 0.1.

        Args:
            initial_network (nx.Graph): Initial cognitive network.
            time_steps (int): Number of evolution steps.
            generator_coeffs (Dict[str, float], optional): Coefficients for each generator,
                e.g., {'E':0.7, 'C':0.2, 'M':0.1}. Defaults to balanced coefficients.

        Returns:
            List[nx.Graph]: Snapshots of the network during evolution (including initial network).
        """
        if generator_coeffs is None:
            generator_coeffs = {'E': 0.5, 'C': 0.3, 'M': 0.2}

        # Construct Lie algebra element A = Σ coeff_i * generator_i.matrix
        A = np.zeros((self.network_size, self.network_size))
        for gen_name, coeff in generator_coeffs.items():
            if gen_name in self.generators:
                A += coeff * self.generators[gen_name].matrix

        networks = [initial_network]
        current_network = initial_network

        for t in range(1, time_steps + 1):
            # Exponential map: exp(t * A) (using fixed step 0.1, adjustable)
            exp_tA = expm(t * 0.1 * A)

            # Apply transformation to network
            new_network = self._apply_lie_transform(current_network, exp_tA)
            networks.append(new_network)
            current_network = new_network

        return networks

    def _apply_lie_transform(self, network: nx.Graph, transform_matrix: np.ndarray) -> nx.Graph:
        """Apply Lie transformation to the cognitive network: update the adjacency matrix using the transformation matrix.

        Args:
            network (nx.Graph): Input network.
            transform_matrix (np.ndarray): Transformation matrix (result of exponential map).

        Returns:
            nx.Graph: Transformed network.
        """
        # Combine network's adjacency matrix with transformation matrix
        nodes = list(network.nodes())
        adj_matrix = nx.to_numpy_array(network, nodelist=nodes)

        # Apply transformation (simplified: right-multiply adjacency matrix by transformation matrix)
        transformed_adj = adj_matrix @ transform_matrix

        # Create new network
        new_network = nx.Graph()
        new_network.add_nodes_from(nodes)

        n = len(nodes)
        for i in range(n):
            for j in range(i + 1, n):
                new_weight = transformed_adj[i, j]
                if new_weight > 0.01:  # Threshold, keep connections > 0.01
                    new_network.add_edge(nodes[i], nodes[j], weight=new_weight)

        return new_network


# Simple test
if __name__ == "__main__":
    # Create a 3-node complete graph
    G = nx.complete_graph(["A", "B", "C"])
    for u, v in G.edges():
        G[u][v]['weight'] = 1.0

    lie_group = CognitiveLieGroup(3)
    evolved = lie_group.evolve_network(G, time_steps=3, generator_coeffs={'E': 0.8, 'C': 0.1, 'M': 0.1})
    print(f"Evolution steps: {len(evolved)}")
    for i, net in enumerate(evolved):
        print(f"Step {i}: edges = {list(net.edges(data=True))}")