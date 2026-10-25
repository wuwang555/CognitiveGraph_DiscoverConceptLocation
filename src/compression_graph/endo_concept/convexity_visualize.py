# -*- coding: utf-8 -*-
"""
convexity_visualize.py -- Plots for the convexity grid.

Reads:
    four_dim_vectors/convexity_sweep/grids/grid_ALL.csv
    four_dim_vectors/config_{X}/scale{N}.csv      (for 4D density)

Writes:
    four_dim_vectors/convexity_sweep/figures/
        2d_lines/        2D line:   x=c_hi,  line=b_lo,  y=metric
        2d_heatmaps/     2D heatmap: x=b_lo, y=c_hi,  color=metric
        3d_surfaces/     3D surface: x=c_hi, y=b_lo, z=metric
        cross_config/    2D line:   x=c_hi,  line=config (b_lo fixed)
        4d_density/      density of (b, c) per (config, scale)

Metrics plotted (5):
    expert_mean_convexity_ratio
    expert_max_convexity_ratio
    general_outside_fraction
    general_mean_convexity_ratio
    volume_ratio

Modes: 4d and 3d.

Usage:
    cd src/compression_graph/endo_concept
    python convexity_visualize.py
    python convexity_visualize.py --root ../four_dim_vectors
    python convexity_visualize.py --only lines heatmaps
"""

import argparse
import os
import sys
from pathlib import Path

_parser = argparse.ArgumentParser()
_parser.add_argument("--only", nargs="+",
                     choices=["lines", "heatmaps", "surfaces",
                              "config", "density"],
                     default=["lines", "heatmaps", "surfaces",
                              "config", "density"])
_parser.add_argument("--b_lo_fixed", type=float, default=0.02,
                     help="Fixed b_lo for cross-config plot.")
_parser.add_argument("--dpi", type=int, default=150)
_parser.add_argument("--method", choices=["grid", "holdout"], default="grid")
_parser.add_argument("--root", default=None)
_args = _parser.parse_args()

_HERE = Path(__file__).resolve().parent
_PROJ = _HERE.parents[2]
_ROOT_DEFAULT = _PROJ / "results" / "four_dim_vectors"

_root = Path(_args.root) if _args.root else _ROOT_DEFAULT
_grid_csv = _root / "convexity_sweep" / "grids" / "grid_ALL.csv"
_fig_root = _root / "convexity_sweep" / "figures"

if _args.method == "holdout":
    _grid_csv = _root / "convexity_sweep" / "holdout" / "grids" / "holdout_ALL.csv"
    _fig_root = _root / "convexity_sweep" / "holdout" / "figures"
    METRICS = [...]
else:
    _grid_csv = _root / "convexity_sweep" / "grids" / "grid_ALL.csv"
    _fig_root = _root / "convexity_sweep" / "figures"
    METRICS = [...]

# 在这里统一创建子目录
for sub in ("2d_lines", "2d_heatmaps", "3d_surfaces",
            "cross_config", "4d_density"):
    (_fig_root / sub).mkdir(parents=True, exist_ok=True)

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401

