# 🧠 Cognitive Graph Theory

## 📖 Project Introduction

This is a cognitive computing framework based on the principle of energy minimization, using graph theory to describe knowledge structures, group theory to analyze cognitive operations, and dynamics to simulate the evolution of thought. This project includes a complete theoretical model, rigorous algebraic verification experiments, and systematic computational experiments across four scales, from 51 to 111 concepts. The core finding indicates that minimizing cognitive energy consumption is the first principle driving the natural emergence of concept compression and principle transfer. Across different levels of knowledge complexity, the system exhibits adaptive laws highly consistent with human cognition.

This work was completed independently by a second-year undergraduate student. The core ideas originated from introspection and abstraction of the author's own thought processes and were subsequently validated through computational experiments. The conclusions resonate deeply in principle with current cutting-edge research directions such as embodied intelligence and the free energy principle.

The core contributions of this project are:

*   **Integration of Multidisciplinary Concepts:** It integrates concepts from cognitive science, mathematical physics, and computer science to provide a unified explanatory framework for knowledge representation, learning, and creative thinking.
*   **Discovery of Novel Cognitive Laws:** Through simulation experiments at four scales (51/71/91/111 concepts), phenomena highly consistent with human learning trajectories were observed, such as the sharp decline in concept compression density with increasing knowledge scale and a strategic phase transition at 111 concepts.
*   **Complete Code Verification:** The implementation relies solely on fundamental scientific libraries (numpy/networkx, etc.) with no black-box dependencies. All phenomena are reproducible and traceable.
*   **Practical Application Exploration:** An additional personalized education prototype system based on this theory acquires cognitive parameters through questionnaires, drives the evolution of cognitive networks, and provides adaptive suggestions for learners (see the 'Personalized Education Experiment Based on Cognition' repository).

---

## Core Ideas and Methods

### Two Fundamental Postulates of Cognitive Graph Theory

1.  **Cognitive Space-Time (Geometric Description)**
    The cognitive state can be represented as a dynamic graph $G(V,E,t)$, where nodes $V$ are concepts, edges $E$ are associations between concepts, and edge weights represent cognitive energy consumption $E_{ij}(t)$. The geometric properties of the network (degree distribution, clustering coefficient, path length, modularity) characterize the knowledge structure.

2.  **Energy Dynamics (Driving Mechanism)**
    System evolution is driven by the minimization of energy consumption. The cognitive energy function is defined as:
    $E_{ij}(t) = \alpha \cdot (1 - \text{sim}_{ij}) + \beta \cdot \frac{1}{1 + H_{ij}(t)} + \gamma \cdot \text{div}_{ij}$
    where $\text{sim}_{ij}$ is semantic similarity, $H_{ij}(t)$ is historical proficiency (simulating forgetting and learning), and $\text{div}_{ij}$ is structural dissimilarity. The system repeatedly "traverses" (cognitive operations) to reduce the global cognitive free energy $F(G)$, thereby self-organizing and evolving.

### Emergent Phenomena

Starting from these two simple postulates, the system spontaneously produces two macroscopic behaviors highly consistent with human cognition:

*   **Concept Compression:** When a group of concepts is frequently co-activated and has high energy costs for external connections, the system compresses them into a macro-node, significantly reducing global energy consumption. For example, "algorithm + neural network + machine learning" ultimately emerges as the higher-order concept "reinforcement learning".
*   **First Principles Transfer:** Low-energy shortcuts are established through highly universal principle nodes (e.g., "pattern recognition," "optimization"), enabling cross-domain mental leaps. For instance, the transfer path "developmental psychology → pattern recognition → metacognition" simulates the creative process of analogical reasoning.

### Algebraic Structure (Theoretical Deepening)

To provide a rigorous mathematical foundation for cognitive operations, we introduce group-theoretic structures:
*   Basic cognitive operations (traverse, learn, forget, compress, transfer) form a **semigroup**, satisfying closure and associativity.
*   The **cognitive symmetry group** $\mathcal{G}$ characterizes the invariance of the network. A Noether-type proposition suggests that continuous symmetries correspond to conserved quantities (e.g., energy, structural entropy).
*   Continuous-time evolution can be described by the **Lie group equation** $\frac{dG(t)}{dt}=A(t)G(t)$, providing a theoretical tool for analyzing the smoothness of cognitive processes.

Algebraic verification experiments (5 sets) confirmed the computational feasibility of the above structures (see Section 5 of the paper and the `src/algebra/` module), although rigorous mathematical derivation is still needed for strict confirmation.

---

## Main Findings and Experimental Results

