"""
Cognitive Graph Visualization Module.

Provides functions for drawing and saving cognitive networks, energy convergence processes, cognitive state changes, etc.
"""

import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import os
from datetime import datetime
from core.cognitive_states import CognitiveState

# Get current timestamp (generated once at module load to ensure consistent filenames within the same batch)
_TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S")
_VIZ_DIR = "results/visualizations"
os.makedirs(_VIZ_DIR, exist_ok=True)


def _auto_save_fig(fig, func_name):
    """
    Automatically save the current figure to the specified directory.

    Parameters
    ----------
    fig : matplotlib.figure.Figure
        Figure object to save.
    func_name : str
        Name of the calling function, used to construct the filename.
    """
    filename = f"{func_name}_{_TIMESTAMP}.png"
    filepath = os.path.join(_VIZ_DIR, filename)
    fig.savefig(filepath, dpi=300, bbox_inches='tight')
    print(f"📸 Chart saved: {filepath}")


def visualize_energy_convergence(energy_history, concept_centers):
    """
    Visualize the energy convergence process, marking the positions where concept compression occurs.

    Parameters
    ----------
    energy_history : list of float
        Average energy history for each iteration.
    concept_centers : dict
        Dictionary of concept compression centers, with values containing 'iteration' and other information.
    """
    fig = plt.figure(figsize=(10, 6))
    plt.plot(energy_history, 'b-', alpha=0.7, linewidth=1)
    plt.xlabel('Iteration')
    plt.ylabel('Average Cognitive Energy')
    plt.title('Cognitive Energy Convergence Process')
    plt.grid(True, alpha=0.3)

    colors = ['red', 'green', 'orange', 'purple']
    for i, (center, info) in enumerate(concept_centers.items()):
        iteration = info['iteration']
        if iteration < len(energy_history):
            color = colors[i % len(colors)]
            plt.axvline(x=iteration, color=color, alpha=0.5, linestyle='--',
                        label=f'Compression: {center}' if i < 4 else "")

    if len(concept_centers) > 0:
        plt.legend(loc='upper right', fontsize=8)

    plt.tight_layout()
    _auto_save_fig(fig, "energy_convergence")
    plt.show()


def visualize_cognitive_states(cognitive_energy_history, energy_history):
    """
    Visualize cognitive state changes (subjective energy) and network energy evolution.

    Parameters
    ----------
    cognitive_energy_history : list of dict
        Each entry should contain 'iteration', 'state', 'energy'.
    energy_history : list of float
        Network average energy history.
    """
    if not cognitive_energy_history:
        return

    # Add iteration numbers to cognitive energy history if not present
    for i, entry in enumerate(cognitive_energy_history):
        if 'iteration' not in entry:
            entry['iteration'] = i

    iterations = [e['iteration'] for e in cognitive_energy_history]
    energies = [e['energy'] for e in cognitive_energy_history]

    # Ensure network energy history length matches
    if len(energy_history) > len(iterations):
        network_energies = energy_history[:len(iterations)]
    else:
        network_energies = energy_history + [energy_history[-1]] * (
                    len(iterations) - len(energy_history)) if energy_history else []

    states = [e['state'] for e in cognitive_energy_history]

    state_colors = {
        CognitiveState.FOCUSED: 'green',
        CognitiveState.EXPLORATORY: 'blue',
        CognitiveState.FATIGUED: 'red',
        CognitiveState.INSPIRED: 'purple'
    }

    colors = [state_colors[state] for state in states]

    fig = plt.figure(figsize=(12, 8))

    plt.subplot(2, 1, 1)
    plt.scatter(iterations, energies, c=colors, alpha=0.6)
    plt.plot(iterations, energies, 'gray', alpha=0.3)
    plt.ylabel('Subjective Cognitive Energy')
    plt.title('Subjective Cognitive State and Energy Changes')

    for state, color in state_colors.items():
        plt.plot([], [], 'o', color=color, label=state.value)
    plt.legend()

    plt.subplot(2, 1, 2)
    if network_energies:
        plt.plot(iterations, network_energies, 'b-', alpha=0.7)
    plt.xlabel('Iteration')
    plt.ylabel('Network Average Energy')
    plt.title('Cognitive Network Energy Evolution')
    plt.grid(True, alpha=0.3)

    plt.tight_layout()
    _auto_save_fig(fig, "cognitive_states")
    plt.show()

    # Print state statistics
    state_counts = {}
    for state in states:
        state_counts[state] = state_counts.get(state, 0) + 1

    print("\n=== Cognitive State Statistics ===")
    for state, count in state_counts.items():
        percentage = (count / len(states)) * 100
        print(f"{state.value}: {count} times ({percentage:.1f}%)")


