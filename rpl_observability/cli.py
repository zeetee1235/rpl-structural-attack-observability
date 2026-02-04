"""CLI entrypoint for observability analysis."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from .analysis import ObservabilityConfig, build_observability_summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="RPL structural observability analysis")
    parser.add_argument("--topology-log", required=True, help="CSV of topology edges")
    parser.add_argument("--routing-log", required=True, help="CSV of routing paths")
    parser.add_argument("--performance-log", required=True, help="CSV of performance metrics")
    parser.add_argument("--attacker-id", default="A", help="Attacker node id")
    parser.add_argument("--output", required=True, help="Output CSV path")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    topology_edges = pd.read_csv(args.topology_log)
    routing_paths = pd.read_csv(args.routing_log)
    performance_metrics = pd.read_csv(args.performance_log)

    config = ObservabilityConfig(attacker_id=str(args.attacker_id))
    summary = build_observability_summary(
        topology_edges=topology_edges,
        routing_paths=routing_paths,
        performance_metrics=performance_metrics,
        config=config,
    )

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    summary.to_csv(output_path, index=False)


if __name__ == "__main__":
    main()
