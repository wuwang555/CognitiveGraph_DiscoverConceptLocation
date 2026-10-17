# -*- coding: utf-8 -*-
"""
Visualization helpers for the compression graph.
"""

from pathlib import Path
from typing import List, Dict, Any, Optional

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np


def plot_compression_graph(graph, out_path: Optional[Path] = None) -> None:
    G = graph.G
    if G.number_of_edges() == 0:
        return

    fig, ax = plt.subplots(figsize=(14, 10))
    pos = nx.spring_layout(G, seed=42, k=0.5)
    counts = np.array([d["count"] for _, _, d in G.edges(data=True)], dtype=float)
    widths = 0.5 + 4.0 * (counts / counts.max() if counts.max() > 0 else counts)

    nx.draw_networkx_nodes(G, pos, node_size=250, node_color="lightblue",
                           edgecolors="black", ax=ax)
    nx.draw_networkx_edges(G, pos, width=widths, alpha=0.5,
                           edge_color="gray", ax=ax)
    nx.draw_networkx_labels(G, pos, font_size=6, ax=ax)
    ax.set_title("Compression graph")
    ax.axis("off")
    plt.tight_layout()
    if out_path:
        plt.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_edge_count_distribution(graph, out_path: Optional[Path] = None) -> None:
    counts = [d["count"] for _, _, d in graph.G.edges(data=True)]
    if not counts:
        return
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.hist(counts, bins=30, edgecolor="black", alpha=0.7)
    ax.set_xlabel("Co-occurrence count")
    ax.set_ylabel("Number of edges")
    ax.set_title("Edge co-occurrence distribution")
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    if out_path:
        plt.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_migration_paths(graph, migrations: List[Dict[str, Any]],
                         out_path: Optional[Path] = None) -> None:
    G = graph.G
    if not migrations:
        return
    fig, ax = plt.subplots(figsize=(14, 10))
    pos = nx.spring_layout(G, seed=42, k=0.5)

    nx.draw_networkx_nodes(G, pos, node_size=150, node_color="lightgray",
                           edgecolors="black", ax=ax)
    nx.draw_networkx_edges(G, pos, alpha=0.1, edge_color="gray", ax=ax)
    nx.draw_networkx_labels(G, pos, font_size=5, ax=ax)

    cmap = plt.cm.tab10
    for i, m in enumerate(migrations):
        path = m["path"]
        color = cmap(i % 10)
        edges = [(path[j], path[j + 1]) for j in range(len(path) - 1)]
        nx.draw_networkx_edges(G, pos, edgelist=edges, width=3.0,
                               edge_color=[color], alpha=0.9, ax=ax)
        nx.draw_networkx_nodes(G, pos, nodelist=path, node_size=350,
                               node_color=[color], ax=ax)

    ax.set_title("Top migration paths")
    ax.axis("off")
    plt.tight_layout()
    if out_path:
        plt.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close(fig)