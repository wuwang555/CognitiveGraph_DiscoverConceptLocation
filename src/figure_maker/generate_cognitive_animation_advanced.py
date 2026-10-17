"""
generate_cognitive_animation_advanced.py

改进版：动态节点布局 + 遍历路径淡出 + 强对比边能耗映射
"""

import sys
import os
import random
import numpy as np
import networkx as nx
import json
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.collections import LineCollection
from matplotlib.patches import FancyArrowPatch
from datetime import datetime

# 导入核心模块（请确保路径正确）
from core.cognitive_graph import BaseCognitiveGraph
from models.enhanced_model import EnergyOptimizedCognitiveGraph
from config import BASE_PARAMETERS

# ========== 配置 ==========
NUM_CONCEPTS = 111         # 51,71,91,111
INDIVIDUAL_ID = 0
MAX_ITERATIONS = 10000     # 总迭代次数
RECORD_INTERVAL = 10       # 每10帧记录一次（降低存储压力）
OUTPUT_FORMAT = 'gif'      # 'gif' or 'mp4'
ANIMATION_INTERVAL_MS = 80 # 每帧间隔(ms)，约12.5 fps
TRAIL_FADE_FRAMES = 5      # 遍历路径停留的帧数
# =========================

class RecordingCognitiveGraph(EnergyOptimizedCognitiveGraph):
    """记录遍历信息和网络快照"""
    def __init__(self, individual_params, network_seed=42, num_concepts=None, save_positions=True):
        super().__init__(individual_params, network_seed, num_concepts)
        self.save_positions = save_positions
        self.iteration_records = []      # 存储每帧数据
        self.current_traversal_info = None
        self.prev_pos = None              # 用于平滑布局的上一帧位置

    def _record_traversal_info(self, path, traversal_type, attempted_edges=None):
        self.current_traversal_info = {
            'type': traversal_type,
            'path': path,
            'attempted_edges': attempted_edges or [],
            'iteration': self.iteration_count
        }

    # ----- 重写遍历方法以捕获尝试的边 -----
    def _find_hard_traversal_path(self, start_node, max_length):
        path = [start_node]
        current = start_node
        attempted = []
        for _ in range(max_length - 1):
            neighbors = list(self.G.neighbors(current))
            if not neighbors:
                break
            neighbors.sort(key=lambda n: self.G[current][n]['weight'])
            found = False
            for nb in neighbors[:3]:
                attempted.append((current, nb))
                if nb not in path:
                    can, _ = self.can_traverse_edge(self.G[current][nb]['weight'], "hard")
                    if can:
                        path.append(nb)
                        current = nb
                        found = True
                        break
            if not found:
                break
        return path if len(path) >= 2 else None, attempted

    def _find_soft_traversal_path(self, start_node, max_length):
        path = [start_node]
        current = start_node
        attempted = []
        for _ in range(max_length - 1):
            neighbors = list(self.G.neighbors(current))
            if not neighbors:
                break
            random.shuffle(neighbors)
            found = False
            for nb in neighbors:
                attempted.append((current, nb))
                if nb not in path:
                    can, _ = self.can_traverse_edge(self.G[current][nb]['weight'], "soft")
                    if can:
                        path.append(nb)
                        current = nb
                        found = True
                        break
            if not found:
                break
        return path if len(path) >= 2 else None, attempted

    def _state_based_hard_traversal(self):
        nodes = list(self.G.nodes())
        if not nodes:
            return
        start = random.choice(nodes)
        path, attempted = self._find_hard_traversal_path(start, 3)
        if path and len(path) >= 2:
            self.traverse_path(path, "hard")
            self._record_traversal_info(path, "hard", attempted)

    def _state_based_soft_traversal(self):
        nodes = list(self.G.nodes())
        if not nodes:
            return
        start = random.choice(nodes)
        path, attempted = self._find_soft_traversal_path(start, 2)
        if path and len(path) >= 2:
            self.traverse_path(path, "soft")
            self._record_traversal_info(path, "soft", attempted)

    def run_with_recording(self, max_iterations=MAX_ITERATIONS, record_interval=RECORD_INTERVAL):
        print(f"开始演化：{max_iterations} 次迭代，记录间隔 {record_interval}")
        self.initialize_semantic_graph()
        self.iteration_records = []
        self.iteration_count = 0

        # 初始布局
        if self.save_positions:
            self.prev_pos = nx.spring_layout(self.G, seed=42, k=0.3, iterations=50)
        else:
            self.prev_pos = None

        for i in range(max_iterations):
            self.iteration_count += 1
            self.current_traversal_info = None

            # 状态更新与操作选择（同前）
            if random.random() < 0.1:
                self.update_cognitive_state()
            op = self._select_operation_based_on_state()
            if op == "hard_traversal":
                self._state_based_hard_traversal()
            elif op == "soft_traversal":
                self._state_based_soft_traversal()
            elif op == "compression":
                self._random_compression()
            elif op == "migration":
                self._random_migration()

            if i % 10 == 0:
                self._apply_forgetting()

            # 记录帧
            if i % record_interval == 0:
                frame = {
                    'iteration': self.iteration_count,
                    'global_energy': self.calculate_network_energy(),
                    'edge_weights': {(u, v): self.G[u][v]['weight'] for u, v in self.G.edges()},
                    'traversal': self.current_traversal_info,
                }
                if self.save_positions:
                    # 基于当前边权重更新布局（以上一帧位置为初始值，实现平滑）
                    G_tmp = nx.Graph()
                    G_tmp.add_nodes_from(self.G.nodes())
                    for (u, v), w in frame['edge_weights'].items():
                        G_tmp.add_edge(u, v, weight=w)
                    new_pos = nx.spring_layout(G_tmp, pos=self.prev_pos, iterations=10, seed=42, k=0.3)
                    frame['positions'] = {node: (float(new_pos[node][0]), float(new_pos[node][1])) for node in new_pos}
                    self.prev_pos = new_pos
                self.iteration_records.append(frame)

            if (i+1) % 1000 == 0:
                print(f"  迭代 {i+1}/{max_iterations}, 能量: {frame['global_energy']:.3f}")

        print(f"演化完成，共记录 {len(self.iteration_records)} 帧")
        return self.iteration_records

    def save_records_to_json(self, filename):
        """将记录的数据保存为 JSON 文件（处理 numpy 类型和元组键）"""

        def convert(obj):
            if isinstance(obj, np.floating):
                return float(obj)
            if isinstance(obj, np.integer):
                return int(obj)
            if isinstance(obj, tuple):
                return list(obj)  # 将元组转为列表
            if isinstance(obj, dict):
                # 检查是否是边权重字典（键为元组）
                if obj and isinstance(next(iter(obj.keys())), tuple):
                    # 转换为 [[u, v, weight], ...] 格式
                    return [[u, v, w] for (u, v), w in obj.items()]
                else:
                    return {k: convert(v) for k, v in obj.items()}
            if isinstance(obj, list):
                return [convert(i) for i in obj]
            return obj

        records_serializable = convert(self.iteration_records)
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(records_serializable, f, indent=2, ensure_ascii=False)
        print(f"数据已保存至: {filename}")