def visualize_graph(G, concept_centers, title="Cognitive Graph", figsize=(12, 8)):
    """
    Visualize the cognitive graph, marking concept compression centers and migration bridges,
    and coloring edges by energy.

    Parameters
    ----------
    G : networkx.Graph
        Cognitive network graph object.
    concept_centers : dict
        Dictionary of concept compression centers.
    title : str, optional
        Chart title.
    figsize : tuple, optional
        Figure size.
    """
    fig = plt.figure(figsize=figsize)
    pos = nx.spring_layout(G, seed=42)

    node_colors = []
    node_sizes = []
    for node in G.nodes():
        if node in concept_centers:
            node_colors.append('red')
            node_sizes.append(2000)
        elif any('migration_bridges' in G.nodes[n] for n in G.nodes()):
            node_colors.append('orange')
            node_sizes.append(1500)
        else:
            node_colors.append('lightblue')
            node_sizes.append(800)

    edge_colors = []
    edge_widths = []
    for u, v in G.edges():
        energy = G[u][v]['weight']
        edge_widths.append(max(0.5, 3 - energy * 1.5))

        if energy < 0.3:
            edge_colors.append('green')
        elif energy < 0.7:
            edge_colors.append('blue')
        else:
            edge_colors.append('gray')

    nx.draw_networkx_nodes(G, pos, node_size=node_sizes,
                           node_color=node_colors, alpha=0.9)
    nx.draw_networkx_edges(G, pos, width=edge_widths,
                           alpha=0.6, edge_color=edge_colors)
    nx.draw_networkx_labels(G, pos, font_size=8,
                            font_family='SimHei')

    plt.title(title, fontsize=16, fontfamily='SimHei')
    plt.axis('off')
    plt.tight_layout()
    _auto_save_fig(fig, "cognitive_graph")
    plt.show()

    # Print network statistics
    nodes = G.number_of_nodes()
    edges = G.number_of_edges()
    avg_energy = np.mean([G[u][v]['weight'] for u, v in G.edges()]) if edges > 0 else 0
    migration_bridges = 0
    for node in G.nodes():
        if 'migration_bridges' in G.nodes[node]:
            migration_bridges += len(G.nodes[node]['migration_bridges'])

    print(f"Network statistics:")
    print(f"  Nodes: {nodes}, Edges: {edges}")
    print(f"  Average energy: {avg_energy:.3f}")
    print(f"  Concept compression centers: {len(concept_centers)}")
    print(f"  Migration bridges: {migration_bridges}")


def visualize_semantic_network(semantic_network, concept_definitions=None, highlight_concepts=None):
    """
    Visualize the semantic concept network.

    Parameters
    ----------
    semantic_network : dict
        Semantic network dictionary, format: {concept: {neighbor: similarity, ...}, ...}.
    concept_definitions : dict, optional
        Concept definition dictionary, used to obtain domain information.
    highlight_concepts : list, optional
        List of concepts to highlight.
    """
    try:
        G = nx.Graph()

        for concept in semantic_network:
            domain = get_domain(concept, concept_definitions) if concept_definitions else "other"
            G.add_node(concept, domain=domain)

        for concept1, neighbors in semantic_network.items():
            for concept2, similarity in neighbors.items():
                if similarity > 0.1:
                    G.add_edge(concept1, concept2, weight=similarity)

        domain_colors = {
            "physics": "lightblue",
            "math": "lightgreen",
            "cs": "lightcoral",
            "principles": "gold",
            "other": "lightgray"
        }

        node_colors = [domain_colors[G.nodes[node].get('domain', 'other')] for node in G.nodes()]

        fig = plt.figure(figsize=(16, 12))
        pos = nx.spring_layout(G, k=3, iterations=50)

        nx.draw_networkx_nodes(G, pos, node_color=node_colors, node_size=500, alpha=0.9)

        edges = G.edges()
        weights = [G[u][v]['weight'] * 3 for u, v in edges]
        nx.draw_networkx_edges(G, pos, width=weights, alpha=0.5, edge_color='gray')

        nx.draw_networkx_labels(G, pos, font_size=8, font_family='SimHei')

        plt.title("Semantic Concept Network", fontsize=16, fontfamily='SimHei')
        plt.axis('off')
        plt.tight_layout()
        _auto_save_fig(fig, "semantic_network")
        plt.show()

    except ImportError:
        print("Need to install networkx and matplotlib to visualize the network")


def get_domain(concept, concept_definitions=None):
    """
    Determine the domain of a concept based on its definition.

    Parameters
    ----------
    concept : str
        Concept name.
    concept_definitions : dict, optional
        Concept definition dictionary, used to assist determination.

    Returns
    -------
    str
        Domain name, such as 'physics', 'math', 'cs', 'principles', 'other'.
    """
    domains = {
        "physics": ["牛顿定律", "力学", "运动学", "能量守恒", "动量", "万有引力", "摩擦力", "静电力"],
        "math": ["微积分", "几何学", "拓扑学", "线性代数", "概率论", "统计学", "代数", "离散数学"],
        "cs": ["算法", "数据结构", "机器学习", "神经网络", "计算机视觉", "自然语言处理", "数据库", "操作系统"],
        "principles": ["优化", "变换", "迭代", "抽象", "模式识别", "对称", "递归", "归纳"]
    }

    for domain, concepts in domains.items():
        if concept in concepts:
            return domain
    return "other"


if __name__ == "__main__":
    # Simple test: create a random graph and call visualization function
    G = nx.erdos_renyi_graph(10, 0.2)
    for u, v in G.edges():
        G[u][v]['weight'] = np.random.random()
    concept_centers = {node: {} for node in list(G.nodes())[:2]}
    visualize_graph(G, concept_centers, title="Test Graph")