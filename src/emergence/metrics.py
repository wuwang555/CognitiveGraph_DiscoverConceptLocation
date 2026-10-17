"""
Natural Emergence Metrics Calculation Module
----------------------
Define NaturalEmergenceMetrics class for calculating metrics of compression emergence, migration emergence,
energy optimization, and structural evolution.
"""

import numpy as np
import networkx as nx
from typing import Dict, List, Any
from collections import defaultdict


class NaturalEmergenceMetrics:
    """Natural Emergence Metrics Calculation Class (Simplified Version)."""

    def __init__(self):
        self.metric_history = defaultdict(list)

    def calculate_emergence_metrics(self, network_history: List[Any],
                                    traversal_history: List[Any],
                                    energy_history: List[float]) -> Dict[str, float]:
        """Calculate comprehensive emergence metrics.

        :param network_history: History of network snapshots (each element is a networkx.Graph or a dict containing 'network')
        :param traversal_history: Traversal history records
        :param energy_history: List of energy history
        :return: Dictionary containing compression emergence, migration emergence, energy optimization,
                 structural evolution, and overall emergence strength
        """
        if len(network_history) < 2:
            return {}

        # Get current and initial networks
        current_net = network_history[-1] if hasattr(network_history[-1], 'nodes') else network_history[-1]['network']
        previous_net = network_history[0] if hasattr(network_history[0], 'nodes') else network_history[0]['network']

        metrics = {
            'compression_emergence': self._measure_compression(current_net, previous_net),
            'migration_emergence': self._measure_migration(traversal_history, current_net),
            'energy_optimization': self._measure_energy_optimization(energy_history),
            'structural_evolution': self._measure_structural_evolution(current_net, previous_net)
        }

        metrics['overall_emergence_strength'] = (
            metrics['compression_emergence'] * 0.3 +
            metrics['migration_emergence'] * 0.3 +
            metrics['energy_optimization'] * 0.2 +
            metrics['structural_evolution'] * 0.2
        )

        self.metric_history['emergence'].append(metrics)
        return metrics

    def _measure_compression(self, current_net: nx.Graph, previous_net: nx.Graph) -> float:
        """Measure concept compression emergence strength: based on increments in clustering coefficient and modularity."""
        try:
            current_clustering = nx.average_clustering(current_net)
            previous_clustering = nx.average_clustering(previous_net)
            clustering_increase = max(0, current_clustering - previous_clustering)

            current_modularity = self._compute_modularity(current_net)
            previous_modularity = self._compute_modularity(previous_net)
            modularity_increase = max(0, current_modularity - previous_modularity)

            return min(1.0, (clustering_increase * 0.6 + modularity_increase * 0.4) * 5)
        except:
            return 0.0

    def _measure_migration(self, traversal_history: List[Any], network: nx.Graph) -> float:
        """Measure principle migration emergence strength: based on ratio of cross-domain paths and efficient paths."""
        if len(traversal_history) < 10:
            return 0.0

        cross_domain_paths = 0
        efficient_paths = 0

        for traversal in traversal_history[-20:]:
            path = self._extract_path(traversal)
            if not path or len(path) < 3:
                continue

            domains = set(self._infer_domain(node) for node in path)
            if len(domains) > 1:
                cross_domain_paths += 1

            efficiency = self._compute_path_efficiency(path, network)
            if efficiency > 0.5:
                efficient_paths += 1

        cross_domain_ratio = cross_domain_paths / len(traversal_history[-20:])
        efficiency_ratio = efficient_paths / len(traversal_history[-20:])

        return min(1.0, (cross_domain_ratio * 0.6 + efficiency_ratio * 0.4) * 2)

    def _measure_energy_optimization(self, energy_history: List[float]) -> float:
        """Measure energy optimization effect: based on recent energy reduction rate and stability."""
        if len(energy_history) < 50:
            return 0.0

        recent = energy_history[-50:]
        earlier = energy_history[-100:-50] if len(energy_history) >= 100 else energy_history[:50]

        if not earlier:
            return 0.0

        recent_avg = np.mean(recent)
        earlier_avg = np.mean(earlier)

        if earlier_avg > 0:
            reduction_rate = (earlier_avg - recent_avg) / earlier_avg
        else:
            reduction_rate = 0

        stability = 1.0 - (np.std(recent) / (np.mean(recent) + 1e-8))

        return min(1.0, max(0, reduction_rate) * 0.7 + stability * 0.3)

    def _measure_structural_evolution(self, current_net: nx.Graph, previous_net: nx.Graph) -> float:
        """Measure structural evolution: based on changes in small-world index and network density."""
        try:
            current_sw = self._small_world_index(current_net)
            previous_sw = self._small_world_index(previous_net)
            sw_improvement = max(0, current_sw - previous_sw)

            current_conn = nx.density(current_net)
            previous_conn = nx.density(previous_net)
            conn_change = abs(current_conn - previous_conn)

            return min(1.0, sw_improvement * 0.6 + conn_change * 0.4)
        except:
            return 0.0

    def _compute_modularity(self, network: nx.Graph) -> float:
        """Simplified modularity calculation: use connected components as communities."""
        try:
            components = list(nx.connected_components(network))
            if len(components) < 2:
                return 0.0
            return nx.algorithms.community.modularity(network, components)
        except:
            return 0.0

    def _small_world_index(self, network: nx.Graph) -> float:
        """Simplified small-world index: average clustering coefficient / average shortest path length (using largest connected component)."""
        try:
            clustering = nx.average_clustering(network)
            if nx.is_connected(network):
                path_length = nx.average_shortest_path_length(network)
            else:
                largest = max(nx.connected_components(network), key=len)
                subgraph = network.subgraph(largest)
                path_length = nx.average_shortest_path_length(subgraph)
            return clustering / (path_length + 1e-8)
        except:
            return 0.0

    def _extract_path(self, traversal: Any):
        """Extract path from traversal record."""
        if isinstance(traversal, (list, tuple)) and len(traversal) > 0:
            return traversal[0] if isinstance(traversal[0], list) else [traversal[0]]
        elif isinstance(traversal, dict) and 'path' in traversal:
            return traversal['path']
        return None

    def _compute_path_efficiency(self, path: List[str], network: nx.Graph) -> float:
        """Compute path efficiency: 1 / (average energy + 0.1)."""
        total_energy = 0
        valid_edges = 0
        for i in range(len(path)-1):
            if network.has_edge(path[i], path[i+1]):
                total_energy += network[path[i]][path[i+1]]['weight']
                valid_edges += 1
        if valid_edges == 0:
            return 0.0
        avg_energy = total_energy / valid_edges
        return 1.0 / (avg_energy + 0.1)

    def _infer_domain(self, concept: str) -> str:
        """Simple domain inference."""
        if 'force' in concept or 'energy' in concept or 'motion' in concept:
            return 'physics'
        elif 'calculus' in concept or 'geometry' in concept or 'algebra' in concept:
            return 'math'
        elif 'algorithm' in concept or 'data' in concept or 'network' in concept:
            return 'cs'
        elif 'optimization' in concept or 'iteration' in concept or 'abstraction' in concept:
            return 'principles'
        else:
            return 'other'

    def get_metric_trends(self) -> Dict[str, float]:
        """Get trends for each metric (mean and slope)."""
        if not self.metric_history['emergence']:
            return {}

        metrics = self.metric_history['emergence']
        trends = {}
        for key in metrics[0].keys():
            values = [m[key] for m in metrics]
            trends[f'{key}_mean'] = np.mean(values)
            trends[f'{key}_trend'] = self._compute_trend(values)
        return trends

    def _compute_trend(self, values: List[float]) -> float:
        """Compute linear trend slope."""
        if len(values) < 2:
            return 0.0
        x = np.arange(len(values))
        return np.polyfit(x, values, 1)[0]


if __name__ == "__main__":
    metrics = NaturalEmergenceMetrics()
    print("NaturalEmergenceMetrics initialized successfully")