def create_animation(records, initial_pos, output_filename):
    if not records:
        print("无记录数据")
        return

    # 预计算所有帧的节点布局（动态布局，平滑过渡）
    print("正在计算动态布局...")
    positions = [initial_pos.copy()]
    prev_pos = initial_pos.copy()
    for idx, frame in enumerate(records[1:], start=1):
        # 基于当前边权重重新计算布局，使用上一帧位置作为初始值
        G_tmp = nx.Graph()
        G_tmp.add_nodes_from(initial_pos.keys())
        for (u, v), w in frame['edge_weights'].items():
            G_tmp.add_edge(u, v, weight=w)
        # spring_layout 支持 pos 参数，实现平滑迁移
        new_pos = nx.spring_layout(G_tmp, pos=prev_pos, iterations=10, seed=42, k=0.3)
        positions.append(new_pos)
        prev_pos = new_pos
        if (idx+1) % 100 == 0:
            print(f"  布局计算 {idx+1}/{len(records)}")
    print("布局计算完成")

    # 全局能量范围（用于颜色和宽度映射）
    all_weights = []
    for frame in records:
        all_weights.extend(frame['edge_weights'].values())
    min_w, max_w = min(all_weights), max(all_weights)
    if max_w == min_w:
        max_w = min_w + 1e-6

    # 非线性映射函数：使低能耗区域差异更明显
    def weight_to_width(w):
        ratio = (w - min_w) / (max_w - min_w)
        # 使用指数放大：低能耗部分宽度变化更敏感
        width = 0.5 + 5.0 * (1 - np.exp(-3 * ratio))
        return min(6.0, width)

    def weight_to_color(w):
        ratio = (w - min_w) / (max_w - min_w)
        # 低能耗(蓝绿) -> 高能耗(红紫)
        r = ratio
        g = 0.2 + 0.6 * (1 - ratio)
        b = 0.8 * (1 - ratio)
        return (r, g, b)

    # 创建图形
    fig, ax = plt.subplots(figsize=(12, 9))
    ax.set_axis_off()

    # 用于存储活动轨迹（每个轨迹包含路径、类型、剩余帧数）
    active_trails = []  # 元素: {'path':list, 'type':str, 'remaining':int, 'attempted':list}

    def update(frame_idx):
        ax.clear()
        ax.set_axis_off()
        frame = records[frame_idx]
        it = frame['iteration']
        edge_weights = frame['edge_weights']
        traversal = frame['traversal']
        pos = positions[frame_idx]

        # 标题
        ax.set_title(f"Iteration: {it}   |   Global Energy: {np.mean(list(edge_weights.values())):.3f}", fontsize=12)

        # 1. 绘制所有边（基础层，浅灰色）
        lines = []
        colors = []
        widths = []
        for (u, v), w in edge_weights.items():
            if u not in pos or v not in pos:
                continue
            x1, y1 = pos[u]
            x2, y2 = pos[v]
            lines.append([(x1, y1), (x2, y2)])
            colors.append(weight_to_color(w))
            widths.append(weight_to_width(w))
        if lines:
            lc = LineCollection(lines, colors=colors, linewidths=widths, alpha=0.7, zorder=1)
            ax.add_collection(lc)

        # 2. 绘制节点
        node_x = [pos[n][0] for n in pos]
        node_y = [pos[n][1] for n in pos]
        ax.scatter(node_x, node_y, s=200, c='lightblue', edgecolors='black', linewidth=1, alpha=0.9, zorder=2)
        for n in pos:
            ax.text(pos[n][0], pos[n][1], n, fontsize=8, ha='center', va='center', weight='bold', zorder=3)

        # 3. 处理当前帧的遍历：添加到活动轨迹列表（停留 TRAIL_FADE_FRAMES 帧）
        if traversal and traversal['path'] and len(traversal['path']) >= 2:
            active_trails.append({
                'path': traversal['path'],
                'type': traversal['type'],
                'attempted': traversal.get('attempted_edges', []),
                'remaining': TRAIL_FADE_FRAMES
            })

        # 4. 绘制所有活动轨迹（根据剩余帧数决定透明度/线宽）
        for trail in active_trails[:]:  # 遍历副本
            alpha = trail['remaining'] / TRAIL_FADE_FRAMES
            # 软遍历：绘制尝试的虚线箭头
            if trail['type'] == 'soft' and trail['attempted']:
                for (u, v) in trail['attempted']:
                    if u in pos and v in pos:
                        x1, y1 = pos[u]
                        x2, y2 = pos[v]
                        arrow = FancyArrowPatch((x1, y1), (x2, y2),
                                                arrowstyle='->', mutation_scale=10,
                                                linestyle='dashed', linewidth=1.5,
                                                color='orange', alpha=alpha*0.7, zorder=4)
                        ax.add_patch(arrow)
            # 绘制实际路径（实线箭头）
            path = trail['path']
            for i in range(len(path)-1):
                u, v = path[i], path[i+1]
                if u in pos and v in pos:
                    x1, y1 = pos[u]
                    x2, y2 = pos[v]
                    color = 'blue' if trail['type'] == 'hard' else 'red'
                    lw = 2.5 if trail['type'] == 'hard' else 2.0
                    arrow = FancyArrowPatch((x1, y1), (x2, y2),
                                            arrowstyle='->', mutation_scale=14,
                                            linestyle='solid', linewidth=lw,
                                            color=color, alpha=alpha, zorder=5)
                    ax.add_patch(arrow)
            # 高亮路径上的节点
            path_nodes = [n for n in path if n in pos]
            if path_nodes:
                x_path = [pos[n][0] for n in path_nodes]
                y_path = [pos[n][1] for n in path_nodes]
                ax.scatter(x_path, y_path, s=250, c='yellow', edgecolors='black', linewidth=2, alpha=alpha, zorder=6)

            # 衰减剩余帧数，若归零则移除
            trail['remaining'] -= 1
        # 移除已消失的轨迹
        active_trails[:] = [t for t in active_trails if t['remaining'] > 0]

        ax.set_xlim(-1.2, 1.2)
        ax.set_ylim(-1.2, 1.2)
        return [ax.title] + ax.collections + ax.patches + ax.texts

    anim = animation.FuncAnimation(fig, update, frames=len(records), interval=ANIMATION_INTERVAL_MS,
                                   repeat=False, blit=False)  # blit=True 因动态添加 patch 而关闭
    if OUTPUT_FORMAT == 'gif':
        anim.save(output_filename, writer='pillow', fps=1000/ANIMATION_INTERVAL_MS)
    else:
        anim.save(output_filename, writer='ffmpeg', fps=1000/ANIMATION_INTERVAL_MS)
    plt.close(fig)
    print(f"动画已保存: {output_filename}")


