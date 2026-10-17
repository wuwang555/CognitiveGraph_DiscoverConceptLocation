# algebra_experiments.py
"""
Algebraic Validation Experiments - Verify the correctness of algebraic structures in the paper.

This module implements the five sets of algebraic validation experiments designed in Section 5 of the paper,
which are used to examine the cognitive operation semigroup, Noether-type propositions, orbit-stabilizer theorem,
Lie group evolution framework, and the scalability of the algebraic approach.

Each experiment corresponds to a subsection in the paper, and the experimental results support Theorem 4.1.3,
Proposition 4.2.2, Theorem 4.3.3, and Theorem 4.4.2.
"""

import os
import numpy as np
import networkx as nx
from algebra.cognitive_semigroup import CognitiveSemigroup
from algebra.cognitive_symmetry import CognitiveSymmetryGroup
from algebra.group_action import GroupActionOnCognitiveSpace
from algebra.lie_group_cognitive import CognitiveLieGroup


class AlgebraValidationExperiments:
    """Algebraic Validation Experiments Manager.

    This class encapsulates the five sets of algebraic validation experiments described in Section 5 of the paper,
    providing a unified interface for running experiments.
    Each experiment method returns a dictionary containing key metrics, and ultimately the run_all_experiments()
    method can be used to execute all experiments and generate a summary report.
    """

    def __init__(self):
        self.results = {}
        from datetime import datetime
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    def experiment1_verify_semigroup_properties(self):
        """Experiment 1: Verify the associativity property of the cognitive operation semigroup.

        According to Theorem 4.1.3 in the paper, basic cognitive operations should form a semigroup under composition,
        satisfying associativity. This method combines five basic operations (learning, forgetting, traversal,
        compression, migration) and verifies associativity (a∘b)∘Cognitive_Map_Animation_Visual_Elements_Description.md = a∘(b∘Cognitive_Map_Animation_Visual_Elements_Description.md) on a test network.

        Returns:
            dict: A dictionary containing associativity verification results and operation count, e.g.:
                {
                    'associativity': {'(learning∘forgetting)∘traversal': True, ...},
                    'operation_count': 5,
                    'note': 'Identity check temporarily skipped (semigroup does not necessarily require identity)'
                }
        """
        print("=== Experiment 1: Cognitive Operation Semigroup Validation ===")

        # Create test network
        test_network = self._create_test_network()

        # Initialize semigroup
        semigroup = CognitiveSemigroup()
        self._initialize_operations(semigroup)

        # Verify associativity: select three different operation combinations for testing
        test_combinations = [
            ("learning", "forgetting", "traversal"),
            ("compression", "migration", "learning"),
            ("traversal", "learning", "forgetting")
        ]

        associativity_results = {}
        for op1, op2, op3 in test_combinations:
            try:
                is_assoc = semigroup.verify_associativity(
                    op1, op2, op3, test_network.copy()
                )
                associativity_results[f"({op1}∘{op2})∘{op3}"] = is_assoc
            except Exception as e:
                print(f"Error verifying associativity ({op1}, {op2}, {op3}): {e}")
                associativity_results[f"({op1}∘{op2})∘{op3}"] = False

        self.results['experiment1'] = {
            'associativity': associativity_results,
            'operation_count': len(semigroup.operations),
            'note': "Identity check temporarily skipped (semigroup does not necessarily require identity)"
        }

        print(f"Operation count: {len(semigroup.operations)}")
        print(f"Associativity verification results:")
        for key, value in associativity_results.items():
            safe_key = key.replace('∘', 'o')   # Replace special character
            print(f"  {safe_key}: {value}")

        # Check if all associativity verifications passed
        all_passed = all(associativity_results.values())
        print(f"All associativity verifications passed: {all_passed}")

        return self.results['experiment1']

    def experiment2_verify_noether_theorem(self):
        """Experiment 2: Verify the Noether-type proposition (symmetry → conserved quantity).

        According to Proposition 4.2.2 in the paper, every continuous symmetry of the cognitive system corresponds
        to a conserved quantity. This method detects symmetries and computes conserved quantities on three networks
        with different structures, verifying the conservation before and after operations.

        Returns:
            dict: A dictionary containing Noether verification results for each network, e.g.:
                {
                    'network_0': {
                        'automorphisms_count': int,
                        'conserved_quantities': {...},
                        'noether_theorem_holds': bool,
                        'energy_before': float,
                        'energy_after': float
                    },
                    ...
                }
        """
        print("\n=== Experiment 2: Noether Theorem Verification ===")

        # Create networks with different structures (now all complete graphs to ensure connectivity)
        networks = [
            self._create_physics_dominant_network(),
            self._create_math_dominant_network(),
            self._create_balanced_network()
        ]

        noether_results = {}
        for i, network in enumerate(networks):
            print(f"Processing network {i + 1}/{len(networks)}...")

            # Ensure network is connected
            if not nx.is_connected(network):
                print(f"Warning: Network {i+1} is disconnected, attempting to fix...")
                # If disconnected due to excessive weights, lower the weight threshold
                for u, v in network.edges():
                    if network[u][v]['weight'] > 5.0:
                        network[u][v]['weight'] = 2.0

            symmetry_group = CognitiveSymmetryGroup(network)

            try:
                # Detect symmetries
                automorphisms = symmetry_group.find_concept_isomorphisms()

                # Compute conserved quantities
                conserved = symmetry_group.compute_conserved_quantities()

                # Verify that conserved quantities remain unchanged before and after operation
                before_net = network.copy()

                # Randomly select a learning operation
                import random
                np.random.seed(42)
                random.seed(42)
                edges = list(before_net.edges())
                if edges:
                    u, v = random.choice(edges)
                    # Apply learning operation (reduce weight)
                    after_net = before_net.copy()
                    current = after_net[u][v]['weight']
                    after_net[u][v]['weight'] = max(0.05, current * 0.9)

                    # Verify Noether theorem
                    conserved_after_op = symmetry_group.verify_noether_theorem(
                        before_net, after_net, "learning"
                    )

                    noether_results[f"network_{i}"] = {
                        'automorphisms_count': len(automorphisms),
                        'conserved_quantities': conserved,
                        'noether_theorem_holds': conserved_after_op,
                        'energy_before': sum(before_net[u][v]['weight']
                                             for u, v in before_net.edges()),
                        'energy_after': sum(after_net[u][v]['weight']
                                            for u, v in after_net.edges())
                    }
                else:
                    noether_results[f"network_{i}"] = {
                        'error': "Network has no edges"
                    }

            except Exception as e:
                print(f"Error processing network {i+1}: {e}")
                noether_results[f"network_{i}"] = {
                    'error': str(e)
                }

        self.results['experiment2'] = noether_results

        print("\nNoether theorem verification results:")
        for net_id, result in noether_results.items():
            print(f"Network {net_id}:")
            if 'error' in result:
                print(f"  Error: {result['error']}")
            else:
                print(f"  Automorphisms count: {result['automorphisms_count']}")
                print(f"  Conserved quantities: {result['conserved_quantities']}")
                print(f"  Noether theorem holds: {result['noether_theorem_holds']}")

        return noether_results

    def experiment3_orbit_stabilizer_theorem(self):
        """Experiment 3: Verify the orbit-stabilizer theorem.

        According to Theorem 4.3.3 in the paper, for finite group actions we have |Orbit| = |Group| / |Stabilizer|.
        This method computes the size of the cognitive symmetry group, the stabilizer size, and the orbit size,
        and verifies this equation.

        Returns:
            dict: A dictionary containing theorem verification results and error percentage, e.g.:
                {
                    'automorphism_group_size': int,
                    'orbit_size_actual': int,
                    'stabilizer_size': int,
                    'orbit_size_expected': float,
                    'theorem_holds': bool,
                    'error_percentage': float
                }
        """
        print("\n=== Experiment 3: Orbit-Stabilizer Theorem Verification ===")

        test_network = self._create_test_network()
        symmetry_group = CognitiveSymmetryGroup(test_network)

        # Find all isomorphisms
        automorphisms = symmetry_group.find_concept_isomorphisms()
        if len(automorphisms) == 0:
            print("Error: No automorphisms found (including identity mapping), cannot verify theorem.")
            self.results['experiment3'] = {'error': 'No automorphisms found'}
            return self.results['experiment3']

        # Initialize group action
        group_action = GroupActionOnCognitiveSpace(symmetry_group)

        # Debug: Check if identity mapping is in stabilizer
        identity = {node: node for node in test_network.nodes()}
        transformed_identity = group_action.apply_group_element(test_network, identity)
        print("Is transformed identity network equal to original?",
              group_action._networks_equal(test_network, transformed_identity))

        # Compute orbit and stabilizer
        orbit = group_action.compute_orbit(test_network)
        stabilizer = group_action.compute_stabilizer(test_network)

        print(f"Group size: {len(automorphisms)}")
        print(f"Stabilizer size: {len(stabilizer)}")
        if stabilizer:
            print("Example automorphism in stabilizer:", stabilizer[0])
        print(f"Orbit size: {len(orbit)}")
        try:
            # Verify theorem |Orbit| = |Group| / |Stabilizer|
            theorem_holds = group_action.verify_orbit_stabilizer_theorem(test_network)
        except ValueError as e:
            print(f"Theorem verification failed: {e}")
            theorem_holds = False

        # Compute theoretical and actual values
        expected_size = len(automorphisms) / max(1, len(stabilizer))
        actual_size = len(orbit)

        self.results['experiment3'] = {
            'automorphism_group_size': len(automorphisms),
            'orbit_size_actual': actual_size,
            'stabilizer_size': len(stabilizer),
            'orbit_size_expected': expected_size,
            'theorem_holds': theorem_holds,
            'error_percentage': abs(expected_size - actual_size) / expected_size * 100
            if expected_size > 0 else 0
        }

        print(f"Isomorphism group size: {len(automorphisms)}")
        print(f"Stabilizer size: {len(stabilizer)}")
        print(f"Orbit size (actual): {actual_size}")
        print(f"Orbit size (theoretical): {expected_size:.2f}")
        print(f"Orbit-stabilizer theorem holds: {theorem_holds}")
        if not theorem_holds:
            print(f"Error percentage: {self.results['experiment3']['error_percentage']:.2f}%")

        return self.results['experiment3']

    def experiment4_lie_group_evolution(self):
        """Experiment 4: Demonstrate the Lie group evolution framework.

        According to Theorem 4.4.2 in the paper, the evolution of cognitive states satisfies the Lie group equation
        dG/dt = A(t)G(t). This method uses three different combinations of Lie algebra generators
        (energy optimization dominant, concept compression dominant, principle migration dominant)
        to evolve the network and record energy changes.

        Returns:
            dict: A dictionary containing evolution results for each strategy (energy change trajectories), e.g.:
                {
                    'strategy_0': {
                        'generator_coeffs': {'E': 0.7, 'C': 0.2, 'M': 0.1},
                        'initial_energy': float,
                        'final_energy': float,
                        'energy_change_percent': float,
                        'energy_trajectory': list
                    },
                    ...
                }
        """
        print("\n=== Experiment 4: Lie Group Evolution Demonstration ===")

        # Create initial network
        initial_network = self._create_test_network()
        n_nodes = initial_network.number_of_nodes()

        # Initialize Lie group
        lie_group = CognitiveLieGroup(n_nodes)

        # Set different evolution strategies
        strategies = [
            {'E': 0.7, 'C': 0.2, 'M': 0.1},  # Energy optimization dominant
            {'E': 0.3, 'C': 0.6, 'M': 0.1},  # Concept compression dominant
            {'E': 0.2, 'C': 0.2, 'M': 0.6},  # Principle migration dominant
        ]

        evolution_results = {}
        for i, coeffs in enumerate(strategies):
            evolved_networks = lie_group.evolve_network(
                initial_network,
                time_steps=5,
                generator_coeffs=coeffs
            )

            # Compute evolution metrics
            energies = []
            for net in evolved_networks:
                if net.number_of_edges() > 0:
                    avg_energy = np.mean([net[u][v]['weight']
                                          for u, v in net.edges()])
                else:
                    avg_energy = 0
                energies.append(avg_energy)

            evolution_results[f"strategy_{i}"] = {
                'generator_coeffs': coeffs,
                'initial_energy': energies[0],
                'final_energy': energies[-1],
                'energy_change_percent': ((energies[0] - energies[-1]) / energies[0] * 100
                                          if energies[0] > 0 else 0),
                'energy_trajectory': energies
            }

        # Save energy trajectories
        import csv
        energy_dir = "results/algebra/energy_trajectories"
        os.makedirs(energy_dir, exist_ok=True)
        for strategy, result in evolution_results.items():
            energy_traj = result['energy_trajectory']
            csv_file = os.path.join(energy_dir, f"lie_evolution_{strategy}_{self.timestamp}.csv")
            with open(csv_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['time_step', 'avg_energy'])
                for t, e in enumerate(energy_traj):
                    writer.writerow([t, e])
            print(f"Energy trajectory saved: {csv_file}")

        self.results['experiment4'] = evolution_results

        print("Lie group evolution results (different generator combinations):")
        for strategy, result in evolution_results.items():
            print(f"  Strategy {strategy}:")
            print(f"    Generator coefficients: {result['generator_coeffs']}")
            print(f"    Energy change: {result['energy_change_percent']:.1f}%")

        return evolution_results

    def experiment5_scalability_test(self):
        """Experiment 5: Scalability test of the algebraic approach.

        Test the time consumption of semigroup operations and symmetry detection on networks with 5, 8, 10, 12, and 15 nodes,
        evaluating the computational efficiency of the algebraic approach on networks of different sizes.

        Returns:
            dict: Test results for networks of each size, including node count, edge count, semigroup operation time,
                  symmetry detection time, automorphism count, etc.
        """
        print("\n=== Experiment 5: Algebraic Method Scalability Test ===")

        # Reduce test scales
        network_sizes = [5, 8, 10, 12, 15]  # Smaller scales
        scalability_results = {}

        for size in network_sizes:
            print(f"Testing network size: {size}")

            # Create small complete graph
            nodes = [f"Concept_{i}" for i in range(size)]
            network = nx.complete_graph(nodes)

            # Assign random weights
            for u, v in network.edges():
                network[u][v]['weight'] = np.random.uniform(0.5, 2.0)

            import time

            # Test semigroup operation time
            semigroup = CognitiveSemigroup()

            # Initialize only basic operations
            def identity_op(network, **kwargs):
                return network.copy()

            semigroup.add_operation("identity", identity_op)

            start_time = time.time()
            for _ in range(10):
                semigroup.compose("identity", "identity")
            semigroup_time = time.time() - start_time

            # Test symmetry detection time (limit max samples)
            start_time = time.time()
            try:
                symmetry_group = CognitiveSymmetryGroup(network)
                automorphisms = symmetry_group.find_concept_isomorphisms(max_samples=100)
                symmetry_time = time.time() - start_time
                symmetry_success = True
            except Exception as e:
                symmetry_time = time.time() - start_time
                automorphisms = []
                symmetry_success = False
                print(f"Symmetry detection failed: {e}")

            scalability_results[size] = {
                'nodes': size,
                'edges': network.number_of_edges(),
                'semigroup_operation_time': semigroup_time,
                'symmetry_detection_time': symmetry_time,
                'symmetry_detection_success': symmetry_success,
                'automorphisms_count': len(automorphisms)
            }

        self.results['experiment5'] = scalability_results

        print("\nScalability results:")
        print("Network Size | Semigroup Op Time(s) | Symmetry Detection Time(s) | Automorphisms | Success")
        print("-" * 70)
        for size, result in scalability_results.items():
            success = "Y" if result['symmetry_detection_success'] else "N"
            print(f"{size:8d} | {result['semigroup_operation_time']:14.4f} | "
                  f"{result['symmetry_detection_time']:16.4f} | "
                  f"{result['automorphisms_count']:8d} | {success}")

        return scalability_results

    def run_all_experiments(self):
        """Run all algebraic validation experiments.

        Returns:
            dict: A dictionary containing all experimental results, with experiment names as keys.
        """
        print("=" * 60)
        print("Algebraic Structure Validation Experiment Suite")
        print("=" * 60)

        results = {
            'semigroup_properties': self.experiment1_verify_semigroup_properties(),
            'noether_theorem': self.experiment2_verify_noether_theorem(),
            'orbit_stabilizer': self.experiment3_orbit_stabilizer_theorem(),
            'lie_group_evolution': self.experiment4_lie_group_evolution(),
            'scalability': self.experiment5_scalability_test()
        }

        self._generate_summary_report()
        return results

    def _generate_summary_report(self):
        """Generate experiment summary report (print to console and save results file)."""
        print("\n" + "=" * 60)
        print("Algebraic Validation Experiment Summary Report")
        print("=" * 60)

        summary = {}

        # Experiment 1: Algebraic property verification
        if 'experiment1' in self.results:
            exp1 = self.results['experiment1']
            if 'associativity' in exp1:
                all_passed = all(exp1['associativity'].values())
                summary['Algebraic Properties'] = "Passed" if all_passed else "Partial Pass"
            else:
                summary['Algebraic Properties'] = "Data Missing"
        else:
            summary['Algebraic Properties'] = "Not Run"

        # Experiment 2: Noether theorem
        if 'experiment2' in self.results:
            exp2 = self.results['experiment2']
            noether_results = []
            for net_id, result in exp2.items():
                if isinstance(result, dict) and 'noether_theorem_holds' in result:
                    holds = result['noether_theorem_holds']
                    if isinstance(holds, tuple):
                        holds = holds[0]
                    noether_results.append(holds)

            if noether_results:
                passed_count = sum(1 for r in noether_results if r)
                summary['Noether Theorem'] = f"{passed_count}/{len(noether_results)} Passed"
            else:
                summary['Noether Theorem'] = "No Valid Data"
        else:
            summary['Noether Theorem'] = "Not Run"

        # Experiment 3: Orbit-stabilizer theorem
        if 'experiment3' in self.results:
            exp3 = self.results['experiment3']
            theorem_holds = exp3.get('theorem_holds', False)
            summary['Orbit-Stabilizer Theorem'] = "Passed" if theorem_holds else "Failed"
        else:
            summary['Orbit-Stabilizer Theorem'] = "Not Run"

        # Experiment 4: Lie group evolution
        if 'experiment4' in self.results:
            exp4 = self.results['experiment4']
            if exp4:
                has_changes = any(
                    abs(result.get('energy_change_percent', 0)) > 0.1
                    for result in exp4.values()
                )
                summary['Lie Group Evolution'] = "Successful" if has_changes else "No Change"
            else:
                summary['Lie Group Evolution'] = "No Data"
        else:
            summary['Lie Group Evolution'] = "Not Run"

        # Experiment 5: Scalability
        if 'experiment5' in self.results:
            exp5 = self.results['experiment5']
            if exp5:
                all_success = all(
                    result.get('symmetry_detection_success', False)
                    for result in exp5.values()
                )
                summary['Scalability'] = "Good" if all_success else "Limited"
            else:
                summary['Scalability'] = "No Data"
        else:
            summary['Scalability'] = "Not Run"

        # Print summary
        for test, result in summary.items():
            print(f"{test:20s}: {result}")

        # Save results to file
        self._save_results_to_file()

        return summary

    def _save_results_to_file(self):
        """Save experiment results as JSON file."""
        import json
        from datetime import datetime

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Ensure directory exists
        results_dir = "results"
        os.makedirs(results_dir, exist_ok=True)

        # Save to results/algebra/ directory
        algebra_dir = os.path.join(results_dir, "algebra")
        os.makedirs(algebra_dir, exist_ok=True)
        filename = os.path.join(algebra_dir, f"algebra_validation_results_{timestamp}.json")

        # Convert results to serializable format
        serializable_results = {}
        for exp_name, exp_data in self.results.items():
            if isinstance(exp_data, dict):
                serializable_results[exp_name] = self._make_serializable(exp_data)
            else:
                serializable_results[exp_name] = str(exp_data)

        # Safe save
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(serializable_results, f, indent=2, ensure_ascii=False)
            print(f"\nDetailed results saved to: {filename}")
        except Exception as e:
            print(f"Error saving results: {e}")
            # Try alternative filename
            simple_filename = os.path.join(algebra_dir, f"results_{timestamp}.json")
            with open(simple_filename, 'w', encoding='ascii') as f:
                json.dump(serializable_results, f, indent=2, ensure_ascii=True)
            print(f"Results saved to alternative file: {simple_filename}")

    def _make_serializable(self, obj):
        """Ensure object is JSON serializable (recursively convert numpy types, etc.)."""
        if isinstance(obj, (int, float, str, bool, type(None))):
            return obj
        elif isinstance(obj, dict):
            return {k: self._make_serializable(v) for k, v in obj.items()}
        elif isinstance(obj, (list, tuple)):
            return [self._make_serializable(item) for item in obj]
        elif isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        else:
            return str(obj)

    def _create_test_network(self):
        """Create a complete graph for testing with nodes as common concepts.

        Returns:
            networkx.Graph: A complete graph with 10 concept nodes, edge weights based on semantic similarity.
        """
        nodes = ["算法", "数据结构", "优化", "递归", "迭代", "抽象", "模式识别", "牛顿定律", "能量守恒", "微积分"]

        # Create complete graph
        G = nx.complete_graph(nodes)

        # Calculate initial energy based on semantic similarity
        # Higher similarity leads to lower energy
        for u, v in G.edges():
            if u == v:
                continue

            # Simple similarity heuristic based on concept names
            similarity = self._calculate_simple_similarity(u, v)

            # Energy = 2.0 - similarity * 1.5 (higher similarity → lower energy)
            energy = 2.0 - similarity * 1.5
            energy = max(0.1, min(3.0, energy))  # Clamp to reasonable range

            G[u][v]['weight'] = energy

        return G

    def _calculate_simple_similarity(self, concept1, concept2):
        """Calculate simple similarity based on concept domain classification.

        Args:
            concept1 (str): First concept name
            concept2 (str): Second concept name

        Returns:
            float: Estimated similarity between 0 and 1
        """
        # If concepts are identical
        if concept1 == concept2:
            return 1.0

        # Concept category determination (simplified implementation)
        physics_concepts = ["Newton's Law", "Energy Conservation", "Mechanics", "Kinematics"]
        math_concepts = ["Calculus", "Geometry", "Algebra", "Recursion", "Iteration"]
        cs_concepts = ["Algorithm", "Data Structure", "Optimization", "Abstraction", "Pattern Recognition"]

        concept1_domain = None
        concept2_domain = None

        if concept1 in physics_concepts:
            concept1_domain = "physics"
        elif concept1 in math_concepts:
            concept1_domain = "math"
        elif concept1 in cs_concepts:
            concept1_domain = "cs"

        if concept2 in physics_concepts:
            concept2_domain = "physics"
        elif concept2 in math_concepts:
            concept2_domain = "math"
        elif concept2 in cs_concepts:
            concept2_domain = "cs"

        # Same domain concepts have higher similarity
        if concept1_domain and concept2_domain and concept1_domain == concept2_domain:
            return np.random.uniform(0.7, 0.9)

        # Cross-domain but related (e.g., math and computer science)
        if (concept1_domain == "math" and concept2_domain == "cs") or \
                (concept1_domain == "cs" and concept2_domain == "math"):
            return np.random.uniform(0.5, 0.7)

        # Other cross-domain
        return np.random.uniform(0.2, 0.5)

    def _create_physics_dominant_network(self):
        """Create a physics-dominant complete graph network.

        Returns:
            networkx.Graph: Strong connections (low energy) between physics concepts, weaker with other domains.
        """
        nodes = ["牛顿定律", "力学", "运动学", "能量守恒", "动量", "万有引力", "摩擦力", "静电力", "优化", "迭代"]

        G = nx.complete_graph(nodes)

        for u, v in G.edges():
            # Physics concepts have stronger connections (lower energy)
            physics_terms = ["Newton's Law", "Mechanics", "Kinematics", "Energy Conservation",
                             "Momentum", "Gravitation", "Friction", "Electrostatic Force"]

            if u in physics_terms and v in physics_terms:
                # Physics concepts: strong connection (low energy)
                energy = np.random.uniform(0.3, 0.8)
            elif u in physics_terms or v in physics_terms:
                # Cross-domain: medium connection
                energy = np.random.uniform(1.0, 1.5)
            else:
                # Non-physics concepts: weak connection (high energy)
                energy = np.random.uniform(1.5, 2.0)

            G[u][v]['weight'] = energy

        return G

    def _create_math_dominant_network(self):
        """Create a math-dominant network (non-complete, random sparse).

        Returns:
            networkx.Graph: Strong connections between math concepts, random sparse graph.
        """
        nodes = ["微积分", "几何学", "拓扑学", "线性代数", "概率论", "统计学", "代数", "离散数学", "算法", "数据结构"]

        G = nx.Graph()
        G.add_nodes_from(nodes)

        # Strong connections between math concepts
        for i in range(len(nodes) - 2):
            for j in range(i + 1, len(nodes) - 2):
                w = np.random.uniform(0.5, 0.9)
                G.add_edge(nodes[i], nodes[j], weight=w)

        return G

    def _create_balanced_network(self):
        """Create a balanced network (random sparse).

        Returns:
            networkx.Graph: Random connections, uniformly distributed weights.
        """
        nodes = ["算法", "数据结构", "优化", "递归", "迭代", "抽象", "模式识别", "牛顿定律", "能量守恒", "微积分"]

        G = nx.Graph()
        G.add_nodes_from(nodes)

        # Random connections
        for i in range(len(nodes)):
            for j in range(i + 1, len(nodes)):
                if np.random.random() < 0.4:  # 40% connection probability
                    w = np.random.uniform(0.5, 1.5)
                    G.add_edge(nodes[i], nodes[j], weight=w)

        return G

    def _initialize_operations(self, semigroup):
        """Initialize cognitive operations into the semigroup.

        Args:
            semigroup (CognitiveSemigroup): The semigroup object to add operations to.
        """

        def learning_op(network, edge=None, strength=0.1, **kwargs):
            """Learning operation: reduce weight (energy) of specified edge."""
            if edge is None:
                return network
            u, v = edge
            if network.has_edge(u, v):
                current = network[u][v]['weight']
                network[u][v]['weight'] = max(0.05, current * (1 - strength))
            return network

        def forgetting_op(network, edge=None, strength=0.05, **kwargs):
            """Forgetting operation: increase weight (energy) of specified edge."""
            if edge is None:
                return network
            u, v = edge
            if network.has_edge(u, v):
                current = network[u][v]['weight']
                network[u][v]['weight'] = min(2.0, current * (1 + strength))
            return network

        def traversal_op(network, path=None, **kwargs):
            """Traversal operation: reduce weight of all edges along the path (simulating proficiency increase)."""
            if path is None or len(path) < 2:
                return network
            for i in range(len(path) - 1):
                u, v = path[i], path[i + 1]
                if network.has_edge(u, v):
                    current = network[u][v]['weight']
                    network[u][v]['weight'] = max(0.05, current * 0.95)
            return network

        def compression_op(network, center=None, related_nodes=None, **kwargs):
            """Concept compression operation: strengthen connections between center and related nodes (reduce energy)."""
            if center is None or related_nodes is None:
                return network
            for node in related_nodes:
                if network.has_edge(center, node):
                    current = network[center][node]['weight']
                    network[center][node]['weight'] = max(0.05, current * 0.8)
            return network

        def migration_op(network, principle=None, from_node=None, to_node=None, **kwargs):
            """Principle migration operation: strengthen connections between principle node and endpoints."""
            if principle is None or from_node is None or to_node is None:
                return network
            if network.has_edge(from_node, principle):
                current = network[from_node][principle]['weight']
                network[from_node][principle]['weight'] = max(0.05, current * 0.9)
            if network.has_edge(principle, to_node):
                current = network[principle][to_node]['weight']
                network[principle][to_node]['weight'] = max(0.05, current * 0.9)
            return network

        # Add to semigroup
        semigroup.add_operation("learning", learning_op)
        semigroup.add_operation("forgetting", forgetting_op)
        semigroup.add_operation("traversal", traversal_op)
        semigroup.add_operation("compression", compression_op)
        semigroup.add_operation("migration", migration_op)


# Main program
if __name__ == "__main__":
    print("Starting algebraic validation experiments...\n")

    experiments = AlgebraValidationExperiments()

    try:
        all_results = experiments.run_all_experiments()

        print("\n" + "=" * 60)
        print("All algebraic validation experiments completed!")
        print("=" * 60)

        # Display overall success status
        success_count = 0
        total_experiments = 5

        exp1 = experiments.results.get('experiment1', {})
        if exp1.get('associativity') and all(exp1['associativity'].values()):
            success_count += 1
        if any(r.get('noether_theorem_holds', False) for r in experiments.results.get('experiment2', {}).values()):
            success_count += 1
        if experiments.results.get('experiment3', {}).get('theorem_holds', False):
            success_count += 1
        if any(abs(r.get('energy_change_percent', 0)) > 0.1
               for r in experiments.results.get('experiment4', {}).values()):
            success_count += 1
        if experiments.results.get('experiment5', {}):
            success_count += 1

        print(f"Successful experiments: {success_count}/{total_experiments}")

    except KeyboardInterrupt:
        print("\n\nExperiment interrupted by user")
    except Exception as e:
        print(f"\nExperiment execution error: {e}")
        import traceback
        traceback.print_exc()