# Endogenous Concept Generation (endo_concept)

Without introducing any new assumptions, this module starts from the two postulates of the first-order cognitive graph and implements the "capturing the essentials" mechanism described in the task report. **Capturing the essentials is specifically defined as**: identifying repeatedly occurring stable units from the compression events output by the first-order system, and assigning them structured definitions; it does not construct higher-level graphs, nor does it turn fixpoints into new nodes and then compress/migrate. 

Note: This module is named `endo_concept` ("endogenous concept generation"), but within the scope of this repository, it **does not** perform what another project does—"constructing a concept-generation graph and reducing hierarchy through re-compression/migration." What it outputs is "the key units the system has already formed and their structured definitions," not the generation result of "making fixpoints into new nodes and constructing higher-level graphs." In terms of actual mechanism, this module performs **fixpoint detection + structured definition**, not "concept generation."

**About the name**: Names such as `endo_concept` are merely **names used in the early experimental stage**. After it was subsequently determined that this module actually performs "capturing the essentials / fixpoint detection" rather than "concept generation," the ideal name should reflect this (for example, something like `fixpoint_detection`). However, because this name already appears in directory names, module import paths, configuration items, and a large number of result paths, renaming it would cause cumbersome chain modifications across the entire project, so **the original name is retained unchanged**. When reading this module, please take the actual mechanism (fixpoint detection + structured definition) as authoritative, not the "concept generation" in the name.

## Module Structure

| File | Purpose |
|------|------|
| `config_endo.py` | Configuration: method selection, thresholds, weights |
| `fixpoint.py` | Fixpoint detection (Methods A / B / C / ABC) |
| `logic_derive.py` | Derive directed logic edges from fixpoints |
| `boundary.py` | Boundary characterization (Φ computation and statistics) |
| `structure.py` | Generate `CONCEPT_STRUCTURE` |
| `multichannel.py` | Multi-channel initial edge weights |
| `high_order.py` | Higher-order term internalization (rewrite the energy consumption formula) |
| `run_endo.py` | End-to-end entry point |

## Switching Fixpoint Detection Methods

**A fixpoint is specifically defined as**: a stable unit identified from compression events that satisfies the following three conditions—(i) sufficiently frequent in events (high support); (ii) indivisible (no more frequent proper subset); (iii) stable member roles (high role consistency). A fixpoint is a **set**, not a node on a graph; its directionality exists only in the `logic` (core→boundary) derived from it, not in the set itself.

Edit `config_endo.py`:

```python
"fixpoint_method": "A",   # "A" | "B" | "C" | "ABC"
```

- **A**: Frequent itemset enumeration. Under `support ≥ fp_min_support`, enumerate all itemsets with `size = minsize..fp_max_itemset_size`; no lower-bound filtering and no role purity filtering.
  - `size=1`: Atomic fixpoint candidates.
  - `size>1`: High-frequency whole candidates at the raw event level; they carry `phi`, can be written as composite concept cards, but are not indivisible atoms.
  - `minsize` is the enumeration lower bound: `minsize=1` outputs size=1..8; `minsize=2` outputs size=2..8; `minsize=3` outputs size=3..8. A outputs with different `minsize` are truncations of the same frequent itemset closure by size lower bound, not independent experiments.
- **B**: Minimal frequent itemsets. Under `support ≥ lattice_min_support`, retain lower-bound itemsets.
- **C**: Role-pure candidates. On top of B, additionally require the average member role consistency ≥ `role_min_stability`.
- **ABC**: The union of the three methods, each retaining its own filtering semantics before merging.

The joint criteria (`use_joint_criteria: True`) will additionally execute a support hard threshold and ranking on top of the selected method; for Method A, `apply_lower_bound=False`, i.e., the joint criteria will not re-compress A into B.

## Running

First ensure that the raw compression events of the first-order system have been produced (`run_static.py`), then:

```bash
cd compression_graph
python endo_concept/run_endo.py
```

## Outputs

Under the `results/compression_graph/endo_concept/` directory:

