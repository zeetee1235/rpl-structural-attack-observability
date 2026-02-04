# RPL Structural Attack Observability

This repository provides a prototype implementation to analyze when selective forwarding attacks
become observable (e.g., PDR drop, delay increase) in RPL/BRPL IoT networks. The goal is to
quantify how topology and routing structure (path diversity, betweenness, attack exposure, etc.)
shape observability rather than propose a detection algorithm.

## Project layout

- `docs/`: Research plan and supporting figures/notes.
- `data/`: Example CSV schemas and data placeholders.
- `rpl_observability/`: Core analysis modules (metrics + observability analysis).
- `scripts/`: CLI wrappers for analyzing logs.

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .

rpl-observability-analyze \
  --topology-log data/topology_edges.csv \
  --routing-log data/routing_paths.csv \
  --performance-log data/performance_metrics.csv \
  --output results/summary.csv
```

The CLI expects CSV logs described in `data/README.md`. It outputs a merged summary with computed
structural metrics and basic observability statistics.

## Notes

This is a prototype implementation meant to evolve alongside the research plan. See
`docs/research_plan.tex` for the latest plan draft.
