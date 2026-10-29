# Compression Association Graph — Second-Order Observation Layer

This module **does not modify** any postulate of the original paper, nor does it change the behavior of `CognitiveUniverseEnhanced`. It does only one thing: aggregate the **concept compression events** produced by the original system into an **undirected weighted graph**, and then, on this graph, use detection mechanisms consistent with the original paper to detect **compression candidates** and **migration candidates**.

## Core Ideas

- A compression event `(center, {members})` is treated as an undirected clique; the co-occurrence count of every unordered pair within the clique is incremented by 1.
- The graph is **undirected**. Because in a single static context, we cannot determine whether a compression is "center → members" or "members → center." The system only records the fact that "these concepts were compressed together."
- Edge weight = **raw co-occurrence count**. No mapping, no cost, no normalization.
- Detection mechanisms are consistent with the original paper:
  - **Migration**: First generate traversal histories through hard traversal and soft traversal; when the average co-occurrence count along a path exceeds an **absolute threshold**, it is recorded as a migration candidate.
  - **Compression**: For each node as center, take its top-k neighbors to form a cluster; compression potential Φ = internal mean co-occurrence / external mean co-occurrence; when it exceeds an **absolute threshold**, it is recorded as a compression candidate.
- The detection results are **candidate concepts**; in a single static context they cannot be externally calibrated, so they are only statistical hypotheses.

**Relationship with Method A**: This module's `candidate_compressions.csv` contains compression candidates detected by Φ, not Method A's frequent itemset output. Method A's `fixpoints.json` is the frequent itemset closure obtained by enumerating `size=minsize..8` on `raw_compression_events.csv` under `support ≥ fp_min_support`.

- Method A's `size=1` outputs are atomic fixpoint candidates;
- Method A's `size>1` outputs are high-frequency whole candidates at the raw event level, carrying `phi`, but they are not indivisible atoms;
- The `phi` in this module's `candidate_compressions.csv` is the compression potential of a "compression candidate cluster," which is not the same layer of data as Method A's itemset `phi`; they cannot be directly mixed.

## Why the Design Is So Simple

- **Absolute thresholds**: No percentiles, so different scales are comparable.
- **No pruning**: Search is performed on the complete graph, consistent with the original paper.
- **No community detection**: That is not a mechanism of the original paper.
- **No cost mapping**: Edge weights are co-occurrence counts, not translated into energy.
- **No improvement ratio**: The original paper's migration criterion does not include this term.
- **No subset/path deduplication**: In reality, compression is inherently multi-granular; preserving subset relations is closer to the true cognitive state in a static context.

## Entry Point

    python compression_graph/run_static.py

## Outputs

Under the `results/compression_graph/` directory:

- `pipeline_scale{N}.json` — complete analysis for each scale
- `graph_scale{N}.png` — compression association graph
- `edge_dist_scale{N}.png` — edge co-occurrence distribution
- `migrations_scale{N}.png` — top migration paths highlighted

CSV tables:

- `summary.csv`                   — per-scale summary
- `raw_compression_events.csv`    — raw compression events
- `compression_edges.csv`         — each edge of the compression association graph
- `candidate_compressions.csv`    — compression candidates (candidate concepts — compression type)
- `candidate_migrations.csv`      — migration candidates (candidate concepts — migration type)

### Table Fields

**summary.csv**

| Column | Meaning |
|----|------|
| `scale` | Concept scale |
| `n_raw_compression_events` | Number of raw compression events (before deduplication) |
| `n_graph_nodes` | Number of graph nodes |
| `n_graph_edges` | Number of graph edges |
| `edge_count_max` | Maximum co-occurrence count |
| `edge_count_mean` | Mean co-occurrence count |
| `n_candidate_compressions` | Number of detected compression candidates |
| `n_candidate_migrations` | Number of detected migration candidates |

**raw_compression_events.csv**

| Column | Meaning |
|----|------|
| `scale` | Concept scale |
| `event_id` | Event ID |
| `detection_iteration` | Iteration step at which detection occurred |
| `center` | Center node selected by the detector |
| `cluster_size` | Cluster size |
| `related_nodes` | Related nodes (pipe-separated) |
| `emergence_strength` | Composite strength given by the original detector |

**compression_edges.csv**

| Column | Meaning |
|----|------|
| `scale` | Concept scale |
| `concept_a` | Concept A |
| `concept_b` | Concept B |
| `count` | Number of times A and B were compressed together |

**candidate_compressions.csv**

| Column | Meaning |
|----|------|
| `scale` | Concept scale |
| `rank` | Rank by Φ in descending order |
| `center` | Center node |
| `cluster` | All concepts in the cluster (pipe-separated) |
| `size` | Cluster size |
| `phi` | Compression potential Φ = internal mean co-occurrence / external mean co-occurrence |

**candidate_migrations.csv**

| Column | Meaning |
|----|------|
| `scale` | Concept scale |
| `rank` | Rank by mean co-occurrence in descending order |
| `length` | Number of path nodes |
| `start` | Start point |
| `end` | End point |
| `path` | Full path (arrow-separated) |
| `score` | Mean co-occurrence count along the path |

## Relationship with the Original Paper

| Original Paper | This Module |
|--------|--------|
| Energy on the cognitive graph | Co-occurrence count on the compression graph |
| Hard traversal / soft traversal | Hard traversal / soft traversal on the compression graph |
| Migration through principle nodes | Migration through intermediate paths |
| Compression potential Φ | Φ = internal mean / external mean |
| Center node frequency Zipf | Compression edge co-occurrence frequency Zipf |
| —— | Candidate concept statistics |

## Important Notes

- Candidates are **hypotheses**, not verified concepts. In a single static context they cannot be externally calibrated; they require manual review, naming, or downstream task validation.
- Method A's `size>1` frequent itemsets are likewise "high-frequency whole candidates," not "already generated new concepts." They have the `core/boundary/logic/energy/phi` structure and can be written as composite concept cards, but they necessarily contain frequent proper subsets, so they are not indivisible atoms.
- This module **does not backfill** the original paper's graph. Backfilling (outputs of Graph 2 entering Graph 1) belongs to the dynamic version and will be delivered later; the `endo_concept` in this repository also does not do this—it still only does "capturing the essentials."
- This module **does not** perform any "engineering" simplification: no pruning, no percentile thresholds, no community detection, no cost mapping, no improvement ratio. These decisions are made to maintain consistency with the original paper's simplicity and to faithfully present the assumption of "no external calibration in a static context" in the data.