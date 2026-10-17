# algebra/cognitive_semigroup.py
"""
Cognitive Operation Semigroup Module

According to Theorem 4.1.3 in the paper, basic cognitive operations form a semigroup under composition.
This module defines cognitive operations (CognitiveOperation) and the semigroup formed by these operations
(CognitiveSemigroup), and provides associativity verification functionality.
"""

import networkx as nx
from typing import List, Tuple, Callable
import numpy as np


class CognitiveOperation:
    """Algebraic representation of a basic cognitive operation.

    Each operation is a callable object that takes a cognitive network and returns a transformed network.

    Attributes:
        name (str): Operation name (e.g., "learning").
        operation (Callable): The specific operation function, signature should be
            func(network: nx.Graph, **kwargs) -> nx.Graph.
    """

    def __init__(self, name: str, operation_func: Callable):
        """
        Args:
            name (str): Operation name.
            operation_func (Callable): Operation function, should accept network and arbitrary keyword arguments,
                and return the transformed network.
        """
        self.name = name
        self.operation = operation_func

    def __call__(self, network: nx.Graph, **kwargs):
        """Call the operation function.

        Args:
            network (nx.Graph): Input cognitive network.
            **kwargs: Additional arguments passed to the operation function (e.g., learning rate, path, etc.).

        Returns:
            nx.Graph: Transformed network.
        """
        return self.operation(network, **kwargs)

    def __repr__(self):
        return f"CognitiveOperation('{self.name}')"


class CognitiveSemigroup:
    """Cognitive Operation Semigroup - Algebraic Implementation.

    This class maintains an operation dictionary and provides functionality for operation composition
    and associativity verification. Operation composition is defined as (op2 ∘ op1)(G) = op2(op1(G)),
    i.e., op1 is applied first, then op2.

    Attributes:
        operations (dict): Mapping from operation name to CognitiveOperation object.
        composition_table (dict): Cache of created composite operations, keyed by (op1, op2).
    """

    def __init__(self):
        self.operations = {}          # operation name -> CognitiveOperation
        self.composition_table = {}    # (op1, op2) -> composite operation name

    def add_operation(self, name: str, operation_func: Callable) -> CognitiveOperation:
        """Add a cognitive operation to the semigroup.

        Args:
            name (str): Operation name, should be unique.
            operation_func (Callable): Operation function.

        Returns:
            CognitiveOperation: The created operation object.
        """
        op = CognitiveOperation(name, operation_func)
        self.operations[name] = op
        return op

    def compose(self, op1: str, op2: str) -> CognitiveOperation:
        """Compose two operations: return the composite operation op2 ∘ op1 (apply op1 first, then op2).

        Args:
            op1 (str): Name of the first operation.
            op2 (str): Name of the second operation.

        Returns:
            CognitiveOperation: The composite operation object.
        """
        key = (op1, op2)
        if key not in self.composition_table:
            def composed_op(network, **kwargs):
                # Apply the first operation
                result1 = self.operations[op1](network, **kwargs)
                # Apply the second operation
                result2 = self.operations[op2](result1, **kwargs)
                return result2

            comp_name = f"{op1}∘{op2}"
            self.composition_table[key] = self.add_operation(comp_name, composed_op)

        return self.composition_table[key]

    def verify_associativity(self, op1: str, op2: str, op3: str, test_network: nx.Graph) -> bool:
        """Verify associativity: (op3 ∘ op2) ∘ op1 = op3 ∘ (op2 ∘ op1).

        Checks by comparing whether the total energy after applying the two composite operations to test_network
        are approximately equal.

        Args:
            op1 (str): Name of the first operation.
            op2 (str): Name of the second operation.
            op3 (str): Name of the third operation.
            test_network (nx.Graph): Initial network for testing.

        Returns:
            bool: True if associativity holds, False otherwise.
        """
        left = self.compose(op1, self.compose(op2, op3).name)
        right = self.compose(self.compose(op1, op2).name, op3)

        # Verify on test network
        result_left = left(test_network.copy())
        result_right = right(test_network.copy())

        # Compare network structure (simplified: total energy)
        left_energy = sum(result_left[u][v]['weight'] for u, v in result_left.edges())
        right_energy = sum(result_right[u][v]['weight'] for u, v in result_right.edges())

        return np.isclose(left_energy, right_energy, rtol=1e-5)

    def find_identity(self, test_network: nx.Graph) -> str:
        """Find a possible identity element (optional; semigroups do not necessarily have identity).

        An identity element e satisfies: for any operation o, e∘o = o and o∘e = o.

        Args:
            test_network (nx.Graph): Initial network for testing.

        Returns:
            str or None: The name of the identity element if found, otherwise None.
        """
        for op_name, op in self.operations.items():
            identity = True
            for other_name, other_op in self.operations.items():
                # Check op ∘ other = other and other ∘ op = other
                comp1 = self.compose(other_name, op_name)
                comp2 = self.compose(op_name, other_name)

                result1 = comp1(test_network.copy())
                result2 = comp2(test_network.copy())
                result_other = other_op(test_network.copy())

                # Simplified comparison: energies are close
                energy1 = sum(result1[u][v]['weight'] for u, v in result1.edges())
                energy2 = sum(result2[u][v]['weight'] for u, v in result2.edges())
                energy_other = sum(result_other[u][v]['weight'] for u, v in result_other.edges())

                if not (np.isclose(energy1, energy_other, rtol=1e-5) and
                        np.isclose(energy2, energy_other, rtol=1e-5)):
                    identity = False
                    break

            if identity:
                return op_name
        return None


# Simple test
if __name__ == "__main__":
    # Create a simple network for testing
    G = nx.Graph()
    G.add_nodes_from(["A", "B", "C"])
    G.add_edge("A", "B", weight=1.0)
    G.add_edge("B", "C", weight=1.0)

    semigroup = CognitiveSemigroup()

    # Define two simple operations
    def op1(net, **kwargs):
        net["A"]["B"]["weight"] *= 0.9
        return net

    def op2(net, **kwargs):
        net["B"]["C"]["weight"] *= 0.8
        return net

    semigroup.add_operation("op1", op1)
    semigroup.add_operation("op2", op2)

    comp = semigroup.compose("op1", "op2")
    print(f"Composite operation name: {comp.name}")
    # Associativity verification (requires three operations, omitted here)
    print("Test completed.")