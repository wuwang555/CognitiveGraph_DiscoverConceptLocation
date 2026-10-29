# CognitiveGraph_DiscoverConceptLocation
# Cognitive Graph Theory: From Second-Order Observation to a Four-Dimensional Concept Space

> This project builds upon the first-order cognitive graph model from *The Geometry, Algebra, and Dynamics of Cognition: A Unified Graph Theory Model Based on the Principle of Minimum Energy Consumption* (hereinafter referred to as "the original paper"), constructing a **second-order observation layer** on top of it: identifying stable structures from the system's spontaneously generated concept compression events, mapping them into a continuous four-dimensional concept space, and performing an operational test of the empirical hypothesis that "concept regions are convex."
>
> The tone of this project is consistent with the original paper: **we do not pursue fitting, only computability**. Each stage explicitly declares "what this stage does" and "what this stage observes," and annotates boundaries at the conclusions.
>
> This repository focuses only on **capturing the essentials**: identifying the stable units that the system repeatedly attends to from compression events, and assigning them structured definitions. It does not do what another project does—"making fixpoints into new nodes, constructing higher-level graphs, then compressing/migrating to reduce hierarchy." Although the module name `endo_concept` is called "endogenous concept generation," within the scope of this repository it is still capturing the essentials, not constructing a concept-generation graph.

---

## I. What We Do Not Do

Before we begin, let us draw the boundaries. This project **does not** do the following:

- **Does not do concept generation**. What this project does is "capturing the essentials"—identifying the minimal stable units (fixpoints) that the system repeatedly attends to from compression events, and assigning them structured definitions. True "concept generation" (making fixpoints into new nodes, constructing higher-level graphs) belongs to subsequent work and is outside the scope of this project.
- **Does not do engineering modifications**. No pruning, percentile thresholds, community detection, or cost mapping are applied to the first-order system. All thresholds remain absolute values, all relations remain as-is, and all multi-granularity outputs (subsets, paths, repetitions) are preserved.
- **Does not do empirical fitting**. This project does not compare with human behavioral data or brain imaging data. Its positioning is a **thought experiment platform**—providing a "possible world" and observing what it produces.

**The only things inherited from the original paper are two postulates**:
1. Cognitive states are dynamic networks `G(V, E, t)`;
2. Network evolution is driven by energy minimization.

Everything this project adds on top of these two postulates is merely **observation**, not **new assumptions**.

---

## II. Overall Design: A Six-Stage Logic Chain

All data, code, and results in this project form a clear six-stage logic chain:

```
First-order system evolution
    ↓ produces compression events
[Stage 1] G2 relation graph construction
    ↓ clique graph building
[Stage 2] Compression/migration candidate detection
    ↓ statistics
[Stage 3] Objective metrics (consistent with the original paper)
    ↓ fixpoint detection (methods A/B/C)
[Stage 4] Fixpoints and structured definitions
    ↓ mapping to continuous space
[Stage 5] Four-dimensional concept space (b, c, g1, g2)
    ↓ convexity testing (self-test + holdout)
[Stage 6] Dialogue with concept space theory
```

**The output of each stage is the input of the next stage**. This is not a parallel set of analysis tools, but a **nested observation structure**: Stage 1 turns system behavior into a graph, Stage 2 detects on the graph, Stage 3 verifies statistical regularities, Stage 4 makes statistical units explicit, Stage 5 replaces discrete labels with continuous coordinates, and Stage 6 extrapolates coordinates to external theories.

Below we explain each stage in turn.

---

## III. Stage 1: G2 Relation Graph Construction

### 3.1 What This Stage Does

After the first-order system `universe.py` runs for 10,000 iterations, it naturally produces "concept compression" events—whenever it discovers a set of tightly related concepts, it records them as a unit. Each compression is a record: `(center, {related_nodes})`.

This stage aggregates these events into an **undirected weighted graph G2**:

- Nodes = concepts
- Edges = "these two concepts appeared together in a compression event"
- Edge weights = co-occurrence count (clique mode: all unordered pairs within one compression event get +1, no normalization)

**Why undirected**: In a single static context, we cannot determine whether a compression is "center → members" or "members → center." The system only records the fact that "these concepts were compressed together." Directionality is deferred to Stage 4, derived from fixpoints.

**Why clique rather than star**: Multi-granularity compression is the system's真实 output. A compression of 5 concepts produces 10 edges, not 4. This is not redundancy; it is fidelity.

