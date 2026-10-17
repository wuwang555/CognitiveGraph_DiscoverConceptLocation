"""
generate_cognitive_animation_fixed.py

修复版：生成认知图动态演化动画，展示硬遍历（单方向流）、软遍历（多方向探索）、边能耗映射为粗细/颜色。
用法：修改下方的 NUM_CONCEPTS 和 INDIVIDUAL_ID，直接运行即可。
"""

import sys
import os
import random
import numpy as np
import networkx as nx
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.patches import FancyArrowPatch
from collections import defaultdict
from datetime import datetime

# 导入核心模块（请确保路径正确）
from core.cognitive_graph import BaseCognitiveGraph
from models.enhanced_model import EnergyOptimizedCognitiveGraph
from config import BASE_PARAMETERS

# ========== 配置 ==========
NUM_CONCEPTS = 51          # 可选: 51, 71, 91, 111
INDIVIDUAL_ID = 0          # 0,1,2 分别对应三个个体
MAX_ITERATIONS = 5000      # 迭代次数（论文中为10000，为加快生成可减少）
RECORD_INTERVAL = 5        # 每5帧记录一次（数值越小动画越精细，文件越大）
OUTPUT_FORMAT = 'gif'      # 'gif' 或 'mp4'
# =========================

class RecordingCognitiveGraph(EnergyOptimizedCognitiveGraph):
    """扩展认知图，记录每次迭代的详细遍历信息，用于动画渲染"""
    def __init__(self, individual_params, network_seed=42, num_concepts=None):
        super().__init__(individual_params, network_seed, num_concepts)
        self.iteration_records = []   # 存储每帧数据
        self.current_traversal_info = None

    def _record_traversal_info(self, path, traversal_type, attempted_edges=None):
        """记录当前迭代的遍历信息（路径、类型、尝试的边）"""
        self.current_traversal_info = {
            'type': traversal_type,
            'path': path,
            'attempted_edges': attempted_edges if attempted_edges else [],
            'iteration': self.iteration_count
        }

    # ---------- 重写遍历方法以捕获尝试的边 ----------
    def _find_hard_traversal_path(self, start_node, max_length):
        """硬遍历：按能耗升序尝试邻居，记录所有被评估的边"""
        path = [start_node]
        current_node = start_node
        attempted_edges = []
        for _ in range(max_length - 1):
            neighbors = list(self.G.neighbors(current_node))
            if not neighbors:
                break
            neighbors.sort(key=lambda n: self.G[current_node][n]['weight'])
            found = False
            for neighbor in neighbors[:3]:
                attempted_edges.append((current_node, neighbor))
                if neighbor not in path:
                    can_traverse, _ = self.can_traverse_edge(
                        self.G[current_node][neighbor]['weight'], "hard"
                    )
                    if can_traverse:
                        path.append(neighbor)
                        current_node = neighbor
                        found = True
                        break
            if not found:
                break
        return path if len(path) >= 2 else None, attempted_edges

    def _find_soft_traversal_path(self, start_node, max_length):
        """软遍历：随机打乱邻居，记录所有尝试的边（多方向探索）"""
        path = [start_node]
        current_node = start_node
        attempted_edges = []
        for _ in range(max_length - 1):
            neighbors = list(self.G.neighbors(current_node))
            if not neighbors:
                break
            random.shuffle(neighbors)
            found = False
            for neighbor in neighbors:
                attempted_edges.append((current_node, neighbor))
                if neighbor not in path:
                    can_traverse, _ = self.can_traverse_edge(
                        self.G[current_node][neighbor]['weight'], "soft"
                    )
                    if can_traverse:
                        path.append(neighbor)
                        current_node = neighbor
                        found = True
                        break
            if not found:
                break
        return path if len(path) >= 2 else None, attempted_edges

    def _state_based_hard_traversal(self):
        """执行硬遍历并记录"""
        nodes = list(self.G.nodes())
        if not nodes:
            return
        start = random.choice(nodes)
        path, attempted = self._find_hard_traversal_path(start, 3)
        if path and len(path) >= 2:
            self.traverse_path(path, "hard")
            self._record_traversal_info(path, "hard", attempted)

    def _state_based_soft_traversal(self):
        """执行软遍历并记录"""
        nodes = list(self.G.nodes())
        if not nodes:
            return
        start = random.choice(nodes)
        path, attempted = self._find_soft_traversal_path(start, 2)
        if path and len(path) >= 2:
            self.traverse_path(path, "soft")
            self._record_traversal_info(path, "soft", attempted)

    def run_with_recording(self, max_iterations=MAX_ITERATIONS):
        """运行演化并记录每一帧的数据"""
        print(f"开始演化：{max_iterations} 次迭代，记录间隔 {RECORD_INTERVAL}")
        self.initialize_semantic_graph()
        self.iteration_records = []
        self.iteration_count = 0

        # 固定节点布局（使用spring_layout，后续所有帧共用）
        self.fixed_pos = nx.spring_layout(self.G, seed=42, k=0.3, iterations=50)
        initial_energy = self.calculate_network_energy()
        self.energy_history = [initial_energy]

        for i in range(max_iterations):
            self.iteration_count += 1
            self.current_traversal_info = None

            # 状态更新（与原始monte_carlo_iteration一致）
            if random.random() < 0.1:
                self.update_cognitive_state()

            # 根据认知状态选择操作
            op = self._select_operation_based_on_state()
            if op == "hard_traversal":
                self._state_based_hard_traversal()
            elif op == "soft_traversal":
                self._state_based_soft_traversal()
            elif op == "compression":
                self._random_compression()
            elif op == "migration":
                self._random_migration()

            # 应用遗忘机制
            if i % 10 == 0:
                self._apply_forgetting()

            current_energy = self.calculate_network_energy()
            self.energy_history.append(current_energy)

            # 记录帧数据
            if i % RECORD_INTERVAL == 0:
                frame = {
                    'iteration': self.iteration_count,
                    'global_energy': current_energy,
                    'edge_weights': {(u, v): self.G[u][v]['weight'] for u, v in self.G.edges()},
                    'traversal': self.current_traversal_info,
                }
                self.iteration_records.append(frame)

            # 进度提示
            if (i+1) % 1000 == 0:
                print(f"  迭代 {i+1}/{max_iterations}, 能量: {current_energy:.3f}")

        print(f"演化完成，共记录 {len(self.iteration_records)} 帧")
        return self.iteration_records


