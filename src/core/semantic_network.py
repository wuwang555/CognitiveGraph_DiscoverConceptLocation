"""
Semantic Network Module
-------------
Define semantic concept network and related classes. Compute similarity between concepts based on keywords and meta-structures,
and support building comprehensive networks, cross-domain path search, and other functions.
"""

import time
from collections import defaultdict
from typing import List, Dict, Optional, Tuple, Any

import jieba
import numpy as np

from config import (
    CORE_CONCEPT_DEFINITIONS, CONCEPT_DOMAINS,
    META_STRUCTURE_MAP, NETWORK_CONFIG, KEYWORD_CONFIG
)


class SemanticConceptNetwork:
    """Semantic concept network based on definition keywords.

    This class maintains concept definitions and keyword lists, computes semantic similarity between concepts
    via Jaccard similarity of keywords and domain similarity. Supports building comprehensive networks,
    recursive expansion, and cross-domain path search.
    """

    def __init__(self):
        self.concept_definitions: Dict[str, Dict] = {}      # concept -> {definition, source, timestamp}
        self.concept_keywords: Dict[str, List[str]] = {}    # concept -> keyword list
        self.semantic_network: Dict[str, Dict[str, float]] = defaultdict(dict)  # concept -> neighbor concept -> similarity

    def add_concept_definition(self, concept: str, definition: str, source: str = "manual") -> None:
        """Add a concept definition and automatically extract keywords.

        :param concept: Concept name
        :param definition: Definition text
        :param source: Source identifier
        """
        self.concept_definitions[concept] = {
            'definition': definition,
            'source': source,
            'timestamp': time.time()
        }

        keywords = self.extract_keywords(definition)
        self.concept_keywords[concept] = keywords

        print(f"Added concept '{concept}': {definition}")
        print(f"  Extracted keywords: {keywords}")

    def extract_keywords(self, text: str, top_k: Optional[int] = None) -> List[str]:
        """Extract keywords from text using jieba segmentation and stop word filtering.

        :param text: Input text
        :param top_k: Number of keywords to return, defaults to reading from config
        :return: List of keywords
        """
        if top_k is None:
            top_k = KEYWORD_CONFIG['top_k']

        words = jieba.cut(text)
        filtered_words = [
            word for word in words
            if len(word) > KEYWORD_CONFIG['min_word_length'] and word not in KEYWORD_CONFIG['stop_words']
        ]

        word_freq = defaultdict(int)
        for word in filtered_words:
            word_freq[word] += 1

        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        return [word for word, freq in sorted_words[:top_k]]

    def expand_concept_network(self, concept: str, max_depth: Optional[int] = None, current_depth: int = 0) -> None:
        """Recursively expand the concept network, connecting the concept's keywords (if they are also defined concepts).

        :param concept: Current concept
        :param max_depth: Maximum recursion depth
        :param current_depth: Current depth
        """
        if max_depth is None:
            max_depth = NETWORK_CONFIG['max_expansion_depth']

        if current_depth >= max_depth or concept not in self.concept_keywords:
            return

        keywords = self.concept_keywords[concept]

        for keyword in keywords:
            if keyword in self.concept_definitions:
                similarity = self.calculate_semantic_similarity(concept, keyword)
                self.semantic_network[concept][keyword] = similarity
                self.semantic_network[keyword][concept] = similarity

                if current_depth < max_depth - 1:
                    self.expand_concept_network(keyword, max_depth, current_depth + 1)

    def calculate_semantic_similarity(self, concept1: str, concept2: str) -> float:
        """Compute semantic similarity between two concepts using a weighted sum of Jaccard similarity (keyword intersection/union) and domain similarity.

        :param concept1: First concept
        :param concept2: Second concept
        :return: Similarity value (0~1)
        """
        if concept1 not in self.concept_keywords or concept2 not in self.concept_keywords:
            return 0.0

        keywords1 = set(self.concept_keywords[concept1])
        keywords2 = set(self.concept_keywords[concept2])

        intersection = len(keywords1.intersection(keywords2))
        union = len(keywords1.union(keywords2))

        if union == 0:
            return 0.0

        jaccard_similarity = intersection / union

        domain_similarity = self._calculate_domain_similarity(concept1, concept2)

        combined_similarity = 0.7 * jaccard_similarity + 0.3 * domain_similarity
        return min(combined_similarity, 1.0)

    def _calculate_domain_similarity(self, concept1: str, concept2: str) -> float:
        """Compute domain similarity based on the concept's domain.

        :return: Domain similarity
        """
        domain1 = self.get_domain(concept1)
        domain2 = self.get_domain(concept2)

        if domain1 == domain2:
            return 1.0
        elif (domain1 == "principles" or domain2 == "principles"):
            return 0.6
        else:
            return 0.2

    def build_comprehensive_network(self, num_concepts: Optional[int] = None) -> None:
        """Build a comprehensive concept network.

        Build all concept nodes based on core concept definitions, compute pairwise similarities, and expand recursively.

        :param num_concepts: Optional, number of core concepts to use (take the first N from config)
        """
        self._predefine_core_concepts(num_concepts)

        all_concepts = list(self.concept_definitions.keys())
        print(f"Building semantic network, total {len(all_concepts)} concepts")

        threshold = NETWORK_CONFIG['similarity_threshold']
        for i, concept1 in enumerate(all_concepts):
            for j, concept2 in enumerate(all_concepts[i + 1:], i + 1):
                similarity = self.calculate_semantic_similarity(concept1, concept2)
                if similarity > threshold:
                    self.semantic_network[concept1][concept2] = similarity
                    self.semantic_network[concept2][concept1] = similarity

        for concept in all_concepts:
            self.expand_concept_network(concept)

        print(f"Semantic network construction completed! Contains {len(self.semantic_network)} concept nodes")
        total_connections = sum(len(neighbors) for neighbors in self.semantic_network.values()) // 2
        print(f"Number of connections: {total_connections}")

    def _predefine_core_concepts(self, num_concepts: Optional[int] = None) -> None:
        """Load core concept definitions from config.

        :param num_concepts: Optional, number of concepts to load
        """
        if num_concepts is not None:
            all_concepts = list(CORE_CONCEPT_DEFINITIONS.keys())
            if num_concepts > len(all_concepts):
                print(f"Warning: Requested {num_concepts} concepts exceeds maximum {len(all_concepts)}, using maximum")
                num_concepts = len(all_concepts)

            selected_concepts = all_concepts[:num_concepts]
            for concept in selected_concepts:
                definition = CORE_CONCEPT_DEFINITIONS[concept]
                self.add_concept_definition(concept, definition, "predefined")
            print(f"Using first {num_concepts} core concepts to build semantic network")
        else:
            for concept, definition in CORE_CONCEPT_DEFINITIONS.items():
                self.add_concept_definition(concept, definition, "predefined")
            print(f"Using all {len(CORE_CONCEPT_DEFINITIONS)} core concepts to build semantic network")

    def find_cross_domain_paths(self, start_concept: str, end_concept: str,
                                 max_path_length: Optional[int] = None) -> List[Tuple[List[str], float]]:
        """Find cross-domain paths between two concepts (breadth-first search).

        :param start_concept: Starting concept
        :param end_concept: Target concept
        :param max_path_length: Maximum path length
        :return: List of (path node list, cumulative similarity)
        """
        if max_path_length is None:
            max_path_length = NETWORK_CONFIG['max_path_length']

        if start_concept not in self.semantic_network or end_concept not in self.semantic_network:
            return []

        max_paths = NETWORK_CONFIG['max_paths_to_find']
        queue = [(start_concept, [start_concept], 1.0)]
        visited = {start_concept}
        found_paths = []

        while queue and len(found_paths) < max_paths:
            current, path, path_similarity = queue.pop(0)

            if current == end_concept and len(path) > 1:
                found_paths.append((path, path_similarity))
                continue

            if len(path) >= max_path_length:
                continue

            for neighbor, similarity in self.semantic_network[current].items():
                if neighbor not in visited:
                    visited.add(neighbor)
                    new_similarity = path_similarity * similarity
                    queue.append((neighbor, path + [neighbor], new_similarity))

        found_paths.sort(key=lambda x: x[1], reverse=True)
        return found_paths

    def get_domain(self, concept: str) -> str:
        """Return the domain of a concept; returns 'other' if not defined."""
        for domain, concepts in CONCEPT_DOMAINS.items():
            if concept in concepts:
                return domain
        return "other"

    def visualize_semantic_network(self, highlight_concepts: Optional[List[str]] = None) -> None:
        """Visualize the semantic network (requires matplotlib)."""
        from utils.visualization import visualize_semantic_network
        visualize_semantic_network(self.semantic_network, self.concept_definitions, highlight_concepts)

        import matplotlib.pyplot as plt
        import os
        from datetime import datetime
        fig_dir = "results/semantic_network"
        os.makedirs(fig_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        plt.tight_layout()
        plt.savefig(os.path.join(fig_dir, f"semantic_network_{timestamp}.png"),
                    dpi=300, bbox_inches='tight')
        print(f"Semantic network figure saved to results/semantic_network/")


class MetaStructureSimilarity:
    """Meta-structure based similarity computation, mapping concepts to meta-structure space and computing cosine similarity."""

    def __init__(self):
        self.meta_structure_map = META_STRUCTURE_MAP
        self.concept_to_meta = {}
        for meta, concepts in self.meta_structure_map.items():
            for concept in concepts:
                self.concept_to_meta[concept] = meta

    def map_to_meta_structure(self, concept: str) -> np.ndarray:
        """Map a concept to a vector in meta-structure space.

        :param concept: Concept name
        :return: Vector of length equal to the number of meta-structures; the corresponding dimension is 1 for an exact match, 0.5 for keyword match.
        """
        meta_vector = np.zeros(len(self.meta_structure_map))
        meta_list = list(self.meta_structure_map.keys())

        if concept in self.concept_to_meta:
            meta = self.concept_to_meta[concept]
            idx = meta_list.index(meta)
            meta_vector[idx] = 1.0

        for i, meta in enumerate(meta_list):
            related_concepts = self.meta_structure_map[meta]
            for related in related_concepts:
                if related in concept:
                    meta_vector[i] = max(meta_vector[i], 0.5)

        return meta_vector

    def meta_structure_similarity(self, concept1: str, concept2: str) -> float:
        """Compute cosine similarity between two concepts in meta-structure space.

        :return: Similarity (0~1)
        """
        vec1 = self.map_to_meta_structure(concept1)
        vec2 = self.map_to_meta_structure(concept2)

        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return dot_product / (norm1 * norm2)


class EnhancedSemanticConceptNetwork(SemanticConceptNetwork):
    """Enhanced semantic concept network, integrating meta-structure similarity, providing multiple similarity calculation methods."""

    def __init__(self, num_concepts: Optional[int] = None):
        super().__init__()
        self.meta_similarity = MetaStructureSimilarity()
        self.concept_frequency = defaultdict(int)
        self.num_concepts = num_concepts

    def build_comprehensive_network(self) -> None:
        """Override parent method, build network using num_concepts."""
        self._predefine_core_concepts(self.num_concepts)

        all_concepts = list(self.concept_definitions.keys())
        print(f"Building enhanced semantic network, total {len(all_concepts)} concepts")

        threshold = NETWORK_CONFIG['similarity_threshold']
        for i, concept1 in enumerate(all_concepts):
            for j, concept2 in enumerate(all_concepts[i + 1:], i + 1):
                similarity = self.calculate_semantic_similarity(concept1, concept2)
                if similarity > threshold:
                    self.semantic_network[concept1][concept2] = similarity
                    self.semantic_network[concept2][concept1] = similarity

        for concept in all_concepts:
            self.expand_concept_network(concept)

        print(f"Enhanced semantic network construction completed! Contains {len(self.semantic_network)} concept nodes")
        total_connections = sum(len(neighbors) for neighbors in self.semantic_network.values()) // 2
        print(f"Number of connections: {total_connections}")

    def calculate_enhanced_similarity(self, concept1: str, concept2: str,
                                      method: str = "combined") -> float:
        """Enhanced similarity calculation, supporting multiple strategies.

        :param concept1: First concept
        :param concept2: Second concept
        :param method: Calculation method, options: 'semantic_only', 'meta_only', 'combined', 'adaptive'
        :return: Similarity value
        """
        if method == "semantic_only":
            return self.calculate_semantic_similarity(concept1, concept2)

        elif method == "meta_only":
            return self.meta_similarity.meta_structure_similarity(concept1, concept2)

        elif method == "combined":
            semantic_sim = self.calculate_semantic_similarity(concept1, concept2)
            meta_sim = self.meta_similarity.meta_structure_similarity(concept1, concept2)

            complexity1 = self._concept_complexity(concept1)
            complexity2 = self._concept_complexity(concept2)
            avg_complexity = (complexity1 + complexity2) / 2

            meta_weight = min(0.7, 0.3 + avg_complexity * 0.4)
            semantic_weight = 1 - meta_weight

            return semantic_weight * semantic_sim + meta_weight * meta_sim

        elif method == "adaptive":
            semantic_sim = self.calculate_semantic_similarity(concept1, concept2)
            meta_sim = self.meta_similarity.meta_structure_similarity(concept1, concept2)
            abstraction_level = self._abstraction_level(concept1, concept2)

            if abstraction_level > 0.6:
                return meta_sim * 0.8 + semantic_sim * 0.2
            elif abstraction_level < 0.3:
                return semantic_sim * 0.8 + meta_sim * 0.2
            else:
                return (semantic_sim + meta_sim) / 2

        return 0.0

    def _concept_complexity(self, concept: str) -> float:
        """Estimate concept complexity based on number of keywords and diversity."""
        if concept not in self.concept_keywords:
            return 0.5

        keywords = self.concept_keywords[concept]
        num_keywords = len(keywords)
        keyword_variety = len(set(keywords)) / max(1, num_keywords)

        complexity = min(1.0, num_keywords / 15 * 0.6 + keyword_variety * 0.4)
        return complexity

    def _abstraction_level(self, concept1: str, concept2: str) -> float:
        """Estimate the average abstraction level of two concepts."""
        def single_concept_abstraction(concept: str) -> float:
            meta_vec = self.meta_similarity.map_to_meta_structure(concept)
            abstraction_score = np.sum(meta_vec) / len(meta_vec)

            if concept in self.concept_definitions:
                definition_length = len(self.concept_definitions[concept]['definition'])
                length_factor = min(1.0, definition_length / 100)
                abstraction_score = 0.7 * abstraction_score + 0.3 * length_factor

            return abstraction_score

        abstraction1 = single_concept_abstraction(concept1)
        abstraction2 = single_concept_abstraction(concept2)
        return (abstraction1 + abstraction2) / 2


if __name__ == "__main__":
    # Simple test
    net = SemanticConceptNetwork()
    net.build_comprehensive_network(num_concepts=51)
    print("Semantic network built successfully")