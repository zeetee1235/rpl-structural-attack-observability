#!/usr/bin/env python3
"""
Extract parent switching intervals and probabilities from COOJA.testlog.

Outputs:
  parent_intervals.csv: run_id, scenario, attack_rate, node, parent, t_start, t_end, duration
  parent_pi.csv:        run_id, scenario, attack_rate, node, parent, pi
  neighbors.csv:        run_id, scenario, attack_rate, node, neighbor
"""

import argparse
import csv
import re
from pathlib import Path
from collections import defaultdict


PARENT_RE = re.compile(r"ev=PARENT")
TS_RE = re.compile(r"ts=(\d+)")
NODE_RE = re.compile(r"node=(\d+)")
PARENT_ID_RE = re.compile(r"parent=(\d+)")
ATTACK_RE = re.compile(r"ATTACK_START")
ATTACK_RATE_RE = re.compile(r"rate=([0-9]*\.?[0-9]+)")


def parse_scenario_from_run_id(run_id: str) -> str:
    m = re.match(r"^(.*)_\d{8}_\d{6}$", run_id)
    return m.group(1) if m else run_id


def parse_parent_events(log_file: Path):
    events = defaultdict(list)  # node -> list of (ts, parent)
    attack_rate = None
    max_ts = 0
    with open(log_file, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            ts_m = TS_RE.search(line)
            if ts_m:
                ts_any = int(ts_m.group(1))
                if ts_any > max_ts:
                    max_ts = ts_any
            if ATTACK_RE.search(line):
                m = ATTACK_RATE_RE.search(line)
                if m:
                    attack_rate = float(m.group(1))
            if not PARENT_RE.search(line):
                continue
            ts_m = TS_RE.search(line)
            node_m = NODE_RE.search(line)
            parent_m = PARENT_ID_RE.search(line)
            if not (ts_m and node_m and parent_m):
                continue
            ts = int(ts_m.group(1))
            node = int(node_m.group(1))
            parent = int(parent_m.group(1))
            events[node].append((ts, parent))
    return events, attack_rate, max_ts


def build_intervals(events, end_ts):
    intervals = []
    for node, evs in events.items():
        evs.sort(key=lambda x: x[0])
        # coalesce consecutive same-parent entries
        coalesced = []
        for ts, parent in evs:
            if not coalesced or coalesced[-1][1] != parent:
                coalesced.append((ts, parent))
        for i, (ts, parent) in enumerate(coalesced):
            if i + 1 < len(coalesced):
                t_end = coalesced[i + 1][0]
            else:
                t_end = end_ts
            if t_end < ts:
                continue
            intervals.append((node, parent, ts, t_end, t_end - ts))
    return intervals


def compute_pi(intervals):
    by_node = defaultdict(list)
    for node, parent, t_start, t_end, duration in intervals:
        by_node[node].append((parent, duration))

    pi_rows = []
    neighbors = set()
    for node, entries in by_node.items():
        total = sum(d for _, d in entries)
        if total <= 0:
            continue
        by_parent = defaultdict(int)
        for parent, duration in entries:
            by_parent[parent] += duration
        for parent, duration in by_parent.items():
            neighbors.add((node, parent))
            pi_rows.append((node, parent, duration / total))
    return pi_rows, neighbors


def main():
    parser = argparse.ArgumentParser(description="Extract parent switching stats from COOJA.testlog")
    parser.add_argument("--log-file", type=Path, required=True, help="Path to *_COOJA.testlog")
    parser.add_argument("--output-dir", type=Path, default=Path("data"), help="Output directory")
    parser.add_argument("--end-ts", type=int, help="Optional override for end timestamp")
    args = parser.parse_args()

    run_id = args.log_file.stem.replace("_COOJA", "")
    scenario = parse_scenario_from_run_id(run_id)

    events, attack_rate, max_ts = parse_parent_events(args.log_file)
    end_ts = args.end_ts if args.end_ts is not None else max_ts

    intervals = build_intervals(events, end_ts)
    pi_rows, neighbors = compute_pi(intervals)

    args.output_dir.mkdir(parents=True, exist_ok=True)

    intervals_path = args.output_dir / "parent_intervals.csv"
    pi_path = args.output_dir / "parent_pi.csv"
    neighbors_path = args.output_dir / "neighbors.csv"

    with open(intervals_path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["run_id", "scenario", "attack_rate", "node", "parent", "t_start", "t_end", "duration"])
        for node, parent, t_start, t_end, duration in intervals:
            w.writerow([run_id, scenario, attack_rate, node, parent, t_start, t_end, duration])

    with open(pi_path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["run_id", "scenario", "attack_rate", "node", "parent", "pi"])
        for node, parent, pi in pi_rows:
            w.writerow([run_id, scenario, attack_rate, node, parent, pi])

    with open(neighbors_path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["run_id", "scenario", "attack_rate", "node", "neighbor"])
        for node, parent in sorted(neighbors):
            w.writerow([run_id, scenario, attack_rate, node, parent])

    print(f"Wrote {intervals_path}, {pi_path}, {neighbors_path}")


if __name__ == "__main__":
    main()
