#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成认知图论论文图文摘要的三阶段图（回调阈值 + 英文节点版）
直接使用 CognitiveUniverseEnhanced 的演化模型，检测阈值从 config 导入，
节点标签显示为英文，便于国际化展示。
"""

import os
import sys
import numpy as np
import networkx as nx
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.collections import LineCollection
from typing import Dict, List, Any, Tuple

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from emergence.universe_enhanced import CognitiveUniverseEnhanced
from emergence.detector_fixed import EmergenceDetectorFixed
from config import EMERGENCE_THRESHOLDS, CORE_CONCEPT_DEFINITIONS

np.random.seed(42)

# ========== 英文映射字典（前71个概念） ==========
ENGLISH_NAMES = {
    "牛顿定律": "Newton's Laws",
    "力学": "Mechanics",
    "运动学": "Kinematics",
    "能量守恒": "Energy Conservation",
    "动量": "Momentum",
    "万有引力": "Gravity",
    "摩擦力": "Friction",
    "静电力": "Electrostatic Force",
    "电磁学": "Electromagnetism",
    "热力学": "Thermodynamics",
    "相对论": "Relativity",
    "量子力学": "Quantum Mechanics",
    "量子场论": "Quantum Field Theory",
    "统计力学": "Statistical Mechanics",
    "宇宙学": "Cosmology",
    "微积分": "Calculus",
    "几何学": "Geometry",
    "拓扑学": "Topology",
    "线性代数": "Linear Algebra",
    "概率论": "Probability Theory",
    "统计学": "Statistics",
    "代数": "Algebra",
    "离散数学": "Discrete Mathematics",
    "微分几何": "Differential Geometry",
    "代数学": "Abstract Algebra",
    "数学分析": "Mathematical Analysis",
    "组合数学": "Combinatorics",
    "数论": "Number Theory",
    "复变函数": "Complex Analysis",
    "实分析": "Real Analysis",
    "泛函分析": "Functional Analysis",
    "算法": "Algorithm",
    "数据结构": "Data Structure",
    "机器学习": "Machine Learning",
    "神经网络": "Neural Network",
    "计算机视觉": "Computer Vision",
    "自然语言处理": "Natural Language Processing",
    "数据库": "Database",
    "操作系统": "Operating System",
    "软件工程": "Software Engineering",
    "计算机网络": "Computer Networks",
    "编译原理": "Compiler Principles",
    "人机交互": "Human-Computer Interaction",
    "信息安全": "Information Security",
    "分布式系统": "Distributed Systems",
    "云计算": "Cloud Computing",
    "物联网": "Internet of Things",
    "深度学习": "Deep Learning",
    "强化学习": "Reinforcement Learning",
    "生成对抗网络": "GAN",
    "注意力机制": "Attention Mechanism",
    "迁移学习": "Transfer Learning",
    "知识图谱": "Knowledge Graph",
    "计算机听觉": "Computer Audition",
    "机器人学": "Robotics",
    "智能体": "Agent",
    "模式识别": "Pattern Recognition",
    "数据挖掘": "Data Mining",
    "专家系统": "Expert System",
    "工作记忆": "Working Memory",
    "长期记忆": "Long-term Memory",
    "认知负荷": "Cognitive Load",
    "元认知": "Metacognition",
    "心理理论": "Theory of Mind",
    "感知心理学": "Perception Psychology",
    "发展心理学": "Developmental Psychology",
    "社会认知": "Social Cognition",
    "决策理论": "Decision Theory",
    "语言习得": "Language Acquisition",
    "认知神经科学": "Cognitive Neuroscience",
    "具身认知": "Embodied Cognition",
    "神经元": "Neuron",
    "突触": "Synapse",
}

# 确保只包含前71个概念
first_71_concepts = list(CORE_CONCEPT_DEFINITIONS.keys())[:71]
ENGLISH_NAMES = {k: ENGLISH_NAMES.get(k, k) for k in first_71_concepts}  # 缺失的保留中文

# 颜色定义
CLUSTER_COLORS = ['#FFB6C1', '#ADD8E6', '#90EE90', '#FFD700', '#FFA07A']
MIGRATION_COLORS = ['#FF4500', '#9400D3', '#2E8B57', '#FF69B4']


class VisualizableUniverse(CognitiveUniverseEnhanced):
    """
    可可视化的认知宇宙，检测阈值从 config 导入，确保与论文实验一致。
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 从 config 导入检测阈值
        adjusted_thresholds = {
            'compression_synergy': 0.76,          # 原 0.76
            'migration_efficiency': 0.35,          # 原 0.35
            'pattern_stability': 0.6,
            'energy_sync_threshold': 0.5,
            'cluster_cohesion': 0.5,
            'min_cluster_size': 2,
            'max_cluster_size': 6,
            'dynamic_cluster_sizing': True,
            'min_connection_strength': 0.3
        }
        self.emergence_detector = EmergenceDetectorFixed(adjusted_thresholds)
        self.snapshots = []          # 存储 (iteration, graph_copy, compressions, migrations)

    def evolve_with_emergence_detection(self, iterations: int = 10000,
                                        detection_interval: int = 200,
                                        capture_iterations: List[int] = [0, 3000, 10000]):
        """
        重写演化方法，在 capture_iterations 指定的迭代步保存网络快照。
        """
        print(f"开始演化: {iterations}次迭代，检测间隔 {detection_interval} (阈值来自 config)")

        # 初始快照
        self._capture_snapshot(0)

        for i in range(1, iterations + 1):
            self.iteration_count += 1

            # 基本能量优化（学习）
            self.basic_energy_optimization()

            # 随机遍历（探索）
            if np.random.random() < 0.3:
                self._random_traversal()

            # 遗忘（每10步）
            if i % 10 == 0:
                self.apply_basic_forgetting()

            # 更新能耗历史
            current_energy = self.calculate_network_energy()
            self.energy_history.append(current_energy)

            # 定期检测涌现
            if i % detection_interval == 0 and i > 200:
                self._detect_emergence(i)

            # 在指定迭代步捕获快照
            if i in capture_iterations:
                self._capture_snapshot(i)

            if i % 500 == 0:
                improvement = ((self.energy_history[0] - current_energy) /
                               self.energy_history[0] * 100) if self.energy_history[0] > 0 else 0
                print(f"迭代 {i}: 能量 = {current_energy:.3f} (改善: {improvement:.1f}%)")
                print(f"  压缩总数: {len(self.observations['natural_compressions'])}")
                print(f"  迁移总数: {len(self.observations['natural_migrations'])}")

        print("演化完成。")
        return self.observations

    def _capture_snapshot(self, iteration: int):
        """捕获当前网络快照及其附近的压缩/迁移事件"""
        G = self.G.copy()

        # 获取该迭代步之前检测到的所有事件
        compressions = self.observations['natural_compressions'][:]  # 全部保留
        migrations = self.observations['natural_migrations'][:]

        # 去重（按中心+相关节点去重）
        unique_comp = []
        seen_comp = set()
        for c in compressions:
            key = (c['center'], tuple(sorted(c.get('related_nodes', []))))
            if key not in seen_comp:
                seen_comp.add(key)
                unique_comp.append(c)

        # 去重迁移（按路径去重）
        unique_mig = []
        seen_mig = set()
        for m in migrations:
            path = tuple(m.get('path', []))
            if path and path not in seen_mig and tuple(reversed(path)) not in seen_mig:
                seen_mig.add(path)
                unique_mig.append(m)

        self.snapshots.append({
            'iteration': iteration,
            'graph': G,
            'compressions': unique_comp,
            'migrations': unique_mig
        })
        print(f"  捕获快照 at 迭代 {iteration}: {len(unique_comp)} 压缩, {len(unique_mig)} 迁移")

    def get_snapshots(self) -> List[Dict]:
        return self.snapshots


