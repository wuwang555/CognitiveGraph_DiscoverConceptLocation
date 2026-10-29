# 内生概念生成（endo_concept）

本模块在 **不引入任何新假设** 的前提下，从一阶认知图的两个公设出发，
实现任务报告中的“抓重点”机制：从压缩事件中识别稳定单元，并为其赋予结构化定义。

注意：本模块名为 `endo_concept`，但在本仓库范围内，它**不做**另一个项目里的“概念生成图构造与降层级再压缩/迁移”。它输出的是“系统已形成的重点单元及其结构化定义”，不是“让不动点成为新节点、构造更高层图”的生成结果。

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

- **A**：频繁项集枚举。在 `support ≥ fp_min_support` 下枚举 `size = minsize..fp_max_itemset_size` 的所有项集，不做下界过滤、不做角色纯筛选。
  - `size=1`：原子不动点候选。
  - `size>1`：原始事件层的高频整体候选；携带 `phi`，可写组合概念卡，但不是不可再分原子。
  - `minsize` 是枚举下界：`minsize=1` 输出 size=1..8；`minsize=2` 输出 size=2..8；`minsize=3` 输出 size=3..8。不同 `minsize` 的 A 输出是同一频繁项集闭包按 size 下界的截断，不是独立实验。
- **B**：最小频繁项集。在 `support ≥ lattice_min_support` 下保留下界项集。
- **C**：角色纯候选。在 B 的基础上要求成员平均角色一致性 ≥ `role_min_stability`。
- **ABC**：三种方法的并集，各自保留自己的过滤语义后再合并。

联合判据（`use_joint_criteria: True`）会在所选方法之上再执行 support 硬阈值和排序；对方法 A，`apply_lower_bound=False`，即联合判据不会把 A 重新压成 B。

## 运行

先确保一阶系统的原始压缩事件已产出（`run_static.py`），然后：

```bash
cd compression_graph
python endo_concept/run_endo.py
```

## 输出

`results/compression_graph/endo_concept/` 目录：

- `endo_summary.csv` — 各规模汇总
- `scale{N}/fixpoints.json` — 不动点列表。对方法 A：包含 `size=minsize..8` 的频繁项集；`size=1` 是原子不动点候选，`size>1` 是高频整体候选，`size≥2` 项集带 `phi`。对方法 B/C：`minsize=1` 下通常输出 size=1 的单概念候选，`phi=null`。
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

## 方法 A 的读法

方法 A 的输出应读作“当前 `support` 阈值下的频繁项集闭包”：

- `size=1`：原子不动点候选，对应概念卡的基节点候选。
- `size>1`：原始事件层的高频整体候选。它具备 `core/boundary/logic/energy/phi`，可以写成组合概念卡；但它必然包含频繁真子集，不是不可再分原子。
- `minsize`：枚举下界。`minsize=1` 给出“原子 + 整体候选”的完整视图；`minsize=2` 只看 size≥2 的整体候选；`minsize=3` 只看 size≥3 的整体候选。不同 `minsize` 不是不同实验，是同一闭包的不同 size 下界视图。
- `phi`：A 的 `size≥2` 项集独有，B/C 在 `minsize=1` 下 `phi=null`。A 是唯一提供组合层压缩势分布的方法。
- 集合关系：只有 support 阈值对齐时才有 C⊂B⊂A；当前三份 `fixpoints.json` 的 support 阈值不同，不能直接做集合包含验证。

## 核心约束（保持不变）

1. 不引入原一阶模型之外的新假设。
2. 保持无向性作为底层，有向性仅从不动点派生。
3. 阈值使用绝对值，保持跨规模可比。
4. 描述是定义形式的属性，不是系统外的动作。
5. 方法 A 的 `minsize` 是枚举下界，不是“只枚举该 size”。不同 `minsize` 的 A 输出是同一频繁项集闭包按 size 下界的截断；`size≥minsize` 项集的 `support`、`phi`、`boundary/logic/energy` 不随 `minsize` 改变。
6. 本仓库的 `endo_concept` 只做“抓重点”，不做另一个项目里的“不动点成节点、构造更高层图、再压缩/迁移降层级”。A 的 `size>1` 是“原始事件层高频整体候选”，是降层级的输入端，不是降层级输出端。