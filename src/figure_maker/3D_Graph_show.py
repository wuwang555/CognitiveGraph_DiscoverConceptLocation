import networkx as nx
import matplotlib.pyplot as plt
import random
from mpl_toolkits.mplot3d import Axes3D
import numpy as np
import math
from collections import defaultdict
import jieba
import time
import sys
import os

np.random.seed(42)
random.seed(42)
# 添加项目路径以便导入config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ===================== 可配置核心参数 =====================
num_layers = 10  # 时间层数
z_start = 0  # Z轴起始值
z_end = 3  # Z轴结束值
node_size = 20  # 节点大小
edge_width = 2  # 每层图内部边的宽度
edge_alpha = 1.0  # 每层图内部边的透明度
label_font_size = 1  # 边标签字体大小
node_label_size = 1  # 节点标签字体大小
# 层间同编号节点连线参数
inter_layer_edge_width = 1  # 层间节点连线宽度
inter_layer_edge_alpha = 1.0  # 层间节点连线透明度
# =====================================================

# ===================== 配置参数 =====================
# 从config中导入部分核心参数
BASE_PARAMETERS = {
    'forgetting_rate': 0.002,
    'base_learning_rate': 0.85,
    'hard_traversal_bias': 0.0,
    'soft_traversal_bias': 0.0,
    'compression_bias': 0.0,
    'migration_bias': 0.0,
    'learning_rate_variation': 0.1
}

# 部分核心概念定义（简化版，用于演示）
CORE_CONCEPT_DEFINITIONS = {
    # 物理学概念
    "牛顿定律": "物体运动的基本定律，描述了力与运动的关系",
    "力学": "研究物体运动和受力情况的物理学分支",
    "能量守恒": "能量既不会凭空产生也不会凭空消失的物理定律",

    # 数学概念
    "微积分": "研究变化和累积的数学分支，包括微分和积分",
    "几何学": "研究空间形状大小和相对位置的数学分支",
    "概率论": "研究随机现象数量规律的数学分支",

    # 计算机科学概念
    "算法": "解决问题的一系列明确的计算步骤",
    "数据结构": "计算机中组织和存储数据的方式",
    "机器学习": "让计算机通过经验自动改进性能的人工智能分支",

    # 基础原理概念
    "优化": "在给定约束下找到最佳解决方案的过程",
    "迭代": "重复反馈过程的活动",
    "抽象": "提取主要特征忽略次要细节的思维过程",
}

# 领域划分
CONCEPT_DOMAINS = {
    "physics": ["牛顿定律", "力学", "能量守恒"],
    "math": ["微积分", "几何学", "概率论"],
    "cs": ["算法", "数据结构", "机器学习"],
    "principles": ["优化", "迭代", "抽象"]
}

# 关键词提取配置
KEYWORD_CONFIG = {
    'top_k': 8,
    'stop_words': {'的', '是', '在', '和', '与', '或', '等', '这个', '那个', '一种'},
    'min_word_length': 1,
}

# 网络构建参数
NETWORK_CONFIG = {
    'similarity_threshold': 0.1,
    'max_expansion_depth': 3,
}


# =====================================================

