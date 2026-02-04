#!/usr/bin/env python3
"""
Monitor a running Cooja simulation by tailing the latest log file.
Shows file size growth and last matching progress lines.
"""

from __future__ import annotations

import argparse
import time
from pathlib import Path


def find_latest_log(output_dir: Path) -> Path | None:
    logs = sorted(output_dir.glob("*.log"), key=lambda p: p.stat().st_mtime, reverse=True)
    return logs[0] if logs else None


def tail_lines(path: Path, num_lines: int) -> list[str]:
    try:
        with path.open("rb") as f:
            f.seek(0, 2)
            end = f.tell()
            size = min(end, 8192)
            f.seek(-size, 2)
            data = f.read().decode(errors="ignore")
    except FileNotFoundError:
        return []
    lines = data.splitlines()
    return lines[-num_lines:]


def main() -> int:
    parser = argparse.ArgumentParser(description="Monitor Cooja simulation progress")
    parser.add_argument("--output-dir", type=Path, default=Path("simulations/output"))
    parser.add_argument("--interval", type=float, default=5.0, help="Refresh interval (seconds)")
    parser.add_argument("--lines", type=int, default=20, help="Lines to show")
    args = parser.parse_args()

    output_dir = args.output_dir
    if not output_dir.exists():
        print(f"[ERROR] Output dir not found: {output_dir}")
        return 1

    last_size = None
    while True:
        log_file = find_latest_log(output_dir)
        if log_file is None:
            print("[INFO] No log files found. Waiting...")
            time.sleep(args.interval)
            continue

        size = log_file.stat().st_size
        delta = "-" if last_size is None else f"+{size - last_size}"
        last_size = size

        print("=" * 60)
        print(f"[INFO] Log: {log_file} size={size} bytes delta={delta}")
        for line in tail_lines(log_file, args.lines):
            print(line)
        time.sleep(args.interval)


if __name__ == "__main__":
    raise SystemExit(main())
