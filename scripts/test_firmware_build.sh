#!/bin/bash
# Verify firmware compilation with ATTACK_RATE

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
FIRMWARE_DIR="$PROJECT_ROOT/simulations/firmware"

echo "========================================="
echo "Testing Firmware Compilation"
echo "========================================="

cd "$FIRMWARE_DIR"

# Test with different attack rates
for RATE in 0.0 0.2 0.6 1.0; do
  echo ""
  echo "Testing with ATTACK_RATE=$RATE"
  echo "-----------------------------------"
  
  # Clean and build
  make clean TARGET=cooja
  
  # Build with explicit ATTACK_RATE
  export ATTACKER_ID=6
  export ATTACK_RATE=$RATE
  export ROOT_ID=1
  
  make rpl-node.cooja TARGET=cooja ATTACKER_ID=$ATTACKER_ID ATTACK_RATE=$ATTACK_RATE ROOT_ID=$ROOT_ID
  
  # Check if the binary contains the rate (converted to string representation)
  if [ -f "build/cooja/rpl-node.cooja" ]; then
    echo "Binary created successfully"
    
    # Try to find ATTACK_RATE in the compiled binary (as a float constant)
    # This is a rough check - floating point constants are hard to search for
    strings build/cooja/rpl-node.cooja | grep -i "attack" | head -5 || echo "No 'attack' strings found"
    
    # Check the preprocessor defines by recompiling with -E flag
    echo ""
    echo "Checking preprocessor defines..."
    gcc -E -DATTACKER_ID=$ATTACKER_ID -DATTACK_RATE=$ATTACK_RATE -DROOT_ID=$ROOT_ID rpl-node.c 2>/dev/null | grep "ATTACK_RATE" | head -3 || echo "Preprocessor check failed"
  else
    echo "ERROR: Build failed!"
    exit 1
  fi
done

echo ""
echo "========================================="
echo "Compilation test complete"
echo "========================================="
echo ""
echo "Now test with actual simulation using:"
echo "./scripts/test_attack_rate.sh"
