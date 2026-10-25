# -*- coding: utf-8 -*-
"""
continuous_vector.py -- Four-dimensional continuous representation.

Replaces the discrete six-quadrant bins with continuous coordinates:

    b  : B-membership   = support in raw compression events
    c  : C-membership   = role consistency in raw compression events
    g1 : G1-energy      = z-scored composite (mean_weight, weight_drop,
                          traversal_freq) from g1_nodes.csv
    g2 : G2-structure   = z-scored composite (weighted degree, betweenness)
                          from the co-occurrence graph rebuilt from raw events

No new simulation. All inputs come from existing exports:

    g1_export/config_{X}/scale{N}/g1_nodes.csv
    endo_result/raw_events_{X}/raw_compression_events.csv

Outputs (per config, per scale):

    four_dim_vectors/config_{X}/scale{N}.csv          (four-dim coords)
    four_dim_vectors/config_{X}/scale{N}_pca.csv      (PCA decomposition)
    four_dim_vectors/config_{X}/scale{N}_knn.csv      (nearest neighbors)
    four_dim_vectors/config_{X}/summary.csv           (per-scale stats)
    four_dim_vectors/all_summary.csv                  (cross-config summary)

Usage:
    python continuous_vector.py --configs A B C
    python continuous_vector.py --configs A --scales 51 91
"""

import argparse
import json
import os
import sys
from collections import Counter
from pathlib import Path
from scipy.spatial import ConvexHull

_parser = argparse.ArgumentParser()
_parser.add_argument("--configs", nargs="+", default=["A", "B", "C"])
_parser.add_argument("--scales", nargs="+", type=int, default=[51, 71, 91, 111])
_parser.add_argument("--g1_root", default=None)
_parser.add_argument("--endo_root", default=None)
_parser.add_argument("--out_dir", default=None)
_parser.add_argument("--knn_k", type=int, default=3)
_parser.add_argument("--method", choices=["grid", "holdout"], default="holdout")
_parser.add_argument("--n-splits", type=int, default=10)
_args = _parser.parse_args()

_HERE = Path(__file__).resolve().parent
for _p in (_HERE, _HERE.parent, _HERE.parent.parent, _HERE.parent.parent.parent):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import numpy as np
import pandas as pd
import networkx as nx

_args.g1_root = Path(_args.g1_root) if _args.g1_root else _HERE / "g1_export"
_args.endo_root = Path(_args.endo_root) if _args.endo_root else _HERE / "endo_result"
_args.out_dir = Path(_args.out_dir) if _args.out_dir else _HERE / "four_dim_vectors"


# ===================================================================== #
# Helpers
# ===================================================================== #
def _z(arr):
    arr = np.asarray(arr, dtype=float)
    m, s = arr.mean(), arr.std()
    return np.zeros_like(arr) if (s == 0 or np.isnan(s)) else (arr - m) / s


def _minmax(arr):
    arr = np.asarray(arr, dtype=float)
    lo, hi = arr.min(), arr.max()
    return np.zeros_like(arr) if (hi - lo == 0) else (arr - lo) / (hi - lo)


def load_g1_nodes(config, scale):
    p = _args.g1_root / f"config_{config}" / f"scale{scale}" / "g1_nodes.csv"
    return pd.read_csv(p) if p.exists() else None


def load_raw_events(config, scale):
    p = _args.endo_root / f"raw_events_{config}" / "raw_compression_events.csv"
    if not p.exists():
        return None
    df = pd.read_csv(p)
    if "scale" in df.columns:
        df = df[df["scale"] == scale]
    return df if not df.empty else None


# ===================================================================== #
# b, c from raw events (continuous)
# ===================================================================== #
def compute_bc_scores(events_df):
    """Return dict concept -> {b, c, n_center, n_member}."""
    n_center = Counter()
    n_member = Counter()
    total_events = 0
    for _, row in events_df.iterrows():
        center = row.get("center")
        if pd.isna(center):
            continue
        total_events += 1
        center = str(center)
        n_center[center] += 1
        raw = row.get("related_nodes", "")
        rel = [] if pd.isna(raw) else [x.strip() for x in str(raw).split("|") if x.strip()]
        for m in rel:
            if m != center:
                n_member[m] += 1

    out = {}
    for x in set(n_center) | set(n_member):
        c_count = n_center.get(x, 0)
        m_count = n_member.get(x, 0)
        total = c_count + m_count
        b = total / max(1, total_events)          # support, in [0, 1]
        c = (max(c_count, m_count) / total) if total > 0 else 0.5
        out[x] = {"b": b, "c": c,
                  "n_center": c_count, "n_member": m_count}
    return out