### 3.2 What This Stage Observes

Taking scale 51 as an example:
- 939 raw compression events → 51 nodes, 224 edges
- Maximum edge weight 341, mean 83.9

Taking scale 111 as an example:
- 133 raw compression events → 111 nodes, 66 edges
- Maximum edge weight 89, mean 27.4

**Key observation**: From 51 to 111, the number of events drops by 86%, the number of edges drops by 70%, but the mean edge weight drops even more (68%). This is consistent with §7.3 of the original paper—"compression density decreases with scale"—the system retains only the most necessary compressions at larger scales.

### 3.3 Data Files

| File | Content |
|------|---------|
| `results/compression_graph/raw_compression_events.csv` | **The sole data source**. Each row = one compression event |
| `results/compression_graph/compression_edges.csv` | Edge table of the relation graph |
| `results/compression_graph/summary.csv` | Per-scale summary |
| `results/compression_graph/pipeline_scale{N}.json` | Full JSON for a single scale |
| `results/compression_graph/graph_scale{N}.png` etc. | Visualizations |

---

## IV. Stage 2: Compression/Migration Candidate Detection

### 4.1 What This Stage Does

Two types of detection **fully consistent with the original paper** are performed on G2:

**Compression detection**: For each node as center, take its top-k neighbors to form a cluster, compute compression potential Φ = internal mean co-occurrence / external mean co-occurrence. When Φ exceeds an absolute threshold, it is recorded as a compression candidate.

**Migration detection**: Generate traversal histories through hard traversal + soft traversal; when the average co-occurrence count along a path exceeds an absolute threshold, it is recorded as a migration candidate.

**Why thresholds are absolute values**: For cross-scale comparability. No percentiles, no relative thresholds. The thresholds for scale 51 and scale 111 are the same.

**Why no pruning/deduplication**: Searches are performed on the complete graph, with no path deduplication and no subset deduplication. In reality, compression is inherently multi-granular; preserving subset relations is closer to the true cognitive state.

### 4.2 What This Stage Observes

Taking scale 111 as an example:
- 63 compression candidates, 0 migration candidates
- Migration threshold scan: cliff to zero at threshold 50

**Key observation**: The number of migrations at scale 111 drops to zero, consistent with the sharp decline in event count (133). This is not a problem with the detector; it is the system "no longer producing detectable migrations" under extreme complexity.

### 4.3 Data Files

| File | Content |
|------|---------|
| `candidate_compressions.csv` | Compression candidates (center/cluster/size/phi) |
| `candidate_migrations.csv` | Migration candidates (start/end/path/score) |
| `threshold_scan_compression.csv` | Compression threshold scan |
| `threshold_scan_migration.csv` | Migration threshold scan |

---

## V. Stage 3: Objective Metrics (Consistent with the Original Paper)

### 5.1 What This Stage Does

This stage is a **distribution-level verification** of the outputs from Stages 1–2. It reproduces the objective metrics from §7.8 / §7.10 of the original paper, but **the object of application has shifted**: the original paper's Zipf is "center node frequency," while this project's Zipf is "edge co-occurrence frequency." This shift is deliberate—it tests "whether the relation graph itself also obeys Zipf."

Four types of metrics:

- **Energy power law**: `E(t) = at⁻ᵇ + c`, fitting the energy decline curve
- **Zipf (three types)**: edge co-occurrence / center frequency / node total frequency
- **Φ distribution**: mean, standard deviation, quantiles of compression potential
- **Threshold scan**: sensitivity of compression/migration

**Why these metrics matter**: They provide **observation evidence independent of Stages 4–6**. Even if Stage 4's fixpoint detection has issues, Zipf and power laws remain evidence of the system's spontaneous regularities.

### 5.2 What This Stage Observes

