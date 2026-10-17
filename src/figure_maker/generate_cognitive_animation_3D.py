"""
generate_cognitive_animation_3d.py

3D 认知图动画：基于 Plotly，边长度与认知能耗成正比（能耗越高边越长）。
采用三维力导向布局动态调整节点位置，直观展示能耗优化过程。
"""

import os
import json
import random
import numpy as np
import networkx as nx
from scipy.spatial.distance import cdist
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime

# 导入核心模块（确保路径正确）
from core.cognitive_graph import BaseCognitiveGraph
from models.enhanced_model import EnergyOptimizedCognitiveGraph
from config import BASE_PARAMETERS

# ========== 配置 ==========
NUM_CONCEPTS = 111        # 概念节点数量
INDIVIDUAL_ID = 0
MAX_ITERATIONS = 10000     # 总迭代次数
RECORD_INTERVAL = 10       # 记录间隔（帧）
ANIMATION_FRAME_INTERVAL_MS = 120   # 每帧间隔（毫秒）

# 3D 布局参数
L_MIN = 0.5                # 最小边长（低能耗）
L_MAX = 2.0                # 最大边长（高能耗）
POS_BOUNDS = 5.0           # 坐标边界
OPTIM_STEPS = 20           # 每帧位置优化迭代步数
OPTIM_LR = 0.02            # 梯度下降学习率
# =========================


class RecordingCognitiveGraph3D(EnergyOptimizedCognitiveGraph):
    """
    扩展 RecordingCognitiveGraph，记录每帧边权重，同时可选择记录 2D 位置
    （3D 位置将在动画生成阶段重新计算）
    """
    def __init__(self, individual_params, network_seed=42, num_concepts=None):
        super().__init__(individual_params, network_seed, num_concepts)
        self.iteration_records = []      # 存储每帧数据
        self.current_traversal_info = None

    def _record_traversal_info(self, path, traversal_type, attempted_edges=None):
        self.current_traversal_info = {
            'type': traversal_type,
            'path': path,
            'attempted_edges': attempted_edges or [],
            'iteration': self.iteration_count
        }

    # ----- 重写遍历方法以捕获尝试的边（同原 2D 版本）-----
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
        print(f"开始 3D 演化：{max_iterations} 次迭代，记录间隔 {record_interval}")
        self.initialize_semantic_graph()
        self.iteration_records = []
        self.iteration_count = 0

        for i in range(max_iterations):
            self.iteration_count += 1
            self.current_traversal_info = None

            # 更新状态与操作选择
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
                self.iteration_records.append(frame)

            if (i+1) % 1000 == 0 and self.iteration_records:
                print(f"  迭代 {i+1}/{max_iterations}, 能量: {self.iteration_records[-1]['global_energy']:.3f}")

        print(f"演化完成，共记录 {len(self.iteration_records)} 帧")
        return self.iteration_records

    def save_records_to_json(self, filename):
        """将记录的数据保存为 JSON（处理 numpy 类型和元组键）"""
        def convert(obj):
            if isinstance(obj, np.floating):
                return float(obj)
            if isinstance(obj, np.integer):
                return int(obj)
            if isinstance(obj, tuple):
                return list(obj)
            if isinstance(obj, dict):
                if obj and isinstance(next(iter(obj.keys())), tuple):
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