# ===================================================================== #
# g1, g2 composites (continuous)
# ===================================================================== #
def compute_g1_scores(g1_df):
    df = g1_df.copy()
    for col in ("mean_weight", "min_weight", "weight_drop", "traversal_freq"):
        if col in df.columns:
            df[col] = df[col].fillna(df[col].median())
    score = (
        0.40 * _z(-df["mean_weight"].values)
        + 0.30 * _z(df["weight_drop"].values)
        + 0.30 * _z(df["traversal_freq"].values)
    )
    return dict(zip(df["concept"], score))


def load_g2_graph(events_df):
    G = nx.Graph()
    counts = Counter()
    for _, row in events_df.iterrows():
        center = row.get("center")
        if pd.isna(center):
            continue
        center = str(center)
        raw = row.get("related_nodes", "")
        rel = [] if pd.isna(raw) else [x.strip() for x in str(raw).split("|") if x.strip()]
        nodes = list(dict.fromkeys([center] + rel))
        for i in range(len(nodes)):
            for j in range(i + 1, len(nodes)):
                counts[tuple(sorted([nodes[i], nodes[j]]))] += 1
    for (u, v), c in counts.items():
        G.add_edge(u, v, count=int(c), weight=int(c))
    return G


def compute_g2_scores(G):
    if G is None or G.number_of_nodes() == 0:
        return {}
    wdeg = dict(G.degree(weight="count"))
    try:
        bt = nx.betweenness_centrality(G)
    except Exception:
        bt = {n: 0.0 for n in G.nodes()}
    nodes = list(G.nodes())
    wd = np.array([wdeg.get(n, 0) for n in nodes], dtype=float)
    btc = np.array([bt.get(n, 0) for n in nodes], dtype=float)
    score = 0.6 * _z(wd) + 0.4 * _z(btc)
    return dict(zip(nodes, score))


# ===================================================================== #
# PCA (numpy-only via SVD)
# ===================================================================== #
def pca_4d(X):
    X_mean = X.mean(axis=0)
    Xc = X - X_mean
    U, S, Vt = np.linalg.svd(Xc, full_matrices=False)
    var = (S ** 2) / ((S ** 2).sum() + 1e-12)
    return var, Vt, X_mean


# ===================================================================== #
# kNN in 4D
# ===================================================================== #
def find_nearest_neighbors(df, k=3):
    X = df[["b", "c_norm", "g1_norm", "g2_norm"]].values
    n = len(X)
    if n <= 1:
        return pd.DataFrame({"concept": df["concept"], "neighbors": [""] * n})

    # pairwise Euclidean distances in normalized 4D
    diff = X[:, None, :] - X[None, :, :]
    dists = np.sqrt((diff ** 2).sum(axis=2))
    np.fill_diagonal(dists, np.inf)

    rows = []
    for i in range(n):
        idx = np.argsort(dists[i])[: min(k, n - 1)]
        nbrs = [(df.iloc[j]["concept"], float(dists[i, j])) for j in idx]
        rows.append({
            "concept": df.iloc[i]["concept"],
            "neighbors": "; ".join(f"{c} ({d:.3f})" for c, d in nbrs),
        })
    return pd.DataFrame(rows)


# ===================================================================== #
# Per (config, scale)
# ===================================================================== #
def process_one(config, scale):
    g1_df = load_g1_nodes(config, scale)
    events_df = load_raw_events(config, scale)
    if g1_df is None or events_df is None:
        return None

    g1_scores = compute_g1_scores(g1_df)
    G2 = load_g2_graph(events_df)
    g2_scores = compute_g2_scores(G2)
    bc = compute_bc_scores(events_df)

    rows = []
    for x in g1_scores.keys():
        b = float(bc.get(x, {}).get("b", 0.0))
        c_raw = float(bc.get(x, {}).get("c", 0.5))
        rows.append({
            "concept": x,
            "b": b,
            "c": c_raw,
            "g1_z": float(g1_scores[x]),
            "g2_z": float(g2_scores.get(x, 0.0)),
            "n_center": int(bc.get(x, {}).get("n_center", 0)),
            "n_member": int(bc.get(x, {}).get("n_member", 0)),
        })
    df = pd.DataFrame(rows)

    # Continuous normalized coordinates for geometric consistency
    df["c_norm"] = (df["c"] - 0.5) * 2      # [0.5, 1] -> [0, 1]
    df["g1_norm"] = _minmax(df["g1_z"].values)
    df["g2_norm"] = _minmax(df["g2_z"].values)

    X = df[["b", "c_norm", "g1_norm", "g2_norm"]].values
    var, components, _ = pca_4d(X)

    df["config"] = config
    df["scale"] = scale
    return df, var, components

