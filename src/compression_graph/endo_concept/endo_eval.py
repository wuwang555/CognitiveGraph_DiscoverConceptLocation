# -*- coding: utf-8 -*-
"""
endo_eval.py -- Verification metrics for endo-concepts.

After revision, the tool focuses on what is statistically meaningful
given the available data.

Removed:
    - meta-spread  (invalid on size-1 fixpoints; meta coverage too low)

Added:
    - domain enrichment ratios (log-ratio, descriptive)
    - cross-scale C/B trajectory analysis + shape classification
    - Kruskal-Wallis across configs (with sample-size caveat)

Checks
------
1. Single-scale: stability gap (Mann-Whitney U, one-sided)   [CORE]
2. Single-scale: domain enrichment (log-ratio)               [descriptive]
3. Single-scale: binomial C/B                                [caveat]
4. Cross-scale:  C/B trajectory shape + Kruskal-Wallis       [descriptive]

Usage
-----
    # Single scale
    python endo_eval.py --mode single --root endo_result --scale 51

    # Cross-scale trajectory
    python endo_eval.py --mode trajectory --root endo_result --scales 51 71 91 111

    # Both (default)
    python endo_eval.py --mode all --root endo_result --scales 51 71 91 111
"""

import argparse
import json
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats


# ===================================================================== #
# Config loading (graceful fallback)
# ===================================================================== #
def _safe_import_config():
    try:
        from config import (
            CONCEPT_DOMAINS_A, CONCEPT_DOMAINS_B, CONCEPT_DOMAINS_C,
        )
        return {
            "A": CONCEPT_DOMAINS_A,
            "B": CONCEPT_DOMAINS_B,
            "C": CONCEPT_DOMAINS_C,
        }
    except Exception as e:
        print(f"[WARN] Could not import configB.md: {e}")
        return {"A": {}, "B": {}, "C": {}}


CONFIG_DOMAINS = _safe_import_config()


# ===================================================================== #
# Helpers
# ===================================================================== #
def build_concept_to_domain(domain_map):
    c2d = {}
    for dom, concepts in domain_map.items():
        for c in concepts:
            c2d[c] = dom
    return c2d


