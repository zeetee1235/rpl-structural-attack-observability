#!/bin/bash

# Run comprehensive experiment matrix
# Tests multiple scenarios with different attack rates

set -e

# Configuration
COOJA_PATH="${COOJA_PATH:-$HOME/contiki-ng/tools/cooja}"
CONTIKI_PATH="${CONTIKI_PATH:-contiki-ng-brpl}"
OUTPUT_DIR="simulations/output"
TIMEOUT=300
ATTACKER_ID=6
ROOT_ID=1
ROUTING="rpl"

# Scenario-specific plan:
# - B(10), C(10): alpha {0,0.4,0.8,1.0}, N=5
# - A, D: alpha {0,1.0}, N=3
# - B(20): alpha {0,0.8,1.0}, N=3
SCENARIO_A="scenario_a_low_exposure"
SCENARIO_B="scenario_b_high_exposure"
SCENARIO_B20="scenario_b_high_exposure_20"
SCENARIO_C="scenario_c_high_pd"
SCENARIO_D="scenario_d_apl_bc"

ATTACK_RATES_BC=(0.0 0.4 0.8 1.0)
ATTACK_RATES_AD=(0.0 1.0)
ATTACK_RATES_B20=(0.0 0.8 1.0)

REPEATS_BC=5
REPEATS_AD=3
REPEATS_B20=3

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Create output directory
mkdir -p "$OUTPUT_DIR"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  RPL Attack Observability Experiments${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo "Configuration:"
echo "  Cooja: $COOJA_PATH"
echo "  Contiki: $CONTIKI_PATH"
echo "  Output: $OUTPUT_DIR"
echo "  Timeout: ${TIMEOUT}s"
total_runs=$(( ( ${#ATTACK_RATES_BC[@]} * REPEATS_BC * 2 ) + ( ${#ATTACK_RATES_AD[@]} * REPEATS_AD * 2 ) + ( ${#ATTACK_RATES_B20[@]} * REPEATS_B20 ) ))
echo "  Scenarios: 5 (A,B,B20,C,D)"
echo "  Total runs: $total_runs"
echo ""

current_run=0
successful_runs=0
failed_runs=0

# Log file
LOG_FILE="$OUTPUT_DIR/experiment_run_$(date +%Y%m%d_%H%M%S).log"
echo "Experiment started at $(date)" > "$LOG_FILE"

run_case() {
    local scenario="$1"
    local rates=("${!2}")
    local repeats="$3"

    local scenario_file="simulations/scenarios/${scenario}.csc"
    if [ ! -f "$scenario_file" ]; then
        echo -e "${RED}[ERROR]${NC} Scenario file not found: $scenario_file"
        return
    fi

    echo -e "\n${BLUE}[SCENARIO]${NC} $scenario (repeats=$repeats)"

    for rate in "${rates[@]}"; do
        for ((rep=1; rep<=repeats; rep++)); do
            current_run=$((current_run + 1))
            echo -e "${YELLOW}  [$current_run/$total_runs]${NC} attack_rate=$rate (rep $rep/$repeats)..."

            start_time=$(date +%s)

            if python3 scripts/run_cooja_headless.py \
                --cooja-path "$COOJA_PATH" \
                --contiki-path "$CONTIKI_PATH" \
                --simulation "$scenario_file" \
                --output-dir "$OUTPUT_DIR" \
                --timeout "$TIMEOUT" \
                --attacker-id "$ATTACKER_ID" \
                --attack-rate "$rate" \
                --root-id "$ROOT_ID" \
                --routing "$ROUTING" \
                >> "$LOG_FILE" 2>&1; then

                end_time=$(date +%s)
                duration=$((end_time - start_time))
                echo -e "${GREEN}    ✓${NC} Completed in ${duration}s"
                successful_runs=$((successful_runs + 1))
            else
                end_time=$(date +%s)
                duration=$((end_time - start_time))
                echo -e "${RED}    ✗${NC} Failed after ${duration}s"
                failed_runs=$((failed_runs + 1))
            fi

            sleep 2
        done
    done
}

run_case "$SCENARIO_B" ATTACK_RATES_BC[@] "$REPEATS_BC"
run_case "$SCENARIO_C" ATTACK_RATES_BC[@] "$REPEATS_BC"
run_case "$SCENARIO_A" ATTACK_RATES_AD[@] "$REPEATS_AD"
run_case "$SCENARIO_D" ATTACK_RATES_AD[@] "$REPEATS_AD"
run_case "$SCENARIO_B20" ATTACK_RATES_B20[@] "$REPEATS_B20"

echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  Experiment Summary${NC}"
echo -e "${BLUE}========================================${NC}"
echo "Total runs:      $total_runs"
echo -e "${GREEN}Successful:${NC}      $successful_runs"
echo -e "${RED}Failed:${NC}          $failed_runs"
echo "Log file:        $LOG_FILE"
echo ""

if [ $failed_runs -eq 0 ]; then
    echo -e "${GREEN}All experiments completed successfully!${NC}"
else
    echo -e "${YELLOW}Some experiments failed. Check log file for details.${NC}"
fi
