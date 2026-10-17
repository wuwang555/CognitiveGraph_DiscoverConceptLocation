import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyArrowPatch
import networkx as nx
import math
import numpy as np

# 设置中文字体，避免乱码
plt.rcParams['font.sans-serif'] = ['SimHei']  # 使用黑体
plt.rcParams['axes.unicode_minus'] = False

# 定义节点（中心 + 7个外围节点）
nodes = ['万有引力定律', '相互作用力', '牛顿', '掉落', '力', '方向性', '苹果', '质量']

# 外围节点对应的方向（角度，从正东逆时针）
# 西(180°), 西北(135°), 北(90°), 东北(45°), 东(0°), 东南(315°), 南(270°)
directions = {
    '相互作用力': 180,
    '牛顿': 135,
    '掉落': 90,
    '力': 45,
    '方向性': 0,
    '苹果': 315,
    '质量': 270
}

# 半径（中心到外围节点的距离）
R = 2.0

# 计算相对坐标（以中心为原点）
pos_rel = {}
pos_rel['万有引力定律'] = (0, 0)
for node, angle in directions.items():
    rad = math.radians(angle)
    x = R * math.cos(rad)
    y = R * math.sin(rad)
    pos_rel[node] = (x, y)

# 定义所有边及其权值（无向边）
edges = []

# 中心与外围的边（注意苹果和质量权值特殊）
center = '万有引力定律'
for node in nodes[1:]:  # 跳过中心
    if node == '苹果':
        w = 0.25
    elif node == '质量':
        w = 0.21
    else:
        w = 0.15  # 小于0.20
    edges.append((center, node, w))

# 外围节点之间的边（按给定顺序连接）
peripheral_edges = [
    ('相互作用力', '牛顿', 0.26),
    ('牛顿', '掉落', 0.43),
    ('掉落', '力', 0.38),
    ('力', '方向性', 0.16),
    ('方向性', '苹果', 0.79),
    ('苹果', '质量', 0.34)
]
edges.extend(peripheral_edges)

# 创建图形和坐标轴
fig, ax = plt.subplots(figsize=(12, 6))
ax.set_aspect('equal')
ax.axis('off')  # 隐藏坐标轴

# 左右图的中心偏移
offset_left = (-5, 0)
offset_right = (5, 0)

# 绘制图的函数
def draw_graph(ax, offset, center_blue=False, draw_circle=False):
    """
    在指定偏移位置绘制图
    offset: (dx, dy) 整体偏移量
    center_blue: 中心节点边框是否为蓝色
    draw_circle: 是否绘制外围虚线圆
    """
    # 节点大小（半径）
    center_r = 0.6
    node_r = 0.4

    # 先绘制所有边（避免被节点遮挡）
    for u, v, w in edges:
        # 获取起点和终点的绝对坐标
        x1, y1 = pos_rel[u][0] + offset[0], pos_rel[u][1] + offset[1]
        x2, y2 = pos_rel[v][0] + offset[0], pos_rel[v][1] + offset[1]

        # 绘制双向箭头（使用FancyArrowPatch，arrowstyle='<->'）
        arrow = FancyArrowPatch((x1, y1), (x2, y2),
                                arrowstyle='<->',      # 两端箭头
                                mutation_scale=15,     # 箭头大小
                                color='black',
                                linewidth=1,
                                linestyle='-')
        ax.add_patch(arrow)

        # 在边的中点添加权值标签（稍微偏移以避免与线重叠）
        mx, my = (x1 + x2) / 2, (y1 + y2) / 2
        # 计算边的法线方向（用于偏移）
        dx, dy = x2 - x1, y2 - y1
        length = math.hypot(dx, dy)
        if length > 0:
            nx_, ny_ = -dy / length, dx / length  # 垂直单位向量
        else:
            nx_, ny_ = 0, 0
        # 偏移量
        offset_dist = 0.15
        mx += nx_ * offset_dist
        my += ny_ * offset_dist

        ax.text(mx, my, f'{w:.2f}', fontsize=8,
                ha='center', va='center',
                bbox=dict(facecolor='white', edgecolor='none', pad=1),
                color='black')

    # 绘制节点
    for node in nodes:
        x, y = pos_rel[node][0] + offset[0], pos_rel[node][1] + offset[1]
        radius = center_r if node == '万有引力定律' else node_r
        # 节点圆
        edgecolor = 'blue' if (center_blue and node == '万有引力定律') else 'black'
        circle = patches.Circle((x, y), radius,
                                facecolor='white',
                                edgecolor=edgecolor,
                                linewidth=2 if node == '万有引力定律' else 1,
                                zorder=10)  # 确保节点在边上
        ax.add_patch(circle)
        # 节点标签
        ax.text(x, y, node, fontsize=8 if node == '万有引力定律' else 7,
                ha='center', va='center', color='black', zorder=11)

    # 如果需要，绘制外围虚线圆（以偏移中心为圆心）
    if draw_circle:
        circle_outline = patches.Circle(offset, radius=3.5,
                                        facecolor='none',
                                        edgecolor='black',
                                        linestyle='dashed',
                                        linewidth=1.5)
        ax.add_patch(circle_outline)

# 绘制左图（中心蓝色边框 + 外围虚线圆）
draw_graph(ax, offset_left, center_blue=True, draw_circle=True)

# 绘制右图（正常黑色边框，无虚线圆）
draw_graph(ax, offset_right, center_blue=False, draw_circle=False)

# 在两个图之间添加红色箭头和说明文字
# 箭头从左向右
arrow_start = (offset_right[0] - 2.5, 0)   # 右图左侧附近
arrow_end = (offset_left[0] + 2.5, 0)    # 左图右侧附近
arrow = FancyArrowPatch(arrow_start, arrow_end,
                        arrowstyle='->',
                        mutation_scale=30,
                        color='red',
                        linewidth=2)
ax.add_patch(arrow)

# 箭头上方的文字
ax.text((arrow_start[0] + arrow_end[0]) / 2, 0.8,
        '检测为一次“概念压缩”',
        fontsize=12, ha='center', va='bottom',
        color='black')

# 调整坐标轴范围，确保所有元素可见
ax.set_xlim(-9, 9)
ax.set_ylim(-4, 4)

# 保存为PNG
plt.savefig('concept_compression.png', dpi=300, bbox_inches='tight')
plt.show()