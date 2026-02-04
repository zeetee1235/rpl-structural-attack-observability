#!/usr/bin/env python3
"""
Compute E_tree from parent_intervals.csv using the last parent snapshot per run.
"""

import argparse
import csv
from collections import defaultdict, deque
from pathlib import Path


def parse_senders(senders_csv):
    if not senders_csv:
        return None
    senders = set()
    with open(senders_csv, newline="") as f:
        r = csv.reader(f)
        for row in r:
            if not row:
                continue
            senders.add(int(row[0]))
    return senders


def main():
    parser = argparse.ArgumentParser(description="Compute E_tree from parent_intervals.csv")
    parser.add_argument("--parent-intervals", type=Path, required=True, help="parent_intervals.csv")
    parser.add_argument("--attacker", type=int, required=True, help="Attacker node id")
    parser.add_argument("--root", type=int, required=True, help="Root node id")
    parser.add_argument("--senders", type=Path, help="CSV of sender node ids (one per line)")
    parser.add_argument("--output", type=Path, default=Path("data/exposure_tree.csv"))
    args = parser.parse_args()

    senders = parse_senders(args.senders)

    rows = []
    with open(args.parent_intervals, newline="") as f:
        r = csv.DictReader(f)
        for row in r:
            rows.append(row)

    by_run = defaultdict(list)
    for row in rows:
        by_run[row["run_id"]].append(row)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w", newline="") as f_out:
        w = csv.writer(f_out)
        w.writerow(["run_id", "scenario", "attack_rate", "attacker", "E_tree", "subtree_size"])

        for run_id, rows_run in by_run.items():
            scenario = rows_run[0].get("scenario")
            attack_rate = rows_run[0].get("attack_rate")

            # last parent snapshot per node (max t_end)
            last_parent = {}
            nodes = set()
            for row in rows_run:
                node = int(row["node"])
                parent = int(row["parent"])
                t_end = int(row["t_end"])
                nodes.add(node)
                nodes.add(parent)
                if node not in last_parent or t_end > last_parent[node][0]:
                    last_parent[node] = (t_end, parent)

            children = defaultdict(list)
            for node, (_, parent) in last_parent.items():
                children[parent].append(node)

            # descendants of attacker
            desc = set()
            q = deque([args.attacker])
            while q:
                cur = q.popleft()
                for ch in children.get(cur, []):
                    if ch not in desc:
                        desc.add(ch)
                        q.append(ch)

            if senders is None:
                senders_run = {n for n in nodes if n not in (args.root, args.attacker)}
            else:
                senders_run = set(senders)

            if not senders_run:
                e_tree = 0.0
            else:
                acc = sum(1 for i in senders_run if i in desc)
                e_tree = acc / len(senders_run)

            w.writerow([run_id, scenario, attack_rate, args.attacker, e_tree, len(desc)])

    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()
