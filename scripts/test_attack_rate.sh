#!/bin/bash
# Test script to verify ATTACK_RATE is properly applied

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Configuration
COOJA_PATH="${COOJA_PATH:-/home/dev/contiki-ng/tools/cooja}"
CONTIKI_PATH="$PROJECT_ROOT/contiki-ng-brpl"
SCENARIO="$PROJECT_ROOT/simulations/scenarios/scenario_b_high_exposure_20.csc"
OUTPUT_DIR="$PROJECT_ROOT/simulations/output"
TIMEOUT=60

# Test parameters
TEST_ATTACKER_ID=6
TEST_ATTACK_RATE=0.6
TEST_ROOT_ID=1

echo "========================================="
echo "Testing ATTACK_RATE Application"
echo "========================================="
echo "Attacker ID: $TEST_ATTACKER_ID"
echo "Attack Rate: $TEST_ATTACK_RATE"
echo "Root ID: $TEST_ROOT_ID"
echo "Scenario: $(basename $SCENARIO)"
echo ""

# Clean previous outputs
rm -f "$OUTPUT_DIR/COOJA.testlog"
rm -f "$OUTPUT_DIR"/*.log

# Run simulation with attack rate
python3 "$SCRIPT_DIR/run_cooja_headless.py" \
  --cooja-path "$COOJA_PATH" \
  --contiki-path "$CONTIKI_PATH" \
  --simulation "$SCENARIO" \
  --output-dir "$OUTPUT_DIR" \
  --timeout "$TIMEOUT" \
  --attacker-id "$TEST_ATTACKER_ID" \
  --attack-rate "$TEST_ATTACK_RATE" \
  --routing rpl

echo ""
echo "========================================="
echo "Analyzing Results"
echo "========================================="

# Check if log exists
if [ ! -f "$OUTPUT_DIR/COOJA.testlog" ]; then
  echo "ERROR: COOJA.testlog not found!"
  exit 1
fi

# Check for ATTACK_RATE in logs
echo "Searching for ATTACK_RATE mentions in logs..."
grep -i "ATTACK_RATE" "$OUTPUT_DIR/COOJA.testlog" | head -20 || echo "No ATTACK_RATE found in logs"

echo ""
echo "Searching for DATA_DROP events..."
DROP_COUNT=$(grep -c "ev=DATA_DROP" "$OUTPUT_DIR/COOJA.testlog" || echo "0")
echo "Total DATA_DROP events: $DROP_COUNT"

if [ "$DROP_COUNT" -eq 0 ]; then
  echo "WARNING: No DATA_DROP events found! ATTACK_RATE may not be applied."
else
  echo "SUCCESS: DATA_DROP events detected. ATTACK_RATE is working!"
fi

echo ""
echo "Searching for DATA_FWD events..."
FWD_COUNT=$(grep -c "ev=DATA_FWD" "$OUTPUT_DIR/COOJA.testlog" || echo "0")
echo "Total DATA_FWD events: $FWD_COUNT"

echo ""
echo "Searching for DATA_TX events..."
TX_COUNT=$(grep -c "ev=DATA_TX" "$OUTPUT_DIR/COOJA.testlog" || echo "0")
echo "Total DATA_TX events: $TX_COUNT"

echo ""
echo "Searching for ROOT_RX events..."
RX_COUNT=$(grep -c "ev=ROOT_RX" "$OUTPUT_DIR/COOJA.testlog" || echo "0")
echo "Total ROOT_RX events: $RX_COUNT"

echo ""
echo "========================================="
echo "Sample OBS Lines (first 10)"
echo "========================================="
grep "^OBS" "$OUTPUT_DIR/COOJA.testlog" | head -10 || echo "No OBS lines found"

echo ""
echo "========================================="
echo "Attack Statistics"
echo "========================================="
if [ "$DROP_COUNT" -gt 0 ] || [ "$FWD_COUNT" -gt 0 ]; then
  TOTAL_ATTACK_TRAFFIC=$((DROP_COUNT + FWD_COUNT))
  if [ "$TOTAL_ATTACK_TRAFFIC" -gt 0 ]; then
    ACTUAL_DROP_RATE=$(awk "BEGIN {printf \"%.2f\", $DROP_COUNT / $TOTAL_ATTACK_TRAFFIC}")
    echo "Expected drop rate: $TEST_ATTACK_RATE"
    echo "Actual drop rate: $ACTUAL_DROP_RATE"
    echo "Total packets through attacker: $TOTAL_ATTACK_TRAFFIC"
    echo "  - Dropped: $DROP_COUNT"
    echo "  - Forwarded: $FWD_COUNT"
  fi
else
  echo "No attack traffic detected yet. Simulation may need more time."
fi

echo ""
echo "Test complete. Check $OUTPUT_DIR/COOJA.testlog for full logs."