def load_fixpoints(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def cores_of(fps):
    return {tuple(sorted(fp["core"])) for fp in fps}


def stability_map(fps):
    return {tuple(sorted(fp["core"])): fp.get("stability", 0.0) for fp in fps}


def fixpoint_main_domain(core, c2d):
    """Majority-vote domain for a fixpoint.

    For size-1 fixpoints this is just the domain of the single concept.
    For size>1 fixpoints it is the most common domain among members.
    """
    domains = [c2d.get(c, "UNKNOWN") for c in core]
    if not domains:
        return "UNKNOWN"
    return Counter(domains).most_common(1)[0][0]


def find_fixpoint_dir(root, scale, config_label, minsize, method):
    """Resolve fixpoint directory across possible layouts."""
    candidates = [
        Path(root) / f"scale{scale}" / f"config_{config_label}"
        / f"minsize_{minsize}" / f"fixpoint_{method}",
        Path(root) / f"scale{scale}" / f"config_{config_label}"
        / f"fixpoint_{method}",
        Path(root) / f"scale{scale}" / f"config_{config_label}"
        / f"minsize_{minsize}_{method}",
    ]
    for p in candidates:
        f = p / "fixpoints.json"
        if f.exists():
            return f
    return None


# ===================================================================== #
# Single-scale analysis
# ===================================================================== #
def analyze_one_scale(root, scale, minsize, configs):
    """Run all single-scale checks and return per-configB.md rows."""
    rows = []
    for cfg in configs:
        b_path = find_fixpoint_dir(root, scale, cfg, minsize, "B")
        c_path = find_fixpoint_dir(root, scale, cfg, minsize, "C")
        if not b_path or not c_path:
            continue

        b_fps = load_fixpoints(b_path)
        c_fps = load_fixpoints(c_path)
        b_cores = cores_of(b_fps)
        c_cores = cores_of(c_fps)
        bc_cores = b_cores - c_cores

        # ---- Check 1: stability gap ----
        b_stab = stability_map(b_fps)
        c_stab = stability_map(c_fps)
        bc_stability = [b_stab[c] for c in bc_cores if c in b_stab]
        c_stability = [c_stab[c] for c in c_cores if c in c_stab]

        p_stab = None
        if len(bc_stability) >= 3 and len(c_stability) >= 3:
            try:
                _, p_stab = stats.mannwhitneyu(
                    c_stability, bc_stability, alternative="greater"
                )
            except Exception:
                pass

        # ---- Check 2: domain composition (log-enrichment) ----
        c2d = build_concept_to_domain(CONFIG_DOMAINS.get(cfg, {}))
        bc_domains = Counter(fixpoint_main_domain(c, c2d) for c in bc_cores)
        c_domains = Counter(fixpoint_main_domain(c, c2d) for c in c_cores)

        bc_total = sum(bc_domains.values())
        c_total = sum(c_domains.values())
        enrichment = {}
        for d in set(bc_domains) | set(c_domains):
            bf = bc_domains.get(d, 0) / bc_total if bc_total else 0.0
            cf = c_domains.get(d, 0) / c_total if c_total else 0.0
            enrichment[d] = float(np.log(max(bf, 1e-6) / max(cf, 1e-6)))

        rows.append({
            "configB.md": cfg,
            "scale": scale,
            "minsize": minsize,
            "n_B": len(b_fps),
            "n_C": len(c_fps),
            "n_BC": len(bc_cores),
            "CB": len(c_fps) / len(b_fps) if b_fps else 0.0,
            "BC_stability_mean":
                float(np.mean(bc_stability)) if bc_stability else 0.0,
            "C_stability_mean":
                float(np.mean(c_stability)) if c_stability else 0.0,
            "MW_stability_p": p_stab,
            "BC_domains": dict(bc_domains),
            "C_domains": dict(c_domains),
            "domain_enrichment": enrichment,
        })
    return rows


def binomial_CB_test(rows):
    """Binomial test: do configs share the same C/B ratio? (level shift only)"""
    if len(rows) < 2:
        return []
    total_b = sum(r["n_B"] for r in rows)
    total_c = sum(r["n_C"] for r in rows)
    if total_b == 0:
        return []
    p_mle = total_c / total_b
    out = []
    for r in rows:
        n, k = r["n_B"], r["n_C"]
        if n == 0:
            continue
        cdf = stats.binom.cdf(k, n, p_mle)
        sf = 1 - stats.binom.cdf(k - 1, n, p_mle)
        p_two = min(1.0, 2 * min(cdf, sf))
        out.append({
            "configB.md": r["configB.md"],
            "n_B": n,
            "n_C": k,
            "observed_CB": round(k / n, 4),
            "pooled_CB": round(p_mle, 4),
            "binomial_two_sided_p": float(p_two),
        })
    return out


# ===================================================================== #
# Cross-scale trajectory analysis
# ===================================================================== #
def classify_trajectory(values, eps=0.05):
    """Classify a C/B sequence into a coarse shape.

    monotonic_up   : no significant decrease, at least one increase
    monotonic_down : no significant increase, at least one decrease
    u_shape        : first significant move is down, last is up
    n_shape        : first significant move is up, last is down
    irregular      : everything else
    """
    if len(values) < 3:
        return "too_short"
    diffs = [values[i + 1] - values[i] for i in range(len(values) - 1)]
    ups = sum(1 for d in diffs if d > eps)
    downs = sum(1 for d in diffs if d < -eps)

    if downs == 0 and ups >= 1:
        return "monotonic_up"
    if ups == 0 and downs >= 1:
        return "monotonic_down"

    signs = [1 if d > eps else (-1 if d < -eps else 0) for d in diffs]
    signs = [s for s in signs if s != 0]
    if len(signs) >= 2:
        if signs[0] == 1 and signs[-1] == -1:
            return "n_shape"
        if signs[0] == -1 and signs[-1] == 1:
            return "u_shape"
    return "irregular"


def analyze_trajectory(root, scales, minsize, configs):
    """C/B trajectory across scales; shape classification; KW test."""
    all_rows = []
    for s in scales:
        all_rows.extend(analyze_one_scale(root, s, minsize, configs))
    if not all_rows:
        return None, None, None, None

    df = pd.DataFrame([
        {k: v for k, v in r.items()
         if k not in ("BC_domains", "C_domains", "domain_enrichment")}
        for r in all_rows
    ])

    pivot = df.pivot(index="scale", columns="configB.md", values="CB").sort_index()

    shapes = {}
    for cfg in pivot.columns:
        shapes[cfg] = classify_trajectory(pivot[cfg].dropna().tolist())

    # KW: groups are by configB.md (each group = one configB.md's C/B across scales)
    groups = [pivot[cfg].dropna().tolist() for cfg in pivot.columns
              if len(pivot[cfg].dropna()) >= 2]

    kw_stat = None
    kw_p = None
    if len(groups) >= 2 and all(len(g) >= 2 for g in groups):
        try:
            kw_stat, kw_p = stats.kruskal(*groups)
        except Exception:
            pass

    return pivot, shapes, (kw_stat, kw_p), df


# ===================================================================== #
# Printers
# ===================================================================== #
def print_single_scale(rows):
    if not rows:
        return

    print("\n" + "=" * 72)
    print("Check 1: Stability gap (Mann-Whitney U, one-sided)  [CORE]")
    print("=" * 72)
    df = pd.DataFrame([{
        "configB.md": r["configB.md"],
        "scale": r["scale"],
        "n_B": r["n_B"],
        "n_C": r["n_C"],
        "C_stability": round(r["C_stability_mean"], 4),
        "BC_stability": round(r["BC_stability_mean"], 4),
        "delta": round(r["C_stability_mean"] - r["BC_stability_mean"], 4),
        "MW_p": r["MW_stability_p"],
    } for r in rows])
    print(df.to_string(index=False))
    for r in rows:
        p = r["MW_stability_p"]
        if p is not None:
            verdict = "PASS" if p < 0.05 else "not significant"
            delta = r["C_stability_mean"] - r["BC_stability_mean"]
            print(f"  [{r['configB.md']}] C vs BC: delta={delta:+.4f}, "
                  f"p={p:.2e}  [{verdict}]")

    print("\n" + "=" * 72)
    print("Check 2: Domain enrichment (B-C vs C), log-ratio  [descriptive]")
    print("=" * 72)
    for r in rows:
        print(f"\n[configB.md {r['configB.md']}]")
        print(f"  B-C domains: {r['BC_domains']}")
        print(f"      C domains: {r['C_domains']}")
        enrich = {k: v for k, v in r["domain_enrichment"].items()
                  if k != "UNKNOWN"}
        if enrich:
            print("  log-enrichment (B-C fraction / C fraction), sorted:")
            for d, v in sorted(enrich.items(), key=lambda kv: kv[1]):
                marker = "↑BC" if v > 0.3 else ("↓BC" if v < -0.3 else "")
                print(f"    {d:24s} {v:+.3f}  {marker}")
            print("  ↑BC: this domain contributes more B-C than C "
                  "(more 'universal' items here)")
            print("  ↓BC: this domain contributes more C than B-C "
                  "(more 'specialized' items here)")

    print("\n" + "=" * 72)
    print("Check 3: Binomial C/B  [caveat: level-shift only]")
    print("=" * 72)
    binom = binomial_CB_test(rows)
    if binom:
        print(pd.DataFrame(binom).to_string(index=False))
        print("\n  Caveat: this test assumes configs differ by a level shift.")
        print("  It does NOT detect trajectory-shape differences.")
        print("  See Check 4 for trajectory analysis.")


def print_trajectory(pivot, shapes, kw, df):
    if pivot is None:
        return

    print("\n" + "=" * 72)
    print("Check 4: C/B trajectory across scales")
    print("=" * 72)
    print(pivot.round(4).to_string())

    print("\n  Trajectory shapes:")
    for cfg, shape in shapes.items():
        values = pivot[cfg].dropna().tolist()
        formatted = " -> ".join(f"{v:.3f}" for v in values)
        print(f"    configB.md {cfg}: {formatted}  [{shape}]")

    if kw is not None and kw[0] is not None and kw[1] is not None:
        kw_stat, kw_p = kw
        print(f"\n  Kruskal-Wallis across configs "
              f"(each group n={len(pivot)}): H={kw_stat:.4f}, p={kw_p:.4f}")
        print("  Note: n per group is small (one value per scale).")
        print("  KW has low power here; treat as descriptive, not inferential.")

    print("\n  Raw counts:")
    print(df.to_string(index=False))


# ===================================================================== #
# Main
# ===================================================================== #
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["single", "trajectory", "all"],
                    default="all")
    ap.add_argument("--root", default="endo_result")
    ap.add_argument("--scale", type=int, default=51)
    ap.add_argument("--scales", nargs="+", type=int,
                    default=[51, 71, 91, 111])
    ap.add_argument("--minsize", type=int, default=1)
    ap.add_argument("--configs", nargs="+", default=["A", "B", "C"])
    ap.add_argument("--csv", default=None,
                    help="If set, save the single-scale summary to this CSV.")
    args = ap.parse_args()

    if args.mode in ("single", "all"):
        rows = analyze_one_scale(args.root, args.scale,
                                 args.minsize, args.configs)
        if not rows:
            print("[ERROR] no single-scale data. Check --root / --scale.")
        else:
            print_single_scale(rows)
            if args.csv:
                out = Path(args.csv)
                out.parent.mkdir(parents=True, exist_ok=True)
                df = pd.DataFrame([
                    {k: v for k, v in r.items()
                     if k not in ("BC_domains", "C_domains",
                                  "domain_enrichment")}
                    for r in rows
                ])
                df.to_csv(out, index=False, encoding="utf-8-sig")
                print(f"\nSaved: {out}")

    if args.mode in ("trajectory", "all"):
        pivot, shapes, kw, df = analyze_trajectory(
            args.root, args.scales, args.minsize, args.configs
        )
        if pivot is None:
            print("[ERROR] no trajectory data.")
        else:
            print_trajectory(pivot, shapes, kw, df)


if __name__ == "__main__":
    main()