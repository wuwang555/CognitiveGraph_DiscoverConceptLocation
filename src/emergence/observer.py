"""
Emergence Phenomenon Observer (Simplified Version)
------------------------
Define EmergenceObserver class to observe and record concept compression and principle migration phenomena in real time.
"""

import numpy as np
from typing import List, Dict, Any, Optional


class EmergenceObserver:
    """Emergence phenomenon observer, periodically detects emergence events from the network and records them."""

    def __init__(self):
        self.observations = {
            'compressions': [],
            'migrations': [],
            'energy_patterns': []
        }

        self.thresholds = {
            'compression_synergy': 0.7,
            'migration_efficiency': 0.3,
            'pattern_stability': 0.6
        }

    def observe_compression_emergence(self, network: Any, energy_history: List[float],
                                      iteration: int) -> List[Dict[str, Any]]:
        """Observe concept compression emergence.

        :param network: Cognitive network (should have nodes() and neighbors() methods)
        :param energy_history: Energy history
        :param iteration: Current iteration number
        :return: List of compression events observed in this step
        """
        compressions = []

        for node in network.nodes():
            neighbors = list(network.neighbors(node))
            if len(neighbors) < 3:
                continue

            cohesion = self._compute_cohesion(node, neighbors, network)
            energy_sync = self._compute_energy_sync(node, neighbors, energy_history)

            if cohesion > 0.5 and energy_sync > self.thresholds['compression_synergy']:
                compression = {
                    'center': node,
                    'related_nodes': neighbors,
                    'cohesion': cohesion,
                    'energy_sync': energy_sync,
                    'iteration': iteration
                }
                compressions.append(compression)
                self.observations['compressions'].append(compression)

        return compressions

    def observe_migration_emergence(self, network: Any, traversal_history: List[Any],
                                    iteration: int) -> List[Dict[str, Any]]:
        """Observe principle migration emergence.

        :param network: Cognitive network
        :param traversal_history: Traversal history
        :param iteration: Current iteration number
        :return: List of migration events observed in this step
        """
        migrations = []

        if len(traversal_history) < 10:
            return migrations

        for traversal in traversal_history[-10:]:
            path = self._extract_path(traversal)
            if not path or len(path) < 3:
                continue

            if self._is_cross_domain(path):
                efficiency = self._compute_path_efficiency(path, network)

                if efficiency > self.thresholds['migration_efficiency']:
                    mediator = self._find_mediator(path)
                    migration = {
                        'principle_node': mediator,
                        'path': path,
                        'efficiency': efficiency,
                        'iteration': iteration
                    }
                    migrations.append(migration)
                    self.observations['migrations'].append(migration)

        return migrations

    def _compute_cohesion(self, center: str, neighbors: List[str], network: Any) -> float:
        """Compute cohesion among neighbor nodes (edge density)."""
        connections = 0
        possible = len(neighbors) * (len(neighbors) - 1) / 2
        for i, n1 in enumerate(neighbors):
            for n2 in neighbors[i+1:]:
                if network.has_edge(n1, n2):
                    connections += 1
        return connections / possible if possible > 0 else 0

    def _compute_energy_sync(self, center: str, neighbors: List[str], energy_history: List[float]) -> float:
        """Compute energy synchrony: based on the flatness of recent energy change trend."""
        if len(energy_history) < 20:
            return 0.5
        recent = energy_history[-20:]
        trend = np.polyfit(range(len(recent)), recent, 1)[0]
        return max(0, 1 - abs(trend))

    def _extract_path(self, traversal: Any) -> Optional[List[str]]:
        """Extract path from traversal record."""
        if isinstance(traversal, (list, tuple)) and len(traversal) > 0:
            return traversal[0] if isinstance(traversal[0], list) else [traversal[0]]
        elif isinstance(traversal, dict) and 'path' in traversal:
            return traversal['path']
        return None

    def _is_cross_domain(self, path: List[str]) -> bool:
        """Determine if a path is cross-domain."""
        domains = set()
        for node in path:
            domain = self._infer_domain(node)
            domains.add(domain)
        return len(domains) > 1

    def _compute_path_efficiency(self, path: List[str], network: Any) -> float:
        """Compute path efficiency: 1 / (total energy + 0.1)."""
        total_energy = 0
        for i in range(len(path)-1):
            if network.has_edge(path[i], path[i+1]):
                total_energy += network[path[i]][path[i+1]]['weight']
        return 1.0 / (total_energy + 0.1) if total_energy > 0 else 0

    def _find_mediator(self, path: List[str]) -> str:
        """Return the middle node of the path as the mediator."""
        if len(path) < 3:
            return path[0] if path else ""
        return path[len(path)//2]

    def _infer_domain(self, concept: str) -> str:
        """Simple domain inference."""
        domain_keywords = {
            'physics': ['力', '运动', '能量', '牛顿'],
            'math': ['积分', '几何', '代数', '概率'],
            'cs': ['算法', '数据', '网络', '学习'],
            'principles': ['优化', '变换', '迭代', '抽象']
        }
        for domain, keywords in domain_keywords.items():
            if any(keyword in concept for keyword in keywords):
                return domain
        return 'other'

    def get_observation_summary(self) -> Dict[str, int]:
        """Return observation statistics summary."""
        return {
            'total_compressions': len(self.observations['compressions']),
            'total_migrations': len(self.observations['migrations']),
            'total_patterns': len(self.observations['energy_patterns'])
        }


if __name__ == "__main__":
    obs = EmergenceObserver()
    print("EmergenceObserver initialized successfully")