def main():
    random.seed(42 + INDIVIDUAL_ID)
    np.random.seed(42 + INDIVIDUAL_ID)

    params = BASE_PARAMETERS.copy()
    params['learning_rate_variation'] = 0.1

    cg = RecordingCognitiveGraph(params, network_seed=42 + INDIVIDUAL_ID, num_concepts=NUM_CONCEPTS,
                                 save_positions=True)
    records = cg.run_with_recording(max_iterations=MAX_ITERATIONS, record_interval=10)
    os.makedirs("../../Fresults/data", exist_ok=True)
    cg.save_records_to_json(f"../../Fresults/data/cognitive_records_{NUM_CONCEPTS}c_ind{INDIVIDUAL_ID}.json")

    # 生成初始布局
    cg.initialize_semantic_graph()  # 临时初始化以获取布局
    initial_pos = nx.spring_layout(cg.G, seed=42, k=0.3, iterations=50)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_dir = "../../Fresults/animations"
    os.makedirs(out_dir, exist_ok=True)
    filename = f"{out_dir}/cognitive_anim_dynamic_{NUM_CONCEPTS}c_ind{INDIVIDUAL_ID}_{timestamp}.{OUTPUT_FORMAT}"

    create_animation(records, initial_pos, filename)
    print("动画生成完成！")


if __name__ == "__main__":
    main()