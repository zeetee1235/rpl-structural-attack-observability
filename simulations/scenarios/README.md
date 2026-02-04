# Cooja Simulation Configuration

This directory contains Cooja simulation scenarios for RPL observability experiments.

## Available Scenarios

### rpl_topology_10nodes.csc

A basic 10-node RPL network topology for testing selective forwarding attack observability.

**Topology:**
- 1 root node (DODAG root)
- 9 regular nodes arranged in a multi-hop tree topology
- Radio range: 50m transmission, 100m interference
- Simulation duration: 10 minutes

**Usage:**

To run this simulation in headless mode:

```bash
python scripts/run_cooja_headless.py \
  --cooja-path /path/to/cooja \
  --contiki-path /path/to/contiki-ng \
  --simulation simulations/scenarios/rpl_topology_10nodes.csc \
  --output-dir simulations/output \
  --timeout 20
```

## Creating Custom Scenarios

1. Design your topology in Cooja GUI
2. Configure simulation parameters (radio model, interference, etc.)
3. Add script runner plugin for automated completion
4. Export as `.csc` file to this directory

## Simulation Script

The ScriptRunner plugin in each scenario uses JavaScript to:
- Set simulation timeout
- Log simulation progress
- Automatically terminate when complete

Example script:
```javascript
TIMEOUT(600000); // 10 minutes
log.log("Simulation started\n");

while(true) {
  YIELD();
  if(time >= 600000000) {
    log.log("Simulation completed\n");
    log.testOK();
  }
}
```

## Scenario Coordinate Plans

See `simulations/scenarios/SCENARIO_COORDINATES.md` for the four baseline scenarios
(A-D) with concrete node coordinates and attacker placement notes.

## Scenario Files (A-D)

- `simulations/scenarios/scenario_a_low_exposure.csc`
- `simulations/scenarios/scenario_b_high_exposure.csc`
- `simulations/scenarios/scenario_c_high_pd.csc`
- `simulations/scenarios/scenario_d_apl_bc.csc`
