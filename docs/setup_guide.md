# Setup Guide

## Prerequisites

### 1. Install Contiki-NG

```bash
git clone https://github.com/contiki-ng/contiki-ng.git
cd contiki-ng
git submodule update --init --recursive
```

### 2. Build Cooja Simulator

```bash
cd tools/cooja
./gradlew jar
```

### 3. Install Python Dependencies

```bash
cd /path/to/rpl-structural-attack-observability
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

## Running Simulations

### Basic Simulation

```bash
python scripts/run_cooja_headless.py \
  --cooja-path /path/to/contiki-ng/tools/cooja \
  --contiki-path /path/to/contiki-ng \
  --simulation simulations/scenarios/rpl_topology_10nodes.csc \
  --output-dir simulations/output \
  --timeout 60
```

### Simulation with Attack Parameters

```bash
python scripts/run_cooja_headless.py \
  --cooja-path ~/contiki-ng/tools/cooja \
  --contiki-path contiki-ng-brpl \
  --simulation simulations/scenarios/scenario_b_high_exposure.csc \
  --output-dir simulations/output \
  --timeout 300 \
  --attacker-id 6 \
  --attack-rate 0.6 \
  --root-id 1 \
  --routing rpl
```

**Parameters:**
- `--attacker-id`: Node ID that performs selective forwarding attack
- `--attack-rate`: Probability of dropping packets (0.0 - 1.0)
- `--root-id`: Root node ID for RPL DAG
- `--routing`: Routing protocol (`rpl` or `brpl`)

### Monitoring Running Simulations

```bash
# Shell-based monitor (refreshes every 2 seconds)
./scripts/monitor_simulation.sh

# Python-based monitor (more features)
python scripts/monitor_simulation.py
```

## Parsing Logs

```bash
# Convert Cooja logs to CSV format
python scripts/parse_cooja_logs.py \
  --log-file simulations/output/COOJA.testlog \
  --output-dir data \
  --scenario scenario_name \
  --scenario-file simulations/scenarios/scenario_b_high_exposure.csc
```

This generates:
- `topology_edges.csv` - Network topology links
- `routing_paths.csv` - Routing table and paths
- `performance_metrics.csv` - PDR, delay, packet counts
- `attack_exposure.csv` - Attack impact metrics

## Data Analysis

```bash
rpl-observability-analyze \
  --topology-log data/topology_edges.csv \
  --routing-log data/routing_paths.csv \
  --performance-log data/performance_metrics.csv \
  --output results/summary.csv
```

## Complete Workflow Example

```bash
# 1. Run simulation with attack
python scripts/run_cooja_headless.py \
  --cooja-path ~/contiki-ng/tools/cooja \
  --contiki-path contiki-ng-brpl \
  --simulation simulations/scenarios/scenario_b_high_exposure.csc \
  --output-dir simulations/output \
  --timeout 300 \
  --attacker-id 6 \
  --attack-rate 0.6

# 2. Parse logs
python scripts/parse_cooja_logs.py \
  --log-file simulations/output/COOJA.testlog \
  --output-dir data \
  --scenario scenario_b \
  --scenario-file simulations/scenarios/scenario_b_high_exposure.csc

# 3. Analyze results
rpl-observability-analyze \
  --topology-log data/topology_edges.csv \
  --routing-log data/routing_paths.csv \
  --performance-log data/performance_metrics.csv \
  --output results/scenario_b_summary.csv
```

## Available Scenarios

See [simulations/scenarios/README.md](../simulations/scenarios/README.md) for detailed scenario descriptions.

- `rpl_topology_10nodes.csc` - Basic 10-node topology for testing
- `scenario_a_low_exposure.csc` - Low attack exposure scenario
- `scenario_b_high_exposure.csc` - High attack exposure (10 nodes)
- `scenario_b_high_exposure_20.csc` - High attack exposure (20 nodes)
- `scenario_c_high_pd.csc` - High path diversity scenario
- `scenario_d_apl_bc.csc` - Average path length and betweenness centrality scenario

## Troubleshooting

See [attack_rate_guide.md](attack_rate_guide.md) for ATTACK_RATE parameter troubleshooting.

### Common Issues

1. **"No rule to make target" errors**: Ensure firmware is pre-built before Cooja starts
2. **ATTACK_RATE shows 0.00**: Check that pre-build strategy is enabled in run_cooja_headless.py
3. **Cooja hangs**: Increase `--timeout` parameter or check simulation complexity
4. **Permission denied**: Make scripts executable with `chmod +x scripts/*.sh`
