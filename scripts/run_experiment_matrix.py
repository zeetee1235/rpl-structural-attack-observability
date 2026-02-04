#!/usr/bin/env python3
"""
Run an experiment matrix for RPL/BRPL observability.

This script is intentionally minimal. It reads a CSV matrix, runs each simulation
headlessly, parses logs, and writes a manifest for traceability.
"""

from __future__ import annotations

import argparse
import csv
import subprocess
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


@dataclass(frozen=True)
class MatrixRow:
    scenario: str
    protocol: str
    attack_rate: float
    seed: int
    simulation: str
    attacker_id: int | None
    root_id: int | None


def load_matrix(matrix_path: Path) -> list[MatrixRow]:
    rows: list[MatrixRow] = []
    with matrix_path.open("r", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            rows.append(
                MatrixRow(
                    scenario=row["scenario"],
                    protocol=row["protocol"],
                    attack_rate=float(row["attack_rate"]),
                    seed=int(row["seed"]),
                    simulation=row["simulation"],
                    attacker_id=int(row["attacker_id"]) if row.get("attacker_id") else None,
                    root_id=int(row["root_id"]) if row.get("root_id") else None,
                )
            )
    return rows


def write_manifest_header(manifest_path: Path) -> None:
    if manifest_path.exists():
        return
    with manifest_path.open("w", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "timestamp",
                "scenario",
                "protocol",
                "attack_rate",
                "seed",
                "simulation",
                "log_file",
                "status",
            ],
        )
        writer.writeheader()


def append_manifest(manifest_path: Path, record: dict[str, str]) -> None:
    with manifest_path.open("a", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=record.keys())
        writer.writerow(record)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run an experiment matrix")
    parser.add_argument("--cooja-path", type=Path, required=True)
    parser.add_argument("--contiki-path", type=Path, required=True)
    parser.add_argument("--matrix", type=Path, required=True, help="CSV matrix file")
    parser.add_argument("--output-dir", type=Path, default=Path("./simulations/output"))
    parser.add_argument("--data-dir", type=Path, default=Path("./data"))
    parser.add_argument("--timeout", type=int, default=20)
    parser.add_argument("--dry-run", action="store_true", help="Print commands only")
    args = parser.parse_args()

    rows = load_matrix(args.matrix)
    manifest_path = args.output_dir / "experiment_manifest.csv"
    args.output_dir.mkdir(parents=True, exist_ok=True)
    write_manifest_header(manifest_path)

    for row in rows:
        command = [
            "python",
            "scripts/run_cooja_headless.py",
            "--cooja-path",
            str(args.cooja_path),
            "--contiki-path",
            str(args.contiki_path),
            "--simulation",
            row.simulation,
            "--output-dir",
            str(args.output_dir),
            "--timeout",
            str(args.timeout),
            "--random-seed",
            str(row.seed),
            "--attack-rate",
            str(row.attack_rate),
            "--routing",
            row.protocol,
        ]
        if row.attacker_id is not None:
            command.extend(["--attacker-id", str(row.attacker_id)])
        if row.root_id is not None:
            command.extend(["--root-id", str(row.root_id)])

        if args.dry_run:
            print("[DRY-RUN]", " ".join(command))
            continue

        result = subprocess.run(command, check=False)
        status = "ok" if result.returncode == 0 else "error"

        latest_log = sorted(args.output_dir.glob("*.log"))[-1] if args.output_dir.glob("*.log") else None
        log_file = str(latest_log) if latest_log else ""

        parse_command = [
            "python",
            "scripts/parse_cooja_logs.py",
            "--log-file",
            log_file,
            "--output-dir",
            str(args.data_dir),
            "--scenario",
            row.scenario,
            "--scenario-file",
            row.simulation,
        ]

        if log_file and not args.dry_run:
            subprocess.run(parse_command, check=False)

        append_manifest(
            manifest_path,
            {
                "timestamp": datetime.now().isoformat(timespec="seconds"),
                "scenario": row.scenario,
                "protocol": row.protocol,
                "attack_rate": str(row.attack_rate),
                "seed": str(row.seed),
                "simulation": row.simulation,
                "log_file": log_file,
                "status": status,
            },
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