We conducted systematic comparative experiments on networks of 51, 71, 91, and 111 concepts, covering interdisciplinary knowledge from physics, mathematics, computer science, and cognitive science. Each scale underwent 10,000 iterations. The experiments compared four paradigms: Random Network Baseline, Simple Q-learning, Preset Algorithm Model (simulating traditional cognitive computing), and Natural Emergence Model (our model).

### Objective Metrics for Quantitative Validation
To strengthen the empirical foundation of the model, we compute a set of objective, reproducible metrics that characterize the system’s macroscopic behavior and its sensitivity to key parameters:

* **Compression threshold scan:** Sweep the compression synergy threshold (0.5–0.9) and count detected compressions to verify that observed phenomena are not artifacts of a single threshold choice. (See `src/analysis/threshold_scan.py`, results in `results/analysis/add_scan/`.)
* **Compression potential:** For each compression event, compute the ratio of internal to external average energy (Φ) and analyze its distribution across scales. (See `src/analysis/run_potential_analysis.py` / `src/analysis/run_potential_analysis_en.py`, results in `results/analysis/potential_analysis/`.)
* **Energy decline rate fitting:** Fit the energy trajectory over iterations to power-law / exponential curves, extracting decay exponents and fit quality to quantify how efficiently the system minimizes energy. (Implemented in the analysis module; results in `results/analysis/objective_metrics/`.)
* **Zipf-like frequency distribution:** Test whether the frequency of concept participation in compression events follows a Zipf/power-law distribution, analogous to word-frequency laws in human language. (Also part of the analysis pipeline.)

### Energy Optimization Performance

| Concept Scale | Natural Emergence Model | Preset Algorithm Model | Relative Advantage |
| :------------ | :---------------------- | :--------------------- | :----------------- |
| 51 concepts   | **86.9%**               | 22.8%                  | +64.1%             |
| 71 concepts   | **72.3%**               | 15.5%                  | +56.8%             |
| 91 concepts   | **61.4%**               | 12.2%                  | +49.2%             |
| 111 concepts  | **47.9%**               | 7.6%                   | +40.3%             |

*   The **Natural Emergence Model** significantly outperformed other paradigms at all scales and exhibited the smallest decay with scale (45.6%), demonstrating strong robustness.
*   The performance of the **Preset Algorithm Model** declined sharply with scale (67.1% drop), exposing the limitations of preset rules in complex cognitive environments.

### Scale Adaptation of Concept Compression

| Scale | Total Compressions | Compressions per Concept | Emergence Intensity Range |
| :---- | :----------------- | :----------------------- | :------------------------ |
| 51    | 466                | 9.14                     | 0.79–0.84                 |
| 71    | 332                | 4.68                     | 0.78–0.84                 |
| 91    | 301                | 3.31                     | 0.81–0.84                 |
| 111   | 43                 | 0.39                     | 0.78–0.97                 |

*   **Compression density drops sharply** (9.14 → 0.39), perfectly simulating the cognitive development trajectory from a beginner's broad connection-building to an expert's deep, precise integration.
*   **A critical phenomenon appears at 111 concepts:** The number of compressions plummets by 85.7%, and the system's strategy shifts from exploratory integration to conservative maintenance, reflecting intelligent management of cognitive load.

### Creative Simulation of Principle Transfer

*   **Transfer Counts:** 0 times at 51 concepts, 3 times each at 71/91 concepts, only 1 time at 111 concepts.
*   **Transfer Efficiency:** Average 0.35–0.45, with a maximum of 0.449 (at 91 concepts).
*   **Hub Node:** "Pattern recognition" appeared in 6 out of 7 transfers, proving that abstract principles serve as bridges for cross-domain thinking.
*   **Transfer Path Stability:** Identical paths recurred across different scales (e.g., "developmental psychology → pattern recognition → metacognition"), validating their effectiveness.

These phenomena closely align with Wallas's four-stage model of creative thinking (Preparation, Incubation, Illumination, Verification), offering a new perspective for computational modeling of creativity.

### Algebraic Verification Experiments
*   **Cognitive Operation Semigroup:** Verified that 13 basic cognitive operations (traverse/learn/forget/compress/transfer) satisfy associativity under composition.
*   **Noether-type Proposition:** Detected trends toward conservation of quantities like global energy and structural entropy in three networks with different structures, supporting the idea of symmetries corresponding to conserved quantities.
*   **Orbit-Stabilizer Theorem:** Confirmed the relationship between orbit size and stabilizer size in the cognitive state space (although high network personalization resulted in zero isomorphisms, the theorem holds in trivial cases).
*   **Lie Group Evolution Demonstration:** Showcased the feasibility of continuous-time cognitive evolution, with different generator combinations leading to varying energy optimization effects (energy-dominant strategy reduced consumption by 37.8%).

