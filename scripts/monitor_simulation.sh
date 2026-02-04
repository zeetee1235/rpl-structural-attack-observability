#!/bin/bash
# Monitor Cooja simulation progress by tailing log files in real-time

set -e

# Default values
OUTPUT_DIR="simulations/output"
INTERVAL=5
NUM_LINES=30

# Parse arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --output-dir)
      OUTPUT_DIR="$2"
      shift 2
      ;;
    --interval)
      INTERVAL="$2"
      shift 2
      ;;
    --lines)
      NUM_LINES="$2"
      shift 2
      ;;
    -h|--help)
      echo "Usage: $0 [OPTIONS]"
      echo ""
      echo "Monitor Cooja simulation progress in real-time"
      echo ""
      echo "Options:"
      echo "  --output-dir DIR   Directory containing simulation logs (default: simulations/output)"
      echo "  --interval SEC     Refresh interval in seconds (default: 5)"
      echo "  --lines N          Number of recent lines to show (default: 30)"
      echo "  -h, --help         Show this help message"
      exit 0
      ;;
    *)
      echo "Unknown option: $1"
      exit 1
      ;;
  esac
done

# Check if output directory exists
if [ ! -d "$OUTPUT_DIR" ]; then
  echo "Error: Output directory does not exist: $OUTPUT_DIR"
  exit 1
fi

echo "=========================================="
echo "COOJA SIMULATION MONITOR"
echo "=========================================="
echo "Output directory: $OUTPUT_DIR"
echo "Refresh interval: ${INTERVAL}s"
echo "Showing last: $NUM_LINES lines"
echo "Press Ctrl+C to stop"
echo "=========================================="
echo ""

# Function to find latest log file
find_latest_log() {
  find "$OUTPUT_DIR" -name "*.log" -type f -printf '%T@ %p\n' 2>/dev/null | sort -rn | head -1 | cut -d' ' -f2-
}

# Function to count events in log
count_events() {
  local log_file="$1"
  
  if [ ! -f "$log_file" ]; then
    return
  fi
  
  echo "=========================================="
  echo "LOG STATISTICS"
  echo "=========================================="
  
  local total_lines=$(wc -l < "$log_file")
  local obs_lines=$(grep -c "^OBS" "$log_file" 2>/dev/null || echo 0)
  local data_tx=$(grep -c "ev=DATA_TX" "$log_file" 2>/dev/null || echo 0)
  local data_rx=$(grep -c "ev=ROOT_RX\|ev=DATA_RX" "$log_file" 2>/dev/null || echo 0)
  local data_drop=$(grep -c "ev=DATA_DROP" "$log_file" 2>/dev/null || echo 0)
  local parent_changes=$(grep -c "ev=PARENT" "$log_file" 2>/dev/null || echo 0)
  local attack_drops=$(grep -c "reason=attack" "$log_file" 2>/dev/null || echo 0)
  
  printf "Total lines:       %8d\n" "$total_lines"
  printf "OBS lines:         %8d\n" "$obs_lines"
  printf "DATA_TX:           %8d\n" "$data_tx"
  printf "DATA_RX (root):    %8d\n" "$data_rx"
  printf "DATA_DROP:         %8d\n" "$data_drop"
  printf "Attack drops:      %8d\n" "$attack_drops"
  printf "Parent changes:    %8d\n" "$parent_changes"
  
  if [ "$data_tx" -gt 0 ]; then
    local pdr=$(awk "BEGIN {printf \"%.2f\", ($data_rx / $data_tx) * 100}")
    printf "Estimated PDR:     %7.2f%%\n" "$pdr"
  fi
  
  echo ""
  echo "Top Events:"
  grep "^OBS" "$log_file" 2>/dev/null | \
    sed 's/.*ev=\([^ ]*\).*/\1/' | \
    sort | uniq -c | sort -rn | head -10 | \
    awk '{printf "  %-20s %6d\n", $2, $1}'
  
  echo "=========================================="
}

# Function to show recent lines with highlighting
show_tail() {
  local log_file="$1"
  local num_lines="$2"
  
  echo ""
  echo "=========================================="
  echo "RECENT LOG LINES (last $num_lines)"
  echo "=========================================="
  
  if [ -f "$log_file" ]; then
    tail -n "$num_lines" "$log_file" | while IFS= read -r line; do
      # Highlight different event types
      if echo "$line" | grep -q "ev=DATA_DROP.*reason=attack"; then
        echo -e "\033[1;31m$line\033[0m"  # Red for attack drops
      elif echo "$line" | grep -q "ev=ROOT_RX"; then
        echo -e "\033[1;32m$line\033[0m"  # Green for root reception
      elif echo "$line" | grep -q "ev=PARENT"; then
        echo -e "\033[1;33m$line\033[0m"  # Yellow for parent changes
      elif echo "$line" | grep -q "ev=ATTACK_STATS"; then
        echo -e "\033[1;35m$line\033[0m"  # Magenta for attack stats
      else
        echo "$line"
      fi
    done
  else
    echo "No log file found yet..."
  fi
  
  echo "=========================================="
}

# Monitoring loop
LAST_LOG=""
while true; do
  # Find latest log file
  LATEST_LOG=$(find_latest_log)
  
  if [ -z "$LATEST_LOG" ]; then
    clear
    echo "=========================================="
    echo "WAITING FOR LOG FILES..."
    echo "=========================================="
    echo "Directory: $OUTPUT_DIR"
    echo "Time: $(date '+%Y-%m-%d %H:%M:%S')"
    echo ""
    echo "No .log files found yet."
    echo "Simulation may not have started."
    sleep "$INTERVAL"
    continue
  fi
  
  # Check if we're monitoring a new file
  if [ "$LATEST_LOG" != "$LAST_LOG" ]; then
    echo ""
    echo "[$(date '+%H:%M:%S')] Now monitoring: $(basename "$LATEST_LOG")"
    LAST_LOG="$LATEST_LOG"
  fi
  
  # Clear screen and show header
  clear
  echo "=========================================="
  echo "SIMULATION MONITOR"
  echo "=========================================="
  echo "Time:      $(date '+%Y-%m-%d %H:%M:%S')"
  echo "Log file:  $(basename "$LATEST_LOG")"
  echo "File size: $(du -h "$LATEST_LOG" | cut -f1)"
  echo "=========================================="
  echo ""
  
  # Show statistics
  count_events "$LATEST_LOG"
  
  # Show recent lines
  show_tail "$LATEST_LOG" "$NUM_LINES"
  
  echo ""
  echo "[Refreshing every ${INTERVAL}s | Press Ctrl+C to stop]"
  
  # Wait for next update
  sleep "$INTERVAL"
done
