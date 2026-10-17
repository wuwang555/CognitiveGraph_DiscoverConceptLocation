"""
Enhanced Q-learning Model - Addresses Dynamic Environment Issues
Uses more reasonable state representation and reward mechanisms to enable the agent to learn low-energy paths.
"""

import networkx as nx
import numpy as np
import random
from typing import Dict, Any, List, Tuple
from core.cognitive_graph import BaseCognitiveGraph

np.random.seed(42)
random.seed(42)

class EnhancedQLearningCognitiveGraph(BaseCognitiveGraph):
    """Enhanced Q-learning cognitive graph model.

    This class models the cognitive graph as a reinforcement learning environment. The agent learns optimal paths
    through network traversal, with the goal of maximizing cumulative reward (i.e., minimizing energy).
    """

    def __init__(self, individual_params: Dict[str, Any], network_seed: int = 42):
        """Initialize enhanced Q-learning cognitive graph.

        Args:
            individual_params (Dict[str, Any]): Individual parameters.
            network_seed (int): Random seed.
        """
        super().__init__(individual_params, network_seed)

        # Q-learning parameters - adjusted for better learning
        self.learning_rate = 0.15  # Moderate learning rate
        self.discount_factor = 0.85  # Lower discount factor to focus on immediate rewards
        self.exploration_rate = 0.25  # Higher initial exploration rate
        self.min_exploration_rate = 0.05
        self.exploration_decay = 0.9995  # Very slow decay

        # Q-table (states × actions)
        # State: current node + cognitive state (simplified encoding)
        self.q_table = None

        # State encoding
        self.state_encoder = {}
        self.state_decoder = {}

        # Current state
        self.current_q_state = None
        self.current_cognitive_state = None

        # Performance tracking
        self.episode_rewards = []
        self.best_paths = {}

    def initialize_network(self, num_nodes=51, connection_prob=0.2):
        """Initialize the network.

        Creates a random graph and assigns random weights to edges.

        Args:
            num_nodes (int): Number of nodes.
            connection_prob (float): Edge connection probability.
        """
        # Create random graph
        self.G = nx.erdos_renyi_graph(num_nodes, connection_prob, seed=self.network_seed)

        # Assign random weights to edges
        for u, v in self.G.edges():
            weight = np.random.uniform(0.5, 1.5)  # Reduce initial weight range
            self.G[u][v]['weight'] = weight
            self.G[u][v]['original_weight'] = weight
            self.G[u][v]['traversal_count'] = 0
            self.last_activation_time[(u, v)] = 0

        # Name nodes (using simple numbers to avoid underscore issues)
        node_names = [f"概念{i}" for i in range(num_nodes)]  # Remove underscores
        mapping = {i: node_names[i] for i in range(num_nodes)}
        self.G = nx.relabel_nodes(self.G, mapping)

        # Initialize state space
        self._initialize_state_space()

        print(f"Enhanced Q-learning network initialization: {num_nodes} nodes, {self.G.number_of_edges()} edges")
        print(f"State space size: {len(self.state_encoder)}")

    def _initialize_state_space(self):
        """Initialize state space.

        State = node × cognitive state (exploration/focused/fatigued), each state assigned a unique integer ID.
        """
        # State = node × cognitive state (simplified)
        # Use special separator '|' to avoid conflicts with node names
        nodes = list(self.G.nodes())
        cognitive_states = ['Exploratory', 'Focused', 'Fatigued']  # Simplified cognitive states

        state_id = 0
        for node in nodes:
            for state in cognitive_states:
                state_key = f"{node}|{state}"  # Use | as separator
                self.state_encoder[state_key] = state_id
                self.state_decoder[state_id] = (node, state)
                state_id += 1

        # Initialize Q-table
        n_states = len(self.state_encoder)
        n_actions = len(nodes)  # Action is choosing the next node
        self.q_table = np.zeros((n_states, n_actions))

        # Initialize small positive values for valid state-action pairs
        for state_key, state_id in self.state_encoder.items():
            # Split using the correct separator
            current_node, _ = state_key.split('|')
            for action_idx, action_node in enumerate(nodes):
                if self.G.has_edge(current_node, action_node):
                    # Valid connection: initialize with small positive value
                    self.q_table[state_id, action_idx] = 0.1

    def encode_state(self, node, cognitive_state):
        """Encode state as integer ID.

        Args:
            node (str): Current node.
            cognitive_state (str): Cognitive state.

        Returns:
            int: State ID.
        """
        state_key = f"{node}|{cognitive_state}"  # Use | as separator
        return self.state_encoder.get(state_key, 0)

    def decode_state(self, state_id):
        """Decode state ID to node and cognitive state.

        Args:
            state_id (int): State ID.

        Returns:
            tuple: (node, cognitive_state)
        """
        return self.state_decoder.get(state_id, ("Unknown", "Unknown"))

    def get_cognitive_state_simplified(self):
        """Simplified cognitive state determination.

        Determines cognitive state based on current iteration count for state space.

        Returns:
            str: Cognitive state, one of 'Exploratory', 'Focused', or 'Fatigued'.
        """
        # Determine cognitive state based on current network energy and iteration count
        if self.iteration_count < 1000:
            return "Exploratory"
        elif self.iteration_count % 100 < 30:
            return "Focused"
        else:
            return "Fatigued"

    def get_possible_actions(self, current_node):
        """Get possible actions from current node (neighbor nodes).

        Args:
            current_node (str): Current node.

        Returns:
            list: Each element is (action_node, action_idx).
        """
        nodes = list(self.G.nodes())

        # If current node has neighbors, prioritize neighbors
        neighbors = list(self.G.neighbors(current_node))
        if neighbors:
            return [(node, idx) for idx, node in enumerate(nodes) if node in neighbors]
        else:
            # If no neighbors, can choose any node (but probability is low)
            return [(node, idx) for idx, node in enumerate(nodes) if node != current_node]

    def choose_action(self, state_id):
        """Choose an action using ε-greedy policy.

        Args:
            state_id (int): Current state ID.

        Returns:
            tuple: (action_node, action_idx), or (None, None) if no possible actions.
        """
        current_node, cognitive_state = self.decode_state(state_id)

        possible_actions = self.get_possible_actions(current_node)
        if not possible_actions:
            return None, None

        # Exploration: choose action randomly
        if random.random() < self.exploration_rate:
            action_node, action_idx = random.choice(possible_actions)
            return action_node, action_idx

        # Exploitation: choose action with highest Q-value
        else:
            best_value = -float('inf')
            best_action = None
            best_idx = None

            for action_node, action_idx in possible_actions:
                if self.q_table[state_id, action_idx] > best_value:
                    best_value = self.q_table[state_id, action_idx]
                    best_action = action_node
                    best_idx = action_idx

            return best_action, best_idx

    def calculate_reward(self, current_node, action_node, cognitive_state):
        """Calculate reward.

        Reward function designed to encourage low-energy paths, considering cognitive state and recent activation.
        Corresponds to the negative correlation with the energy function E_ij(t): low energy → high reward.

        Args:
            current_node (str): Current node.
            action_node (str): Chosen action node.
            cognitive_state (str): Cognitive state.

        Returns:
            float: Reward value.
        """
        if not self.G.has_edge(current_node, action_node):
            return -2.0  # Penalty for invalid connections

        # Base reward: negative edge weight (lower energy → higher reward)
        weight = self.G[current_node][action_node]['weight']
        base_reward = 1.5 - weight  # Adjust reward range to positive values

        # Cognitive state bonus
        state_bonus = 0
        if cognitive_state == "Focused":
            state_bonus = 0.3
        elif cognitive_state == "Exploratory":
            state_bonus = 0.1
        else:  # Fatigued
            state_bonus = -0.2

        # Learning progress bonus: if this edge was recently learned
        time_since_activation = self.iteration_count - self.last_activation_time.get((current_node, action_node), 0)
        recency_bonus = 0.2 if time_since_activation < 100 else 0

        total_reward = base_reward + state_bonus + recency_bonus

        return max(-1.0, total_reward)  # Ensure reward is not less than -1.0

    def update_q_value(self, state_id, action_idx, reward, next_state_id):
        """Update Q-value using the Bellman equation.

        Q(s,a) ← Q(s,a) + α [r + γ max_a' Q(s',a') - Q(s,a)]

        Args:
            state_id (int): Current state ID.
            action_idx (int): Action index.
            reward (float): Received reward.
            next_state_id (int): Next state ID.
        """
        current_q = self.q_table[state_id, action_idx]

        # Maximum Q-value of the next state
        next_max_q = np.max(self.q_table[next_state_id, :]) if np.any(self.q_table[next_state_id, :] != 0) else 0

        # Bellman equation
        target_q = reward + self.discount_factor * next_max_q
        new_q = current_q + self.learning_rate * (target_q - current_q)

        # Clamp Q-value to avoid extremes
        self.q_table[state_id, action_idx] = np.clip(new_q, -5.0, 5.0)

    def apply_learning_from_experience(self, current_node, action_node, reward):
        """Learn from experience, adjust edge weights (simulating Hebbian learning).

        Positive reward reduces edge weight (energy), negative reward increases edge weight.

        Args:
            current_node (str): Current node.
            action_node (str): Chosen action node.
            reward (float): Received reward.
        """
        if not self.G.has_edge(current_node, action_node):
            return

        current_weight = self.G[current_node][action_node]['weight']

        # Learning based on reward: positive reward reduces weight, negative reward increases weight
        learning_rate = 0.1
        weight_change = -learning_rate * reward  # Negative correlation: higher reward → more weight reduction

        new_weight = max(0.1, min(2.0, current_weight + weight_change))
        self.G[current_node][action_node]['weight'] = new_weight

        # Update activation time
        self.last_activation_time[(current_node, action_node)] = self.iteration_count

    def qlearning_step(self):
        """Perform one Q-learning step, including action selection, reward calculation, and Q-value update.

        Returns:
            float: Obtained reward.
        """
        if self.current_q_state is None:
            # Initialize state
            random_node = random.choice(list(self.G.nodes()))
            cognitive_state = self.get_cognitive_state_simplified()
            self.current_q_state = self.encode_state(random_node, cognitive_state)
            self.current_cognitive_state = cognitive_state

        # Choose action
        action_node, action_idx = self.choose_action(self.current_q_state)
        if action_node is None:
            return 0

        # Get current node
        current_node, _ = self.decode_state(self.current_q_state)

        # Calculate reward
        reward = self.calculate_reward(current_node, action_node, self.current_cognitive_state)

        # Record traversal
        self.traversal_history.append({
            'path': [current_node, action_node],
            'iteration': self.iteration_count,
            'reward': reward,
            'cognitive_state': self.current_cognitive_state
        })

        # Determine next state
        next_cognitive_state = self.get_cognitive_state_simplified()
        next_state_id = self.encode_state(action_node, next_cognitive_state)

        # Update Q-value
        self.update_q_value(self.current_q_state, action_idx, reward, next_state_id)

        # Learn from experience (adjust edge weights)
        self.apply_learning_from_experience(current_node, action_node, reward)

        # Update current state
        self.current_q_state = next_state_id
        self.current_cognitive_state = next_cognitive_state

        return reward

    def apply_intelligent_forgetting(self):
        """Intelligent forgetting mechanism, adjusting edge weights based on Q-values and activation time.

        Edges not activated for a long time gradually return to original weight, simulating forgetting.
        """
        current_time = self.iteration_count

        for u, v in self.G.edges():
            time_since_activation = current_time - self.last_activation_time.get((u, v), 0)

            if time_since_activation > 200:  # Long inactivity
                # Encode state (using simplified cognitive state)
                cognitive_state = self.get_cognitive_state_simplified()
                state_id = self.encode_state(u, cognitive_state)

                # Find corresponding action index
                nodes = list(self.G.nodes())
                if v in nodes:
                    action_idx = nodes.index(v)

                    # Q-value based forgetting: lower Q-value → faster forgetting
                    q_value = self.q_table[state_id, action_idx]
                    forget_factor = 0.1 * (2.0 - np.tanh(q_value))  # Lower Q-value → larger forget factor

                    current_weight = self.G[u][v]['weight']
                    original_weight = self.G[u][v].get('original_weight', 1.5)

                    # Regress toward original weight
                    new_weight = current_weight + (original_weight - current_weight) * forget_factor
                    new_weight = max(0.1, min(2.0, new_weight))

                    self.G[u][v]['weight'] = new_weight

    def find_best_path(self, start_node, end_node, max_length=5):
        """Find the optimal path based on learned Q-values.

        Args:
            start_node (str): Starting node.
            end_node (str): Target node.
            max_length (int): Maximum path length.

        Returns:
            tuple: (path list, total Q-value), or (None, 0) if no path.
        """
        if start_node not in self.G or end_node not in self.G:
            return None, 0

        nodes = list(self.G.nodes())

        # Initialize
        path = [start_node]
        current_node = start_node
        total_q_value = 0

        for step in range(max_length - 1):
            if current_node == end_node:
                break

            # Get current state
            cognitive_state = self.get_cognitive_state_simplified()
            state_id = self.encode_state(current_node, cognitive_state)

            # Choose next node with highest Q-value (excluding visited nodes)
            best_q = -float('inf')
            best_next = None

            for neighbor in self.G.neighbors(current_node):
                if neighbor in path:  # Avoid cycles
                    continue

                if neighbor in nodes:
                    action_idx = nodes.index(neighbor)
                    q_value = self.q_table[state_id, action_idx]

                    if q_value > best_q:
                        best_q = q_value
                        best_next = neighbor

            if best_next is None:
                break

            path.append(best_next)
            total_q_value += best_q
            current_node = best_next

        return path, total_q_value

    def enhanced_training(self, max_iterations=5000):
        """Enhanced Q-learning training main loop.

        Args:
            max_iterations (int): Maximum number of iterations.

        Returns:
            float: Energy improvement percentage.
        """
        print(f"Starting enhanced Q-learning training: {max_iterations} iterations")

        initial_energy = self.calculate_network_energy()
        self.energy_history.append(initial_energy)

        total_reward = 0
        exploration_history = []

        for iteration in range(max_iterations):
            self.iteration_count += 1

            # Perform Q-learning step
            reward = self.qlearning_step()
            total_reward += reward

            # Apply intelligent forgetting periodically
            if iteration % 100 == 0:
                self.apply_intelligent_forgetting()

            # Decay exploration rate
            if iteration % 50 == 0:
                self.exploration_rate = max(self.min_exploration_rate,
                                          self.exploration_rate * self.exploration_decay)
                exploration_history.append(self.exploration_rate)

            # Record energy
            if iteration % 10 == 0:
                current_energy = self.calculate_network_energy()
                self.energy_history.append(current_energy)

            # Periodic reporting
            if iteration % 500 == 0:
                current_energy = self.calculate_network_energy()
                improvement = ((initial_energy - current_energy) / initial_energy * 100) if initial_energy > 0 else 0
                avg_reward = total_reward / (iteration + 1) if iteration > 0 else 0

                # Show exploration progress
                explored_ratio = np.mean(self.q_table != 0)

                print(f"Iteration {iteration}: energy={current_energy:.3f} (improvement:{improvement:.1f}%)")
                print(f"  exploration_rate={self.exploration_rate:.3f}, avg_reward={avg_reward:.3f}, Q-table exploration={explored_ratio:.3f}")

                # Show an example path
                if iteration > 1000 and len(self.G.nodes()) >= 5:
                    nodes = list(self.G.nodes())
                    start = nodes[0]
                    end = nodes[4]
                    path, q_value = self.find_best_path(start, end)
                    if path and len(path) > 1:
                        print(f"  Example path {start}->{end}: {'->'.join(path)} (Q-value:{q_value:.3f})")

        final_energy = self.calculate_network_energy()
        total_improvement = ((initial_energy - final_energy) / initial_energy * 100) if initial_energy > 0 else 0

        print(f"\nEnhanced Q-learning training completed!")
        print(f"Initial energy: {initial_energy:.3f}, Final energy: {final_energy:.3f}")
        print(f"Total improvement: {total_improvement:.1f}%")
        print(f"Average reward: {total_reward / max_iterations:.3f}")
        print(f"Final exploration rate: {self.exploration_rate:.4f}")

        # Analyze Q-table
        q_stats = self._analyze_q_table()
        print(f"Q-table statistics: {q_stats}")

        return total_improvement

    def _analyze_q_table(self):
        """Analyze Q-table, return statistics.

        Returns:
            dict: Q-table statistics.
        """
        if self.q_table is None:
            return {}

        flat_q = self.q_table.flatten()
        non_zero_q = flat_q[flat_q != 0]

        stats = {
            'size': self.q_table.shape,
            'total_entries': self.q_table.size,
            'non_zero_entries': len(non_zero_q),
            'sparsity': 1 - (len(non_zero_q) / self.q_table.size),
            'mean': np.mean(non_zero_q) if len(non_zero_q) > 0 else 0,
            'std': np.std(non_zero_q) if len(non_zero_q) > 0 else 0,
            'min': np.min(non_zero_q) if len(non_zero_q) > 0 else 0,
            'max': np.max(non_zero_q) if len(non_zero_q) > 0 else 0,
            'positive_ratio': np.sum(non_zero_q > 0) / len(non_zero_q) if len(non_zero_q) > 0 else 0
        }

        return stats

    def run_experiment(self, num_nodes=51, max_iterations=5000):
        """Run a complete experiment, including network initialization, training, and result collection.

        Args:
            num_nodes (int): Number of nodes.
            max_iterations (int): Maximum number of iterations.

        Returns:
            dict: Experiment results dictionary.
        """
        self.initialize_network(num_nodes)
        improvement = self.enhanced_training(max_iterations)

        # Collect statistics
        q_stats = self._analyze_q_table()

        # Test optimal path finding
        path_examples = []
        if num_nodes >= 10:
            nodes = list(self.G.nodes())
            for i in range(3):
                start = nodes[i]
                end = nodes[i + 3]
                path, q_value = self.find_best_path(start, end)
                if path:
                    path_examples.append({
                        'start': start,
                        'end': end,
                        'path': '->'.join(path),
                        'q_value': q_value
                    })

        return {
            'model_type': 'enhanced_qlearning',
            'num_nodes': num_nodes,
            'iterations': max_iterations,
            'initial_energy': self.energy_history[0] if self.energy_history else 0,
            'final_energy': self.calculate_network_energy(),
            'improvement': improvement,
            'q_table_stats': q_stats,
            'exploration_rate_final': self.exploration_rate,
            'path_examples': path_examples,
            'network_stats': self.get_network_stats()
        }


if __name__ == "__main__":
    # Simple test: create a small network and run short training
    print("Testing EnhancedQLearningCognitiveGraph...")
    params = {}  # Empty params, use defaults
    model = EnhancedQLearningCognitiveGraph(params)
    result = model.run_experiment(num_nodes=51, max_iterations=8000)
    print("Test completed. Improvement rate:", result['improvement'])