class ThreeStageVisualizer:
    """三阶段认知图可视化器"""

    def __init__(self, num_concepts: int = 71, iterations: int = 10000):
        self.num_concepts = num_concepts
        self.iterations = iterations
        self.universe = None
        self.english_names = ENGLISH_NAMES  # 英文映射

    def run_evolution(self):
        """初始化宇宙并演化，获取快照"""
        print("初始化认知宇宙...")
        self.universe = VisualizableUniverse(
            individual_params=None,
            network_seed=42,
            num_concepts=self.num_concepts
        )
        self.universe.initialize_semantic_network()

        # 运行演化，在 0, 3000, 10000 步捕获快照
        self.universe.evolve_with_emergence_detection(
            iterations=self.iterations,
            capture_iterations=[0, 3000, 10000]
        )

        return self.universe.get_snapshots()

    def draw_three_stages(self, snapshots: List[Dict], output_path: str = "../../Fresults/figures/cognitive_graph_three_stages.png"):
        """绘制三个阶段的对比图"""
        if len(snapshots) != 3:
            raise ValueError(f"需要3个快照，当前有 {len(snapshots)}")

        fig, axes = plt.subplots(1, 3, figsize=(18, 6))

        # 专业英文标题
        titles = ['Initial Cognitive Graph',
                  'Evolving Cognitive Landscape',
                  'Converged Cognitive Structure']
        times = ['t = 0', 't = 3000', 't = 10000']

        for idx, (ax, title, time) in enumerate(zip(axes, titles, times)):
            snapshot = snapshots[idx]
            G = snapshot['graph']
            compressions = snapshot['compressions']
            migrations = snapshot['migrations']

            # 固定布局
            pos = nx.spring_layout(G, seed=42, k=2, iterations=50)

            # 绘制基础灰色边
            self._draw_network_baseline(ax, G, pos)

            # 绘制迁移路径（彩色粗边）
            self._draw_migrations(ax, G, pos, migrations)

            # 绘制压缩集群（虚线框）
            self._draw_compression_clusters(ax, G, pos, compressions)

            # 绘制节点（根据压缩集群着色），并使用英文标签
            self._draw_nodes(ax, G, pos, compressions)

            ax.set_title(f"{title}\n{time}", fontsize=14, fontweight='bold')
            ax.axis('off')

        # 图注
        legend_elements = [
            plt.Line2D([0], [0], color='gray', lw=2, label='Ordinary edge (thicker = lower energy)'),
            plt.Line2D([0], [0], color='orange', lw=4, label='Principle migration path'),
            patches.Patch(facecolor='lightblue', edgecolor='blue', alpha=0.5, label='Concept compression cluster'),
            plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='gray', markersize=10, label='Ordinary node'),
            plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='lightcoral', markersize=10, label='Compression center')
        ]
        fig.legend(handles=legend_elements, loc='lower center', ncol=5, bbox_to_anchor=(0.5, -0.05), fontsize=10)

        plt.tight_layout(rect=[0, 0.05, 1, 1])
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.show()
        print(f"三阶段图已保存至 {output_path}")

    # ---------- 绘图辅助方法 ----------
    def _draw_network_baseline(self, ax, G, pos):
        edges = G.edges()
        if not edges:
            return
        weights = [G[u][v]['weight'] for u, v in edges]
        min_w, max_w = min(weights), max(weights)
        # 线宽范围 0.5~3.0，权重越小线越粗
        linewidths = [0.5 + 2.5 * (1 - (w - min_w) / (max_w - min_w + 1e-6)) for w in weights]

        segments = [[pos[u], pos[v]] for u, v in edges]
        lc = LineCollection(segments, colors='gray', linewidths=linewidths, alpha=0.6, zorder=1)
        ax.add_collection(lc)

    def _draw_migrations(self, ax, G, pos, migrations):
        for i, mig in enumerate(migrations[:4]):
            path = mig.get('path', [])
            if len(path) < 2:
                continue
            color = MIGRATION_COLORS[i % len(MIGRATION_COLORS)]
            for j in range(len(path)-1):
                u, v = path[j], path[j+1]
                if not G.has_edge(u, v):
                    continue
                x1, y1 = pos[u]
                x2, y2 = pos[v]
                line = plt.Line2D([x1, x2], [y1, y2], color=color, linewidth=4,
                                  alpha=0.9, zorder=2, solid_capstyle='round')
                ax.add_line(line)

    def _draw_compression_clusters(self, ax, G, pos, compressions):
        for i, comp in enumerate(compressions[:5]):
            center = comp.get('center')
            related = comp.get('related_nodes', [])
            if not center:
                continue
            cluster_nodes = [center] + related
            x_coords = [pos[n][0] for n in cluster_nodes if n in pos]
            y_coords = [pos[n][1] for n in cluster_nodes if n in pos]
            if not x_coords or not y_coords:
                continue
            x_min, x_max = min(x_coords), max(x_coords)
            y_min, y_max = min(y_coords), max(y_coords)
            pad_x = (x_max - x_min) * 0.2 + 0.2
            pad_y = (y_max - y_min) * 0.2 + 0.2
            rect = patches.Rectangle(
                (x_min - pad_x, y_min - pad_y),
                x_max - x_min + 2*pad_x,
                y_max - y_min + 2*pad_y,
                linewidth=2, edgecolor=CLUSTER_COLORS[i % len(CLUSTER_COLORS)],
                facecolor='none', linestyle='--', alpha=0.7, zorder=3
            )
            ax.add_patch(rect)

    def _draw_nodes(self, ax, G, pos, compressions):
        # 构建节点所属集群映射
        node_to_clusters = {n: [] for n in G.nodes()}
        for i, comp in enumerate(compressions):
            center = comp.get('center')
            related = comp.get('related_nodes', [])
            for n in [center] + related:
                if n in node_to_clusters:
                    node_to_clusters[n].append(i)

        for node in G.nodes():
            x, y = pos[node]
            clusters = node_to_clusters.get(node, [])
            if not clusters:
                color = '#D3D3D3'
                edgecolor = 'gray'
                size = 600
            elif len(clusters) == 1:
                color = CLUSTER_COLORS[clusters[0] % len(CLUSTER_COLORS)]
                edgecolor = 'darkblue'
                # 中心节点稍微放大
                is_center = any(node == c.get('center') for c in compressions if c.get('center') == node)
                size = 800 if is_center else 700
            else:
                # 多归属节点：白色填充，黑色边框
                color = 'white'
                edgecolor = 'black'
                size = 700

            ax.scatter(x, y, s=size, c=color, edgecolors=edgecolor,
                       linewidths=1.5, zorder=4, alpha=0.9)
            # 使用英文标签
            label = self.english_names.get(node, node)
            ax.text(x, y, label, fontsize=6, ha='center', va='center', zorder=6)


if __name__ == "__main__":
    viz = ThreeStageVisualizer(num_concepts=71, iterations=10000)
    snapshots = viz.run_evolution()
    viz.draw_three_stages(snapshots, "../../Fresults/figures/cognitive_graph_three_stages.png")