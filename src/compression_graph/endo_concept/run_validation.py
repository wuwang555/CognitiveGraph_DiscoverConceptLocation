# -*- coding: utf-8 -*-
"""
run_validation.py -- Orchestrate G1 export + six-quadrant evaluation
                    across A/B/C configs.

Because `config.py` reads CONFIG_METHOD from the environment at import
time, we spin up one subprocess per config to isolate module caches.

Usage
-----
    cd src/compression_graph/endo_concept
    python run_validation.py                       # all configs
    python run_validation.py --configs A B         # subset
    python run_validation.py --skip-export         # reuse existing G1
"""
import argparse
import os
import subprocess
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--configs", nargs="+", default=["A", "B", "C"])
    ap.add_argument("--scales", nargs="+", type=int, default=[51, 71, 91, 111])
    ap.add_argument("--iterations", type=int, default=10000)
    ap.add_argument("--skip-export", action="store_true")
    args = ap.parse_args()

    ok_configs = []

    for config in args.configs:
        print("\n" + "=" * 72)
        print(f"# Config {config}")
        print("=" * 72)

        if not args.skip_export:
            env = os.environ.copy()
            env["CONFIG_METHOD"] = config
            cmd = [
                sys.executable, str(_HERE / "g1_exporter.py"),
                "--config", config,
                "--iterations", str(args.iterations),
                "--scales", *[str(s) for s in args.scales],
            ]
            print(">>", " ".join(cmd))
            r = subprocess.run(cmd, env=env)
            if r.returncode != 0:
                print(f"[error] G1 export failed for config {config}")
                continue

        cmd = [
            sys.executable, str(_HERE / "six_quadrant_eval.py"),
            "--config", config,
            "--scales", *[str(s) for s in args.scales],
        ]
        print(">>", " ".join(cmd))
        r = subprocess.run(cmd)
        if r.returncode != 0:
            print(f"[error] six-quadrant eval failed for config {config}")
            continue
        ok_configs.append(config)

    print("\n" + "=" * 72)
    print(f"Completed: {ok_configs}")
    print("=" * 72)


if __name__ == "__main__":
    main()