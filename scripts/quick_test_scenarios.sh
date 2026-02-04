#!/bin/bash

# Quick test of multiple scenarios
# Shorter timeout for rapid testing

set -e

COOJA_PATH="${COOJA_PATH:-$HOME/contiki-ng/tools/cooja}"
CONTIKI_PATH="${CONTIKI_PATH:-contiki-ng-brpl}"
OUTPUT_DIR="simulations/output"
TIMEOUT=60  # Short timeout for testing
ATTACKER_ID=6
ROOT_ID=1
ROUTING="rpl"

# Test scenarios
SCENARIOS=(
    "scenario_a_low_exposure"
    "scenario_b_high_exposure"
    "scenario_c_high_pd"
)

# Test just a few attack rates
ATTACK_RATES=(0.0 0.6)

GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

mkdir -p "$OUTPUT_DIR"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  Quick Scenario Test${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo "Testing ${#SCENARIOS[@]} scenarios × ${#ATTACK_RATES[@]} rates"
echo "Timeout: ${TIMEOUT}s per simulation"
echo ""

total_runs=$((${#SCENARIOS[@]} * ${#ATTACK_RATES[@]}))
current_run=0
results_summary="$OUTPUT_DIR/quick_test_summary_$(date +%Y%m%d_%H%M%S).txt"

echo "Quick Test Results - $(date)" > "$results_summary"
echo "======================================" >> "$results_summary"
echo "" >> "$results_summary"

for scenario in "${SCENARIOS[@]}"; do
    scenario_file="simulations/scenarios/${scenario}.csc"
    
    echo -e "\n${BLUE}[SCENARIO]${NC} $scenario"
    echo "Scenario: $scenario" >> "$results_summary"
    
    for rate in "${ATTACK_RATES[@]}"; do
        current_run=$((current_run + 1))
        echo -e "${YELLOW}  [$current_run/$total_runs]${NC} attack_rate=$rate"
        
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
            > /dev/null 2>&1; then
            
            echo -e "${GREEN}    ✓${NC} Success"
            
            # Analyze results
            if [ -f "$OUTPUT_DIR/COOJA.testlog" ]; then
                drops=$(grep -c "DATA_DROP" "$OUTPUT_DIR/COOJA.testlog" || echo "0")
                fwds=$(grep -c "DATA_FWD" "$OUTPUT_DIR/COOJA.testlog" || echo "0")
                tx=$(grep -c "DATA_TX" "$OUTPUT_DIR/COOJA.testlog" || echo "0")
                rx=$(grep -c "ROOT_RX" "$OUTPUT_DIR/COOJA.testlog" || echo "0")
                
                total=$((drops + fwds))
                if [ $total -gt 0 ]; then
                    actual_rate=$(python3 -c "print(f'{$drops/$total:.3f}')" 2>/dev/null || echo "N/A")
                else
                    actual_rate="N/A"
                fi
                
                echo "      TX: $tx, RX: $rx, DROP: $drops, FWD: $fwds, Actual rate: $actual_rate"
                
                echo "  Rate $rate: TX=$tx, RX=$rx, DROP=$drops, FWD=$fwds, Actual=$actual_rate" >> "$results_summary"
            fi
        else
            echo -e "${RED}    ✗${NC} Failed"
            echo "  Rate $rate: FAILED" >> "$results_summary"
        fi
        
        sleep 1
    done
    
    echo "" >> "$results_summary"
done

echo ""
echo -e "${GREEN}Test complete!${NC} Results saved to:"
echo "  $results_summary"
cat "$results_summary"