# ===================================================================== #
# Convexity test (Gärdenfors empirical hypothesis)
# --------------------------------------------------------------------- #
# Gärdenfors (2000, 2014) treats "concept regions are convex" as an
# *empirical hypothesis*, not an a priori axiom (see his reply to
# Hernández-Conde). Tětková et al. (2023) operationalize this by
# measuring the convexity ratio of sampled point clouds in latent spaces.
#
# We apply the same operationalization to the 4D space:
#
#   S_expert  = { x : c(x) >= c_hi  and  b(x) >= b_lo }
#   S_general = { x : b(x) >= b_lo  and  c(x) <  c_hi }
#
# Then:
#   1. Build Conv(S_expert).
#   2. For every point in S_expert, compute the convexity ratio
#      ratio(x) = ||x - centroid|| / ||x* - centroid||,
#      where x* is the intersection of ray(centroid -> x) with the
#      convex-hull boundary.
#   3. For every point in S_general, compute the same ratio
#      *with respect to Conv(S_expert)*.
#
# Interpretation:
#   - ratio < 1   -> inside the hull
#   - ratio ~ 1   -> on the boundary
#   - ratio > 1   -> outside
#
# Gärdenfors' hypothesis predicts:
#   * mean_expert_convexity_ratio  <=~ 1.0  (expert points are convex)
#   * general_outside_fraction      > 0    (B−C lies outside / on boundary)
#   * general_mean_convexity_ratio  > 1.0  (B−C is a boundary layer)
# ===================================================================== #

def _point_in_hull(point, hull, tolerance=1e-9):
    """True iff point is inside the convex hull (inclusive of boundary)."""
    return all(
        np.dot(eq[:-1], point) + eq[-1] <= tolerance
        for eq in hull.equations
    )


def _convexity_ratio(points, hull):
    """Convexity ratio of each point w.r.t. a given convex hull.

    ratio(p) = ||p - centroid|| / ||p* - centroid||
    where p* = ray(centroid -> p) ∩ boundary(Conv(hull)).

    Reference: Tětková et al. 2023, "On the convexity of latent
    representation spaces" — same definition, applied here in 4D.
    """
    points = np.asarray(points, dtype=float)
    if len(points) == 0:
        return np.array([])

    centroid = points.mean(axis=0)
    eqs = hull.equations          # (m, dim+1), rows: a·x + b <= 0

    ratios = np.zeros(len(points))
    for i, p in enumerate(points):
        direction = p - centroid
        norm = float(np.linalg.norm(direction))
        if norm < 1e-12:
            ratios[i] = 0.0
            continue
        direction = direction / norm

        # Intersect ray centroid + t * direction with every facet plane.
        # Solve  a·(centroid + t·d) + b = 0  for t.
        a = eqs[:, :-1]                     # (m, dim)
        b = eqs[:, -1]                      # (m,)
        denom = a @ direction               # (m,)
        num = -(a @ centroid + b)           # (m,)
        with np.errstate(divide="ignore", invalid="ignore"):
            t_candidates = np.where(
                np.abs(denom) > 1e-12,
                num / denom,
                np.inf,
            )
        t_candidates = t_candidates[t_candidates > 0]
        if len(t_candidates) == 0:
            ratios[i] = np.inf
        else:
            t_boundary = float(np.min(t_candidates))
            ratios[i] = norm / t_boundary
    return ratios


