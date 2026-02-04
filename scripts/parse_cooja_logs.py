#!/usr/bin/env python3
"""
Parse Cooja simulation logs and extract topology, routing, performance, and exposure data.
Expects structured OBS log format described in docs/logging_spec.md.
"""

import argparse
import re
from pathlib import Path
from typing import Dict, List, Tuple
import csv
from dataclasses import dataclass, asdict
from collections import defaultdict
import math
import xml.etree.ElementTree as ET


@dataclass
class TopologyEdge:
    """Represents a network edge in the topology."""
    source: int
    target: int
    weight: float = 1.0


@dataclass
class RoutingPath:
    """Represents a routing path from node to root."""
    time_window: str
    node_id: int
    path: str


@dataclass
class PerformanceMetric:
    """Represents performance metrics for a node."""
    time_window: str
    node_id: int
    pdr: float
    delay_ms: float
    jitter_ms: float
    tx_count: int
    rx_count: int
    drop_count: int
    parent_churn: int
    attack_rate: float
    scenario: str


class CoojaLogParser:
    """Parser for Cooja simulation logs (OBS format)."""
    
    def __init__(self, log_file: Path, window_seconds: int = 600, scenario_file: Path | None = None):
        """Initialize parser with log file."""
        self.log_file = log_file
        self.window_seconds = window_seconds
        self.scenario_file = scenario_file
        self.topology_edges: List[TopologyEdge] = []
        self.routing_paths: List[RoutingPath] = []
        self.performance_metrics: List[PerformanceMetric] = []
        self.attack_exposure_rows: List[Dict[str, object]] = []
        
        self.patterns = {
            'obs': re.compile(r'^OBS\s+'),
        }

    def _parse_obs_line(self, line: str) -> Dict[str, str]:
        line = line.strip()
        if "OBS " in line and not line.startswith("OBS "):
            line = line[line.index("OBS "):]
        if not self.patterns["obs"].match(line):
            return {}
        parts = line.split()
        kv_pairs = {}
        for token in parts[1:]:
            if "=" in token:
                key, value = token.split("=", 1)
                kv_pairs[key] = value
        return kv_pairs

    def _time_window(self, ts_ms: int) -> str:
        idx = ts_ms // (self.window_seconds * 1000)
        return f"t{idx + 1}"
    
    def parse(self, scenario: str = "default") -> None:
        """
        Parse the log file and extract data.
        
        Args:
            scenario: Scenario identifier for this simulation
        """
        print(f"[INFO] Parsing log file: {self.log_file}")
        
        if not self.log_file.exists():
            raise FileNotFoundError(f"Log file not found: {self.log_file}")
        
        with open(self.log_file, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
        
        tx_counts = defaultdict(int)
        rx_counts = defaultdict(int)
        drop_counts = defaultdict(int)
        delays = defaultdict(list)
        attack_rates = {}
        parent_map = defaultdict(dict)  # window -> node_id -> parent_id
        parent_churn = defaultdict(int)  # node_id -> churn count
        last_parent = {}
        root_id = None
        attacker_rx = defaultdict(int)  # window -> count
        attacker_fwd = defaultdict(int)
        attacker_drop = defaultdict(int)
        attacker_id = None
        
        for line in lines:
            fields = self._parse_obs_line(line)
            if not fields:
                continue

            ts_ms = int(fields.get("ts", "0"))
            window = self._time_window(ts_ms)
            node = int(fields.get("node", "0"))
            ev = fields.get("ev", "")

            if ev == "ROOT":
                root_id = node

            if ev == "NEIGHBOR":
                neighbor = int(fields.get("neighbor", "0"))
                rssi = int(fields.get("rssi", "-100"))
                weight = max(0.1, min(1.0, (rssi + 100) / 50))
                self.topology_edges.append(TopologyEdge(node, neighbor, weight))

            if ev == "PARENT":
                parent_id = int(fields.get("parent", "0"))
                parent_map[window][node] = parent_id
                if node in last_parent and last_parent[node] != parent_id:
                    parent_churn[node] += 1
                last_parent[node] = parent_id

            if ev == "DATA_TX":
                tx_counts[node] += 1

            if ev == "ROOT_RX":
                src = int(fields.get("src", "0"))
                rx_counts[src] += 1

            if ev == "DELAY":
                src = int(fields.get("src", "0"))
                delay = float(fields.get("delay_ms", "0"))
                delays[src].append(delay)

            if ev == "DATA_RX":
                attacker_rx[window] += 1

            if ev == "DATA_FWD":
                attacker_fwd[window] += 1

            if ev == "DATA_DROP":
                attacker_drop[window] += 1
                drop_counts[node] += 1

            if ev == "ATTACK_START":
                attack_rates[node] = float(fields.get("rate", "0"))
                attacker_id = node
        
        # Build routing paths from parent map
        for window, window_map in parent_map.items():
            for node_id in window_map.keys():
                path = self._construct_path(node_id, window_map)
                self.routing_paths.append(RoutingPath(window, node_id, path))
        
        # Calculate performance metrics
        all_nodes = set(tx_counts.keys()) | set(rx_counts.keys()) | set(drop_counts.keys())
        for node_id in all_nodes:
            tx = tx_counts.get(node_id, 0)
            rx = rx_counts.get(node_id, 0)
            drops = drop_counts.get(node_id, 0)

            pdr = (rx / tx) if tx > 0 else 0.0

            node_delays = delays.get(node_id, [])
            avg_delay = sum(node_delays) / len(node_delays) if node_delays else 0.0
            jitter = (
                (sum((d - avg_delay) ** 2 for d in node_delays) / len(node_delays)) ** 0.5
                if node_delays
                else 0.0
            )

            attack_rate = attack_rates.get(node_id, 0.0)

            self.performance_metrics.append(
                PerformanceMetric(
                    time_window="t1",
                    node_id=node_id,
                    pdr=pdr,
                    delay_ms=avg_delay,
                    jitter_ms=jitter,
                    tx_count=tx,
                    rx_count=rx,
                    drop_count=drops,
                    parent_churn=parent_churn.get(node_id, 0),
                    attack_rate=attack_rate,
                    scenario=scenario
                )
            )

        # Attack exposure per window (ground truth)
        root_total = sum(rx_counts.values())
        for window in sorted(attacker_rx.keys()):
            recv_data = attacker_rx[window]
            fwd_data = attacker_fwd[window]
            drop_data = attacker_drop[window]
            exposure = (recv_data / root_total) if root_total > 0 else 0.0
            self.attack_exposure_rows.append(
                {
                    "time_window": window,
                    "attacker_id": attacker_id if attacker_id is not None else "",
                    "recv_data": recv_data,
                    "fwd_data": fwd_data,
                    "drop_data": drop_data,
                    "root_rx_total": root_total,
                    "exposure": exposure,
                }
            )

        if not self.topology_edges and self.scenario_file:
            self._build_topology_from_csc(self.scenario_file)

    def _build_topology_from_csc(self, scenario_file: Path) -> None:
        if not scenario_file.exists():
            return
        tree = ET.parse(scenario_file)
        root = tree.getroot()
        tx_range = 0.0
        for elem in root.iter():
            if elem.tag == "transmitting_range":
                try:
                    tx_range = float(elem.text.strip())
                except Exception:
                    tx_range = 0.0
        positions = {}
        for mote in root.iter("mote"):
            node_id = None
            x = y = None
            for iface in mote.findall("interface_config"):
                if iface.text and "Position" in iface.text:
                    x_elem = iface.find("x")
                    y_elem = iface.find("y")
                    if x_elem is not None and y_elem is not None:
                        x = float(x_elem.text)
                        y = float(y_elem.text)
                if iface.text and "ContikiMoteID" in iface.text:
                    id_elem = iface.find("id")
                    if id_elem is not None:
                        node_id = int(id_elem.text)
            if node_id is not None and x is not None and y is not None:
                positions[node_id] = (x, y)

        if tx_range <= 0 or not positions:
            return
        nodes = sorted(positions.keys())
        for i, src in enumerate(nodes):
            for dst in nodes[i + 1:]:
                sx, sy = positions[src]
                dx, dy = positions[dst]
                dist = math.hypot(sx - dx, sy - dy)
                if dist <= tx_range:
                    self.topology_edges.append(TopologyEdge(src, dst, 1.0))
                    self.topology_edges.append(TopologyEdge(dst, src, 1.0))
        
        print(f"[INFO] Extracted {len(self.topology_edges)} topology edges")
        print(f"[INFO] Extracted {len(self.routing_paths)} routing paths")
        print(f"[INFO] Extracted {len(self.performance_metrics)} performance metrics")
    
    def _construct_path(self, node_id: int, parent_map: Dict[int, int]) -> str:
        """
        Construct full path from node to root.
        
        Args:
            node_id: Starting node
            parent_map: Mapping of node_id -> parent_id
            
        Returns:
            Path string in format "node1>node2>root"
        """
        path = [node_id]
        current = node_id
        visited = set()
        
        # Follow parent pointers to root
        while current in parent_map and current not in visited:
            visited.add(current)
            parent = parent_map[current]
            path.append(parent)
            current = parent
            
            # Prevent infinite loops
            if len(path) > 100:
                break
        
        return ">".join(map(str, path))
    
    def export_to_csv(self, output_dir: Path) -> Dict[str, Path]:
        """
        Export parsed data to CSV files.
        
        Args:
            output_dir: Directory to save CSV files
            
        Returns:
            Dictionary mapping data type to output file path
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        
        output_files = {}
        
        # Export topology edges
        if self.topology_edges:
            topology_file = output_dir / "topology_edges.csv"
            with open(topology_file, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=['source', 'target', 'weight'])
                writer.writeheader()
                for edge in self.topology_edges:
                    writer.writerow(asdict(edge))
            output_files['topology'] = topology_file
            print(f"[INFO] Exported topology to {topology_file}")
        
        # Export routing paths
        if self.routing_paths:
            routing_file = output_dir / "routing_paths.csv"
            with open(routing_file, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=['time_window', 'node_id', 'path'])
                writer.writeheader()
                for path in self.routing_paths:
                    writer.writerow(asdict(path))
            output_files['routing'] = routing_file
            print(f"[INFO] Exported routing paths to {routing_file}")
        
        # Export performance metrics
        if self.performance_metrics:
            performance_file = output_dir / "performance_metrics.csv"
            with open(performance_file, 'w', newline='') as f:
                writer = csv.DictWriter(
                    f,
                    fieldnames=[
                        'time_window',
                        'node_id',
                        'pdr',
                        'delay_ms',
                        'jitter_ms',
                        'tx_count',
                        'rx_count',
                        'drop_count',
                        'parent_churn',
                        'attack_rate',
                        'scenario'
                    ]
                )
                writer.writeheader()
                for metric in self.performance_metrics:
                    writer.writerow(asdict(metric))
            output_files['performance'] = performance_file
            print(f"[INFO] Exported performance metrics to {performance_file}")

        # Export attack exposure
        if self.attack_exposure_rows:
            exposure_file = output_dir / "attack_exposure.csv"
            with open(exposure_file, 'w', newline='') as f:
                writer = csv.DictWriter(
                    f,
                    fieldnames=[
                        "time_window",
                        "attacker_id",
                        "recv_data",
                        "fwd_data",
                        "drop_data",
                        "root_rx_total",
                        "exposure",
                    ],
                )
                writer.writeheader()
                for row in self.attack_exposure_rows:
                    writer.writerow(row)
            output_files['exposure'] = exposure_file
            print(f"[INFO] Exported attack exposure to {exposure_file}")
        
        return output_files


def main():
    """Main entry point for the log parser."""
    parser = argparse.ArgumentParser(
        description="Parse Cooja simulation logs and extract data for observability analysis"
    )
    parser.add_argument(
        "--log-file",
        type=Path,
        required=True,
        help="Path to Cooja log file (.log or .testlog)"
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("./data"),
        help="Directory to save CSV output files (default: ./data)"
    )
    parser.add_argument(
        "--scenario",
        type=str,
        default="default",
        help="Scenario identifier for this simulation (default: default)"
    )
    parser.add_argument(
        "--window-seconds",
        type=int,
        default=600,
        help="Time window size in seconds for routing paths (default: 600)"
    )
    parser.add_argument(
        "--scenario-file",
        type=Path,
        help="Optional .csc file to derive topology edges from coordinates"
    )
    
    args = parser.parse_args()
    
    try:
        # Parse log file
        log_parser = CoojaLogParser(
            args.log_file,
            window_seconds=args.window_seconds,
            scenario_file=args.scenario_file,
        )
        log_parser.parse(scenario=args.scenario)
        
        # Export to CSV
        output_files = log_parser.export_to_csv(args.output_dir)
        
        print(f"\n✓ Successfully parsed log file and exported data")
        print(f"  Output directory: {args.output_dir}")
        for data_type, file_path in output_files.items():
            print(f"  - {data_type}: {file_path.name}")
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
