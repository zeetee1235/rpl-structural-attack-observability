#!/usr/bin/env python3

"""
Analyze all completed simulation results and generate summary report
"""

import re
import sys
from pathlib import Path
from datetime import datetime
import csv

def parse_cooja_testlog(log_file):
    """Parse COOJA.testlog and extract statistics"""
    if not log_file.exists():
        return None
    
    with open(log_file) as f:
        lines = f.readlines()
    
    stats = {
        'total_lines': len(lines),
        'data_tx': 0,
        'root_rx': 0,
        'data_drop': 0,
        'data_fwd': 0,
        'attack_rate_logged': None,
        'sim_time_ms': 0,
        'nodes': set(),
    }
    
    for line in lines:
        if 'DATA_TX' in line:
            stats['data_tx'] += 1
        if 'ROOT_RX' in line:
            stats['root_rx'] += 1
        if 'DATA_DROP' in line:
            stats['data_drop'] += 1
        if 'DATA_FWD' in line:
            stats['data_fwd'] += 1
        
        if 'ATTACK_START' in line:
            match = re.search(r'rate=(\d+\.\d+)', line)
            if match:
                stats['attack_rate_logged'] = float(match.group(1))
        
        # Extract timestamp
        match = re.search(r'ts=(\d+)', line)
        if match:
            stats['sim_time_ms'] = max(stats['sim_time_ms'], int(match.group(1)))
        
        # Extract node ID
        match = re.search(r'node=(\d+)', line)
        if match:
            stats['nodes'].add(int(match.group(1)))
    
    # Calculate derived metrics
    if stats['data_tx'] > 0:
        stats['pdr'] = stats['root_rx'] / stats['data_tx']
    else:
        stats['pdr'] = 0.0
    
    total_through_attacker = stats['data_drop'] + stats['data_fwd']
    if total_through_attacker > 0:
        stats['actual_drop_rate'] = stats['data_drop'] / total_through_attacker
    else:
        stats['actual_drop_rate'] = None
    
    stats['num_nodes'] = len(stats['nodes'])
    stats['sim_time_sec'] = stats['sim_time_ms'] / 1000.0
    
    return stats

def find_log_files(output_dir):
    """Find all simulation log files"""
    output_path = Path(output_dir)
    log_files = {}
    
    # Pattern: scenario_name_timestamp.log
    for log_file in output_path.glob("scenario_*.log"):
        # Find corresponding COOJA.testlog
        testlog = output_path / "COOJA.testlog"
        if testlog.exists() and testlog.stat().st_mtime > log_file.stat().st_mtime - 60:
            # Parse scenario name and timestamp
            parts = log_file.stem.split('_')
            scenario = '_'.join(parts[:-2]) if len(parts) > 2 else log_file.stem
            
            log_files[log_file] = {
                'scenario': scenario,
                'log': log_file,
                'testlog': testlog,
                'timestamp': log_file.stat().st_mtime
            }
    
    return log_files

def main():
    output_dir = Path("simulations/output")
    
    print("=" * 70)
    print("  Simulation Results Analysis")
    print("=" * 70)
    print()
    
    # Find and analyze logs
    log_files = find_log_files(output_dir)
    
    if not log_files:
        print("No simulation log files found in", output_dir)
        return
    
    print(f"Found {len(log_files)} simulation runs\n")
    
    results = []
    
    for log_info in sorted(log_files.values(), key=lambda x: x['timestamp']):
        scenario = log_info['scenario']
        testlog = log_info['testlog']
        
        print(f"Analyzing: {scenario}")
        
        stats = parse_cooja_testlog(testlog)
        
        if stats:
            print(f"  Nodes: {stats['num_nodes']}")
            print(f"  Sim time: {stats['sim_time_sec']:.1f}s")
            print(f"  TX: {stats['data_tx']}, RX: {stats['root_rx']}, PDR: {stats['pdr']:.2%}")
            
            if stats['attack_rate_logged'] is not None:
                print(f"  Attack rate (logged): {stats['attack_rate_logged']:.2f}")
            
            if stats['actual_drop_rate'] is not None:
                print(f"  DROP: {stats['data_drop']}, FWD: {stats['data_fwd']}")
                print(f"  Actual drop rate: {stats['actual_drop_rate']:.2%}")
            
            results.append({
                'scenario': scenario,
                'num_nodes': stats['num_nodes'],
                'sim_time_sec': stats['sim_time_sec'],
                'data_tx': stats['data_tx'],
                'root_rx': stats['root_rx'],
                'pdr': stats['pdr'],
                'data_drop': stats['data_drop'],
                'data_fwd': stats['data_fwd'],
                'attack_rate_logged': stats['attack_rate_logged'],
                'actual_drop_rate': stats['actual_drop_rate'],
            })
        else:
            print(f"  No data found")
        
        print()
    
    # Save summary CSV
    if results:
        csv_file = output_dir / f"simulation_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        with open(csv_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=results[0].keys())
            writer.writeheader()
            writer.writerows(results)
        
        print(f"Summary saved to: {csv_file}")
    
    print("=" * 70)

if __name__ == "__main__":
    main()