class SemanticConceptNetwork:
    """基于定义关键词的语义概念网络"""

    def __init__(self):
        self.concept_definitions = {}
        self.concept_keywords = {}
        self.semantic_network = defaultdict(dict)

    def add_concept_definition(self, concept, definition, source="manual"):
        """添加概念定义"""
        self.concept_definitions[concept] = {
            'definition': definition,
            'source': source,
            'timestamp': time.time()
        }

        keywords = self.extract_keywords(definition)
        self.concept_keywords[concept] = keywords

    def extract_keywords(self, text, top_k=None):
        """从文本中提取关键词"""
        if top_k is None:
            top_k = KEYWORD_CONFIG['top_k']

        # 使用jieba进行分词
        words = jieba.cut(text)

        # 过滤停用词和短词
        filtered_words = [
            word for word in words
            if len(word) > KEYWORD_CONFIG['min_word_length'] and word not in KEYWORD_CONFIG['stop_words']
        ]

        # 统计词频
        word_freq = defaultdict(int)
        for word in filtered_words:
            word_freq[word] += 1

        # 返回频率最高的关键词
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        return [word for word, freq in sorted_words[:top_k]]

    def build_network(self):
        """构建语义网络"""
        # 添加所有概念定义
        for concept, definition in CORE_CONCEPT_DEFINITIONS.items():
            self.add_concept_definition(concept, definition, "predefined")

        # 构建相似度网络
        all_concepts = list(self.concept_definitions.keys())
        threshold = NETWORK_CONFIG['similarity_threshold']

        for i, concept1 in enumerate(all_concepts):
            for j, concept2 in enumerate(all_concepts[i + 1:], i + 1):
                similarity = self.calculate_semantic_similarity(concept1, concept2)
                if similarity > threshold:
                    self.semantic_network[concept1][concept2] = similarity
                    self.semantic_network[concept2][concept1] = similarity

        print(f"语义网络构建完成! 包含 {len(self.semantic_network)} 个概念节点")
        total_connections = sum(len(neighbors) for neighbors in self.semantic_network.values()) // 2
        print(f"网络连接数: {total_connections}")

    def calculate_semantic_similarity(self, concept1, concept2):
        """计算两个概念的语义相似度"""
        if concept1 not in self.concept_keywords or concept2 not in self.concept_keywords:
            return 0.0

        keywords1 = set(self.concept_keywords[concept1])
        keywords2 = set(self.concept_keywords[concept2])

        # Jaccard相似度
        intersection = len(keywords1.intersection(keywords2))
        union = len(keywords1.union(keywords2))

        if union == 0:
            return 0.0

        jaccard_similarity = intersection / union

        # 考虑领域相似性
        domain_similarity = self._calculate_domain_similarity(concept1, concept2)

        # 综合相似度
        combined_similarity = 0.7 * jaccard_similarity + 0.3 * domain_similarity

        return min(combined_similarity, 1.0)

    def _calculate_domain_similarity(self, concept1, concept2):
        """计算领域相似度"""
        domain1 = self.get_domain(concept1)
        domain2 = self.get_domain(concept2)

        if domain1 == domain2:
            return 1.0
        elif domain1 == "principles" or domain2 == "principles":
            return 0.6  # 原理节点与各领域都有一定相似性
        else:
            return 0.2  # 不同领域的基础相似度

    def get_domain(self, concept):
        """获取概念所属领域"""
        for domain, concepts in CONCEPT_DOMAINS.items():
            if concept in concepts:
                return domain
        return "other"


class EnhancedSemanticConceptNetwork(SemanticConceptNetwork):
    """增强的语义概念网络"""

    def __init__(self):
        super().__init__()
        self.concept_frequency = defaultdict(int)

    def calculate_enhanced_similarity(self, concept1, concept2, method="adaptive"):
        """增强的相似度计算"""
        semantic_sim = self.calculate_semantic_similarity(concept1, concept2)

        if method == "adaptive":
            # 自适应方法：根据概念抽象程度调整
            abstraction_level = self._abstraction_level(concept1, concept2)

            if abstraction_level > 0.6:  # 高度抽象
                # 抽象概念更看重领域相似性
                domain_sim = self._calculate_domain_similarity(concept1, concept2)
                return 0.7 * domain_sim + 0.3 * semantic_sim
            else:  # 具体概念
                return semantic_sim

        return semantic_sim

    def _abstraction_level(self, concept1, concept2):
        """评估概念的抽象程度"""
        abstraction_keywords = {'原理', '定律', '理论', '方法', '过程'}

        def get_keyword_count(concept):
            if concept not in self.concept_keywords:
                return 0
            return sum(1 for word in self.concept_keywords[concept] if word in abstraction_keywords)

        count1 = get_keyword_count(concept1)
        count2 = get_keyword_count(concept2)

        return (count1 + count2) / 4.0  # 归一化


