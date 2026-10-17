# 内生概念生成（endo_concept）

本模块在 **不引入任何新假设** 的前提下，从一阶认知图的两个公设出发，
实现任务报告中的内生概念生成机制。

## 模块结构

| 文件 | 作用 |
|------|------|
| `config_endo.py` | 配置：方法选择、阈值、权重 |
| `fixpoint.py` | 不动点检测（方法 A / B / C / ABC） |
| `logic_derive.py` | 从不动点派生有向逻辑边 |
| `boundary.py` | 边界刻画（Φ 计算与统计） |
| `structure.py` | 生成 `CONCEPT_STRUCTURE` |
| `multichannel.py` | 多通道初始边权 |
| `high_order.py` | 高阶项内化（改写能耗公式） |
| `run_endo.py` | 端到端入口 |

## 切换不动点检测方法

编辑 `config_endo.py`：

```python
"fixpoint_method": "A",   # "A" | "B" | "C" | "ABC"
```

- **A**：频繁项集挖掘（Apriori 枚举）
- **B**：包含格分析（下界元素）
- **C**：位置稳定性分析
- **ABC**：三种方法的并集

联合判据（`use_joint_criteria: True`）会在所选方法之上再执行：

1. 支持度 > `joint_support_min`
2. 在包含格中处于下界
3. 平均稳定性 > `joint_stability_min`

## 运行

先确保一阶系统的原始压缩事件已产出（`run_static.py`），然后：

```bash
cd compression_graph
python endo_concept/run_endo.py
```

## 输出

`results/compression_graph/endo_concept/` 目录：

- `endo_summary.csv` — 各规模汇总
- `scale{N}/fixpoints.json` — 不动点列表
- `scale{N}/logic_edges.csv` — 有向逻辑边
- `scale{N}/concept_structure.json` — 结构化定义
- `scale{N}/edge_weights.csv` — 多通道初始权重与高阶修正后的权重

## 与任务报告的对应

| 报告章节 | 实现文件 |
|---------|---------|
| 二、能耗公式（多通道 / 高阶项） | `multichannel.py` / `high_order.py` |
| 三、边界 | `boundary.py` |
| 四、逻辑 | `logic_derive.py` |
| 五、不动点（A/B/C/联合判据） | `fixpoint.py` |
| 六、描述（`CONCEPT_STRUCTURE`） | `structure.py` |
| 七、定义形式 | `structure.py` |
| 八、内生概念生成流程 | `run_endo.py` |

## 核心约束（保持不变）

1. 不引入原一阶模型之外的新假设。
2. 保持无向性作为底层，有向性仅从不动点派生。
3. 阈值使用绝对值，保持跨规模可比。
4. 描述是定义形式的属性，不是系统外的动作。