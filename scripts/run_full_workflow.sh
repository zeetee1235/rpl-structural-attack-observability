#!/bin/bash
# Complete workflow to run Cooja simulation and analyze results

set -e  # Exit on error

# Configuration
COOJA_PATH="${COOJA_PATH:-$HOME/contiki-ng-brpl/tools/cooja}"
CONTIKI_PATH="${CONTIKI_PATH:-$HOME/contiki-ng-brpl}"
SIMULATION="${1:-simulations/scenarios/rpl_topology_10nodes.csc}"
SCENARIO="${2:-experiment_1}"
TIMEOUT="${3:-20}"

# Directories
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUTPUT_DIR="$PROJECT_ROOT/simulations/output"
DATA_DIR="$PROJECT_ROOT/data"
RESULTS_DIR="$PROJECT_ROOT/results"

echo "=========================================="
echo "RPL Observability Simulation Workflow"
echo "=========================================="
echo "Cooja path:     $COOJA_PATH"
echo "Contiki path:   $CONTIKI_PATH"
echo "Simulation:     $SIMULATION"
echo "Scenario:       $SCENARIO"
echo "Timeout:        $TIMEOUT minutes"
echo "=========================================="
echo ""

# Step 1: Run simulation
echo "[1/3] Running Cooja simulation..."
python "$PROJECT_ROOT/scripts/run_cooja_headless.py" \
  --cooja-path "$COOJA_PATH" \
  --contiki-path "$CONTIKI_PATH" \
  --simulation "$PROJECT_ROOT/$SIMULATION" \
  --output-dir "$OUTPUT_DIR" \
  --timeout "$TIMEOUT"

if [ $? -ne 0 ]; then
  echo "❌ Simulation failed!"
  exit 1
fi

# Find the most recent log file
LATEST_LOG=$(ls -t "$OUTPUT_DIR"/*.log 2>/dev/null | head -n1)

if [ -z "$LATEST_LOG" ]; then
  echo "❌ No log file found in $OUTPUT_DIR"
  exit 1
fi

echo "✓ Simulation completed successfully"
echo "  Log file: $LATEST_LOG"
echo ""

# Step 2: Parse logs
echo "[2/3] Parsing simulation logs..."
python "$PROJECT_ROOT/scripts/parse_cooja_logs.py" \
  --log-file "$LATEST_LOG" \
  --output-dir "$DATA_DIR" \
  --scenario "$SCENARIO" \
  --scenario-file "$PROJECT_ROOT/$SIMULATION"

if [ $? -ne 0 ]; then
  echo "❌ Log parsing failed!"
  exit 1
fi

echo "✓ Logs parsed successfully"
echo ""

# Step 3: Run observability analysis
echo "[3/3] Running observability analysis..."
mkdir -p "$RESULTS_DIR"

# Check if rpl-observability-analyze is available
if command -v rpl-observability-analyze &> /dev/null; then
  rpl-observability-analyze \
    --topology-log "$DATA_DIR/topology_edges.csv" \
    --routing-log "$DATA_DIR/routing_paths.csv" \
    --performance-log "$DATA_DIR/performance_metrics.csv" \
    --output "$RESULTS_DIR/summary_${SCENARIO}.csv"
  
  if [ $? -ne 0 ]; then
    echo "❌ Analysis failed!"
    exit 1
  fi
  
  echo "✓ Analysis completed successfully"
  echo "  Results: $RESULTS_DIR/summary_${SCENARIO}.csv"
else
  echo "⚠️  rpl-observability-analyze not found. Skipping analysis."
  echo "   Install with: pip install -e ."
fi

echo ""
echo "=========================================="
echo "✓ Workflow completed successfully!"
echo "=========================================="
echo "Data files:"
echo "  - $DATA_DIR/topology_edges.csv"
echo "  - $DATA_DIR/routing_paths.csv"
echo "  - $DATA_DIR/performance_metrics.csv"
if [ -f "$RESULTS_DIR/summary_${SCENARIO}.csv" ]; then
  echo "Results:"
  echo "  - $RESULTS_DIR/summary_${SCENARIO}.csv"
fi
echo "=========================================="
