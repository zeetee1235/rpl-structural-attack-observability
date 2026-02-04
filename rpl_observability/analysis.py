"""Observability analysis combining structural metrics with performance logs."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from .metrics import (
    compute_attack_exposure,
    compute_average_path_length,
    compute_betweenness_centrality,
    compute_path_diversity,
    parse_path_series,
)


@dataclass(frozen=True)
class ObservabilityConfig:
    attacker_id: str


def build_observability_summary(
    topology_edges: pd.DataFrame,
    routing_paths: pd.DataFrame,
    performance_metrics: pd.DataFrame,
    config: ObservabilityConfig,
) -> pd.DataFrame:
    """Build per-window observability summary.

    Returns a DataFrame with structural metrics (APL, PD, exposure, BC) joined with
    performance metrics (PDR, delay, attack rate) for each window and node.
    """
    routing_paths = routing_paths.copy()
    routing_paths["parsed_path"] = parse_path_series(routing_paths["path"])

    grouped = routing_paths.groupby(["time_window", "node_id"], dropna=False)
    rows = []
    for (time_window, node_id), group in grouped:
        paths = group["parsed_path"].tolist()
        rows.append(
            {
                "time_window": time_window,
                "node_id": str(node_id),
                "avg_path_length": compute_average_path_length(paths),
                "path_diversity": compute_path_diversity(paths),
                "attack_exposure": compute_attack_exposure(paths, config.attacker_id),
            }
        )

    metrics_df = pd.DataFrame(rows)
    metrics_df["betweenness_centrality"] = compute_betweenness_centrality(
        topology_edges, config.attacker_id
    )

    performance_metrics = performance_metrics.copy()
    performance_metrics["node_id"] = performance_metrics["node_id"].astype(str)

    summary = metrics_df.merge(
        performance_metrics,
        on=["time_window", "node_id"],
        how="left",
    )
    return summary
