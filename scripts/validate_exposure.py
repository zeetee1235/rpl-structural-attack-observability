#!/usr/bin/env python3
"""
Compare E_log (proxy) with E_mix and E_tree.
Outputs exposure_comparison.csv and prints simple correlations.
"""

import argparse
import csv
from collections import defaultdict
from pathlib import Path
import math


def load_csv(path):
    with open(path, newline="") as f:
        return list(csv.DictReader(f))


def mean(values):
    vals = [v for v in values if v is not None]
    if not vals:
        return None
    return sum(vals) / len(vals)


def corr(x, y):
    pairs = [(a, b) for a, b in zip(x, y) if a is not None and b is not None]
    if len(pairs) < 2:
        return None
    xs, ys = zip(*pairs)
    mx = sum(xs) / len(xs)
    my = sum(ys) / len(ys)
    num = sum((a - mx) * (b - my) for a, b in pairs)
    den = math.sqrt(sum((a - mx) ** 2 for a in xs) * sum((b - my) ** 2 for b in ys))
    if den == 0:
        return None
    return num / den


def main():
    parser = argparse.ArgumentParser(description="Validate exposure estimates")
    parser.add_argument("--summary", type=Path, required=True, help="simulation_summary_*.csv")
    parser.add_argument("--exposure-mix", type=Path, required=True, help="exposure_mix.csv")
    parser.add_argument("--exposure-tree", type=Path, required=True, help="exposure_tree.csv")
    parser.add_argument("--output", type=Path, default=Path("data/exposure_comparison.csv"))
    args = parser.parse_args()

    summary = load_csv(args.summary)
    mix = load_csv(args.exposure_mix)
    tree = load_csv(args.exposure_tree)

    # aggregate summary by scenario + attack_rate
    s_by_key = defaultdict(list)
    for row in summary:
        key = (row["scenario"], row.get("attack_rate_logged"))
        e_log = float(row["exposure_e1_prime"]) if row.get("exposure_e1_prime") not in (None, "", "None") else None
        pdr = float(row["pdr_clipped"]) if row.get("pdr_clipped") not in (None, "", "None") else None
        s_by_key[key].append((e_log, pdr))

    mix_by_key = defaultdict(list)
    for row in mix:
        key = (row["scenario"], row.get("attack_rate"))
        mix_by_key[key].append(float(row["E_mix"]))

    tree_by_key = defaultdict(list)
    for row in tree:
        key = (row["scenario"], row.get("attack_rate"))
        tree_by_key[key].append(float(row["E_tree"]))

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w", newline="") as f_out:
        w = csv.writer(f_out)
        w.writerow(["scenario", "attack_rate", "E_log", "E_mix", "E_tree", "PDR_star"])
        rows = []
        for key in sorted(s_by_key.keys()):
            e_log = mean([v[0] for v in s_by_key[key]])
            pdr = mean([v[1] for v in s_by_key[key]])
            e_mix = mean(mix_by_key.get(key, []))
            e_tree = mean(tree_by_key.get(key, []))
            w.writerow([key[0], key[1], e_log, e_mix, e_tree, pdr])
            rows.append((e_log, e_mix, e_tree, pdr))

    e_logs = [r[0] for r in rows]
    e_mixes = [r[1] for r in rows]
    e_trees = [r[2] for r in rows]
    pdrs = [r[3] for r in rows]

    print(f"Wrote {args.output}")
    print("Correlation:")
    print(f"  E_log vs E_mix: {corr(e_logs, e_mixes)}")
    print(f"  E_log vs E_tree: {corr(e_logs, e_trees)}")
    print(f"  PDR* vs (alpha*E_mix): compute offline if needed")


if __name__ == "__main__":
    main()