- **Energy power law**: R² > 0.9999 for all four scales, with exponent b monotonically decreasing from 0.32 to 0.18
- **Edge Zipf**: slope −1.03 to −1.18 (deviating from the original paper's −1.36, but same direction)
- **Φ distribution**: mean monotonically increasing from 1.82 (scale 51) to 2.63 (scale 111), standard deviation increasing from 0.23 to 0.80
- **Threshold scan**: scale 111 drops to zero after compression threshold 2.25, migration threshold cliffs at 50

**Key observation**: The Φ mean monotonically increases with scale, consistent with the expectation that "large-scale systems have clearer boundaries and more severe differentiation." The Zipf slope deviates slightly, possibly due to the different statistical objects of "edge co-occurrence" vs. "center frequency"; this deviation itself is a reportable phenomenon, not a defect.

### 5.3 Data Files

| File | Content |
|------|---------|
| `power_law.csv` | Energy power law fitting |
| `zipf_edges.csv` / `zipf_centers.csv` / `zipf_node_totals.csv` | Three types of Zipf |
| `potential.csv` | Φ distribution statistics |
| `threshold_scan_{compression,migration}.csv` | Threshold scans |

---

## VI. Stage 4: Fixpoint Detection and Structured Definitions

### 6.1 What This Stage Does

**This is the turning point of the entire project**. The first three stages do "statistics"; Stage 4 begins **making statistical units explicit**.

**Fixpoint** = a **stable unit** identified from compression events. It satisfies:
- Sufficiently frequent in events (high support)
- Indivisible (no more frequent proper subset)
- Stable member roles (high role consistency)

This stage provides **three independent fixpoint detection methods**, sharing the same power set enumeration but with completely independent filtering rules and parameters:

| Method | Search space | Filtering rules | Semantics |
|------|---------|---------|------|
| **A** | Power set, `size = minsize..fp_max_itemset_size` | `support ≥ fp_min_support`, no lower-bound filtering, no role purity filtering | Frequent itemset closure; `size=1` is atomic fixpoint candidate, `size>1` is high-frequency whole candidate at the raw event level |
| **B** | Power set | `support ≥ lattice_min_support` + lower-bound filtering | Minimal frequent itemset candidate (indivisible) |
| **C** | Power set | `support ≥ role_min_support` + lower-bound filtering + role consistency ≥ `role_min_stability` | Role-pure candidate (functionally single) |

**The semantics of the three methods must be read separately**:

- **A**: Enumerates all frequent itemsets with `size = minsize..fp_max_itemset_size` under `support ≥ fp_min_support`. `minsize` is the enumeration lower bound, not the unique size. A does no lower-bound filtering and no role purity filtering.
  - A's `size=1` output is **atomic fixpoint candidates**: single concepts, writable as concept cards, corresponding to base node candidates for subsequent concept graphs.
  - A's `size>1` output is **high-frequency whole candidates at the raw event level**: multi-concept combinations with `core/boundary/logic/energy/phi`, writable as composite concept cards; but they necessarily contain frequent proper subsets, so they are not "indivisible atoms" but rather "candidates for the whole as a concept."
- **B**: Under `support ≥ lattice_min_support`, retains itemsets that have no frequent proper subsets, i.e., minimal frequent itemsets. B's `size=1` output is single-concept minimal frequent unit candidates.
- **C**: On top of B, additionally requires the average member role consistency ≥ `role_min_stability`, i.e., role-pure candidates. C's `size=1` output is single-concept role-pure atomic candidates.

**Set relations**: C ⊂ B ⊂ A holds only when support thresholds are aligned. The current three `fixpoints.json` files have different support thresholds (A uses `fp_min_support`, B uses `lattice_min_support`, C uses `role_min_support`), so file-based set inclusion verification cannot be done directly.

**The `minsize` semantics of Method A**: A outputs with different `minsize` are truncations of the same frequent itemset closure by size lower bound. `minsize=2` removes size=1, retaining size≥2; `minsize=3` removes size=1, 2, retaining size≥3. For the same itemset with `size≥minsize`, `support`, `phi`, `boundary/logic/energy` do not change with `minsize`.

**A's unique observable**: A's `size≥2` itemsets carry `phi = internal mean co-occurrence / external mean co-occurrence`; B/C have `phi=null` under `minsize=1`. Therefore A is the only method providing the distribution of compression potential at the composite level.

**Key design: Role consistency**. The original paper uses positional stability `S(x) = 1 − std(rank)/mean(rank)`, which explodes numerically when `mean → 0`—any concept that "occasionally acts as a member" has S collapse to 0, causing the entire group to be rejected. This project replaces it with:

```
role(x) = max(n_center, n_member) / (n_center + n_member)   ∈ [0.5, 1.0]
```

All-center → 1.0; all-member → 1.0; 50/50 → 0.5. Symmetric, bounded, no numerical explosion.

### 6.2 Structured Definitions

Each fixpoint carries five fields:

```json
{
  "core": ["fixpoint members"],
  "boundary": ["edge concepts pointing to the core"],
  "logic": {"edge concept": 0.85},
  "energy": {"edge concept": 0.31},
  "sources": ["supporting event IDs"]
}
```

**This is not a new mechanism; it is the definition form itself**. The original paper's definition form is a string (`"Newton's laws": "fundamental laws of object motion…"`); this project upgrades the definition form to a structure. "Description" is not an additional action performed by the system; it is an inherent property of the definition form.

### 6.3 What This Stage Observes

Taking scale 51, config_A as an example, Method A's output count varies with different `minsize`, but these are not three independent methods—they are different size lower-bound views of the same closure:

| Output | Meaning | Note |
|------|---------|------|
| C | Role-pure atomic candidates | C/B ratio 58.1% |
| B | Minimal frequent unit candidates | — |
| A-minsize1 | Includes `size=1` atomic fixpoint candidates + `size>1` high-frequency whole candidates | Full closure view |
| A-minsize2 | Retains only `size≥2` high-frequency whole candidates | Removes `size=1` |
| A-minsize3 | Retains only `size≥3` high-frequency whole candidates | Removes `size=1`, `2` |

**Key observations**:

- B and C's `minsize` parameter does not participate in the main search space; their main filtering is lower-bound and role purity; A's `minsize` directly determines the enumeration lower bound.
- A's `size=1` and B's `size=1` are semantically close, but A does no lower-bound filtering, so A retains all frequent itemsets; B retains only lower-bound itemsets.
- A's `size>1` is not a "larger-granularity version" of B/C, but rather the composite layer that B/C will not output due to lower-bound filtering. They carry `phi` and are A's unique observation window.
- In Stages 5–6 of this repository, only `minsize=1` A/B/C outputs are used; A outputs with `minsize>1` are retained as observation data for "high-frequency whole candidates at the raw event level" and do not enter the four-dimensional space or convexity testing.
- When support thresholds are aligned, C ⊂ B holds strictly, differing by 1–16.

**Key observation (cross-concept-set)**: This project introduces **three concept sets** for comparison:

- **config_A** (cross-domain): Physics + Mathematics + CS + AI + Cognition + Neuroscience + Philosophy + Economics + Engineering + Principles, 120 concepts in total
- **config_B** (CS single-domain): Algorithms + Theory + Languages + Systems + Networks + Databases + AI + Software Engineering + Security, 120 concepts in total
- **config_C** (Mathematics single-domain): Logic + Number Systems + Algebra + Analysis + Geometry + Topology + Number Theory + Applied Mathematics, 120 concepts in total

The C/B ratios of the three concept sets exhibit three different trajectories:
- A: Monotonic increase (0.58 → 0.72 → 0.75 → 0.92)
- B: U-shaped (0.76 → 0.70 → 0.61 → 0.85)
- C: n-shaped (0.52 → 0.58 → 0.76 → 0.66)

**This is not noise; it is a direct reflection of three "concept addition orders"**: A is cross-domain breadth gradually pieced together, B is subdomain blocks added in order, C is mathematical hierarchy progression.

### 6.4 Data Files

| File | Content |
|------|---------|
| `endo_result/endo_summary.csv` | Summary across config/scale/minsize/method |
| `endo_result/scale{N}/config_{X}/minsize_{K}/fixpoint_{M}/fixpoints.json` | Fixpoint lists |
| `.../concept_structure.json` | Structured definitions |
| `.../logic_edges.csv` | Directed logic edges |
| `.../edge_weights.csv` | Multi-channel + higher-order corrected edge weights |
| `.../run_meta.json` | Reproducibility metadata |
| `.../data_analysis/` | Analysis notes and background explanations |

---

## VII. Stage 5: Four-Dimensional Concept Space

### 7.1 What This Stage Does

The fixpoints output by Stage 4 are **discrete labels** ("this belongs to C, that belongs to B−C"). But discrete labels have a fundamental problem: **boundaries cannot be handled**. If a concept "sometimes acts as center and sometimes as member," is it C or B−C? What is the difference between thresholds 0.7 and 0.71?

This stage replaces discrete labels with **four-dimensional continuous coordinates**:

| Dimension | Meaning | Source |
|------|------|------|
| **b** | B membership = support (frequency of appearance in compression events) | `raw_events` statistics |
| **c** | C membership = role consistency (`max(n_center, n_member)/total`) | Same as above |
| **g1** | Degree of minimization in the G1 energy graph (z-score) | `g1_export` |
| **g2** | Centrality in the G2 relation graph (z-score) | `raw_events` reconstruction |

**This is not introducing new dimensions; it is unfolding existing dimensions from "binary" to "continuous"**. `in_B ∈ {True, False}` becomes `b ∈ [0, 1]`; `in_C ∈ {True, False}` becomes `c ∈ [0.5, 1]`; `g1 > 0 / g2 > 0` becomes retained z-scores.

**Why G1 uses energy semantics rather than topological semantics**: G1 is an approximately fully connected graph. On this graph, all nodes have degrees close to n−1, so "degree" and "centrality" have no discriminative power. A node's "importance" is not reflected in "how many edges it connects" but in **to what degree its edge-weight energy has been minimized**. Therefore G1's positive signal starts from energy semantics: node mean edge weight (low = frequently learned), edge weight drop magnitude (large = learned a lot), traversal frequency (high = frequently activated).

### 7.2 What This Stage Observes

**The most important observation: PC1 is the C axis**. Across 12 (config, scale) combinations, the first principal component is always "role convergence" (variance 67–75%), the second principal component is the G1/G2 joint axis, and the fourth principal component is the B axis. **This means: the largest difference between concepts comes from role consistency, not structural stability.**

**Why B is PC4**: B's variance is small, not because B is unimportant, but because B is a "scarce resource"—only a few concepts can become minimal frequent itemsets. This scarcity itself is the statistical expression of "limited stable cores."

**The three concept sets have different coupling structures**:

| config | corr_b_c vs. scale | corr_b_g1 | corr_c_g2 |
|--------|------------------|-----------|-----------|
| A | Decreasing (0.72 → 0.35) | High (0.3–0.67) | Negative (−0.44) |
| B | Fluctuating (0.81 → 0.56 → 0.95) | Approaching 0 | Negative (−0.24) |
| C | Increasing (0.50 → 0.97) | Low (0.1–0.27) | Near 0 |

**These are not three "layers"; they are three "general-layer formation mechanisms"**: A picks up general quantities through energy (G1), B through the relation graph (G2), C through structural position.

### 7.3 Data Files

| File | Content |
|------|---------|
| `four_dim_vectors/config_{X}/scale{N}.csv` | Four-dimensional coordinates (one row per concept) |
| `.../scale{N}_pca.csv` | PCA decomposition (PC1 = C axis) |
| `.../scale{N}_knn.csv` | 4D kNN neighbors |
| `four_dim_vectors/all_summary.csv` | Cross config/scale descriptive statistics + correlation matrices + PCA variance |
| `g1_export/config_{X}/scale{N}/g1_nodes.csv` | G1 node-level aggregation (for g1_z) |
| `g1_export/config_{X}/scale{N}/g1_edges.csv` | G1 edge table |
| `g1_export/config_{X}/scale{N}/energy_history.csv` | Global energy series |
| `g1_export/config_{X}/scale{N}/traversal_freq.csv` | Node traversal frequency |

---

## VIII. Stage 6: Convexity Testing (Dialogue with Concept Space Theory)

### 8.1 What This Stage Does

The first five stages are all within the framework of the original paper. Stage 6 is the first **extrapolation to external theories**.

Gärdenfors's concept space theory claims that "concept regions are convex." This claim has undergone a key shift in the literature: from "necessary constraint" to "testable prediction." Gärdenfors himself explicitly states: "The convexity criterion is not proposed as something that must necessarily hold for some application, but as a testable prediction. If it were guaranteed to hold, it would have no empirical content."

This project grounds this "testable prediction" in the four-dimensional concept space. **Two types of tests**:

**Self-test version**: Build a convex hull using expert points, then test expert points against themselves. Outputs:
- `expert_mean_convexity_ratio` (average distance ratio of expert points to their own convex hull)
- `general_outside_fraction` (fraction of general points outside the expert convex hull)
- `volume_ratio` (expert convex hull volume / full convex hull volume)

**Holdout version**: Build a convex hull using half of the expert points, test the other half + all general points for position. Outputs:
- `test_expert_inside_fraction` (fraction of held-out expert points inside the training convex hull)
- `general_inside_fraction` (fraction of general points inside the training convex hull)
- `separation = test_inside − general_inside`

**Why two versions are needed**: All "approximately 1.0" values in the self-test version are **reflexivity of the convex hull definition** (building a convex hull with experts and testing experts against themselves necessarily yields ≤ 1.0). `general_outside_fraction = 1.0` is a **necessary consequence of c-axis mutual exclusivity**. **Only the holdout version is a true test.**

**Why both 4D and 3D modes**: 4D includes the c dimension; experts and general points are mutually exclusive along the c axis, so the convex hulls necessarily do not intersect. After removing the c axis (3D mode `(b, g1, g2)`), the two have the possibility of geometric overlap, and `general_inside` has its first chance to be non-zero.

### 8.2 What This Stage Observes

**Core finding: The self-test version and the holdout version are two different universes.**

| Metric | Self-test version | Holdout version |
|------|--------|--------|
| `expert_inside` (4D) | **≈ 1.0** (identity) | **0.02 – 0.58** |
| `expert_inside` (3D) | **0.86 – 1.0** | **0.03 – 0.70** |
| `general_inside` (4D) | **0.0** (identity) | **0.0** (still identity) |
| `general_inside` (3D) | **0.0** | **0.0 – 0.24** |
| `separation` (3D) | ≈ 0 (meaningless for self-test) | **0.02 – 0.38** |

**Core conclusions of the holdout method**:

- **The expert layer is not strictly convex**. After holding out half, only 20%–35% of the other half falls inside the training convex hull. This is not "non-convex" (non-convex would be ≈ 0), nor "strictly convex" (strictly convex would be ≈ 1); it is **approximately convex** or **star-shaped approximation**.
- **The general layer partially mixes into the convex hull**. At b=0.02/0.05, about 20% of general points fall inside the expert convex hull. This indicates that the "expert vs. general" dichotomy is **not a hard boundary but a gradient band** geometrically.
- **Separation 0.07–0.38**. According to the previously set `separation > 0.5 strong separation`, no group reaches it. But `separation > 0.2` generally holds at b=0.0.

**Differences among the three concept sets**:

| config | `separation` (3D, c_hi=0.65, b_lo=0.1) | Interpretation |
|--------|---------------------------------------|------|
| Mathematics | **0.151** | Has clear family resemblance structure, approximately convex |
| Cross-domain | 0.083 | In between |
| CS | **0.036** | Interface/bridging, non-convex |

**config_B (CS) shows negative separation (−0.035, −0.048) at c_hi=0.65, b_lo=0.02/0.05**—general points are more likely to fall inside the convex hull than held-out expert points. This is a direct signal that "the CS expert layer is geometrically completely non-convex."

### 8.3 Dialogue with the Literature

| Literature | Empirical correspondence | Conclusion |
|------|---------|------|
| **Gärdenfors**: "Convexity is a testable prediction" | `test_inside` = 0.2–0.7, `separation` = 0.07–0.38 | Partially holds, not strict |
| **Hernández-Conde**: "Convexity as a necessary constraint is problematic" | Expert layer not strictly convex; 20% of general points mix into convex hull | Supports the critique |
| **Bechberger & Kühnberger**: "Replace with star-shaped sets" | `separation` = 0.07–0.38 corresponds to "has a core but is not strictly convex" | Supports star-shaped approximation |
| **Tětková et al.**: "Approximate convexity is ubiquitous" | `test_inside` 0.2–0.7 (not ≈ 1.0) | "Approximate" holds but strength is limited |
| **Jagiełło et al.**: "Concept fields can be non-convex" | config_B's negative separation (−0.05) | Directly supports non-convex concept fields |

**Comprehensive positioning**: **Convexity holds as an approximation, not as a strict constraint**. This falls exactly between Gärdenfors's "testable prediction" and Hernández-Conde's "necessary constraint critique." This project is not an "arbiter"; it is **making the conditions of arbitration themselves observable, reproducible, and evidence-based**.

### 8.4 Data Files

| File | Content |
|------|---------|
| `convexity_sweep/grids/grid_ALL.csv` | Self-test grid |
| `convexity_sweep/pivots/pivot_*_{3d,4d}.csv` | Self-test pivot tables |
| `convexity_sweep/holdout/grids/holdout_ALL.csv` | Holdout grid (★ core data) |
| `convexity_sweep/holdout/pivots/pivot_*.csv` | Holdout pivot tables |
| `convexity_sweep/holdout/pivots/pivot_separation_3d_{A,B,C}.csv` | Separation for three configs |
| `convexity_sweep/figures/` | 2D line plots / 2D heatmaps / 3D surfaces / density plots |

---

## IX. Auxiliary Data: G1 Export, Six Quadrants, Algebra Verification

### 9.1 G1 Export (`g1_export/`)

Provides data for Stage 5's `g1_z`. G1 is a fully connected energy graph; a node's importance is not "degree" but "to what degree its edge weights have been minimized." Four files:

- `g1_nodes.csv`: Node-level aggregation (mean_weight, min_weight, weight_drop, traversal_freq)
- `g1_edges.csv`: Edge table (weight, original_weight, traversal_count, similarity)
- `energy_history.csv`: Global energy series
- `traversal_freq.csv`: Node traversal frequency

**This is not an independent stage; it is an input to Stage 5**.

### 9.2 Six Quadrants (`six_quadrant_results/`, historical)

The six quadrants are an **intermediate product of the project's methodological evolution**. It divides each concept into six discrete quadrants by `(G1 strong/weak, G2 strong/weak, in_B, in_C)` (meta-concept/general layer/expert layer/compression product/background path/background catalog).

**It exposed the fundamental problem of discretization**: A@111's principles (transformation, iteration, abstraction) are neither in the meta-concept quadrant (because they are in B/C) nor in the expert layer quadrant (because G2 is negative), falling into "unclassified." **Meta-concepts falling into "unclassified" is not a classification failure; it is that the discrete boxes are insufficient.**

Stage 5's four-dimensional continuous coordinates replaced the six quadrants. It is retained to **demonstrate methodological evolution**—not to preserve a "better method," but to preserve "the step from discrete to continuous."

### 9.3 Algebra Verification (`src/algebra/results/algebra/`)

Independent verification corresponding to the group theory section of §§4–5 of the original paper. Contains computation results for cognitive operation semigroups, Noether correspondence, orbit-stabilizer theorem, and Lie group evolution. **It is not on the logic chain of "relation graph → fixpoint → four-dimensional space → convexity"**; it is a parallel branch of "algebraic structure verification."

---

## X. Possible Contributions

Under the positioning of a "second-order observation layer," this project may provide the following contributions:

### 10.1 Formalization Contribution: Making "Second-Order Observation" Computable

The original paper's "compression/migration" is an **observer's diagnostic tool**. This project formalizes this diagnostic tool itself into data objects:
- Compression events → G2 relation graph
- Relation graph → compression/migration candidates
- Event sequences → fixpoints
- Fixpoints → structured definitions
- Structures → four-dimensional coordinates

**Every step is computable, and every step's output is traceable**.

### 10.2 Methodological Contribution: Three Independent Fixpoint Detection Methods

The original paper's positional stability `1 − std/mean` is numerically unstable. This project replaces it with role consistency and implements three independent methods (A/B/C); when support thresholds are aligned, C ⊂ B ⊂ A is verifiable. **This is not a "better algorithm"; it is a "comparable granularity spectrum."** A's `size=1` is atomic fixpoint candidates, `size>1` is high-frequency whole candidates at the raw event level; B is minimal frequent itemset candidates; C is role-pure candidates.

### 10.3 Empirical Contribution: Three C/B Trajectories

The three concept sets give three different C/B trajectories (A monotonically increasing / B U-shaped / C n-shaped). This is not parameter noise; it is **a direct reflection of three "concept addition orders."** It provides a method for "measuring concept set structure using the C/B ratio."

### 10.4 Theoretical Contribution: From Discrete to Continuous

Four-dimensional continuous coordinates replace the six-quadrant discrete labels. PC1 = C axis (variance 67–75%) is the first time data answers "what is the largest difference between concepts." **This is not a "better classification"; it is "realizing that classification itself may be a redundant action."**

### 10.5 Literature Contribution: The First Operational Test of the Convexity Hypothesis

The holdout method makes Gärdenfors's convexity hypothesis measurable for the first time, turning it from philosophical debate into measurement: `test_inside` = 0.2–0.7, `separation` = 0.07–0.38. **The conclusion is not "support" or "oppose," but "providing the conditional spectrum of measurement"—under what conditions, for which point sets, and with what strength, convexity holds.**

---

## XI. Limitations and Boundaries

### 11.1 Limited Concept Set Size

120 concepts is still very small compared to real knowledge systems. Future expansion needs to incorporate knowledge bases such as WordNet and ConceptNet.

### 11.2 Single Static Context

This project is entirely in a single static context (consistent with the original paper). Multi-context coupling belongs to subsequent work.

### 11.3 Limitations of Convexity Testing

- **`gof` being always 1.0 in 4D mode is a definitional artifact**. This result has no empirical content.
- **Too few samples at b_lo=0.2** (n_expert often < 10), statistically unstable.
- **The holdout method is only "one" testing approach**. Other approaches (persistent homology, kernel density estimation) may give different numbers.

### 11.4 Structural Discontinuity at A@111

The flattening of A@111's principles (n_events plummeting from 897 to 133, PC1 loadings mixing in b) is not the fourth point of a natural trajectory but a structural discontinuity. **It should not be directly compared with 51/71/91.**

### 11.5 "Capturing the Essentials" Is Not "Concept Generation"

What this repository does is "capturing the essentials": identifying the stable units that the system repeatedly attends to from compression events, and assigning them structured definitions. Although the module name `endo_concept` is called "endogenous concept generation," within the scope of this repository it is still capturing the essentials—it outputs "the key units the system has already formed and their structured definitions," not what another project does—"making fixpoints into new nodes, constructing higher-level graphs, then compressing/migrating to reduce hierarchy."

Method A's `size=1` is atomic fixpoint candidates; `size>1` is high-frequency whole candidates at the raw event level. The latter can be written as composite concept cards and are candidates for "the whole as a concept," but they are not indivisible atoms, nor are they high-compactness wholes after hierarchy reduction. **Do not misread A's size>1 output as "new concepts have been generated"**—it is a candidate pool of "which wholes repeatedly appear in raw events and are worth entering the subsequent hierarchy-reduction process."

---

## XII. Quick Start

```bash
# 1. First-order system evolution, generating raw_compression_events.csv
python src/compression_graph/run_static.py

# 2. Objective metrics (consistent with the original paper)
python src/compression_graph/objective_metrics/run_all.py

# 3. Fixpoint detection (A/B/C three methods, multiple minsize)
python src/compression_graph/endo_concept/run_endo.py
# Note: minsize is only the enumeration lower bound for Method A; A outputs with different minsize are truncations of the same frequent itemset closure by size lower bound.
# Stages 5–6 use only minsize=1 A/B/C outputs; A outputs with minsize>1 are retained as observation data for "high-frequency whole candidates at the raw event level."

# 4. Export G1 energy graph
python src/compression_graph/endo_concept/g1_exporter.py --config A
python src/compression_graph/endo_concept/g1_exporter.py --config B
python src/compression_graph/endo_concept/g1_exporter.py --config C

# 5. Four-dimensional concept space
python src/compression_graph/endo_concept/continuous_vector.py --configs A B C

# 6. Convexity testing (self-test + holdout)
python src/compression_graph/endo_concept/continuous_vector.py \
    --method holdout --configs A B C --n-splits 20

# 7. Convexity visualization
python src/compression_graph/endo_concept/convexity_visualize.py --method holdout
```

**Dependencies**: `numpy`, `pandas`, `networkx`, `scipy`, `matplotlib`, `jieba`.

---

## XIII. One-Sentence Summary

**Building on the two postulates of *The Geometry, Algebra, and Dynamics of Cognition*, this project constructs a second-order observation mechanism: turning the system's compression behavior into a relation graph (Stage 1), detecting compression/migration on the graph (Stage 2), verifying statistical regularities (Stage 3), extracting fixpoints (Stage 4), mapping to a four-dimensional continuous space (Stage 5), and using the holdout method to perform the first operational test of the convexity hypothesis in concept space theory (Stage 6). The core findings are: discrete labels are insufficient; continuous coordinates are the truth; convexity holds as an approximation, not as a strict constraint; the three concept sets have different C/B trajectories, corresponding to three general-layer formation mechanisms. This is not "validating the original paper"; it is "extending the original paper's observations to deeper levels"—from system behavior to relation graphs, from statistics to structure, from discrete to continuous, from internal framework to external literature. Method A's `size=1` is atomic fixpoint candidates, `size>1` is high-frequency whole candidates at the raw event level; A is the only method providing the composite-layer `phi` distribution.**