def convexity_test(df,
                   feature_cols=None,
                   c_hi=0.60,
                   b_lo=None):
    """Test Gärdenfors' convexity hypothesis on the 4D point cloud.

    Parameters
    ----------
    df : DataFrame
        Must contain columns `b`, `c`, and feature_cols.
    feature_cols : list[str]
        Defaults to ['b', 'c_norm', 'g1_norm', 'g2_norm'].
    c_hi : float
        Role-purity threshold defining S_expert.
    b_lo : float or None
        Minimum b to be considered. Defaults to df['b'].quantile(0.25).

    Returns
    -------
    dict with:
        n_expert, n_general,
        expert_mean_convexity_ratio,
        expert_max_convexity_ratio,
        general_outside_fraction,
        general_mean_convexity_ratio,
        volume_ratio,
        status   (str: 'ok' | 'insufficient_points' | 'degenerate')
    """
    if feature_cols is None:
        feature_cols = ["b", "c_norm", "g1_norm", "g2_norm"]
    if b_lo is None:
        b_lo = float(df["b"].quantile(0.25))

    expert_mask = (df["c"] >= c_hi) & (df["b"] >= b_lo)
    general_mask = (df["b"] >= b_lo) & (df["c"] < c_hi)

    expert_pts = df.loc[expert_mask, feature_cols].values.astype(float)
    general_pts = df.loc[general_mask, feature_cols].values.astype(float)

    result = {
        "n_expert": int(len(expert_pts)),
        "n_general": int(len(general_pts)),
        "c_hi": float(c_hi),
        "b_lo": float(b_lo),
    }

    # Degenerate cases -----------------------------------------------------
    if len(expert_pts) < len(feature_cols) + 1:
        result.update({
            "status": "insufficient_points",
            "expert_mean_convexity_ratio": None,
            "expert_max_convexity_ratio": None,
            "general_outside_fraction": None,
            "general_mean_convexity_ratio": None,
            "volume_ratio": None,
        })
        return result

    try:
        expert_hull = ConvexHull(expert_pts)
    except Exception as e:
        result.update({
            "status": f"degenerate: {type(e).__name__}",
            "expert_mean_convexity_ratio": None,
            "expert_max_convexity_ratio": None,
            "general_outside_fraction": None,
            "general_mean_convexity_ratio": None,
            "volume_ratio": None,
        })
        return result

    # Expert-side convexity -----------------------------------------------
    expert_ratios = _convexity_ratio(expert_pts, expert_hull)
    expert_ratios = expert_ratios[np.isfinite(expert_ratios)]

    # General-side position relative to the expert hull -------------------
    if len(general_pts) > 0:
        general_inside = np.array(
            [_point_in_hull(p, expert_hull) for p in general_pts]
        )
        general_ratios = _convexity_ratio(general_pts, expert_hull)
        general_ratios = general_ratios[np.isfinite(general_ratios)]
        general_outside_fraction = float(1.0 - general_inside.mean())
        general_mean_ratio = (
            float(np.mean(general_ratios)) if len(general_ratios) else None
        )
    else:
        general_outside_fraction = None
        general_mean_ratio = None

    # Volume ratio (expert hull vs joint hull) ----------------------------
    try:
        joint_hull = ConvexHull(np.vstack([expert_pts, general_pts]))
        volume_ratio = float(expert_hull.volume / joint_hull.volume)
    except Exception:
        volume_ratio = None

    result.update({
        "status": "ok",
        "expert_mean_convexity_ratio": float(np.mean(expert_ratios))
            if len(expert_ratios) else None,
        "expert_max_convexity_ratio": float(np.max(expert_ratios))
            if len(expert_ratios) else None,
        "general_outside_fraction": general_outside_fraction,
        "general_mean_convexity_ratio": general_mean_ratio,
        "volume_ratio": volume_ratio,
    })
    return result

# ===================================================================== #
# Holdout convexity test (the real test)
# --------------------------------------------------------------------- #
# The self-test version (convexity_test) uses the expert points to build
# the hull and then evaluates the same expert points. This guarantees
# expert_mean_convexity_ratio <= 1.0 by definition, and general_outside_
# fraction == 1.0 whenever expert/general are separated along any single
# axis (which they are, by construction, in 4D).
#
# The holdout version splits the expert points in half: build the hull on
# one half, evaluate the *other* half plus all general points. Now:
#
#   test_expert_inside_fraction : fraction of held-out expert points
#                                 inside the training hull
#                                 ~ 1.0  -> expert region is convex
#                                 ~ 0.5  -> not convex
#   general_inside_fraction     : fraction of general points inside the
#                                 training hull
#                                 ~ 0    -> general is outside
#   separation = test_inside - general_inside
#                                 > 0.5  -> strong separation
#                                 ~ 0    -> indistinguishable
#
# Repeated over n_splits random partitions; mean and std are reported.
# ===================================================================== #

