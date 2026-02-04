# RPL Structural Attack Observability

Analysis framework for quantifying when selective forwarding attacks become observable in RPL/BRPL IoT networks. Focus on topology and routing structure (path diversity, betweenness, attack exposure) rather than detection algorithms.

## Quick Start

```bash
# Setup
python -m venv .venv
source .venv/bin/activate
pip install -e .

# Run simulation with attack
python scripts/run_cooja_headless.py \
  --cooja-path ~/contiki-ng/tools/cooja \
  --contiki-path contiki-ng-brpl \
  --simulation simulations/scenarios/scenario_b_high_exposure.csc \
  --attacker-id 6 \
  --attack-rate 0.6

# Parse logs and analyze
python scripts/parse_cooja_logs.py \
  --log-file simulations/output/COOJA.testlog \
  --output-dir data

rpl-observability-analyze \
  --topology-log data/topology_edges.csv \
  --routing-log data/routing_paths.csv \
  --performance-log data/performance_metrics.csv \
  --output results/summary.csv
```

## Project Structure

```
├── docs/                    # Documentation and research plan
├── data/                    # CSV data schemas and outputs
├── rpl_observability/       # Analysis modules (metrics, observability)
├── scripts/                 # CLI tools and test scripts
├── simulations/            
│   ├── scenarios/          # Cooja simulation configurations (.csc)
│   └── firmware/           # RPL/BRPL node firmware
└── contiki-ng-brpl/        # Modified Contiki-NG (submodule)
```

## Documentation

- **[Paper (PDF)](docs/paper.pdf)** - Current draft report
- **[Setup Guide](docs/setup_guide.md)** - Installation and configuration
- **[Attack Rate Guide](docs/attack_rate_guide.md)** - Troubleshooting attack parameters
- **[Changelog](docs/changelog.md)** - Version history and updates
- **[Scenarios](simulations/scenarios/README.md)** - Available simulation scenarios

## Key Features

- Headless Cooja simulation automation
- RPL/BRPL routing protocol support
- Selective forwarding attack simulation with configurable rates
- Structural metrics computation (betweenness, path diversity, exposure)
- Real-time monitoring and testing tools

## Testing

```bash
# Test firmware compilation
./scripts/test_firmware_build.sh

# Test attack simulation
./scripts/test_attack_rate.sh

# Monitor running simulation
./scripts/monitor_simulation.sh
```

## Citation

This is research prototype code accompanying an ongoing study. See [docs/research_plan.tex](docs/research_plan.tex) for details.

## License

MIT
