"""
Emergence Phenomenon Detector (Fixed Version)
-------------------------
Define EmergenceDetectorFixed class to detect spontaneous concept compression and principle migration phenomena
from the cognitive network. Includes calculation of cohesion, energy synchrony, emergence strength, etc.
"""

import numpy as np
import networkx as nx
from collections import defaultdict
from typing import Dict, List, Any, Tuple, Optional


class EmergenceDetectorFixed:
    """Fixed emergence phenomenon detector for detecting concept compression and principle migration.

    Detection thresholds can be specified during initialization; default values are empirically set.
    Includes deduplication mechanisms to avoid recording the same emergence event multiple times.
    """

    def __init__(self, detection_thresholds: Optional[Dict[str, float]] = None):
        """
        :param detection_thresholds: Threshold dictionary; supports the following keys:
            - compression_synergy: Compression synergy threshold (default 0.76)
            - migration_efficiency: Migration efficiency threshold (default 0.35)
            - pattern_stability: Pattern stability threshold (default 0.7)
            - energy_sync_threshold: Energy synchrony threshold (default 0.65)
            - cross_domain_gain: Cross-domain gain (default 0.2)
            - cluster_cohesion: Cluster cohesion threshold (default 0.7)
            - min_cluster_size: Minimum cluster size (default 2)
            - max_cluster_size: Maximum cluster size (default 6)
            - dynamic_cluster_sizing: Whether to dynamically determine cluster size (default True)
            - compression_persistence: Compression persistence requirement (default 3)
            - migration_confidence: Migration confidence threshold (default 0.75)
            - min_connection_strength: Minimum connection strength (default 0.5)
        """
        self.thresholds = detection_thresholds or {
            'compression_synergy': 0.76,
            'migration_efficiency': 0.35,
            'pattern_stability': 0.7,
            'energy_sync_threshold': 0.65,
            'cross_domain_gain': 0.2,
            'cluster_cohesion': 0.7,
            'min_cluster_size': 2,
            'max_cluster_size': 6,
            'dynamic_cluster_sizing': True,
            'compression_persistence': 3,
            'migration_confidence': 0.75,
            'min_connection_strength': 0.5
        }
        self.compression_history = defaultdict(list)
        self.migration_history = defaultdict(list)
        self.detection_history = {
            'compressions': [],
            'migrations': [],
            'patterns': []
        }

    def detect_spontaneous_compression(self, network: nx.Graph,
                                       energy_history: List[float],
                                       traversal_history: Optional[List[Any]] = None) -> List[Dict[str, Any]]:
        """Detect spontaneous concept compression phenomena.

        Compression candidates must satisfy:
            - The degree of the center node is within an appropriate range
            - Neighbor connection strengths exceed the threshold
            - Cluster cohesion, energy synchrony, and comprehensive emergence strength all exceed thresholds

        :param network: Current cognitive network
        :param energy_history: Network average energy history
        :param traversal_history: Traversal history (unused, retained for interface)
        :return: List of compression candidates, each a dictionary containing center node, related nodes, and various metrics
        """
        compression_candidates = []

        if len(energy_history) < 50:
            return compression_candidates

        node_degrees = dict(network.degree())
        candidate_nodes = [
            node for node, degree in node_degrees.items()
            if 3 <= degree <= 15
        ]

        for center in candidate_nodes:
            neighbors = list(network.neighbors(center))

            if len(neighbors) < self.thresholds['min_cluster_size']:
                continue

            connection_strengths = []
            for neighbor in neighbors:
                if network.has_edge(center, neighbor):
                    weight = network[center][neighbor]['weight']
                    strength = 1.0 / (1.0 + weight)
                    if strength > self.thresholds['min_connection_strength']:
                        connection_strengths.append((neighbor, strength))

            if len(connection_strengths) < self.thresholds['min_cluster_size']:
                continue

            connection_strengths.sort(key=lambda x: x[1], reverse=True)

            if self.thresholds['dynamic_cluster_sizing']:
                cluster_size = self._determine_dynamic_cluster_size(connection_strengths)
            else:
                cluster_size = self.thresholds['max_cluster_size']

            selected_neighbors = [n for n, s in connection_strengths[:cluster_size]]

            cohesion = self._compute_cluster_cohesion(center, selected_neighbors, network)

            energy_sync = self._compute_energy_synchronization_improved(
                center, selected_neighbors, network, energy_history
            )

            emergence_strength = self._compute_comprehensive_emergence_strength(
                center, selected_neighbors, network, cohesion, energy_sync
            )

            if (emergence_strength > self.thresholds['compression_synergy'] and
                    cohesion > self.thresholds['cluster_cohesion'] and
                    energy_sync > self.thresholds['energy_sync_threshold']):

                if not self._is_duplicate_compression(center, selected_neighbors):
                    potential = self._compute_compression_potential(center, selected_neighbors, network)
                    compression_candidates.append({
                        'center': center,
                        'related_nodes': selected_neighbors,
                        'energy_synergy': energy_sync,
                        'cohesion': cohesion,
                        'emergence_strength': emergence_strength,
                        'cluster_size': len(selected_neighbors),
                        'avg_connection_strength': np.mean([s for _, s in connection_strengths[:cluster_size]]),
                        'compression_potential': potential  # Added field
                    })

        return compression_candidates[:10]

    def _determine_dynamic_cluster_size(self, connection_strengths: List[Tuple[str, float]]) -> int:
        """Dynamically determine cluster size based on the distribution of connection strengths.

        Find the point where strength drops significantly (below mean - 0.5 * std). If none, return a moderate size.

        :param connection_strengths: List of (node, strength) sorted descending by strength
        :return: Cluster size
        """
        strengths = [s for _, s in connection_strengths]
        avg_strength = np.mean(strengths)
        std_strength = np.std(strengths)

        for i in range(1, len(strengths)):
            if strengths[i] < avg_strength - 0.5 * std_strength:
                return max(self.thresholds['min_cluster_size'],
                           min(i, self.thresholds['max_cluster_size']))

        return min(len(strengths),
                   max(self.thresholds['min_cluster_size'] + 2,
                       len(strengths) // 2))

    def _compute_energy_synchronization_improved(self, center: str, neighbors: List[str],
                                                 network: nx.Graph, energy_history: List[float]) -> float:
        """Compute the energy change synchrony between the center node and its neighbors.

        :return: Synchrony score [0,1]
        """
        if len(neighbors) < 2:
            return 0.0

        center_trend = self._compute_energy_trend(center, network, energy_history)
        neighbor_trends = []
        for neighbor in neighbors:
            trend = self._compute_energy_trend(neighbor, network, energy_history)
            neighbor_trends.append(trend)

        if not neighbor_trends:
            return 0.0

        avg_neighbor_trend = np.mean(neighbor_trends)
        trend_similarity = 1.0 - abs(center_trend - avg_neighbor_trend)
        return max(0.0, trend_similarity)

    def _compute_energy_trend(self, node: str, network: nx.Graph,
                              energy_history: List[float], window_size: int = 20) -> float:
        """Estimate the node-related energy trend (based on the current average energy of its incident edges)."""
        if len(energy_history) < window_size:
            return 0.0

        recent_energies = []
        for neighbor in network.neighbors(node):
            if network.has_edge(node, neighbor):
                recent_energies.append(network[node][neighbor]['weight'])

        if not recent_energies:
            return 0.0

        return np.mean(recent_energies)

    def _compute_comprehensive_emergence_strength(self, center: str, neighbors: List[str],
                                                  network: nx.Graph, cohesion: float,
                                                  energy_sync: float) -> float:
        """Comprehensive emergence strength, combining cohesion, energy synchrony, connection density, and semantic coherence."""
        connection_density = self._compute_connection_density(neighbors, network)
        semantic_coherence = self._estimate_semantic_coherence(center, neighbors)

        emergence_strength = (
                0.3 * cohesion +
                0.3 * energy_sync +
                0.2 * connection_density +
                0.2 * semantic_coherence
        )
        return min(1.0, emergence_strength)

    def _compute_connection_density(self, nodes: List[str], network: nx.Graph) -> float:
        """Compute the internal connection density of a set of nodes."""
        if len(nodes) < 2:
            return 0.0

        possible = len(nodes) * (len(nodes) - 1) / 2
        actual = 0
        for i, n1 in enumerate(nodes):
            for n2 in nodes[i + 1:]:
                if network.has_edge(n1, n2):
                    actual += 1
        return actual / possible if possible > 0 else 0.0

    def _estimate_semantic_coherence(self, center: str, neighbors: List[str]) -> float:
        """Estimate semantic coherence among nodes using a heuristic based on character overlap in node names."""
        center_words = set(center)
        scores = []
        for neighbor in neighbors:
            neighbor_words = set(neighbor)
            overlap = len(center_words.intersection(neighbor_words))
            total = len(center_words.union(neighbor_words))
            if total > 0:
                scores.append(overlap / total)
        return np.mean(scores) if scores else 0.0

    def _compute_cluster_cohesion(self, center: str, neighbors: List[str], network: nx.Graph) -> float:
        """Compute cohesion among neighbor nodes (edge density)."""
        if len(neighbors) < 2:
            return 0.0

        total_possible = len(neighbors) * (len(neighbors) - 1) / 2
        actual_connections = 0
        for i, n1 in enumerate(neighbors):
            for n2 in neighbors[i + 1:]:
                if network.has_edge(n1, n2):
                    actual_connections += 1
        return actual_connections / total_possible if total_possible > 0 else 0.0

    def detect_emergent_migration(self, network: nx.Graph,
                                  traversal_history: Optional[List[Any]] = None,
                                  current_iteration: int = 0,
                                  semantic_network: Optional[Any] = None) -> List[Dict[str, Any]]:
        """Detect emergent principle migration phenomena.

        Analyze recent traversal paths, identify those containing principle nodes and crossing domains, and compute efficiency gains.

        :param network: Current cognitive network
        :param traversal_history: Traversal history records
        :param current_iteration: Current iteration number
        :param semantic_network: Semantic network (optional, for more refined judgments)
        :return: List of migration candidates
        """
        migrations = []

        if traversal_history is None or len(traversal_history) < 10:
            return migrations

        recent_paths = []
        for traversal in traversal_history[-20:]:
            path = self._extract_traversal_path(traversal)
            if path and len(path) >= 3:
                recent_paths.append(path)

        for path in recent_paths:
            principle_nodes = [node for node in path if self._is_principle_node(node)]

            if len(principle_nodes) > 0 and self._is_cross_domain_path(path):
                path_efficiency = self._calculate_path_efficiency(path, network)

                if path_efficiency > self.thresholds['migration_efficiency']:
                    principle_node = principle_nodes[0]

                    migration = {
                        'type': 'first_principles_migration',
                        'principle_node': principle_node,
                        'from_node': path[0],
                        'to_node': path[-1],
                        'efficiency_gain': path_efficiency,
                        'path': path,
                        'emergence_iteration': current_iteration,
                        'domain_span': self._calculate_domain_span_simple(path)
                    }
                    migrations.append(migration)

        return migrations

    def _extract_traversal_path(self, traversal: Any) -> Optional[List[str]]:
        """Extract path list from a traversal record."""
        if isinstance(traversal, dict) and 'path' in traversal:
            return traversal['path']
        elif isinstance(traversal, (list, tuple)) and len(traversal) > 0:
            if isinstance(traversal[0], list):
                return traversal[0]
            elif len(traversal) >= 3:
                return traversal[0] if isinstance(traversal[0], list) else [traversal[0]]
        return None

    def _is_principle_node(self, node: str) -> bool:
        """Check if the node name contains principle-related keywords."""
        principle_keywords = ['优化', '变换', '抽象', '模式', '递归', '迭代', '对称', '归纳']
        return any(keyword in node for keyword in principle_keywords)

    def _is_cross_domain_path(self, path: List[str]) -> bool:
        """Check if the path spans multiple domains."""
        if len(path) < 2:
            return False
        domains = [self._infer_domain(node) for node in path]
        return len(set(domains)) > 1

    def _calculate_path_efficiency(self, path: List[str], network: nx.Graph) -> float:
        """Compute path efficiency: 1 / (total energy * path length)."""
        total_energy = 0.0
        for i in range(len(path) - 1):
            if network.has_edge(path[i], path[i + 1]):
                total_energy += network[path[i]][path[i + 1]]['weight']
        if total_energy > 0:
            efficiency = 1.0 / (total_energy * len(path))
            return min(efficiency, 1.0)
        return 0.0

    def _calculate_domain_span_simple(self, path: List[str]) -> int:
        """Calculate the number of domains covered by the path."""
        domains = set()
        for node in path:
            domains.add(self._infer_domain(node))
        return len(domains)

    def _infer_domain(self, concept: str) -> str:
        """Infer the domain of a concept based on keywords."""
        domain_keywords = {
            'physics': ['力', '运动', '能量', '动量', '牛顿', '引力', '摩擦', '静电'],
            'math': ['积分', '几何', '代数', '概率', '统计', '微积分', '拓扑', '线性'],
            'cs': ['算法', '数据', '网络', '学习', '智能', '机器', '计算机', '视觉'],
            'principles': ['优化', '变换', '抽象', '模式', '递归', '迭代', '对称', '归纳'],
            'cognitive': ['认知', '记忆', '注意', '元认知', '心理'],
            'neuroscience': ['神经', '突触', '海马', '前额叶'],
            'philosophy': ['认识论', '本体论', '逻辑学', '伦理学']
        }
        for domain, keywords in domain_keywords.items():
            if any(keyword in concept for keyword in keywords):
                return domain
        return 'other'

    def calculate_compression_confidence(self, compression: Dict[str, Any]) -> float:
        """Calculate the confidence of a compression event."""
        synergy = compression.get('energy_synergy', 0)
        cohesion = compression.get('cohesion', 0)
        cluster_size = compression.get('cluster_size', 0)

        confidence = (
                0.4 * synergy +
                0.3 * cohesion +
                0.2 * min(1.0, cluster_size / 6) +
                0.1 * self._calculate_temporal_stability(compression)
        )
        return min(1.0, confidence)

    def calculate_migration_confidence(self, migration: Dict[str, Any]) -> float:
        """Calculate the confidence of a migration event."""
        efficiency = migration.get('efficiency_gain', 0)
        domain_span = migration.get('domain_span', 0)
        path_length = len(migration.get('path', []))

        confidence = (
                0.5 * efficiency +
                0.2 * min(1.0, domain_span / 3) +
                0.2 * (1.0 / max(1, path_length)) +
                0.1 * self._calculate_innovation_score(migration)
        )
        return min(1.0, confidence)

    def _calculate_temporal_stability(self, compression: Dict[str, Any]) -> float:
        """Calculate the temporal stability of compression (based on historical records)."""
        center = compression['center']
        current_strength = compression['emergence_strength']

        if center in self.compression_history:
            historical_strengths = [c['emergence_strength'] for c in self.compression_history[center]]
            avg_historical = np.mean(historical_strengths)
            stability = 1.0 - abs(current_strength - avg_historical)
            return max(0, stability)
        return 0.5

    def _calculate_innovation_score(self, migration: Dict[str, Any]) -> float:
        """Calculate the innovation score of a migration."""
        path = migration.get('path', [])
        principle_node = migration.get('principle_node', '')

        innovation_score = 0.0
        if len(path) >= 3:
            if principle_node not in self.migration_history:
                innovation_score += 0.3

            domains = [self._infer_domain(node) for node in path]
            unique_domains = len(set(domains))
            innovation_score += min(0.7, unique_domains * 0.2)

        return innovation_score

    def _is_duplicate_compression(self, center: str, neighbors: List[str]) -> bool:
        """Check if the same compression event has already been recorded."""
        key = (center, tuple(sorted(neighbors)))
        if key in self.compression_history:
            return True
        self.compression_history[key] = True
        return False

    def _compute_compression_potential(self, center: str, neighbors: List[str], network: nx.Graph) -> float:
        """Compute cluster compression potential Φ = internal average energy / external average energy."""
        cluster_nodes = {center} | set(neighbors)
        internal_energy = 0.0
        internal_count = 0
        external_energy = 0.0
        external_count = 0
        processed_edges = set()

        for v in cluster_nodes:
            for u in network.neighbors(v):
                edge = tuple(sorted((v, u)))
                if edge in processed_edges:
                    continue
                processed_edges.add(edge)
                weight = network[v][u]['weight']
                if u in cluster_nodes:
                    internal_energy += weight
                    internal_count += 1
                else:
                    external_energy += weight
                    external_count += 1

        avg_internal = internal_energy / internal_count if internal_count > 0 else 0.0
        avg_external = external_energy / external_count if external_count > 0 else None

        if avg_external is None or avg_external == 0:
            # No external connections; potential is undefined, set to None (JSON serializes as null)
            return None
        return avg_internal / avg_external


if __name__ == "__main__":
    # Simple test
    detector = EmergenceDetectorFixed()
    print("EmergenceDetectorFixed initialized successfully")