class CognitiveGraph3DAnimator:
    def __init__(self, records, node_list):
        self.records = records
        self.nodes = node_list
        self.num_nodes = len(node_list)
        self.node_to_idx = {node: i for i, node in enumerate(node_list)}
        all_weights = []
        for rec in records:
            all_weights.extend(rec['edge_weights'].values())
        self.min_w = min(all_weights)
        self.max_w = max(all_weights)
        if self.max_w == self.min_w:
            self.max_w = self.min_w + 1e-6
        self.positions = [None] * len(records)

    def _target_length(self, weight):
        ratio = (weight - self.min_w) / (self.max_w - self.min_w)
        return L_MIN + (L_MAX - L_MIN) * ratio

    def _optimize_positions(self, init_pos, edge_weights, steps=OPTIM_STEPS, lr=OPTIM_LR):
        pos = init_pos.copy()
        target_dist = np.full((self.num_nodes, self.num_nodes), L_MAX * 2.0)
        for (u, v), w in edge_weights.items():
            i, j = self.node_to_idx[u], self.node_to_idx[v]
            L = self._target_length(w)
            target_dist[i, j] = L
            target_dist[j, i] = L
        eps = 1e-6
        for _ in range(steps):
            dist = cdist(pos, pos)
            dist = np.maximum(dist, eps)
            grad = np.zeros_like(pos)
            for i in range(self.num_nodes):
                for j in range(i+1, self.num_nodes):
                    err = dist[i, j] - target_dist[i, j]
                    force = err / dist[i, j]
                    direction = (pos[i] - pos[j]) / dist[i, j]
                    grad[i] += force * direction
                    grad[j] -= force * direction
            pos -= lr * grad
            pos = np.clip(pos, -POS_BOUNDS, POS_BOUNDS)
            if np.any(np.isnan(pos)):
                print(f"Warning: NaN detected, resetting to init_pos")
                pos = init_pos + np.random.randn(*init_pos.shape) * 0.01
                break
        return pos

    def compute_all_positions(self):
        print("正在计算 3D 动态布局...")
        init_pos = np.random.randn(self.num_nodes, 3) * 0.5
        first_weights = self.records[0]['edge_weights']
        self.positions[0] = self._optimize_positions(init_pos, first_weights, steps=OPTIM_STEPS*2)
        print(f"第0帧位置范围: x [{self.positions[0][:,0].min():.2f}, {self.positions[0][:,0].max():.2f}], "
              f"y [{self.positions[0][:,1].min():.2f}, {self.positions[0][:,1].max():.2f}], "
              f"z [{self.positions[0][:,2].min():.2f}, {self.positions[0][:,2].max():.2f}]")
        for i in range(1, len(self.records)):
            prev_pos = self.positions[i-1]
            weights = self.records[i]['edge_weights']
            self.positions[i] = self._optimize_positions(prev_pos, weights, steps=OPTIM_STEPS)
            if np.any(np.isnan(self.positions[i])):
                self.positions[i] = prev_pos.copy()
            if (i+1) % 100 == 0:
                print(f"  布局计算 {i+1}/{len(self.records)}")
        print("布局计算完成")

    # 固定返回三个桶的边轨迹（总是三个 Scatter3d）
    def _get_edge_traces_fixed(self, frame_idx):
        rec = self.records[frame_idx]
        pos = self.positions[frame_idx]
        edge_weights = rec['edge_weights']
        # 三个等级：低能耗（绿）、中能耗（橙）、高能耗（红）
        low_thresh = self.min_w + 0.5 * (self.max_w - self.min_w)
        colors = ['green', 'orange', 'red']
        labels = ['Low', 'Medium', 'High']
        bucket_lines = {0: {'x': [], 'y': [], 'z': []},
                        1: {'x': [], 'y': [], 'z': []},
                        2: {'x': [], 'y': [], 'z': []}}
        for (u, v), w in edge_weights.items():
            if u not in self.node_to_idx or v not in self.node_to_idx:
                continue
            i, j = self.node_to_idx[u], self.node_to_idx[v]
            if w <= low_thresh:
                bucket = 0
            else:
                bucket = 1 if w <= self.max_w else 2
            bucket_lines[bucket]['x'].extend([pos[i,0], pos[j,0], None])
            bucket_lines[bucket]['y'].extend([pos[i,1], pos[j,1], None])
            bucket_lines[bucket]['z'].extend([pos[i,2], pos[j,2], None])
        traces = []
        for b in range(3):
            data = bucket_lines[b]
            traces.append(go.Scatter3d(
                x=data['x'], y=data['y'], z=data['z'],
                mode='lines',
                line=dict(width=1.2, color=colors[b]),
                name=f'Energy: {labels[b]}',
                showlegend=(frame_idx == 0),
                hoverinfo='none'
            ))
        return traces

    # 节点痕迹：无任何文字，纯标记
    def _get_node_trace_fixed(self, frame_idx):
        pos = self.positions[frame_idx]
        if np.any(np.isnan(pos)):
            pos = np.zeros((self.num_nodes, 3))
        return go.Scatter3d(
            x=pos[:,0], y=pos[:,1], z=pos[:,2],
            mode='markers',
            marker=dict(size=3, color='lightblue', line=dict(width=0.5, color='darkblue')),
            name='Concepts',
            showlegend=(frame_idx == 0),
            hoverinfo='none'
        )

    # 遍历路径（固定一条轨迹，无路径时为空）
    def _get_path_trace_fixed(self, frame_idx):
        rec = self.records[frame_idx]
        traversal = rec.get('traversal')
        if not traversal or not traversal.get('path') or len(traversal['path']) < 2:
            return go.Scatter3d(x=[], y=[], z=[], mode='lines', name='Traversal', showlegend=False)
        path = traversal['path']
        pos = self.positions[frame_idx]
        x, y, z = [], [], []
        for k in range(len(path)-1):
            u, v = path[k], path[k+1]
            if u not in self.node_to_idx or v not in self.node_to_idx:
                continue
            iu, iv = self.node_to_idx[u], self.node_to_idx[v]
            x.extend([pos[iu,0], pos[iv,0], None])
            y.extend([pos[iu,1], pos[iv,1], None])
            z.extend([pos[iu,2], pos[iv,2], None])
        color = 'blue' if traversal['type'] == 'hard' else 'red'
        return go.Scatter3d(
            x=x, y=y, z=z,
            mode='lines',
            line=dict(width=2.5, color=color),
            name='Traversal Path',
            showlegend=(frame_idx == 0)
        )

    # 高亮节点（固定一条轨迹，无数据时为空）
    def _get_highlight_trace_fixed(self, frame_idx):
        rec = self.records[frame_idx]
        traversal = rec.get('traversal')
        if not traversal or not traversal.get('path'):
            return go.Scatter3d(x=[], y=[], z=[], mode='markers', name='Highlight', showlegend=False)
        path = traversal['path']
        pos = self.positions[frame_idx]
        indices = [self.node_to_idx[n] for n in path if n in self.node_to_idx]
        if not indices:
            return go.Scatter3d(x=[], y=[], z=[], mode='markers', name='Highlight', showlegend=False)
        return go.Scatter3d(
            x=pos[indices,0], y=pos[indices,1], z=pos[indices,2],
            mode='markers',
            marker=dict(size=6, color='yellow', line=dict(width=0.5, color='black')),
            name='Highlighted Nodes',
            showlegend=(frame_idx == 0)
        )

    def create_animation(self, output_filename):
        if self.positions[0] is None:
            self.compute_all_positions()

        frames = []
        for i in range(len(self.records)):
            edge_traces = self._get_edge_traces_fixed(i)
            node_trace = self._get_node_trace_fixed(i)
            path_trace = self._get_path_trace_fixed(i)
            highlight_trace = self._get_highlight_trace_fixed(i)
            frame_data = edge_traces + [node_trace, path_trace, highlight_trace]
            frames.append(go.Frame(data=frame_data, name=str(i)))

        # 第一帧初始数据
        first_edge = self._get_edge_traces_fixed(0)
        first_node = self._get_node_trace_fixed(0)
        first_path = self._get_path_trace_fixed(0)
        first_highlight = self._get_highlight_trace_fixed(0)
        first_data = first_edge + [first_node, first_path, first_highlight]

        fig = go.Figure(
            data=first_data,
            layout=go.Layout(
                title=dict(text="Cognitive Graph 3D Evolution", font=dict(size=14)),
                scene=dict(
                    xaxis=dict(title='', range=[-POS_BOUNDS, POS_BOUNDS], showticklabels=False),
                    yaxis=dict(title='', range=[-POS_BOUNDS, POS_BOUNDS], showticklabels=False),
                    zaxis=dict(title='', range=[-POS_BOUNDS, POS_BOUNDS], showticklabels=False),
                    camera=dict(eye=dict(x=1.8, y=1.8, z=1.5)),
                    aspectmode='cube'
                ),
                updatemenus=[dict(
                    type='buttons',
                    showactive=False,
                    buttons=[dict(label='Play',
                                  method='animate',
                                  args=[None, dict(frame=dict(duration=ANIMATION_FRAME_INTERVAL_MS, redraw=True),
                                                   fromcurrent=True, mode='immediate')]),
                             dict(label='Pause',
                                  method='animate',
                                  args=[[None], dict(frame=dict(duration=0, redraw=False),
                                                     mode='immediate')])]
                )],
                sliders=[dict(
                    steps=[dict(method='animate', args=[[str(i)], dict(mode='immediate', frame=dict(duration=0, redraw=True))],
                                label=f"{self.records[i]['iteration']}") for i in range(len(self.records))],
                    transition=dict(duration=0),
                    currentvalue=dict(prefix='Iteration: ', font=dict(size=12))
                )],
                margin=dict(l=0, r=0, t=40, b=20),
                legend=dict(orientation='v', yanchor='top', y=1, xanchor='right', x=1)
            ),
            frames=frames
        )

        fig.write_html(output_filename)
        print(f"3D 动画已保存: {output_filename}")