### Visualizing Cognitive Graph Evolution
![71‑concept scale animation](results/Fresults/animations/cognitive_anim_dynamic_71c_ind0_20260406_190427.gif)

#### Visual Legend of the Cognitive Animation

| Element | Color / Style | Meaning |
|---------|---------------|---------|
| **Node** | Light blue circle, black border | Represents a concept (e.g., "algorithm", "neural network", "energy conservation") |
| **Node label** | Black text | Name of the concept |
| **Ordinary edge** | Blue‑green → red‑purple gradient, variable thickness | Cognitive association between concepts. **Color**: Blue‑green = low cognitive energy (well learned), red‑purple = high energy (unfamiliar). **Thickness**: Thicker = higher energy (resistance), thinner = lower energy (fluent) |
| **Hard traversal path** | Blue solid arrow | System performs “hard traversal” – follows existing low‑energy paths for efficient, deterministic cognition, consolidating known knowledge |
| **Soft traversal attempts** | Orange dashed arrows | Multiple directions explored during soft traversal, reflecting exploration |
| **Soft traversal chosen path** | Red solid arrow | Final path selected after soft traversal, used to explore new associations or cross‑domain connections |
| **Highlighted node** | Yellow circle, black border | Node currently visited on the traversal path – the concept being activated/accessed |
| **Title bar** | Text at top‑left | Current iteration number and global average energy of the network |

- Edge colors and thicknesses change dynamically with iterations, reflecting how cognitive energy evolves through learning/forgetting.
- Hard traversal normally follows a single path (blue solid arrow); soft traversal first tries several directions (orange dashed arrows) before committing to the actual path (red solid arrow).
- Node positions may shift slowly if dynamic layout is enabled, representing the reconfiguration of cognitive space.

---

## Application Exploration: Personalized Education Prototype (Example)

Based on Cognitive Graph Theory, we developed a simple education system prototype to demonstrate the theory's potential for practical application:

1.  **User Questionnaire:** Collects the learner's cognitive parameters, such as abstraction ability and memory capacity, through subjective and multiple-choice questions.
2.  **Cognitive Graph Construction:** Initializes a personalized cognitive network (node weights, edge energy consumption) based on the parameters.
3.  **Simulate Learning Process:** Runs the energy minimization evolution, observing the occurrence of concept compression and transfer.
4.  **Learning Path Generation:** Recommends suitable learning paths based on the evolution results (e.g., "You might try understanding the new concept 'metacognition' through 'pattern recognition'").

> Currently, the recommendation layer is an interface design. It can be connected to external large models to generate natural language explanations; the system only provides structured recommendations. See the 'Personalized Education Experiment Based on Cognition' repository for code.

---

## Quick Start

### Environment Requirements
*   Python 3.9+
*   Requires only basic libraries (`numpy`, `pandas`, `matplotlib`, `networkx`, `scipy`, `openpyxl`, `jieba`). No deep learning frameworks are needed, ensuring lightweight and reproducible code.

### Install Dependencies
```bash
pip install -r requirements.txt
```

### Run Experiments
```bash
# One-click run for all scale comparison experiments (51/71/91/111 concepts)
python run_experiments.py

# Run emergence study for a single scale
python src/experiments/emergence_study_fixed.py --size 111

# Run algebraic verification experiments
python src/algebra/algebra_experiments.py

# Run objective metric analyses (threshold scan, compression potential)
python src/analysis/threshold_scan.py
python src/analysis/run_potential_analysis.py   # Chinese version
python src/analysis/run_potential_analysis_en.py # English version
```

### View Results
Experimental results are saved in the `results/` directory:
*   Files like `51_concepts.xlsx`: Detailed records of compression/transfer for each scale.
*   `batch_experiments/`: Batch experiment configurations, summary charts (performance comparison plots, scale effect curves).
*   `analysis/add_scan/`: Threshold scan results.
*   `analysis/potential_analysis/`: Compression potential distribution plots and summary statistics.
*   `emergence/`: Detailed emergence detection records.
*   `visualizations/`: Cognitive network evolution diagrams, state distribution plots, etc.

- For details, you can directly refer to the file `results/DATA_DICTIONARY.md`, which provides explanations for all the data in the results folder.
---

## Project Structure