def create_animation(records, pos, output_filename):
    """根据记录的数据生成动画"""
    if not records:
        print("没有记录数据")
        return

    # 获取所有节点
    nodes = list(pos.keys())

    # 全局边权重范围（用于归一化宽度和颜色）
    all_weights = []
    for frame in records:
        all_weights.extend(frame['edge_weights'].values())
    min_w, max_w = min(all_weights), max(all_weights)
    if max_w == min_w:
        max_w = min_w + 1e-6

    # 宽度映射：能耗越高边越粗（直观表现“能耗高=粗”），范围 [0.5, 4.0]
    def weight_to_width(w):
        return 0.5 + 3.0 * (w - min_w) / (max_w - min_w)

    # 颜色映射：低能耗(绿) -> 高能耗(红)
    def weight_to_color(w):
        ratio = (w - min_w) / (max_w - min_w)
        return (ratio, 1.0 - ratio, 0.0)  # 红绿渐变

    fig, ax = plt.subplots(figsize=(12, 9))
    ax.set_axis_off()

    def update(frame_idx):
        ax.clear()
        ax.set_axis_off()
        frame = records[frame_idx]
        it = frame['iteration']
        energy = frame['global_energy']
        edge_weights = frame['edge_weights']
        traversal = frame['traversal']

        ax.set_title(f"Iteration: {it}   |   Global Energy: {energy:.3f}", fontsize=12)

        # 绘制所有边（基础层）
        for (u, v), w in edge_weights.items():
            if u not in pos or v not in pos:
                continue
            x1, y1 = pos[u]
            x2, y2 = pos[v]
            width = weight_to_width(w)
            color = weight_to_color(w)
            ax.plot([x1, x2], [y1, y2], lw=width, color=color, alpha=0.6, solid_capstyle='round', zorder=1)

        # 绘制节点（使用散点图）
        x_vals = [pos[n][0] for n in nodes]
        y_vals = [pos[n][1] for n in nodes]
        ax.scatter(x_vals, y_vals, s=200, c='lightblue', edgecolors='black', linewidth=1, alpha=0.9, zorder=2)

        # 绘制节点标签
        for n in nodes:
            ax.text(pos[n][0], pos[n][1], n, fontsize=8, ha='center', va='center', weight='bold', zorder=3)

        # 如果有遍历信息，绘制箭头
        if traversal and traversal['path'] and len(traversal['path']) >= 2:
            path = traversal['path']
            trav_type = traversal['type']
            attempted = traversal.get('attempted_edges', [])

            # 软遍历：绘制所有尝试的边（虚线箭头）
            if trav_type == 'soft' and attempted:
                for (u, v) in attempted:
                    if u in pos and v in pos:
                        x1, y1 = pos[u]
                        x2, y2 = pos[v]
                        arrow = FancyArrowPatch((x1, y1), (x2, y2),
                                                arrowstyle='->', mutation_scale=12,
                                                linestyle='dashed', linewidth=1.5,
                                                color='orange', alpha=0.7, zorder=4)
                        ax.add_patch(arrow)

            # 绘制实际遍历路径（实线箭头）
            for i in range(len(path)-1):
                u, v = path[i], path[i+1]
                if u in pos and v in pos:
                    x1, y1 = pos[u]
                    x2, y2 = pos[v]
                    color = 'blue' if trav_type == 'hard' else 'red'
                    lw = 2.5 if trav_type == 'hard' else 2.0
                    arrow = FancyArrowPatch((x1, y1), (x2, y2),
                                            arrowstyle='->', mutation_scale=15,
                                            linestyle='solid', linewidth=lw,
                                            color=color, alpha=0.9, zorder=5)
                    ax.add_patch(arrow)

            # 高亮路径上的节点（用黄色圆圈再次绘制）
            path_nodes = [n for n in path if n in pos]
            if path_nodes:
                x_path = [pos[n][0] for n in path_nodes]
                y_path = [pos[n][1] for n in path_nodes]
                ax.scatter(x_path, y_path, s=250, c='yellow', edgecolors='black', linewidth=2, zorder=6)

        ax.set_xlim(-1.2, 1.2)
        ax.set_ylim(-1.2, 1.2)

        # 返回所有可迭代对象（避免空列表警告）
        return [ax.title] + ax.patches + list(ax.collections) + list(ax.texts)

    # 创建动画
    anim = animation.FuncAnimation(fig, update, frames=len(records), interval=100, repeat=False, blit=False)

    # 保存动画
    if OUTPUT_FORMAT == 'gif':
        anim.save(output_filename, writer='pillow', fps=10)
    else:
        anim.save(output_filename, writer='ffmpeg', fps=10)
    plt.close(fig)
    print(f"动画已保存: {output_filename}")


def main():
    # 设置随机种子
    random.seed(42 + INDIVIDUAL_ID)
    np.random.seed(42 + INDIVIDUAL_ID)

    # 创建个体参数
    individual_params = BASE_PARAMETERS.copy()
    individual_params['learning_rate_variation'] = 0.1

    # 初始化认知图（使用 RecordingCognitiveGraph）
    cg = RecordingCognitiveGraph(individual_params, network_seed=42+INDIVIDUAL_ID, num_concepts=NUM_CONCEPTS)

    # 运行并记录
    records = cg.run_with_recording(max_iterations=MAX_ITERATIONS)

    # 生成动画文件名
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_dir = "../../Fresults/animations"
    os.makedirs(out_dir, exist_ok=True)
    filename = f"{out_dir}/cognitive_anim_{NUM_CONCEPTS}c_ind{INDIVIDUAL_ID}_{timestamp}.{OUTPUT_FORMAT}"

    # 创建动画
    create_animation(records, cg.fixed_pos, filename)
    print("完成！")


if __name__ == "__main__":
    main()