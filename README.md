# RPL Structural Attack Observability

This repository provides a prototype implementation to analyze when selective forwarding attacks
become observable (e.g., PDR drop, delay increase) in RPL/BRPL IoT networks. The goal is to
quantify how topology and routing structure (path diversity, betweenness, attack exposure, etc.)
shape observability rather than propose a detection algorithm.


## Project layout

- `docs/`: Research plan and supporting figures/notes.
- `data/`: Example CSV schemas and data placeholders.
- `rpl_observability/`: Core analysis modules (metrics + observability analysis).
- `scripts/`: CLI wrappers for analyzing logs and running simulations.
- `simulations/`: Cooja simulation scenarios and firmware for generating experimental data.

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

## Running Cooja Simulations

This project supports headless Cooja simulations to generate experimental data automatically.

### Prerequisites

1. Install Contiki-NG:
   ```bash
   git clone https://github.com/contiki-ng/contiki-ng.git
   cd contiki-ng
   git submodule update --init --recursive
   ```

2. Build Cooja:
   ```bash
   cd tools/cooja
   ./gradlew jar
   ```

### Running a simulation

```bash
# Run the 10-node topology simulation
python scripts/run_cooja_headless.py \
  --cooja-path /path/to/contiki-ng/tools/cooja \
  --contiki-path /path/to/contiki-ng \
  --simulation simulations/scenarios/rpl_topology_10nodes.csc \
  --output-dir simulations/output \
  --timeout 20
```

### Parsing simulation logs

```bash
# Parse Cooja output and convert to CSV format
python scripts/parse_cooja_logs.py \
  --log-file simulations/output/rpl_topology_10nodes_20260204_120000.log \
  --output-dir data \
  --scenario topology_10nodes
```

### Full workflow

```bash
# 1. Run simulation
python scripts/run_cooja_headless.py \
  --cooja-path ~/contiki-ng/tools/cooja \
  --contiki-path ~/contiki-ng \
  --simulation simulations/scenarios/rpl_topology_10nodes.csc \
  --output-dir simulations/output

# 2. Parse logs
python scripts/parse_cooja_logs.py \
  --log-file simulations/output/rpl_topology_10nodes_*.log \
  --output-dir data

# 3. Analyze results
rpl-observability-analyze \
  --topology-log data/topology_edges.csv \
  --routing-log data/routing_paths.csv \
  --performance-log data/performance_metrics.csv \
  --output results/summary.csv
```

See `simulations/scenarios/README.md` for more information on available scenarios.

## Notes

This is a prototype implementation meant to evolve alongside the research plan. See
`docs/research_plan.tex` for the latest plan draft.