```
├── README.md                           # English documentation
├── README_zh.md                        # Chinese documentation
├── LICENSE                              # MIT License
├── requirements.txt                     # Dependency list
├── .gitignore                           # Git ignore configuration
├── config.py                            # Global configuration file (concept sets, thresholds, parameters)
├── run_experiments.py                   # One-click run script
├── logs/                                # Run logs (reproducibility check)
│   └── reproducibility_*.log
├── paper/                               # Paper LaTeX source and figures
│   └── Manuscript/                      # Manuscript source files
│       ├── CognitiveGraph.tex
│       ├── references.bib
│       └── figures/
│           ├── cognitive_graph_three_stages.png
│           └── cognitive_graph_three_stages_zh.png
├── results/                             # Experiment outputs (only core files)
│   ├── DATA_DICTIONARY.md                # Data dictionary
│   ├── 111_concepts.xlsx                # Emergence results for 111 concepts
│   ├── 91_concepts.xlsx
│   ├── 71_concepts.xlsx
│   ├── 51_concepts.xlsx
│   ├── algebra/                         # Algebraic verification results (single file)
│   ├── analysis/                        # Objective metric analysis results
│   │   ├── add_scan/                    # Threshold scan results
│   │   ├── objective_metrics/           # Summary metrics and figures
│   │   └── potential_analysis/          # Compression potential distribution plots
│   ├── batch_experiments/               # Batch experiment summaries (single configuration)
│   ├── emergence/                       # Emergence detection records (single run)
│   ├── population/                      # Population evolution energy trajectories (single run)
│   ├── semantic_network/                # Semantic network visualizations
│   └── visualizations/                  # Cognitive network evolution diagrams
└── src/                                  # Source code main directory
    ├── __init__.py
    ├── main.py                            # Program entry point
    ├── algebra/                           # Algebraic structure module
    │   ├── algebra_experiments.py
    │   ├── cognitive_semigroup.py
    │   ├── cognitive_symmetry.py
    │   ├── group_action.py
    │   ├── integration.py
    │   ├── lie_group_cognitive.py
    │   └── __init__.py
    ├── analysis/                          # Objective metric analysis module
    │   ├── analyze_wallas_phases.py
    │   ├── benchmark_with_without_detection.py
    │   ├── run_potential_analysis.py
    │   ├── run_potential_analysis_en.py
    │   ├── threshold_scan.py
    │   └── __init__.py
    ├── core/                              # Core cognitive graph model
    │   ├── cognitive_graph.py
    │   ├── cognitive_states.py
    │   ├── semantic_network.py
    │   └── __init__.py
    ├── emergence/                          # Emergence detection and observation
    │   ├── detector_fixed.py
    │   ├── metrics.py
    │   ├── observer.py
    │   ├── universe.py
    │   ├── universe_enhanced.py
    │   └── __init__.py
    ├── experiments/                        # Experiment workflows
    │   ├── batch_experiments.py
    │   ├── emergence_study_fixed.py
    │   ├── population_study.py
    │   └── __init__.py
    ├── models/                             # Comparison model implementations
    │   ├── enhanced_model.py
    │   ├── qlearning_enhanced.py
    │   ├── random_network.py
    │   └── __init__.py
    ├── py_figure_maker/                    # 3D visualization tools
    │   ├── 3D_Graph_show.py
    │   ├── concept_compress_show2.py
    │   └── Graphical_Abstract.py
    └── utils/                              # Utility functions
        ├── analysis.py
        ├── individual_variation.py
        ├── visualization.py
        └── __init__.py
---

## Citation

If you find this work interesting or useful, please consider citing our paper (preprint/in press):

```bibtex
@article{zeng2026cognitive,
  title={The Geometry, Algebra, and Dynamics of Cognition: A Unified Graph Model Based on the Principle of Energy Minimization},
  author={Zeng, Mingjia},
  journal={arXiv preprint},
  year={2026}
}
```

---

## Contact and Acknowledgments

**Author:** Mingjia Zeng (Second-year Undergraduate, Jinan University)  
**Email:** 2024100846@qq.com  
The project is continuously updated. Discussions, suggestions, and collaborations are welcome!

**Acknowledgments:** Thanks to Karl Friston's free energy principle for its philosophical foundation, Gärdenfors' theory of conceptual spaces for geometric inspiration, and all friends who provided inspiration through intellectual exchange. All code in this project was implemented independently. Part of the semantic processing referenced another Chinese meta-structure analysis project.

---

## 🙌 Contributions and Feedback
Feel free to submit suggestions, report issues, or discuss collaboration possibilities via Issues or PRs. We especially welcome students interested in educational applications to join us in advancing the transition from theory to practice.

---

## Core Philosophy

> **Cognition knows no bounds, learning has no end.**  
> Technology is merely a tool for understanding the world; true intelligence lies not in computational power, but in the insight into underlying principles.  
> Energy minimization is not just an optimization strategy, but a fundamental law of cognitive organization.

> **Our exploration aligns with the frontiers of science:** The cognitive graph model, built independently from self-observation, strikingly coincides with key consensuses reached by top global scholars through different paths. This suggests that profound thinking about the nature of cognition is a core driving force for advancing artificial intelligence.