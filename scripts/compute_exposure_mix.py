#!/usr/bin/env python3
"""
Compute E_mix from parent_pi.csv by solving linear system for q_i.
"""

import argparse
import csv
from collections import defaultdict
from pathlib import Path
import math


def load_pi(pi_file):
    rows = []
    with open(pi_file, newline="") as f:
        r = csv.DictReader(f)
        for row in r:
            rows.append(row)
    return rows


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


def solve_linear_system(A, b):
    # Simple Gauss-Jordan elimination
    n = len(b)
    if n == 0:
        return []
    # Augmented matrix
    M = [A[i][:] + [b[i]] for i in range(n)]
    for i in range(n):
        # Find pivot
        pivot = i
        for j in range(i, n):
            if abs(M[j][i]) > abs(M[pivot][i]):
                pivot = j
        if abs(M[pivot][i]) < 1e-12:
            continue
        M[i], M[pivot] = M[pivot], M[i]
        # Normalize
        div = M[i][i]
        M[i] = [v / div for v in M[i]]
        # Eliminate
        for j in range(n):
            if j == i:
                continue
            factor = M[j][i]
            if abs(factor) < 1e-12:
                continue
            M[j] = [M[j][k] - factor * M[i][k] for k in range(n + 1)]
    return [M[i][n] for i in range(n)]


def main():
    parser = argparse.ArgumentParser(description="Compute E_mix from parent_pi.csv")
    parser.add_argument("--parent-pi", type=Path, required=True, help="parent_pi.csv")
    parser.add_argument("--attacker", type=int, required=True, help="Attacker node id")
    parser.add_argument("--root", type=int, required=True, help="Root node id")
    parser.add_argument("--senders", type=Path, help="CSV of sender node ids (one per line)")
    parser.add_argument("--output", type=Path, default=Path("data/exposure_mix.csv"))
    parser.add_argument("--q-output", type=Path, default=Path("data/q_values.csv"))
    args = parser.parse_args()

    rows = load_pi(args.parent_pi)
    senders = parse_senders(args.senders)

    # group by run_id
    by_run = defaultdict(list)
    for row in rows:
        by_run[row["run_id"]].append(row)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.q_output.parent.mkdir(parents=True, exist_ok=True)

    with open(args.output, "w", newline="") as f_out, open(args.q_output, "w", newline="") as f_q:
        w_out = csv.writer(f_out)
        w_q = csv.writer(f_q)
        w_out.writerow(["run_id", "scenario", "attack_rate", "attacker", "E_mix"])
        w_q.writerow(["run_id", "scenario", "attack_rate", "node", "q"])

        for run_id, rows_run in by_run.items():
            scenario = rows_run[0].get("scenario")
            attack_rate = rows_run[0].get("attack_rate")

            pi = defaultdict(dict)  # node -> parent -> pi
            nodes = set()
            for row in rows_run:
                node = int(row["node"])
                parent = int(row["parent"])
                p = float(row["pi"])
                pi[node][parent] = pi[node].get(parent, 0.0) + p
                nodes.add(node)
                nodes.add(parent)

            # normalize rows
            for node in list(pi.keys()):
                total = sum(pi[node].values())
                if total > 0:
                    for parent in list(pi[node].keys()):
                        pi[node][parent] /= total

            if senders is None:
                senders_run = {n for n in nodes if n not in (args.root, args.attacker)}
            else:
                senders_run = set(senders)

            unknowns = [n for n in nodes if n not in (args.root, args.attacker)]
            index = {n: i for i, n in enumerate(unknowns)}
            n = len(unknowns)

            A = [[0.0 for _ in range(n)] for _ in range(n)]
            b = [0.0 for _ in range(n)]

            for node in unknowns:
                i = index[node]
                A[i][i] = 1.0
                if node not in pi:
                    b[i] = 0.0
                    continue
                for parent, p in pi[node].items():
                    if parent == args.attacker:
                        b[i] += p * 1.0
                    elif parent == args.root:
                        b[i] += 0.0
                    elif parent in index:
                        A[i][index[parent]] -= p
                    else:
                        b[i] += 0.0

            q_unknowns = solve_linear_system(A, b)
            q = {args.attacker: 1.0, args.root: 0.0}
            for node, val in zip(unknowns, q_unknowns):
                q[node] = max(0.0, min(1.0, val))

            # compute E_mix
            if not senders_run:
                e_mix = 0.0
            else:
                total = len(senders_run)
                acc = sum(q.get(i, 0.0) for i in senders_run)
                e_mix = acc / total

            w_out.writerow([run_id, scenario, attack_rate, args.attacker, e_mix])
            for node, val in q.items():
                w_q.writerow([run_id, scenario, attack_rate, node, val])

    print(f"Wrote {args.output} and {args.q_output}")


if __name__ == "__main__":
    main()
