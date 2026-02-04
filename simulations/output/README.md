# Simulation Output Directory

This directory stores output from Cooja simulations.

## File Structure

After running simulations, you'll find files in this format:

```
rpl_topology_10nodes_20260204_120000.log       # Main simulation log
rpl_topology_10nodes_20260204_120000_COOJA.testlog  # Cooja test log
```

## Log Files

- **`.log` files**: Contain all console output from simulation nodes including:
  - Network initialization messages
  - Routing updates (parent selection, rank changes)
  - Packet transmission/reception events
  - Performance metrics (PDR, delay)
  - Attack behavior logs

- **`_COOJA.testlog` files**: Contain Cooja framework messages and test results

## Processing Logs

Use the `parse_cooja_logs.py` script to extract structured data from log files:

```bash
python scripts/parse_cooja_logs.py \
  --log-file simulations/output/rpl_topology_10nodes_20260204_120000.log \
  --output-dir data \
  --scenario my_experiment
```

This will generate CSV files in the `data/` directory ready for observability analysis.
