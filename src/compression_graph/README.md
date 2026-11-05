# Compression Association Graph — Second-Order Observation Layer

This module **does not modify** any postulate of the original paper, nor does it change the behavior of `CognitiveUniverseEnhanced`. It does only one thing: aggregate the **concept compression events** produced by the original system into an **undirected weighted graph**, and then, on this graph, use detection mechanisms consistent with the original paper to detect **compression candidates** and **migration candidates**.

**The second-order observation layer is specifically defined as**: the layer that does not modify the operating rules of the first-order system, but performs secondary statistics, structure identification, and candidate detection on the outputs (compression events) of the first-order system, and records the results as traceable data objects.

## Core Ideas

- **A concept compression event is specifically defined as**: a record `(center, {members})` that the system records in a certain detection, indicating that "these concepts were treated together as one unit by the system in this detection."
- A compression event `(center, {members})` is treated as an undirected clique; the co-occurrence count of every unordered pair within the clique is incremented by 1.
- **The compression association graph is specifically defined as**: a graph with concepts as nodes, "once appeared together in a compression event" as undirected edges, and co-occurrence count as edge weight.
- The graph is **undirected**. Because in a single static context, we cannot determine whether a compression is "center → members" or "members → center." The system only records the fact that "these concepts were compressed together."
- Edge weight = **raw co-occurrence count**. No mapping, no cost, no normalization.
- The detection mechanisms are consistent with the original paper:
  - **A migration candidate is specifically defined as**: first, traversal histories are generated through hard traversal and soft traversal; when the average co-occurrence count of a path exceeds an **absolute threshold**, it is recorded as a migration candidate. **Hard traversal / soft traversal are specifically defined as**: two traversal modes that advance deterministically / randomly along edge weights in the sense of the original paper; this module does not change their rules and only reuses their outputs.
  - **A compression candidate is specifically defined as**: for each node as center, take its top-k neighbors to form a cluster; the compression potential `Φ = internal mean co-occurrence / external mean co-occurrence`; when it exceeds an **absolute threshold**, it is recorded as a compression candidate. `Φ` is a ratio of edge-weight structure, not a semantic judgment of "degree of concept merging."
- **A candidate concept is specifically defined as**: the collective name for the above two types of candidates; it is a statistical hypothesis given by the detector on the edge-weight structure, not a validated concept. In a single static context, they cannot be externally calibrated, so they are only statistical hypotheses.

**Relationship to Method A**: The `candidate_compressions.csv` of this module contains compression candidates detected by Φ, not the frequent itemset outputs of Method A. Method A's `fixpoints.json` is the frequent itemset closure obtained by enumerating `size=minsize..8` on `raw_compression_events.csv` under `support ≥ fp_min_support`.

- Method A's `size=1` are atomic fixpoint candidates;
- Method A's `size>1` are high-frequency whole candidates at the raw event level, carrying `phi`, but they are not indivisible atoms;
- The `phi` in this module's `candidate_compressions.csv` is the compression potential of a "compression candidate cluster," and is not the same layer of data as Method A's itemset `phi`; the two cannot be directly mixed.

## Why the Design Is So Simple

- **Absolute thresholds**: no percentiles, so different scales are comparable.
- **No pruning**: search is performed on the complete graph, consistent with the original paper.
- **No community detection**: that is not the mechanism of the original paper.
- **No cost mapping**: edge weight is just co-occurrence count, not translated into energy.
- **No improvement ratio**: the original paper's migration criterion does not include this term.
- **No subset/path deduplication**: in reality, compression is inherently multi-granular; preserving subset relations is closer to the true cognitive state in a static context.

## Entry Point

    python compression_graph/run_static.py

## Outputs

Under the `results/compression_graph/` directory:

- `pipeline_scale{N}.json` — complete analysis for each scale
- `graph_scale{N}.png` — compression association graph
- `edge_dist_scale{N}.png` — edge co-occurrence distribution
- `migrations_scale{N}.png` — top migration path highlights

CSV tables:

- `summary.csv`                   — summary per scale
- `raw_compression_events.csv`    — raw compression events
- `compression_edges.csv`         — each edge of the compression association graph
- `candidate_compressions.csv`    — compression candidates (candidate concepts — compression type)
- `candidate_migrations.csv`      — migration candidates (candidate concepts — migration type)

### Fields of Each Table

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
| `event_id` | Event index |
| `detection_iteration` | Iteration step at which detection occurred |
| `center` | Center node selected by the detector |
| `cluster_size` | Cluster size |
| `related_nodes` | Related nodes (pipe-separated) |
| `emergence_strength` | Comprehensive strength given by the original detector |

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
| `rank` | Rank in descending order of Φ |
| `center` | Center node |
| `cluster` | All concepts in the cluster (pipe-separated) |
| `size` | Cluster size |
| `phi` | Compression potential Φ = internal mean co-occurrence / external mean co-occurrence |

**candidate_migrations.csv**

| Column | Meaning |
|----|------|
| `scale` | Concept scale |
| `rank` | Rank in descending order of mean co-occurrence |
| `length` | Number of nodes in the path |
| `start` | Start point |
| `end` | End point |
| `path` | Full path (arrow-separated) |
| `score` | Mean co-occurrence count of the path |

## Relationship to the Original Paper

| Original paper | This module |
|--------|--------|
| Energy on the cognitive graph | Co-occurrence count on the compression graph |
| Hard traversal / soft traversal | Hard traversal / soft traversal on the compression graph |
| Migration through principle nodes | Migration through intermediate paths |
| Compression potential Φ | Φ = internal mean / external mean |
| Center node frequency Zipf | Compression edge co-occurrence frequency Zipf |
| —— | Candidate concept statistics |

## Important Notes

- Candidates are **hypotheses**, not validated concepts. In a single static context, they cannot be externally calibrated and require manual review, naming, or downstream task testing.
- Method A's `size>1` frequent itemsets are likewise "high-frequency whole candidates," not "already generated new concepts." They have the `core/boundary/logic/energy/phi` structure and can be written as **composite concept cards**. **A composite concept card is specifically defined as**: a structured record that writes a multi-concept whole according to the fields `core/boundary/logic/energy/phi`; it indicates that "this whole repeatedly appears in raw events," not that "it has been reduced in hierarchy into a new node." It necessarily contains frequent proper subsets, so it is not an indivisible atom.
- This module **does not backfill** the original paper's graph. Backfilling (outputs of Graph 2 entering Graph 1) belongs to the dynamic version and will be delivered later; the `endo_concept` in this repository also does not do this—it still only does "capturing the essentials."
- This module **does not** perform any "engineering" simplification: no pruning, no percentile thresholds, no community detection, no cost mapping, no improvement ratio. These decisions are made to maintain consistency with the original paper's simplicity, and also to let the assumption "no external calibration in a static context" be faithfully presented in the data.