# Font fallback for Chinese / safety
plt.rcParams["font.sans-serif"] = ["SimHei", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False


METRICS = [
    "expert_mean_convexity_ratio",
    "expert_max_convexity_ratio",
    "general_outside_fraction",
    "general_mean_convexity_ratio",
    "volume_ratio",
]
MODES = ["4d", "3d"]

# 路径根据 method 决定
if _args.method == "holdout":
    _grid_csv = _root / "convexity_sweep" / "holdout" / "grids" / "holdout_ALL.csv"
    _fig_root = _root / "convexity_sweep" / "holdout" / "figures"
    METRICS = [
        "test_expert_inside_fraction",
        "test_expert_inside_std",
        "general_inside_fraction",
        "general_inside_std",
        "separation",
        "test_expert_mean_ratio",
        "general_mean_ratio",
    ]
else:
    _grid_csv = _root / "convexity_sweep" / "grids" / "grid_ALL.csv"
    _fig_root = _root / "convexity_sweep" / "figures"
    METRICS = [
        "expert_mean_convexity_ratio",
        "expert_max_convexity_ratio",
        "general_outside_fraction",
        "general_mean_convexity_ratio",
        "volume_ratio",
    ]
# ===================================================================== #
# Load
# ===================================================================== #
def load_grid():
    if not _grid_csv.exists():
        print(f"[ERROR] missing {_grid_csv}")
        print("        run `python continuous_vector.py` first.")
        sys.exit(1)
    df = pd.read_csv(_grid_csv)
    df = df[df["status"] == "ok"].copy()   # drop degenerate rows
    return df


# ===================================================================== #
# 2D line plots: x = c_hi, y = metric, one line per b_lo
# ===================================================================== #
def plot_2d_lines(grid):
    out_dir = _fig_root / "2d_lines"
    print("\n[2d_lines]")
    for mode in MODES:
        sub = grid[grid["mode"] == mode]
        if sub.empty:
            continue
        for metric in METRICS:
            if metric not in sub.columns:
                continue
            fig, ax = plt.subplots(figsize=(7, 4.5))
            for b_lo, g in sub.groupby("b_lo"):
                g = g.sort_values("c_hi")
                y = g.groupby("c_hi")[metric].mean()
                y = y.reindex(sorted(y.index))
                ax.plot(y.index, y.values, marker="o",
                        label=f"b_lo={b_lo}")
            ax.set_xlabel("c_hi")
            ax.set_ylabel(metric)
            ax.set_title(f"[{mode}]  {metric}\n"
                         f"x=c_hi, y=metric, lines=b_lo")
            ax.grid(True, alpha=0.3)
            ax.legend(fontsize=8)
            plt.tight_layout()
            path = out_dir / f"{mode}_{metric}.png"
            plt.savefig(path, dpi=_args.dpi)
            plt.close(fig)
            print(f"  [saved] {path.name}")


# ===================================================================== #
# 2D heatmap: x = b_lo, y = c_hi, color = metric
# ===================================================================== #
def plot_2d_heatmaps(grid):
    out_dir = _fig_root / "2d_heatmaps"
    print("\n[2d_heatmaps]")
    for mode in MODES:
        sub = grid[grid["mode"] == mode]
        if sub.empty:
            continue
        for metric in METRICS:
            if metric not in sub.columns:
                continue
            pv = sub.pivot_table(index="c_hi", columns="b_lo",
                                 values=metric, aggfunc="mean")
            if pv.empty:
                continue
            fig, ax = plt.subplots(figsize=(7, 5))
            im = ax.imshow(pv.values, aspect="auto",
                           origin="lower", cmap="viridis")
            ax.set_xticks(range(len(pv.columns)))
            ax.set_xticklabels([f"{x:g}" for x in pv.columns])
            ax.set_yticks(range(len(pv.index)))
            ax.set_yticklabels([f"{x:g}" for x in pv.index])
            ax.set_xlabel("b_lo")
            ax.set_ylabel("c_hi")
            ax.set_title(f"[{mode}]  {metric}\n"
                         f"x=b_lo, y=c_hi, color=metric")
            cbar = plt.colorbar(im, ax=ax)
            cbar.set_label(metric)
            plt.tight_layout()
            path = out_dir / f"{mode}_{metric}.png"
            plt.savefig(path, dpi=_args.dpi)
            plt.close(fig)
            print(f"  [saved] {path.name}")


# ===================================================================== #
# 3D surface: (c_hi, b_lo) -> metric
# ===================================================================== #
def plot_3d_surfaces(grid):
    out_dir = _fig_root / "3d_surfaces"
    print("\n[3d_surfaces]")
    for mode in MODES:
        sub = grid[grid["mode"] == mode]
        if sub.empty:
            continue
        for metric in METRICS:
            if metric not in sub.columns:
                continue
            pv = sub.pivot_table(index="c_hi", columns="b_lo",
                                 values=metric, aggfunc="mean")
            if pv.shape[0] < 2 or pv.shape[1] < 2:
                continue
            X, Y = np.meshgrid(pv.columns.values, pv.index.values)
            Z = pv.values
            fig = plt.figure(figsize=(8, 6))
            ax = fig.add_subplot(111, projection="3d")
            surf = ax.plot_surface(X, Y, Z, cmap="viridis",
                                   edgecolor="none", alpha=0.9)
            ax.set_xlabel("b_lo")
            ax.set_ylabel("c_hi")
            ax.set_zlabel(metric)
            ax.set_title(f"[{mode}]  {metric}\n"
                         f"x=b_lo, y=c_hi, z=metric")
            fig.colorbar(surf, ax=ax, shrink=0.6, label=metric)
            plt.tight_layout()
            path = out_dir / f"{mode}_{metric}.png"
            plt.savefig(path, dpi=_args.dpi)
            plt.close(fig)
            print(f"  [saved] {path.name}")


# ===================================================================== #
# Cross-config: x = c_hi, one line per config (fixed b_lo)
# ===================================================================== #
def plot_cross_config(grid):
    out_dir = _fig_root / "cross_config"
    print(f"\n[cross_config] (fixed b_lo={_args.b_lo_fixed})")
    for mode in MODES:
        sub = grid[(grid["mode"] == mode)
                   & (np.isclose(grid["b_lo"], _args.b_lo_fixed))]
        if sub.empty:
            print(f"  [skip] {mode}: no rows at b_lo={_args.b_lo_fixed}")
            continue
        for metric in METRICS:
            if metric not in sub.columns:
                continue
            fig, ax = plt.subplots(figsize=(7, 4.5))
            for config, g in sub.groupby("config"):
                y = g.groupby("c_hi")[metric].mean().sort_index()
                ax.plot(y.index, y.values, marker="o",
                        label=f"config {config}")
            ax.set_xlabel("c_hi")
            ax.set_ylabel(metric)
            ax.set_title(f"[{mode}]  {metric}  (b_lo={_args.b_lo_fixed})\n"
                         f"x=c_hi, y=metric, lines=config")
            ax.grid(True, alpha=0.3)
            ax.legend(fontsize=8)
            plt.tight_layout()
            path = out_dir / f"{mode}_{metric}.png"
            plt.savefig(path, dpi=_args.dpi)
            plt.close(fig)
            print(f"  [saved] {path.name}")


# ===================================================================== #
# 4D density: (b, c) per (config, scale)
# ===================================================================== #
def plot_4d_density():
    out_dir = _fig_root / "4d_density"
    print("\n[4d_density]  (b vs c)")
    for config in ("A", "B", "C"):
        for scale in (51, 71, 91, 111):
            p = _root / f"config_{config}" / f"scale{scale}.csv"
            if not p.exists():
                continue
            df = pd.read_csv(p)
            if "b" not in df.columns or "c" not in df.columns:
                continue
            fig, ax = plt.subplots(figsize=(6, 5))
            hb = ax.hexbin(df["b"], df["c"], gridsize=20,
                           cmap="viridis", mincnt=1)
            fig.colorbar(hb, ax=ax, label="count")
            ax.set_xlabel("b (support)")
            ax.set_ylabel("c (role consistency)")
            ax.set_title(f"config {config}, scale {scale}\n"
                         f"x=b, y=c, color=count")
            ax.grid(True, alpha=0.2)
            plt.tight_layout()
            path = out_dir / f"config_{config}_scale{scale}.png"
            plt.savefig(path, dpi=_args.dpi)
            plt.close(fig)
            print(f"  [saved] {path.name}")


# ===================================================================== #
def main():
    print("=" * 70)
    print("convexity_visualize")
    print(f"  root   = {_root}")
    print(f"  figs   = {_fig_root}")
    print(f"  only   = {_args.only}")
    print("=" * 70)

    if not _grid_csv.exists():
        print(f"[ERROR] {_grid_csv} not found.")
        return

    grid = load_grid()
    print(f"  loaded {len(grid)} grid rows (status=ok only)")

    if "lines" in _args.only:
        plot_2d_lines(grid)
    if "heatmaps" in _args.only:
        plot_2d_heatmaps(grid)
    if "surfaces" in _args.only:
        plot_3d_surfaces(grid)
    if "config" in _args.only:
        plot_cross_config(grid)
    if "density" in _args.only:
        plot_4d_density()

    print(f"\nDone. Figures under: {_fig_root}")


if __name__ == "__main__":
    main()