def main():
    random.seed(42 + INDIVIDUAL_ID)
    np.random.seed(42 + INDIVIDUAL_ID)

    params = BASE_PARAMETERS.copy()
    params['learning_rate_variation'] = 0.1

    # 运行认知图演化并记录
    cg = RecordingCognitiveGraph3D(params, network_seed=42 + INDIVIDUAL_ID, num_concepts=NUM_CONCEPTS)
    records = cg.run_with_recording(max_iterations=MAX_ITERATIONS, record_interval=RECORD_INTERVAL)

    # 保存原始数据（可选）
    cg.save_records_to_json(f"../../Fresults/data/cognitive_records_3d_{NUM_CONCEPTS}c_ind{INDIVIDUAL_ID}.json")

    # 获取节点列表（顺序与记录中的 edge_weights 键一致）
    node_list = list(cg.G.nodes())
    # 如果第一帧边权重中出现了节点但 node_list 遗漏（不会），确保包含所有节点
    all_nodes = set()
    for rec in records:
        for u, v in rec['edge_weights'].keys():
            all_nodes.add(u)
            all_nodes.add(v)
    node_list = sorted(all_nodes)

    # 生成 3D 动画
    animator = CognitiveGraph3DAnimator(records, node_list)
    os.makedirs("../../Fresults/animations", exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_file = f"../../Fresults/animations/cognitive_3d_{NUM_CONCEPTS}c_ind{INDIVIDUAL_ID}_{timestamp}.html"
    animator.create_animation(out_file)
    print("3D 动画生成完成！")


if __name__ == "__main__":
    main()