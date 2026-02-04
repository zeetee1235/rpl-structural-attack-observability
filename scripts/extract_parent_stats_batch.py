#!/usr/bin/env python3
"""
Batch extraction of parent switching stats from multiple *_COOJA.testlog files.

Outputs combined CSVs:
  parent_intervals.csv
  parent_pi.csv
  neighbors.csv
"""

import argparse
import csv
import glob
import re
from pathlib import Path
from collections import defaultdict
from datetime import datetime


PARENT_RE = re.compile(r"ev=PARENT")
TS_RE = re.compile(r"ts=(\d+)")
NODE_RE = re.compile(r"node=(\d+)")
PARENT_ID_RE = re.compile(r"parent=(\d+)")
ATTACK_RE = re.compile(r"ATTACK_START")
ATTACK_RATE_RE = re.compile(r"rate=([0-9]*\.?[0-9]+)")


def parse_scenario_from_run_id(run_id: str) -> str:
    m = re.match(r"^(.*)_\d{8}_\d{6}$", run_id)
    return m.group(1) if m else run_id


def extract_timestamp_from_run_id(run_id: str):
    m = re.match(r"^.*_(\d{8})_(\d{6})$", run_id)
    if not m:
        return None
    try:
        return datetime.strptime(m.group(1) + m.group(2), "%Y%m%d%H%M%S").timestamp()
    except Exception:
        return None


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
        coalesced = []
        for ts, parent in evs:
            if not coalesced or coalesced[-1][1] != parent:
                coalesced.append((ts, parent))
        for i, (ts, parent) in enumerate(coalesced):
            t_end = coalesced[i + 1][0] if i + 1 < len(coalesced) else end_ts
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
    parser = argparse.ArgumentParser(description="Batch extract parent switching stats")
    parser.add_argument("--log-glob", type=str, default="simulations/output/*_COOJA.testlog",
                        help="Glob for COOJA testlogs")
    parser.add_argument("--since-log", type=Path,
                        help="Only include runs after this experiment_run_*.log timestamp")
    parser.add_argument("--output-dir", type=Path, default=Path("data"))
    args = parser.parse_args()

    since_ts = None
    if args.since_log and args.since_log.exists():
        name = args.since_log.stem.replace("experiment_run_", "")
        try:
            since_ts = datetime.strptime(name, "%Y%m%d_%H%M%S").timestamp()
        except Exception:
            since_ts = None

    testlogs = sorted(glob.glob(args.log_glob))
    if not testlogs:
        raise SystemExit("No testlogs found")

    intervals_all = []
    pi_all = []
    neighbors_all = set()

    for path in testlogs:
        log_file = Path(path)
        run_id = log_file.stem.replace("_COOJA", "")
        ts = extract_timestamp_from_run_id(run_id)
        if since_ts is not None and ts is not None and ts < since_ts:
            continue
        scenario = parse_scenario_from_run_id(run_id)
        events, attack_rate, max_ts = parse_parent_events(log_file)
        if not events:
            continue
        intervals = build_intervals(events, max_ts)
        pi_rows, neighbors = compute_pi(intervals)
        for node, parent, t_start, t_end, duration in intervals:
            intervals_all.append([run_id, scenario, attack_rate, node, parent, t_start, t_end, duration])
        for node, parent, pi in pi_rows:
            pi_all.append([run_id, scenario, attack_rate, node, parent, pi])
        for node, parent in neighbors:
            neighbors_all.add((run_id, scenario, attack_rate, node, parent))

    args.output_dir.mkdir(parents=True, exist_ok=True)
    intervals_path = args.output_dir / "parent_intervals.csv"
    pi_path = args.output_dir / "parent_pi.csv"
    neighbors_path = args.output_dir / "neighbors.csv"

    with open(intervals_path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["run_id", "scenario", "attack_rate", "node", "parent", "t_start", "t_end", "duration"])
        w.writerows(intervals_all)

    with open(pi_path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["run_id", "scenario", "attack_rate", "node", "parent", "pi"])
        w.writerows(pi_all)

    with open(neighbors_path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["run_id", "scenario", "attack_rate", "node", "neighbor"])
        for row in sorted(neighbors_all):
            w.writerow(row)

    print(f"Wrote {intervals_path}, {pi_path}, {neighbors_path}")


if __name__ == "__main__":
    main()