def convexity_test_holdout(df,
                           feature_cols=None,
                           c_hi=0.85,
                           b_lo=None,
                           n_splits=10,
                           random_state=42):
    """Split-half convexity test.

    Half of the expert points build the hull; the other half and all
    general points are evaluated. Repeated over ``n_splits`` random
    partitions. This is the version that actually tests whether the
    expert region is convex.

    Parameters
    ----------
    df : DataFrame with columns b, c, c_norm, g1_norm, g2_norm.
    feature_cols : list[str] or None
        Defaults to ['b', 'c_norm', 'g1_norm', 'g2_norm'] (4D).
    c_hi : float
    b_lo : float or None
    n_splits : int
    random_state : int

    Returns
    -------
    dict with status in {'ok','insufficient_points','degenerate'}.
    """
    if feature_cols is None:
        feature_cols = ["b", "c_norm", "g1_norm", "g2_norm"]
    if b_lo is None:
        b_lo = float(df["b"].quantile(0.25))

    expert_mask = (df["c"] >= c_hi) & (df["b"] >= b_lo)
    general_mask = (df["b"] >= b_lo) & (df["c"] < c_hi)

    expert_pts = df.loc[expert_mask, feature_cols].values.astype(float)
    general_pts = df.loc[general_mask, feature_cols].values.astype(float)

    result = {
        "n_expert": int(len(expert_pts)),
        "n_general": int(len(general_pts)),
        "c_hi": float(c_hi),
        "b_lo": float(b_lo),
        "n_splits": int(n_splits),
    }

    # Need at least two halves, each with dim+1 points
    min_half = len(feature_cols) + 1
    if len(expert_pts) < 2 * min_half:
        result.update({"status": "insufficient_points"})
        return result

    inside_fracs = []          # held-out expert inside hull
    general_fracs = []         # general inside hull
    test_ratio_means = []
    general_ratio_means = []
    n_ok = 0

    for seed in range(n_splits):
        rng = np.random.default_rng(random_state + seed)
        idx = rng.permutation(len(expert_pts))
        half = len(expert_pts) // 2
        train_pts = expert_pts[idx[:half]]
        test_pts  = expert_pts[idx[half:]]

        try:
            hull = ConvexHull(train_pts)
        except Exception:
            continue

        # Held-out expert points
        test_inside = np.array([_point_in_hull(p, hull) for p in test_pts])
        inside_fracs.append(float(test_inside.mean()))

        # General points
        if len(general_pts) > 0:
            gen_inside = np.array([_point_in_hull(p, hull)
                                   for p in general_pts])
            general_fracs.append(float(gen_inside.mean()))

        # Optional: mean convexity ratio
        tr = _convexity_ratio(test_pts, hull)
        tr = tr[np.isfinite(tr)]
        if len(tr):
            test_ratio_means.append(float(np.mean(tr)))

        if len(general_pts) > 0:
            gr = _convexity_ratio(general_pts, hull)
            gr = gr[np.isfinite(gr)]
            if len(gr):
                general_ratio_means.append(float(np.mean(gr)))

        n_ok += 1

    if n_ok == 0:
        result.update({"status": "all_splits_degenerate"})
        return result

    test_mean = float(np.mean(inside_fracs))
    test_std  = float(np.std(inside_fracs))

    if general_fracs:
        gen_mean = float(np.mean(general_fracs))
        gen_std  = float(np.std(general_fracs))
        separation = float(test_mean - gen_mean)
    else:
        gen_mean = None
        gen_std  = None
        separation = None

    result.update({
        "status": "ok",
        "n_splits_ok": int(n_ok),
        # ★ 关键指标
        "test_expert_inside_fraction": test_mean,
        "test_expert_inside_std":      test_std,
        "general_inside_fraction":     gen_mean,
        "general_inside_std":          gen_std,
        "separation":                  separation,
        # 辅助
        "test_expert_mean_ratio":
            float(np.mean(test_ratio_means)) if test_ratio_means else None,
        "general_mean_ratio":
            float(np.mean(general_ratio_means)) if general_ratio_means else None,
    })
    return result


def convexity_sweep_holdout(df,
                            c_hi_values=None,
                            b_lo_values=None,
                            feature_cols=None,
                            n_splits=10,
                            random_state=42):
    """Run convexity_test_holdout on the (c_hi × b_lo) grid."""
    if c_hi_values is None:
        c_hi_values = np.arange(0.50, 0.96, 0.05)
    if b_lo_values is None:
        b_lo_values = _default_b_lo_values(df)

    rows = []
    for c_hi in c_hi_values:
        for b_lo in b_lo_values:
            r = convexity_test_holdout(
                df,
                feature_cols=feature_cols,
                c_hi=round(float(c_hi), 4),
                b_lo=round(float(b_lo), 4),
                n_splits=n_splits,
                random_state=random_state,
            )
            r["c_hi"] = round(float(c_hi), 4)
            r["b_lo"] = round(float(b_lo), 4)
            rows.append(r)
    return rows


def convexity_sweep_dual_holdout(df,
                                 c_hi_values=None,
                                 b_lo_values=None,
                                 n_splits=10,
                                 random_state=42):
    """Run convexity_sweep_holdout in both 4D and 3D modes."""
    out = []
    for mode, cols in [
        ("4d", ["b", "c_norm", "g1_norm", "g2_norm"]),
        ("3d", ["b", "g1_norm", "g2_norm"]),
    ]:
        rows = convexity_sweep_holdout(
            df,
            c_hi_values=c_hi_values,
            b_lo_values=b_lo_values,
            feature_cols=cols,
            n_splits=n_splits,
            random_state=random_state,
        )
        for r in rows:
            r["mode"] = mode
        out.extend(rows)
    return out



