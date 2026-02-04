"""Structural metric calculations for RPL/BRPL observability analysis."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import networkx as nx
import numpy as np
import pandas as pd


@dataclass(frozen=True)
class PathStats:
    node_id: str
    path: list[str]


def parse_path_series(path_series: Iterable[str]) -> list[list[str]]:
    """Parse path strings like `nodeA>nodeB>root` into lists."""
    parsed = []
    for path in path_series:
        if pd.isna(path):
            parsed.append([])
        else:
            parsed.append([token.strip() for token in str(path).split(">") if token.strip()])
    return parsed


def compute_average_path_length(paths: Iterable[list[str]]) -> float:
    """Compute mean hop count from a collection of paths."""
    hop_counts = [max(len(path) - 1, 0) for path in paths if path]
    if not hop_counts:
        return 0.0
    return float(np.mean(hop_counts))


def compute_path_diversity(paths: Iterable[list[str]]) -> int:
    """Compute path diversity as number of unique paths observed."""
    unique_paths = {tuple(path) for path in paths if path}
    return len(unique_paths)


def compute_attack_exposure(paths: Iterable[list[str]], attacker_id: str) -> float:
    """Estimate attack exposure probability based on observed paths.

    Exposure is the fraction of observed paths that traverse the attacker node.
    """
    paths_list = [path for path in paths if path]
    if not paths_list:
        return 0.0
    exposed = sum(1 for path in paths_list if attacker_id in path)
    return float(exposed / len(paths_list))


def compute_betweenness_centrality(edges: pd.DataFrame, attacker_id: str) -> float:
    """Compute betweenness centrality for attacker node given topology edges."""
    graph = nx.Graph()
    for _, row in edges.iterrows():
        weight = float(row.get("weight", 1.0))
        graph.add_edge(str(row["source"]), str(row["target"]), weight=weight)
    if attacker_id not in graph:
        return 0.0
    centrality = nx.betweenness_centrality(graph, weight="weight")
    return float(centrality.get(attacker_id, 0.0))
