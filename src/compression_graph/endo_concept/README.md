# Endogenous Concept Generation (endo_concept)

This module, **without introducing any new assumptions**, starts from the two postulates of the first-order cognitive graph and implements the "capturing the essentials" mechanism described in the task report: identifying stable units from compression events and assigning them structured definitions.

Note: This module is named `endo_concept`, but within the scope of this repository it **does not** perform the "concept-generation graph construction and hierarchy-reduction re-compression/migration" of another project. What it outputs is "the key units the system has already formed and their structured definitions," not the generation result of "making fixpoints into new nodes and constructing higher-level graphs."

## Module Structure

| File | Purpose |
|------|------|
| `config_endo.py` | Configuration: method selection, thresholds, weights |
| `fixpoint.py` | Fixpoint detection (Methods A / B / C / ABC) |
| `logic_derive.py` | Derive directed logic edges from fixpoints |
| `boundary.py` | Boundary characterization (Φ computation and statistics) |
| `structure.py` | Generate `CONCEPT_STRUCTURE` |
| `multichannel.py` | Multi-channel initial edge weights |
| `high_order.py` | Higher-order term internalization (rewriting the energy consumption formula) |
| `run_endo.py` | End-to-end entry point |

## Switching Fixpoint Detection Methods

Edit `config_endo.py`:

```python
"fixpoint_method": "A",   # "A" | "B" | "C" | "ABC"
```

- **A**: Frequent itemset enumeration. Under `support ≥ fp_min_support`, enumerate all itemsets with `size = minsize..fp_max_itemset_size`, with no lower-bound filtering and no role purity filtering.
  - `size=1`: Atomic fixpoint candidates.
  - `size>1`: High-frequency whole candidates at the raw event level; they carry `phi` and can be written as composite concept cards, but they are not indivisible atoms.
  - `minsize` is the enumeration lower bound: `minsize=1` outputs size=1..8; `minsize=2` outputs size=2..8; `minsize=3` outputs size=3..8. A outputs with different `minsize` are truncations of the same frequent itemset closure by size lower bound, not independent experiments.
- **B**: Minimal frequent itemsets. Under `support ≥ lattice_min_support`, retain lower-bound itemsets.
- **C**: Role-pure candidates. On top of B, additionally require the average member role consistency ≥ `role_min_stability`.
- **ABC**: The union of the three methods, each retaining its own filtering semantics before merging.

Joint criteria (`use_joint_criteria: True`) will additionally apply a hard support threshold and ranking on top of the selected method; for Method A, `apply_lower_bound=False`, meaning the joint criteria will not re-compress A into B.

## Running

First ensure the raw compression events of the first-order system have been produced (`run_static.py`), then:

```bash
cd compression_graph
python endo_concept/run_endo.py
```

## Outputs

Under the `results/compression_graph/endo_concept/` directory:

- `endo_summary.csv` — per-scale summary
- `scale{N}/fixpoints.json` — fixpoint list. For Method A: contains frequent itemsets with `size=minsize..8`; `size=1` are atomic fixpoint candidates, `size>1` are high-frequency whole candidates, and itemsets with `size≥2` carry `phi`. For Methods B/C: under `minsize=1`, typically outputs single-concept candidates with size=1 and `phi=null`.
- `scale{N}/logic_edges.csv` — directed logic edges
- `scale{N}/concept_structure.json` — structured definitions
- `scale{N}/edge_weights.csv` — multi-channel initial weights and higher-order corrected weights

## Correspondence with the Task Report

| Report Section | Implementation File |
|---------|---------|
| II. Energy consumption formula (multi-channel / higher-order terms) | `multichannel.py` / `high_order.py` |
| III. Boundary | `boundary.py` |
| IV. Logic | `logic_derive.py` |
| V. Fixpoints (A/B/C/joint criteria) | `fixpoint.py` |
| VI. Description (`CONCEPT_STRUCTURE`) | `structure.py` |
| VII. Definition form | `structure.py` |
| VIII. Endogenous concept generation pipeline | `run_endo.py` |

## How to Read Method A

Method A's output should be read as "the frequent itemset closure under the current `support` threshold":

- `size=1`: Atomic fixpoint candidates, corresponding to base node candidates for concept cards.
- `size>1`: High-frequency whole candidates at the raw event level. They have `core/boundary/logic/energy/phi` and can be written as composite concept cards; but they necessarily contain frequent proper subsets, so they are not indivisible atoms.
- `minsize`: Enumeration lower bound. `minsize=1` gives the complete view of "atoms + whole candidates"; `minsize=2` looks only at whole candidates with size≥2; `minsize=3` looks only at whole candidates with size≥3. Different `minsize` values are not different experiments; they are different size lower-bound views of the same closure.
- `phi`: Unique to A's `size≥2` itemsets; B/C have `phi=null` under `minsize=1`. A is the only method providing the composite-layer compression potential distribution.
- Set relations: C⊂B⊂A holds only when support thresholds are aligned; the current three `fixpoints.json` files have different support thresholds, so set inclusion verification cannot be done directly.

## Core Constraints (Unchanged)

1. Do not introduce new assumptions beyond the original first-order model.
2. Keep undirectedness as the foundation; directionality is derived only from fixpoints.
3. Thresholds use absolute values to maintain cross-scale comparability.
4. Description is an attribute of the definition form, not an action external to the system.
5. Method A's `minsize` is the enumeration lower bound, not "enumerate only that size." A outputs with different `minsize` are truncations of the same frequent itemset closure by size lower bound; for itemsets with `size≥minsize`, `support`, `phi`, and `boundary/logic/energy` do not change with `minsize`.
6. The `endo_concept` in this repository only does "capturing the essentials"; it does not do what another project does—"making fixpoints into nodes, constructing higher-level graphs, then compressing/migrating to reduce hierarchy." A's `size>1` are "high-frequency whole candidates at the raw event level," which are the input side of hierarchy reduction, not the output side of hierarchy reduction.