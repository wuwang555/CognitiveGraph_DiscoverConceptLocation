# -*- coding: utf-8 -*-
"""
Compression / migration detector on the compression graph.

Mechanism mirrors the original paper's EmergenceDetectorFixed:
  - First build a traversal history via hard and soft walks
  - Then detect migrations (paths whose average co-occurrence
    exceeds an absolute threshold)
  - Separately detect compression clusters (Phi = internal /
    external co-occurrence exceeds an absolute threshold)

All thresholds are absolute, so different scales remain comparable.
No pruning, no percentile, no community detection, no cost mapping.
"""

import random
from typing import List, Dict, Any, Optional

import networkx as nx


class CompressionGraphDetector:
    def __init__(self, graph, config):
        self.graph = graph
        self.cfg = config
        self.rng = random.Random(config.get("random_seed", 42))

    # ================================================================== #
    # Migration detection
    # ================================================================== #
    def detect_migration(self) -> List[Dict[str, Any]]:
        history = self._build_traversal_history()
        threshold = self.cfg["migration_threshold"]

        migrations = []
        seen = set()

        for path in history:
            if len(path) < self.cfg["min_path_nodes"]:
                continue
            key = tuple(path)
            rkey = tuple(reversed(path))
            if key in seen or rkey in seen:
                continue
            seen.add(key)

            score = self._path_score(path)
            if score < threshold:
                continue

            migrations.append({
                "path": list(path),
                "length": len(path),
                "start": path[0],
                "end": path[-1],
                "score": score,
            })

        migrations.sort(key=lambda x: x["score"], reverse=True)
        return migrations

    def _build_traversal_history(self) -> List[List[str]]:
        G = self.graph.G
        if G.number_of_nodes() < 2:
            return []

        history = []

        # Hard traversal: seed from edges
        edges = list(G.edges())
        self.rng.shuffle(edges)
        n_hard = min(self.cfg["n_hard_walks"], len(edges) * 2)
        for u, v in edges[: n_hard // 2]:
            history.append(self._hard_walk(u))
            history.append(self._hard_walk(v))

        # Soft traversal: random start-end pairs, probabilistic walk
        nodes = list(G.nodes())
        n_soft = self.cfg["n_soft_walks"]
        for _ in range(n_soft):
            if len(nodes) < 2:
                break
            start, goal = self.rng.sample(nodes, 2)
            path = self._soft_walk(start, goal)
            if path is not None:
                history.append(path)

        return history

    def _hard_walk(self, start: str) -> List[str]:
        """From start, always pick the highest-count unvisited neighbor."""
        max_hops = self.cfg["max_path_nodes"] - 1
        path = [start]
        visited = {start}

        for _ in range(max_hops):
            current = path[-1]
            nbrs = [n for n in self.graph.G.neighbors(current) if n not in visited]
            if not nbrs:
                break
            nxt = max(nbrs, key=lambda n: self.graph.G[current][n]["count"])
            path.append(nxt)
            visited.add(nxt)

        return path

    def _soft_walk(self, start: str, goal: str) -> Optional[List[str]]:
        """From start, probabilistically walk (weighted by count) to goal."""
        max_hops = self.cfg["max_path_nodes"] - 1
        path = [start]
        visited = {start}
        current = start

        for _ in range(max_hops):
            if current == goal and len(path) >= self.cfg["min_path_nodes"]:
                return path

            nbrs = [n for n in self.graph.G.neighbors(current) if n not in visited]
            if not nbrs:
                return None

            weights = [self.graph.G[current][n]["count"] for n in nbrs]
            total = sum(weights)
            if total <= 0:
                return None

            r = self.rng.random() * total
            acc = 0.0
            nxt = nbrs[-1]
            for n, w in zip(nbrs, weights):
                acc += w
                if r <= acc:
                    nxt = n
                    break

            path.append(nxt)
            visited.add(nxt)
            current = nxt

        if current == goal and len(path) >= self.cfg["min_path_nodes"]:
            return path
        return None

    def _path_score(self, path: List[str]) -> float:
        if len(path) < 2:
            return 0.0
        counts = []
        for i in range(len(path) - 1):
            u, v = path[i], path[i + 1]
            if not self.graph.G.has_edge(u, v):
                return 0.0
            counts.append(self.graph.G[u][v]["count"])
        return sum(counts) / len(counts)

    # ================================================================== #
    # Compression detection
    # ================================================================== #
    def detect_compression(self) -> List[Dict[str, Any]]:
        """
        For each node as center, take the top-k neighbors by count,
        compute Phi = internal_avg / external_avg, and keep clusters
        whose Phi exceeds the absolute threshold.
        """
        G = self.graph.G
        min_k = self.cfg["min_cluster_size"]
        max_k = self.cfg["max_cluster_size"]
        threshold = self.cfg["compression_threshold"]

        clusters = []

        for center in G.nodes():
            nbrs = list(G.neighbors(center))
            if len(nbrs) < min_k:
                continue

            nbrs.sort(key=lambda n: G[center][n]["count"], reverse=True)
            max_here = min(max_k, len(nbrs))

            for k in range(min_k, max_here + 1):
                members = nbrs[:k]
                cluster = [center] + members
                phi = self._compression_potential(cluster)
                if phi is None or phi < threshold:
                    continue
                clusters.append({
                    "center": center,
                    "cluster": list(cluster),
                    "size": len(cluster),
                    "phi": phi,
                })

        clusters.sort(key=lambda x: x["phi"], reverse=True)
        return clusters

    def _compression_potential(self, cluster: List[str]) -> Optional[float]:
        G = self.graph.G
        S = set(cluster)

        internal = []
        external = []
        for u in S:
            for v in G.neighbors(u):
                c = G[u][v]["count"]
                if v in S:
                    if u < v:
                        internal.append(c)
                else:
                    external.append(c)

        if not internal or not external:
            return None
        avg_in = sum(internal) / len(internal)
        avg_ex = sum(external) / len(external)
        if avg_ex == 0:
            return None
        return avg_in / avg_ex