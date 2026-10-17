# Compression Graph — Second-order Observation Layer

This module does not modify the original Cognitive Graph Theory
postulates. It builds an undirected weighted graph from the
original system's compression events, and detects compression /
migration candidates on it, mirroring the original paper's
detection mechanism.

## Core Idea

- A compression event `(center, {members})` is treated as an
  undirected clique. Each unordered pair gets +1.
- The graph is undirected because, in a single static context,
  we cannot decide whether a compression is "center → member" or
  "member → center". Only the fact "these concepts were compressed
  together" is recorded.
- Edge weight = raw co-occurrence count. No mapping, no cost,
  no normalization.
- Detection mirrors the original paper:
  - **Migration**: build a traversal history via hard and soft
    walks; a path is a migration candidate if its average
    co-occurrence exceeds an absolute threshold.
  - **Compression**: for each center, take the top-k neighbors,
    compute Phi = internal_avg / external_avg; keep clusters
    whose Phi exceeds an absolute threshold.
- Both detection results are **statistical candidates**. They are
  not validated concepts.

## Design Choices (intentionally minimal)

- Absolute thresholds, not percentile: scales remain comparable.
- No pruning, no top-k neighbor restriction for search.
- No community detection.
- No cost mapping.
- No improvement ratio.
- No subset / path deduplication beyond exact duplicates.

## Entry point

    python compression_graph/run_static.py

## Output

`results/compression_graph/`:

- `pipeline_scale{N}.json` — full analysis per scale
- `graph_scale{N}.png`
- `edge_dist_scale{N}.png`
- `migrations_scale{N}.png`

CSV tables:

- `summary.csv`                   — per-scale summary
- `raw_compression_events.csv`    — raw compression events
- `compression_edges.csv`         — compression graph edges
- `candidate_compressions.csv`    — compression candidates
- `candidate_migrations.csv`      — migration candidates

## Relationship to the original paper

| Original paper              | This module                        |
|-----------------------------|-------------------------------------|
| energy on cognitive graph   | count on compression graph          |
| hard / soft traversal       | hard / soft walk on compression graph |
| migration via principle node | migration via intermediate path    |
| compression potential Phi   | Phi = internal / external           |
| Zipf of centers             | Zipf of edge co-occurrence          |
| —                           | concept candidate statistics        |

## Caveats

- Candidates are **hypotheses** in a single static context.
  They require external calibration before being called concepts.
- No feedback to the original graph is performed here. That is
  reserved for a future dynamic version.