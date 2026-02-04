"""Convenience wrapper for running the observability analysis."""

from __future__ import annotations

import argparse

from rpl_observability.cli import main as cli_main


def main() -> None:
    parser = argparse.ArgumentParser(description="Wrapper around rpl-observability-analyze")
    parser.parse_args()
    cli_main()


if __name__ == "__main__":
    main()