- `endo_summary.csv` — summary per scale
- `scale{N}/fixpoints.json` — fixpoint list. For Method A: contains frequent itemsets with `size=minsize..8`; `size=1` are atomic fixpoint candidates, `size>1` are high-frequency whole candidates, and itemsets with `size≥2` carry `phi`. For Methods B/C: under `minsize=1`, usually outputs single-concept candidates with size=1, `phi=null`.
- `scale{N}/logic_edges.csv` — directed logic edges
- `scale{N}/concept_structure.json` — structured definitions
- `scale{N}/edge_weights.csv` — multi-channel initial weights and weights after higher-order correction

Where:

- **A directed logic edge is specifically defined as**: an edge from the `core` of a fixpoint to its `boundary`, with weight taken from the strength given by the `logic` field; it carries directionality and is the layer of structure derived from fixpoints on top of the undirected substrate.
- **A structured definition (`concept_structure.json`) is specifically defined as**: a structured record that writes a fixpoint according to the five fields `core / boundary / logic / energy / sources`; it is the definition form itself, not an additional action performed by the system.
- **Multi-channel initial edge weights are specifically defined as**: combining three signals—`sim` (semantic similarity), `logic` (directed logic strength), and `energy` (energy semantics)—according to configured weights into one initial edge weight, for subsequent higher-order term internalization by `high_order.py`.

## Correspondence with the Task Report

| Report Section | Implementation File |
|---------|---------|
| II. Energy consumption formula (multi-channel / higher-order terms) | `multichannel.py` / `high_order.py` |
| III. Boundary | `boundary.py` |
| IV. Logic | `logic_derive.py` |
| V. Fixpoint (A/B/C/joint criteria) | `fixpoint.py` |
| VI. Description (`CONCEPT_STRUCTURE`) | `structure.py` |
| VII. Definition form | `structure.py` |
| VIII. Endogenous concept generation process | `run_endo.py` |

## How to Read Method A

The output of Method A should be read as "the frequent itemset closure under the current `support` threshold":

- `size=1`: Atomic fixpoint candidates, corresponding to base node candidates for concept cards.
- `size>1`: High-frequency whole candidates at the raw event level. They have `core/boundary/logic/energy/phi` and can be written as composite concept cards; but they necessarily contain frequent proper subsets, so they are not indivisible atoms. **A composite concept card is specifically defined as**: a structured record that writes a multi-concept whole according to the fields `core/boundary/logic/energy/phi`; it indicates that "this whole repeatedly appears in raw events," not that "it has been reduced in hierarchy into a new node."
- `minsize`: Enumeration lower bound. `minsize=1` gives the complete view of "atoms + whole candidates"; `minsize=2` looks only at whole candidates with size≥2; `minsize=3` looks only at whole candidates with size≥3. Different `minsize` values are not different experiments; they are different size lower-bound views of the same closure.
- `phi`: Unique to A's `size≥2` itemsets; B/C have `phi=null` under `minsize=1`. A is the only method providing the distribution of compression potential at the composite level.
- Set relations: C⊂B⊂A holds only when support thresholds are aligned; the current three `fixpoints.json` files have different support thresholds, so set inclusion verification cannot be done directly.

## Core Constraints (Remain Unchanged)

1. Do not introduce new assumptions beyond the original first-order model.
2. Maintain undirectedness as the substrate; directionality is derived only from fixpoints.
3. Thresholds use absolute values to maintain cross-scale comparability.
4. Description is an attribute of the definition form, not an action outside the system.
5. Method A's `minsize` is the enumeration lower bound, not "enumerate only that size." A outputs with different `minsize` are truncations of the same frequent itemset closure by size lower bound; the `support`, `phi`, and `boundary/logic/energy` of itemsets with `size≥minsize` do not change with `minsize`.
6. The `endo_concept` in this repository only does "capturing the essentials"; it does not do what another project does—"turn fixpoints into nodes, construct higher-level graphs, then compress/migrate to reduce hierarchy." A's `size>1` are "high-frequency whole candidates at the raw event level"; they are the input end of hierarchy reduction, not the output end of hierarchy reduction.