# ===================================================================== #
# Convexity grid sweep (c_hi × b_lo, dual-mode)
# ===================================================================== #
def _default_b_lo_values(df, b_lo_grid=None):
    """Fixed b_lo grid, filtered to values that keep enough points.

    A fixed grid (not per-scale quantiles) is used so that pivots and
    figures are comparable across configs and scales.

    Default grid: [0.0, 0.02, 0.05, 0.10, 0.20]
    A value is kept only if at least `min_n` points survive `b >= b_lo`.
    """
    if b_lo_grid is None:
        b_lo_grid = [0.0, 0.02, 0.05, 0.10, 0.20]
    n = len(df)
    min_n = max(6, int(0.05 * n))
    vals = []
    for b in b_lo_grid:
        if (df["b"] >= b).sum() >= min_n:
            vals.append(round(float(b), 4))
    return vals if vals else [0.0]


def convexity_sweep(df,
                    c_hi_values=None,
                    b_lo_values=None,
                    feature_cols=None):
    """Run convexity_test on a (c_hi × b_lo) grid for one feature mode.

    Parameters
    ----------
    df : DataFrame with columns b, c, c_norm, g1_norm, g2_norm.
    c_hi_values : iterable[float] or None
        Default: np.arange(0.50, 0.96, 0.05).
    b_lo_values : iterable[float] or None
        Default: _default_b_lo_values(df) = [0, q10, q25, q50] (dedup).
    feature_cols : list[str] or None
        Default: ['b', 'c_norm', 'g1_norm', 'g2_norm'] (4D).

    Returns
    -------
    list[dict] : one row per (c_hi, b_lo) combination.
    """
    if c_hi_values is None:
        c_hi_values = np.arange(0.50, 0.96, 0.05)
    if b_lo_values is None:
        b_lo_values = _default_b_lo_values(df)
    if feature_cols is None:
        feature_cols = ["b", "c_norm", "g1_norm", "g2_norm"]

    rows = []
    for c_hi in c_hi_values:
        for b_lo in b_lo_values:
            r = convexity_test(df,
                               feature_cols=feature_cols,
                               c_hi=round(float(c_hi), 4),
                               b_lo=round(float(b_lo), 4))
            r["c_hi"] = round(float(c_hi), 4)
            r["b_lo"] = round(float(b_lo), 4)
            rows.append(r)
    return rows


def convexity_sweep_dual(df,
                         c_hi_values=None,
                         b_lo_values=None):
    """Run convexity_sweep in both 4D and 3D modes.

    Returns
    -------
    list[dict] : 4D rows followed by 3D rows; each row has 'mode' in {'4d','3d'}.
    """
    out = []
    for mode, cols in [
        ("4d", ["b", "c_norm", "g1_norm", "g2_norm"]),
        ("3d", ["b", "g1_norm", "g2_norm"]),
    ]:
        rows = convexity_sweep(df,
                               c_hi_values=c_hi_values,
                               b_lo_values=b_lo_values,
                               feature_cols=cols)
        for r in rows:
            r["mode"] = mode
        out.extend(rows)
    return out

