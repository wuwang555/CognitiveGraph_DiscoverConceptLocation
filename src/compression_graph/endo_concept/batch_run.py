# -*- coding: utf-8 -*-
"""
Batch experiment runner.

For each CONFIG_METHOD in {"A", "B"}:
  1. Run `run_static.py` to generate that configB.md's raw compression events.
  2. Copy raw_compression_events.csv to endo_result/raw_events_{X}/.
  3. Run `run_endo.py` with ENDO_RAW_CSV / ENDO_OUTPUT_DIR / CONFIG_METHOD.

run_endo.py itself loops over:
  - scales           : [51, 71, 91, 111]
  - min_itemset_sizes: [1, 2, 3]
  - fixpoint_methods : ["A", "B", "C", "ABC"]

Final layout:
    endo_result/
        endo_summary.csv
        raw_events_A/raw_compression_events.csv
        raw_events_B/raw_compression_events.csv
        scale51/config_A/minsize_1/fixpoint_A/{fixpoints.json, ...}
        scale51/config_A/minsize_1/fixpoint_B/...
        ...
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path

_HERE = Path(__file__).resolve().parent      # .../endo_concept
_CG = _HERE.parent                            # .../compression_graph
_PROJ = _CG.parent                            # project root


def _run(cmd, cwd, env):
    print(f"\n$ (cwd={cwd}) {' '.join(str(x) for x in cmd)}")
    subprocess.run(
        [str(x) for x in cmd],
        cwd=str(cwd),
        env=env,
        check=True,
    )


def main():
    config_methods = ["C"]

    base_env = os.environ.copy()
    base_env["PYTHONHASHSEED"] = "0"       # 固定 set/frozenset 迭代顺序

    raw_root = _PROJ / "results" / "compression_graph"
    endo_result = _PROJ / "results" / "endo_result"
    endo_result.mkdir(parents=True, exist_ok=True)

    for config_method in config_methods:
        env = base_env.copy()
        env["CONFIG_METHOD"] = config_method

        print(f"\n{'#' * 70}")
        print(f"# CONFIG_METHOD = {config_method}")
        print(f"{'#' * 70}")

        # 1. Generate raw compression events for this configB.md
        _run(
            [sys.executable, _CG / "run_static.py"],
            cwd=_CG,
            env=env,
        )

        # 2. Preserve this configB.md's raw events
        src = raw_root / "raw_compression_events.csv"
        dst_dir = endo_result / f"raw_events_{config_method}"
        dst_dir.mkdir(parents=True, exist_ok=True)
        dst = dst_dir / "raw_compression_events.csv"
        if src.exists():
            shutil.copy(src, dst)
            print(f"[copy] {src} -> {dst}")
        else:
            print(f"[WARN] raw events not found: {src}")
            continue

        # 3. Run the full endo grid for this configB.md
        env["ENDO_RAW_CSV"] = str(dst)
        env["ENDO_OUTPUT_DIR"] = str(endo_result)
        _run(
            [sys.executable, _HERE / "run_endo.py"],
            cwd=_HERE,
            env=env,
        )

    # ---- Final summary ----
    summary = endo_result / "endo_summary.csv"
    if summary.exists():
        import pandas as pd
        print(f"\n{'=' * 70}")
        print(f"All done. Summary: {summary}")
        print(pd.read_csv(summary).to_string(index=False))
    else:
        print("\n[WARN] endo_summary.csv was not produced.")


if __name__ == "__main__":
    main()