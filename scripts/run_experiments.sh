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

# Scenarios to test
SCENARIOS=(
    "scenario_a_low_exposure"
    "scenario_b_high_exposure"
    "scenario_b_high_exposure_20"
    "scenario_c_high_pd"
    "scenario_d_apl_bc"
)

# Attack rates to test
ATTACK_RATES=(0.0 0.2 0.4 0.6 0.8 1.0)

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
echo "  Scenarios: ${#SCENARIOS[@]}"
echo "  Attack rates: ${#ATTACK_RATES[@]}"
echo "  Total runs: $((${#SCENARIOS[@]} * ${#ATTACK_RATES[@]}))"
echo ""

# Counter
total_runs=$((${#SCENARIOS[@]} * ${#ATTACK_RATES[@]}))
current_run=0
successful_runs=0
failed_runs=0

# Log file
LOG_FILE="$OUTPUT_DIR/experiment_run_$(date +%Y%m%d_%H%M%S).log"
echo "Experiment started at $(date)" > "$LOG_FILE"

# Run experiments
for scenario in "${SCENARIOS[@]}"; do
    scenario_file="simulations/scenarios/${scenario}.csc"
    
    if [ ! -f "$scenario_file" ]; then
        echo -e "${RED}[ERROR]${NC} Scenario file not found: $scenario_file"
        continue
    fi
    
    echo -e "\n${BLUE}[SCENARIO]${NC} $scenario"
    
    for rate in "${ATTACK_RATES[@]}"; do
        current_run=$((current_run + 1))
        
        echo -e "${YELLOW}  [$current_run/$total_runs]${NC} Testing attack_rate=$rate..."
        
        start_time=$(date +%s)
        
        # Run simulation
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
            
            # Quick stats
            if [ -f "$OUTPUT_DIR/COOJA.testlog" ]; then
                drops=$(grep -c "DATA_DROP" "$OUTPUT_DIR/COOJA.testlog" || echo "0")
                fwds=$(grep -c "DATA_FWD" "$OUTPUT_DIR/COOJA.testlog" || echo "0")
                echo "      DROP: $drops, FWD: $fwds"
            fi
        else
            end_time=$(date +%s)
            duration=$((end_time - start_time))
            
            echo -e "${RED}    ✗${NC} Failed after ${duration}s"
            failed_runs=$((failed_runs + 1))
        fi
        
        # Brief pause between runs
        sleep 2
    done
done

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