class SemanticEnhancedCognitiveGraph:
    """语义增强认知图"""

    def __init__(self, individual_params, num_concepts=None, network_seed=42):
        self.G = nx.Graph()
        self.individual_params = individual_params
        self.network_seed = network_seed
        self.iteration_count = 0

        # 参数设置
        self._setup_parameters(individual_params)

        # 语义网络
        self.semantic_network = EnhancedSemanticConceptNetwork()
        self.semantic_network.build_network()

        # 历史记录
        self.traversal_history = []
        self.energy_history = []
        self.last_activation_time = {}

        # 设置随机种子
        random.seed(network_seed)
        np.random.seed(network_seed)

        # 初始化图
        self._initialize_graph(num_concepts)

    def _setup_parameters(self, individual_params):
        """设置个体参数"""
        self.forgetting_rate = individual_params.get('forgetting_rate', 0.002)
        self.base_learning_rate = individual_params.get('base_learning_rate', 0.85)
        self.learning_rate_variation = individual_params.get('learning_rate_variation', 0.1)
        self.traversal_preference = individual_params.get('traversal_preference', 0.5)  # 0-1, 越高越倾向遍历相似节点

    def _initialize_graph(self, num_concepts=None):
        """基于语义网络初始化图"""
        # 获取所有概念或指定数量的概念
        all_concepts = list(self.semantic_network.concept_definitions.keys())
        if num_concepts and num_concepts < len(all_concepts):
            concepts = all_concepts[:num_concepts]
        else:
            concepts = all_concepts

        # 添加节点
        self.G.add_nodes_from(concepts)

        # 基于语义相似度添加边
        edge_count = 0
        for i, concept1 in enumerate(concepts):
            for j, concept2 in enumerate(concepts[i + 1:], i + 1):
                # 计算语义相似度
                similarity = self.semantic_network.calculate_enhanced_similarity(concept1, concept2, "adaptive")

                # 基于相似度设置初始能量（相似度越高，能量越低）
                if similarity > 0.1:  # 相似度阈值
                    energy = 2.0 - similarity * 1.5
                    energy = max(0.3, min(2.0, energy))

                    self.G.add_edge(concept1, concept2,
                                    weight=energy,
                                    original_weight=energy,
                                    similarity=similarity,
                                    traversal_count=0)

                    # 初始化激活时间
                    self.last_activation_time[(concept1, concept2)] = 0
                    edge_count += 1

        print(f"语义增强图初始化: {len(concepts)}节点, {edge_count}条边")
        print(f"初始全局能量: {self.calculate_network_energy():.3f}")

    def calculate_network_energy(self):
        """计算网络平均能耗"""
        if self.G.number_of_edges() == 0:
            return 0
        energies = [self.G[u][v]['weight'] for u, v in self.G.edges()]
        return np.mean(energies)

    def calculate_semantic_similarity(self, node1, node2):
        """计算语义相似度"""
        return self.semantic_network.calculate_enhanced_similarity(node1, node2, "adaptive")

    def record_edge_activation(self, u, v):
        """记录边的激活并应用学习效应"""
        # 更新激活时间
        self.last_activation_time[(u, v)] = self.iteration_count

        # 应用学习效应：降低这条边的能耗
        if self.G.has_edge(u, v):
            current_energy = self.G[u][v]['weight']
            similarity = self.G[u][v].get('similarity', 0.5)

            # 学习率计算（相似度越高，学习效果越好）
            base_learning = self.base_learning_rate
            similarity_bonus = 0.2 * similarity  # 相似度带来的学习加成
            learning_rate = base_learning + similarity_bonus

            # 添加个体变异
            individual_variation = np.random.uniform(
                1 - self.learning_rate_variation,
                1 + self.learning_rate_variation
            )
            learning_rate *= individual_variation

            # 应用学习
            learning_effect = learning_rate * (current_energy / 2.0)
            new_energy = max(0.05, current_energy * (1 - learning_effect))
            self.G[u][v]['weight'] = new_energy

            # 更新遍历计数
            if 'traversal_count' not in self.G[u][v]:
                self.G[u][v]['traversal_count'] = 0
            self.G[u][v]['traversal_count'] += 1

    def apply_forgetting(self):
        """应用遗忘机制"""
        current_time = self.iteration_count

        for u, v in self.G.edges():
            time_since_activation = current_time - self.last_activation_time.get((u, v), 0)

            if time_since_activation > 0:  # 只有长时间未激活的边才会遗忘
                current_energy = self.G[u][v]['weight']
                original_energy = self.G[u][v].get('original_weight', 2.0)
                similarity = self.G[u][v].get('similarity', 0.5)

                # 遗忘函数：基于时间的指数衰减
                # 相似度提供保护（相似度越高，遗忘越慢）
                similarity_protection = 1.0 - (similarity * 0.3)

                # 遗忘因子
                forget_factor = self._compute_forget_factor(time_since_activation)
                forget_factor *= similarity_protection

                # 应用遗忘：能耗向原始值恢复
                new_energy = current_energy + (original_energy - current_energy) * forget_factor
                new_energy = min(new_energy, original_energy)  # 不超过原始值

                self.G[u][v]['weight'] = max(0.1, new_energy)

    def _compute_forget_factor(self, time_gap):
        """计算遗忘因子"""
        # 基于指数衰减的遗忘函数
        base_rate = self.forgetting_rate

        # 时间间隔越长，遗忘越强
        time_factor = 1 - math.exp(-time_gap / 800)

        # 综合遗忘因子
        forget_factor = base_rate * time_factor
        return min(forget_factor, 0.15)  # 最大遗忘率15%

    def semantic_guided_traversal(self):
        """语义引导的遍历"""
        nodes = list(self.G.nodes())
        if len(nodes) < 2:
            return None

        # 选择起始节点
        start_node = random.choice(nodes)
        path = [start_node]
        current_node = start_node

        # 随机走2-4步
        path_length = random.randint(2, 4)

        for step in range(path_length - 1):
            neighbors = list(self.G.neighbors(current_node))
            if not neighbors:
                break

            # 基于语义相似度和当前偏好选择下一个节点
            next_node = self._select_next_node(current_node, neighbors)

            if next_node not in path:  # 避免循环
                path.append(next_node)
                current_node = next_node
            else:
                break

        if len(path) >= 2:
            # 记录遍历
            self.traversal_history.append({
                'path': path.copy(),
                'iteration': self.iteration_count,
                'type': 'semantic_guided'
            })

            # 更新激活时间并应用学习
            for i in range(len(path) - 1):
                u, v = path[i], path[i + 1]
                if self.G.has_edge(u, v):
                    self.record_edge_activation(u, v)

            # 50%的概率也激活语义相似的边（模拟概念扩散）
            if random.random() < 0.5 and len(path) > 1:
                for node in path:
                    # 找到语义相似的邻居
                    similar_neighbors = self._find_semantically_similar_nodes(node)
                    for neighbor in similar_neighbors[:2]:  # 最多激活2个相似邻居
                        if self.G.has_edge(node, neighbor):
                            self.record_edge_activation(node, neighbor)

            return path
        return None

    def _select_next_node(self, current_node, neighbors):
        """基于语义相似度选择下一个节点"""
        if random.random() < self.traversal_preference:
            # 基于语义相似度选择
            neighbor_similarities = []
            for neighbor in neighbors:
                similarity = self.calculate_semantic_similarity(current_node, neighbor)
                edge_weight = self.G[current_node][neighbor]['weight']

                # 综合考虑相似度和边权重（相似度高且权重低的优先）
                score = similarity * 0.7 + (1.0 / (edge_weight + 0.1)) * 0.3
                neighbor_similarities.append((neighbor, score))

            # 按得分排序
            neighbor_similarities.sort(key=lambda x: x[1], reverse=True)

            # 选择前3个中的一个
            top_candidates = neighbor_similarities[:3]
            if top_candidates:
                # 使用softmax概率选择
                scores = [score for _, score in top_candidates]
                probs = self._softmax(scores)
                selected_idx = np.random.choice(len(top_candidates), p=probs)
                return top_candidates[selected_idx][0]

        # 随机选择
        return random.choice(neighbors)

    def _find_semantically_similar_nodes(self, node, threshold=0.3):
        """寻找语义相似的节点"""
        similar_nodes = []
        all_nodes = list(self.G.nodes())

        for other_node in all_nodes:
            if other_node != node:
                similarity = self.calculate_semantic_similarity(node, other_node)
                if similarity > threshold:
                    similar_nodes.append((other_node, similarity))

        # 按相似度排序
        similar_nodes.sort(key=lambda x: x[1], reverse=True)
        return [node for node, _ in similar_nodes]

    def _softmax(self, x):
        """softmax函数"""
        e_x = np.exp(np.array(x) - np.max(x))
        return e_x / e_x.sum()

    def evolve_one_step(self):
        """演化一步"""
        self.iteration_count += 1

        # 语义引导的遍历
        self.semantic_guided_traversal()

        # 应用遗忘（每10步应用一次）
        if self.iteration_count % 10 == 0:
            self.apply_forgetting()

        # 记录当前网络能量
        current_energy = self.calculate_network_energy()
        self.energy_history.append(current_energy)

        return current_energy

    def evolve_multiple_steps(self, steps=100):
        """演化多步"""
        energies = []
        for i in range(steps):
            energy = self.evolve_one_step()
            energies.append(energy)

        return energies

    def get_network_snapshot(self):
        """获取网络快照"""
        return {
            'iteration': self.iteration_count,
            'graph': self.G.copy(),
            'avg_energy': self.calculate_network_energy(),
            'traversal_count': len(self.traversal_history),
            'node_count': self.G.number_of_nodes(),
            'edge_count': self.G.number_of_edges()
        }