# ===================================================================== #
# Main
# ===================================================================== #
def main():
    print("=" * 70)
    print("Continuous four-dimensional representation")
    print(f"  method  = {_args.method}")
    print(f"  configs = {_args.configs}")
    print(f"  scales  = {_args.scales}")
    print(f"  g1_root = {_args.g1_root}")
    print(f"  endo    = {_args.endo_root}")
    print(f"  out     = {_args.out_dir}")
    print("=" * 70)

    # ---- grids ----
    c_hi_values = [round(x, 2) for x in np.arange(0.50, 0.96, 0.05)]
    b_lo_grid = [0.0, 0.02, 0.05, 0.10, 0.20]
    print(f"  c_hi grid = {c_hi_values}")
    print(f"  b_lo grid = {b_lo_grid}  (fixed, per-scale filtered)")
    print(f"  modes     = 4d (b, c, g1, g2) + 3d (b, g1, g2)")
    if _args.method == "holdout":
        print(f"  n_splits  = {_args.n_splits}")

    # ---- output dirs ----
    _args.out_dir.mkdir(parents=True, exist_ok=True)
    if _args.method == "holdout":
        conv_root = _args.out_dir / "convexity_sweep" / "holdout"
    else:
        conv_root = _args.out_dir / "convexity_sweep"
    grids_dir = conv_root / "grids"
    pivots_dir = conv_root / "pivots"
    grids_dir.mkdir(parents=True, exist_ok=True)
    pivots_dir.mkdir(parents=True, exist_ok=True)

    # ---- accumulate ----
    all_rows = []
    sweep_all = []

    # ================================================================== #
    # Per (config, scale)
    # ================================================================== #
    for config in _args.configs:
        out_dir = _args.out_dir / f"config_{config}"
        out_dir.mkdir(parents=True, exist_ok=True)

        for scale in _args.scales:
            print(f"\n[config={config}, scale={scale}]")
            result = process_one(config, scale)
            if result is None:
                print("  [skip] missing g1_nodes.csv or raw events")
                continue

            df, var, comp = result
            n = len(df)

            # ---------- four-dim vectors ----------
            vec_csv = out_dir / f"scale{scale}.csv"
            df.to_csv(vec_csv, index=False, encoding="utf-8-sig")
            print(f"  [saved] {vec_csv.name}  ({n} concepts)")

            # ---------- PCA ----------
            pca_df = pd.DataFrame({
                "component": [f"PC{i+1}" for i in range(4)],
                "var_explained": var,
                "cumulative": np.cumsum(var),
                "b_loading": comp[:, 0],
                "c_loading": comp[:, 1],
                "g1_loading": comp[:, 2],
                "g2_loading": comp[:, 3],
            })
            pca_df.to_csv(out_dir / f"scale{scale}_pca.csv",
                          index=False, encoding="utf-8-sig")
            print(f"  [saved] scale{scale}_pca.csv  "
                  f"PC1={var[0]:.3f}  PC2={var[1]:.3f}")

            # ---------- kNN ----------
            knn_df = find_nearest_neighbors(df, k=_args.knn_k)
            knn_df.to_csv(out_dir / f"scale{scale}_knn.csv",
                          index=False, encoding="utf-8-sig")
            print(f"  [saved] scale{scale}_knn.csv")

            # ---------- convexity grid, dual-mode ----------
            b_lo_values = _default_b_lo_values(df, b_lo_grid=b_lo_grid)

            if _args.method == "holdout":
                sweep_rows = convexity_sweep_dual_holdout(
                    df,
                    c_hi_values=c_hi_values,
                    b_lo_values=b_lo_values,
                    n_splits=_args.n_splits,
                )
            else:
                sweep_rows = convexity_sweep_dual(
                    df,
                    c_hi_values=c_hi_values,
                    b_lo_values=b_lo_values,
                )

            for r in sweep_rows:
                r["config"] = config
                r["scale"] = scale
            sweep_all.extend(sweep_rows)

            grid_df = pd.DataFrame(sweep_rows)
            grid_name = (f"holdout_{config}_scale{scale}.csv"
                         if _args.method == "holdout"
                         else f"grid_{config}_scale{scale}.csv")
            grid_df.to_csv(grids_dir / grid_name,
                           index=False, encoding="utf-8-sig")
            print(f"  [saved] grids/{grid_name}  ({len(sweep_rows)} rows)")

            # console probe
            if _args.method == "holdout":
                for mode in ("4d", "3d"):
                    sub = grid_df[(grid_df["mode"] == mode)
                                  & (grid_df["c_hi"].isin([0.75, 0.85]))]
                    for _, r in sub.iterrows():
                        te = r.get("test_expert_inside_fraction")
                        gi = r.get("general_inside_fraction")
                        sp = r.get("separation")
                        f = lambda v: " None" if v is None or pd.isna(v) else f"{v:6.3f}"
                        print(f"    [{mode} c={r['c_hi']:.2f} b={r['b_lo']:.4f}] "
                              f"n_exp={r['n_expert']:>3d} "
                              f"n_gen={r['n_general']:>3d} "
                              f"test_in={f(te)} "
                              f"gen_in={f(gi)} "
                              f"sep={f(sp)}")
            else:
                for mode in ("4d", "3d"):
                    sub = grid_df[(grid_df["mode"] == mode)
                                  & (grid_df["c_hi"].isin([0.75, 0.85]))]
                    for _, r in sub.iterrows():
                        gof = r.get("general_outside_fraction")
                        emc = r.get("expert_mean_convexity_ratio")
                        f = lambda v: " None" if v is None or pd.isna(v) else f"{v:6.3f}"
                        print(f"    [{mode} c={r['c_hi']:.2f} b={r['b_lo']:.4f}] "
                              f"n_exp={r['n_expert']:>3d} "
                              f"n_gen={r['n_general']:>3d} "
                              f"exp_ratio={f(emc)} "
                              f"out_frac={f(gof)}")

            # descriptive stats (unchanged)
            corr = df[["b", "c_norm", "g1_z", "g2_z"]].corr(method="spearman")
            all_rows.append({
                "config": config, "scale": scale, "n_concepts": n,
                "b_q25": float(df["b"].quantile(0.25)),
                "b_q50": float(df["b"].quantile(0.50)),
                "b_q75": float(df["b"].quantile(0.75)),
                "c_q25": float(df["c"].quantile(0.25)),
                "c_q50": float(df["c"].quantile(0.50)),
                "c_q75": float(df["c"].quantile(0.75)),
                "g1_q25": float(df["g1_z"].quantile(0.25)),
                "g1_q50": float(df["g1_z"].quantile(0.50)),
                "g1_q75": float(df["g1_z"].quantile(0.75)),
                "g2_q25": float(df["g2_z"].quantile(0.25)),
                "g2_q50": float(df["g2_z"].quantile(0.50)),
                "g2_q75": float(df["g2_z"].quantile(0.75)),
                "corr_b_c":   float(corr.iloc[0, 1]),
                "corr_b_g1":  float(corr.iloc[0, 2]),
                "corr_b_g2":  float(corr.iloc[0, 3]),
                "corr_c_g1":  float(corr.iloc[1, 2]),
                "corr_c_g2":  float(corr.iloc[1, 3]),
                "corr_g1_g2": float(corr.iloc[2, 3]),
                "pca_pc1_var":  float(var[0]),
                "pca_pc2_var":  float(var[1]),
                "pca_pc12_cum": float(var[0] + var[1]),
            })

    # ================================================================== #
    # Save all_summary.csv
    # ================================================================== #
    if all_rows:
        summary = pd.DataFrame(all_rows)
        summary.to_csv(_args.out_dir / "all_summary.csv",
                       index=False, encoding="utf-8-sig")
        print(f"\n[saved] all_summary.csv")

    # ================================================================== #
    # Convexity summaries
    # ================================================================== #
    if not sweep_all:
        print("\n[skip] no convexity results.")
        return

    all_grid = pd.DataFrame(sweep_all)
    front = [c for c in ["config", "scale", "mode", "c_hi", "b_lo"]
             if c in all_grid.columns]
    rest = [c for c in all_grid.columns if c not in front]
    all_grid = all_grid[front + rest]

    all_name = ("holdout_ALL.csv" if _args.method == "holdout"
                else "grid_ALL.csv")
    all_grid.to_csv(grids_dir / all_name,
                    index=False, encoding="utf-8-sig")
    print(f"\n[saved] grids/{all_name}  ({len(all_grid)} rows)")

    # Pivot metrics depend on method
    if _args.method == "holdout":
        metrics = [
            "test_expert_inside_fraction",
            "test_expert_inside_std",
            "general_inside_fraction",
            "general_inside_std",
            "separation",
            "test_expert_mean_ratio",
            "general_mean_ratio",
        ]
    else:
        metrics = [
            "expert_mean_convexity_ratio",
            "expert_max_convexity_ratio",
            "general_outside_fraction",
            "general_mean_convexity_ratio",
            "volume_ratio",
        ]

    for mode in ("4d", "3d"):
        sub = all_grid[all_grid["mode"] == mode]
        if sub.empty:
            continue
        for metric in metrics:
            if metric not in sub.columns:
                continue
            pv = sub.pivot_table(index="c_hi", columns="b_lo",
                                 values=metric, aggfunc="mean")
            fname = f"pivot_{metric}_{mode}.csv"
            pv.to_csv(pivots_dir / fname, encoding="utf-8-sig")
            print(f"  [saved] pivots/{fname}")

    # Per-config 3D separation table (holdout only)
    if _args.method == "holdout":
        for config in _args.configs:
            sub = all_grid[(all_grid["mode"] == "3d")
                           & (all_grid["config"] == config)]
            if sub.empty:
                continue
            pv = sub.pivot_table(index="c_hi", columns="b_lo",
                                 values="separation", aggfunc="mean")
            fname = f"pivot_separation_3d_{config}.csv"
            pv.to_csv(pivots_dir / fname, encoding="utf-8-sig")
            print(f"  [saved] pivots/{fname}")

    # Console pivots
    for mode in ("4d", "3d"):
        sub = all_grid[all_grid["mode"] == mode]
        if sub.empty:
            continue
        if _args.method == "holdout":
            key_metrics = ["test_expert_inside_fraction",
                           "general_inside_fraction",
                           "separation"]
        else:
            key_metrics = ["general_outside_fraction",
                           "general_mean_convexity_ratio"]
        for metric in key_metrics:
            if metric not in sub.columns:
                continue
            pv = sub.pivot_table(index="c_hi", columns="b_lo",
                                 values=metric, aggfunc="mean")
            print("\n" + "=" * 70)
            print(f"[{mode}] {metric}  (rows=c_hi, cols=b_lo)")
            print("=" * 70)
            print(pv.round(3).to_string())

if __name__ == "__main__":
    main()