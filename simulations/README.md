# Headless Cooja Setup Guide

Complete guide for running automated Cooja simulations for RPL observability experiments.

## Overview

This setup enables:
- Automated execution of Cooja simulations without GUI
- Systematic data collection from network simulations
- Reproducible experiments for attack observability analysis

## Directory Structure

```
simulations/
├── scenarios/          # Cooja .csc simulation files
│   ├── rpl_topology_10nodes.csc
│   └── README.md
├── firmware/           # Node firmware source code
│   └── README.md
└── output/            # Simulation logs and results
    └── README.md

scripts/
├── run_cooja_headless.py    # Headless Cooja runner
├── parse_cooja_logs.py      # Log parser to CSV
└── run_full_workflow.sh     # Complete automation workflow
```

## Prerequisites

### 1. Install Contiki-NG

```bash
# Clone Contiki-NG
cd ~/
git clone https://github.com/contiki-ng/contiki-ng.git
cd contiki-ng
git submodule update --init --recursive

# Install dependencies (Ubuntu/Debian)
sudo apt-get update
sudo apt-get install -y build-essential doxygen git curl \
  wireshark python3-serial default-jdk ant
```

### 2. Build Cooja

```bash
cd ~/contiki-ng/tools/cooja
./gradlew jar

# Verify installation
ls build/libs/cooja.jar
```

### 3. Install Python Dependencies

```bash
cd /path/to/rpl-structural-attack-observability
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

## Usage

### Method 1: Individual Scripts

#### Run simulation:
```bash
python scripts/run_cooja_headless.py \
  --cooja-path ~/contiki-ng/tools/cooja \
  --contiki-path ~/contiki-ng \
  --simulation simulations/scenarios/rpl_topology_10nodes.csc \
  --output-dir simulations/output \
  --timeout 20
```

#### Parse logs:
```bash
python scripts/parse_cooja_logs.py \
  --log-file simulations/output/rpl_topology_10nodes_*.log \
  --output-dir data \
  --scenario experiment_1
```

#### Analyze results:
```bash
rpl-observability-analyze \
  --topology-log data/topology_edges.csv \
  --routing-log data/routing_paths.csv \
  --performance-log data/performance_metrics.csv \
  --output results/summary.csv
```

### Method 2: Automated Workflow

```bash
# Set paths (or export as environment variables)
export COOJA_PATH=~/contiki-ng/tools/cooja
export CONTIKI_PATH=~/contiki-ng

# Run complete workflow
./scripts/run_full_workflow.sh \
  simulations/scenarios/rpl_topology_10nodes.csc \
  experiment_1 \
  20
```

Arguments:
1. Simulation file path (default: `simulations/scenarios/rpl_topology_10nodes.csc`)
2. Scenario name (default: `experiment_1`)
3. Timeout in minutes (default: `20`)

## Creating Custom Simulations

### 1. Design topology in Cooja GUI

```bash
cd ~/contiki-ng/tools/cooja
java -jar build/libs/cooja.jar
```

### 2. Configure simulation settings

- Set radio model (UDGM, Unit Disk Graph Medium)
- Configure transmission and interference ranges
- Place nodes in desired topology
- Add mote types and firmware

### 3. Add automation script

In Cooja, add ScriptRunner plugin with:

```javascript
TIMEOUT(600000); // 10 minutes in ms
log.log("Simulation started\n");

while(true) {
  YIELD();
  if(time >= 600000000) { // 10 minutes in microseconds
    log.log("Simulation completed\n");
    log.testOK();
  }
}
```

### 4. Save simulation

Save as `.csc` file in `simulations/scenarios/` directory.

## Firmware Development

See `simulations/firmware/README.md` for details on creating RPL node firmware.

Basic requirements:
- Initialize RPL routing
- Send periodic packets
- Log routing metrics (parent, rank)
- Optional: Implement attack behavior

## Troubleshooting

### Cooja fails to start
- Verify Java installation: `java -version` (requires JDK 11+)
- Check cooja.jar exists: `ls ~/contiki-ng/tools/cooja/build/libs/cooja.jar`
- Rebuild if needed: `cd ~/contiki-ng/tools/cooja && ./gradlew jar`

### Simulation hangs
- Increase timeout: `--timeout 30`
- Check simulation script timeout matches command timeout
- Review log files for errors

### No data in parsed CSV
- Verify log format matches parser regex patterns
- Check that nodes are logging expected information
- Review raw log file content

### Memory issues
- Increase Java heap size in `run_cooja_headless.py`:
  ```python
  "-Xms1024m",
  "-Xmx8192m",  # Increase to 8GB
  ```

## Advanced Usage

### Batch simulations

```bash
#!/bin/bash
for seed in {1..10}; do
  python scripts/run_cooja_headless.py \
    --cooja-path ~/contiki-ng/tools/cooja \
    --contiki-path ~/contiki-ng \
    --simulation simulations/scenarios/rpl_topology_10nodes.csc \
    --output-dir simulations/output \
    --random-seed $seed \
    --timeout 20
done
```

### Parallel execution

```bash
# Run multiple simulations in parallel using GNU parallel
parallel -j 4 python scripts/run_cooja_headless.py \
  --cooja-path ~/contiki-ng/tools/cooja \
  --contiki-path ~/contiki-ng \
  --simulation simulations/scenarios/rpl_topology_10nodes.csc \
  --output-dir simulations/output/seed_{} \
  --random-seed {} \
  ::: {1..10}
```

### Custom log parsing

Extend `parse_cooja_logs.py` by modifying the regex patterns in the `patterns` dictionary to match your firmware's log format.

## References

- [Contiki-NG Documentation](https://docs.contiki-ng.org/)
- [Cooja Simulator Guide](https://docs.contiki-ng.org/en/develop/doc/tutorials/Running-Contiki-NG-in-Cooja.html)
- [RPL Protocol Overview](https://datatracker.ietf.org/doc/html/rfc6550)