def create_semantic_3d_dynamic_graph(num_concepts=12, num_layers=10):
    """创建语义增强的3D动态图"""

    # 创建语义增强认知图
    individual_params = BASE_PARAMETERS.copy()
    individual_params['traversal_preference'] = 0.7  # 较高语义引导偏好

    semantic_graph = SemanticEnhancedCognitiveGraph(
        individual_params=individual_params,
        num_concepts=num_concepts,
        network_seed=42
    )

    # 1. 生成基础XY坐标（基于初始图结构和语义相似度）
    print("生成基础布局...")
    pos_2d_base = nx.spring_layout(semantic_graph.G, seed=100, k=1.0)

    # 2. 计算Z轴各层的取值
    z_values = np.linspace(z_start, z_end, num_layers, dtype=float)

    # 3. 存储每个层的图快照和位置
    layer_graphs = []
    layer_positions = []

    # 计算每个层之间的演化步数
    total_steps = 500  # 总演化步数
    steps_per_layer = total_steps // num_layers

    print(f"开始演化，总步数: {total_steps}, 每层步数: {steps_per_layer}")

    for layer_idx, z in enumerate(z_values):
        print(f"生成第 {layer_idx + 1}/{num_layers} 层 (Z={z:.2f})...")

        # 演化一定步数
        if layer_idx > 0:
            semantic_graph.evolve_multiple_steps(steps_per_layer)

        # 获取当前图状态
        current_graph = semantic_graph.G.copy()
        layer_graphs.append(current_graph)

        # 计算当前层的布局
        if layer_idx == 0:
            # 第一层使用基础布局
            current_pos = pos_2d_base.copy()
        else:
            # 后续层基于前一层的布局和当前权重进行调整
            prev_pos = layer_positions[-1].copy()
            current_pos = {}

            # 基于权重调整节点位置（权重越低，节点越靠近）
            for node in current_graph.nodes():
                if node in prev_pos:
                    base_x, base_y = prev_pos[node]
                    adjustment_x, adjustment_y = 0, 0

                    # 计算来自邻居的吸引力
                    for neighbor in current_graph.neighbors(node):
                        if neighbor in prev_pos:
                            if current_graph.has_edge(node, neighbor):
                                weight = current_graph[node][neighbor]['weight']
                                similarity = current_graph[node][neighbor].get('similarity', 0.5)

                                # 权重越低，吸引力越强；相似度越高，吸引力越强
                                attraction = (1.0 / (weight + 0.1)) * (0.5 + 0.5 * similarity)

                                neighbor_x, neighbor_y = prev_pos[neighbor]
                                dx = neighbor_x - base_x
                                dy = neighbor_y - base_y
                                dist = np.sqrt(dx ** 2 + dy ** 2) + 0.01

                                # 调整位置
                                adjustment_x += attraction * dx / dist * 0.03
                                adjustment_y += attraction * dy / dist * 0.03

                    current_pos[node] = (base_x + adjustment_x, base_y + adjustment_y)
                else:
                    # 新节点使用随机位置
                    current_pos[node] = (random.uniform(-1, 1), random.uniform(-1, 1))

        layer_positions.append(current_pos)

    # 4. 创建3D绘图环境
    fig = plt.figure(figsize=(16, 12))
    ax = fig.add_subplot(111, projection='3d')

    # 5. 循环绘制每个Z层的图
    colors = plt.cm.Set3(np.linspace(0, 1, num_layers))

    # 计算节点的平均位置，用于标签定位
    avg_positions = defaultdict(list)
    for pos_dict in layer_positions:
        for node, (x, y) in pos_dict.items():
            avg_positions[node].append((x, y))

    node_avg_pos = {}
    for node, positions in avg_positions.items():
        if positions:
            avg_x = np.mean([p[0] for p in positions])
            avg_y = np.mean([p[1] for p in positions])
            node_avg_pos[node] = (avg_x, avg_y)

    for idx, (z, graph, pos_2d) in enumerate(zip(z_values, layer_graphs, layer_positions)):
        print(f"绘制第 {idx + 1} 层...")

        # 5.1 绘制当前层的节点
        x_coords = [pos_2d[node][0] for node in graph.nodes()]
        y_coords = [pos_2d[node][1] for node in graph.nodes()]
        z_coords = [z] * len(graph.nodes())

        # 根据领域为节点着色
        domain_colors = []
        for node in graph.nodes():
            domain = semantic_graph.semantic_network.get_domain(node)
            if domain == "physics":
                domain_colors.append('lightcoral')
            elif domain == "math":
                domain_colors.append('lightblue')
            elif domain == "cs":
                domain_colors.append('lightgreen')
            elif domain == "principles":
                domain_colors.append('gold')
            else:
                domain_colors.append('lightgray')

        ax.scatter(x_coords, y_coords, z_coords,
                   s=node_size, c=domain_colors, edgecolors="black",
                   depthshade=True, alpha=0.8)

        # 5.2 绘制当前层的边
        for (u, v) in graph.edges():
            x1, y1 = pos_2d[u]
            x2, y2 = pos_2d[v]
            z1 = z2 = z

            # 边的颜色和宽度基于权重和语义相似度
            weight = graph[u][v]['weight']
            similarity = graph[u][v].get('similarity', 0.5)

            # 权重越低，边越粗（连接越强）
            linewidth = max(0.5, 3.0 / (weight + 0.5))

            # 相似度越高，边颜色越深
            alpha = max(0.05, min(0.3, similarity * 0.5))

            # 根据权重选择颜色
            if weight < 0.5:
                edge_color = 'darkgreen'
            elif weight < 1.0:
                edge_color = 'green'
            elif weight < 1.5:
                edge_color = 'orange'
            else:
                edge_color = 'red'

            ax.plot([x1, x2], [y1, y2], [z1, z2],
                    color=edge_color, linewidth=linewidth, alpha=alpha)

    # 6. 绘制节点标签（使用平均位置）
    for node, (avg_x, avg_y) in node_avg_pos.items():
        # 找到该节点最常出现的Z层
        node_z_values = []
        for idx, graph in enumerate(layer_graphs):
            if node in graph.nodes():
                node_z_values.append(z_values[idx])

        if node_z_values:
            avg_z = np.mean(node_z_values)
            # 缩短长标签
            label = node if len(node) <= 4 else node[:3] + "."
            ax.text(avg_x, avg_y, avg_z, label,
                    fontsize=node_label_size, fontweight="bold",
                    ha="center", va="center", color='black')

    # 7. 绘制层间同编号节点的连线 - 修改为不同颜色
    print("绘制层间节点连线...")

    # 收集所有节点（在所有层中出现过的）
    all_nodes = set()
    for graph in layer_graphs:
        all_nodes.update(graph.nodes())

    # 为每个节点分配一个独特的颜色
    cmap = plt.cm.tab20  # 使用tab20颜色映射，有20种不同的颜色
    node_colors = {}
    for i, node in enumerate(all_nodes):
        # 使用循环颜色映射，确保每个节点有不同颜色
        color_idx = i % 20  # tab20有20种颜色
        node_colors[node] = cmap(color_idx)

    # 绘制每个节点的层间连线
    for node in node_avg_pos.keys():
        node_coords = []

        # 收集该节点在所有层的坐标
        for idx, (z, graph, pos_2d) in enumerate(zip(z_values, layer_graphs, layer_positions)):
            if node in pos_2d:
                x, y = pos_2d[node]
                node_coords.append((x, y, z))

        if len(node_coords) >= 2:
            # 拆分X/Y/Z坐标列表
            x_list = [coord[0] for coord in node_coords]
            y_list = [coord[1] for coord in node_coords]
            z_list = [coord[2] for coord in node_coords]

            # 获取该节点的颜色
            node_color = node_colors.get(node, 'red')

            # 绘制该节点在各层间的连线
            ax.plot(x_list, y_list, z_list,
                    color=node_color, linewidth=inter_layer_edge_width,
                    alpha=inter_layer_edge_alpha, linestyle="--")

    # 8. 添加语义相似度最高的连接
    print("添加语义相似度最高的连接...")
    if layer_graphs[-1].number_of_edges() > 0:
        # 找出最后一层中语义相似度最高的边
        edges_with_similarity = []
        for u, v, data in layer_graphs[-1].edges(data=True):
            if 'similarity' in data:
                edges_with_similarity.append(((u, v), data['similarity']))

        if edges_with_similarity:
            # 按相似度排序
            edges_with_similarity.sort(key=lambda x: x[1], reverse=True)

            # 绘制前3条高相似度边
            for (u, v), similarity in edges_with_similarity[:3]:
                if u in layer_positions[-1] and v in layer_positions[-1]:
                    x1, y1 = layer_positions[-1][u]
                    x2, y2 = layer_positions[-1][v]
                    z = z_values[-1] + 0.05  # 稍微抬高

                    ax.plot([x1, x2], [y1, y2], [z, z],
                            color='purple', linewidth=3, alpha=0.7, linestyle='-')

                    # 添加标签
                    mid_x = (x1 + x2) / 2
                    mid_y = (y1 + y2) / 2
                    ax.text(mid_x, mid_y, z, f"相似度: {similarity:.2f}",
                            fontsize=7, color='purple', ha='center')

    # 9. 图形美化与标签设置
    ax.set_xlabel("X Axis", fontsize=12)
    ax.set_ylabel("Y Axis", fontsize=12)
    ax.set_zlabel("Time Axis", fontsize=12)

    title = f"3D Semantic-Enhanced Cognitive Graph Evolution\n"
    title += f"Layers: {num_layers}, Concepts: {num_concepts}, Steps: {semantic_graph.iteration_count}"
    ax.set_title(title, fontsize=14, pad=20)

    # 添加图例 - 节点领域颜色图例
    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor='lightcoral', alpha=0.8, label='Physics'),
        Patch(facecolor='lightblue', alpha=0.8, label='Math'),
        Patch(facecolor='lightgreen', alpha=0.8, label='Computer Science'),
        Patch(facecolor='gold', alpha=0.8, label='Principles'),
        Patch(facecolor='lightgray', alpha=0.8, label='Other'),
    ]
    ax.legend(handles=legend_elements, loc='upper right', fontsize=9)

    ax.grid(False)

    # 10. 添加能量历史图表（在左下角）
    if semantic_graph.energy_history:
        from mpl_toolkits.axes_grid1.inset_locator import inset_axes
        ax_inset = inset_axes(ax, width="30%", height="20%", loc='lower left')
        ax_inset.plot(semantic_graph.energy_history, 'b-', linewidth=1.5)
        ax_inset.set_title("Network Energy Trend", fontsize=8)
        ax_inset.set_xlabel("Step", fontsize=6)
        ax_inset.set_ylabel("Avg Energy", fontsize=6)
        ax_inset.grid(True, alpha=0.3)
        ax_inset.tick_params(labelsize=6)

        # 标记演化层
        for i, z in enumerate(z_values[1:], 1):
            step = i * steps_per_layer
            if step < len(semantic_graph.energy_history):
                ax_inset.axvline(x=step, color='r', linestyle='--', alpha=0.3, linewidth=0.5)

    # 11. 添加节点颜色图例（显示部分节点）
    # 由于节点可能很多，只显示前5个节点的颜色
    node_list = list(all_nodes)
    if len(node_list) > 0:
        node_legend_elements = []
        for i, node in enumerate(node_list[:5]):  # 只显示前5个节点的颜色
            node_color = node_colors.get(node, 'black')
            node_legend_elements.append(
                Patch(facecolor=node_color, alpha=0.8, label=f'Node: {node}')
            )

        # 添加第二个图例
        from matplotlib.legend import Legend
        legend2 = Legend(ax, node_legend_elements,
                         ['Node Colors (Sample)'] + [f'  {node}' for node in node_list[:5]],
                         loc='lower right', fontsize=7, title='Node Trajectory Colors')
        ax.add_artist(legend2)

    plt.tight_layout()
    plt.show()

    # 12. 打印统计信息
    print(f"\n=== 语义增强图演化统计 ===")
    print(f"总迭代步数: {semantic_graph.iteration_count}")
    print(f"遍历次数: {len(semantic_graph.traversal_history)}")
    print(f"初始平均权重: {semantic_graph.energy_history[0]:.3f}" if semantic_graph.energy_history else "N/A")
    print(f"最终平均权重: {semantic_graph.energy_history[-1]:.3f}" if semantic_graph.energy_history else "N/A")

    if semantic_graph.energy_history and len(semantic_graph.energy_history) > 1:
        improvement = ((semantic_graph.energy_history[0] - semantic_graph.energy_history[-1]) /
                       semantic_graph.energy_history[0] * 100)
        print(f"权重改善: {improvement:.1f}%")

    # 13. 打印语义信息
    print(f"\n=== 语义网络信息 ===")
    print(f"概念总数: {len(semantic_graph.semantic_network.concept_definitions)}")

    # 示例相似度计算
    print(f"\n示例概念相似度:")
    concepts = list(semantic_graph.G.nodes())[:5]
    for i, concept1 in enumerate(concepts):
        for j, concept2 in enumerate(concepts[i + 1:], i + 1):
            similarity = semantic_graph.calculate_semantic_similarity(concept1, concept2)
            print(f"  {concept1} <-> {concept2}: {similarity:.3f}")

    return semantic_graph, layer_graphs, layer_positions


# 运行主函数
if __name__ == "__main__":
    print("开始创建语义增强的3D动态图...")

    # 初始化jieba
    jieba.initialize()

    # 创建语义增强的3D动态图
    semantic_graph, layer_graphs, layer_positions = create_semantic_3d_dynamic_graph(
        num_concepts=12,
        num_layers=num_layers
    )

    print("\n演化完成！")