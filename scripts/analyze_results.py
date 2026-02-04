#!/usr/bin/env python3

"""
Analyze all completed simulation results and generate summary report
"""

import re
import sys
from pathlib import Path
from datetime import datetime
import csv
import math
import argparse

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
        'attacker_id': None,
        'sim_time_ms': 0,
        'nodes': set(),
        'parent_events': 0,
        'parent_attack_events': 0,
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
            match = re.search(r'node=(\d+)', line)
            if match:
                stats['attacker_id'] = int(match.group(1))
        
        # Extract timestamp
        match = re.search(r'ts=(\d+)', line)
        if match:
            stats['sim_time_ms'] = max(stats['sim_time_ms'], int(match.group(1)))
        
        # Extract node ID
        match = re.search(r'node=(\d+)', line)
        if match:
            stats['nodes'].add(int(match.group(1)))

        if 'PARENT' in line:
            stats['parent_events'] += 1
            if stats['attacker_id'] is not None:
                match = re.search(r'parent=(\d+)', line)
                if match and int(match.group(1)) == stats['attacker_id']:
                    stats['parent_attack_events'] += 1
    
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
    stats['pdr_clipped'] = min(1.0, stats['pdr'])
    if stats['parent_events'] > 0:
        stats['exposure_e1_prime'] = stats['parent_attack_events'] / stats['parent_events']
    else:
        stats['exposure_e1_prime'] = None
    
    return stats

def find_log_files(output_dir, min_timestamp=None):
    """Find all simulation log files"""
    output_path = Path(output_dir)
    log_files = {}
    
    # Pattern: scenario_name_timestamp.log
    for log_file in output_path.glob("scenario_*.log"):
        if min_timestamp is not None and log_file.stat().st_mtime < min_timestamp:
            continue
        # Find corresponding per-run COOJA testlog
        testlog = output_path / f"{log_file.stem}_COOJA.testlog"
        if testlog.exists():
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

def t_critical_95(n):
    if n <= 1:
        return 0.0
    table = {
        2: 12.706,
        3: 4.303,
        4: 3.182,
        5: 2.776,
        6: 2.571,
        7: 2.447,
        8: 2.365,
        9: 2.306,
        10: 2.262,
    }
    return table.get(n, 1.96)

def main():
    parser = argparse.ArgumentParser(description="Analyze simulation results")
    parser.add_argument(
        "--log-file",
        type=Path,
        help="Experiment run log file to scope analysis (optional)",
    )
    args = parser.parse_args()

    output_dir = Path("simulations/output")
    min_timestamp = None
    if args.log_file and args.log_file.exists():
        try:
            ts_str = args.log_file.stem.replace("experiment_run_", "")
            min_timestamp = datetime.strptime(ts_str, "%Y%m%d_%H%M%S").timestamp()
        except Exception:
            min_timestamp = args.log_file.stat().st_mtime
    
    print("=" * 70)
    print("  Simulation Results Analysis")
    print("=" * 70)
    print()
    
    # Find and analyze logs
    log_files = find_log_files(output_dir, min_timestamp=min_timestamp)
    
    if not log_files:
        print("No simulation log files found in", output_dir)
        return
    
    print(f"Found {len(log_files)} simulation runs\n")
    
    results = []
    grouped = {}
    
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
                'pdr_clipped': stats['pdr_clipped'],
                'data_drop': stats['data_drop'],
                'data_fwd': stats['data_fwd'],
                'attack_rate_logged': stats['attack_rate_logged'],
                'actual_drop_rate': stats['actual_drop_rate'],
                'exposure_e1_prime': stats['exposure_e1_prime'],
            })
            key = (scenario, stats['attack_rate_logged'])
            grouped.setdefault(key, []).append(stats['pdr_clipped'])
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

    # Print CI summary per scenario/alpha
    if grouped:
        print("\nPDR* 95% CI (by scenario, attack_rate):")
        for (scenario, rate) in sorted(grouped.keys(), key=lambda x: (x[0], x[1] if x[1] is not None else -1)):
            values = grouped[(scenario, rate)]
            n = len(values)
            mean = sum(values) / n if n > 0 else 0.0
            if n > 1:
                var = sum((v - mean) ** 2 for v in values) / (n - 1)
                s = math.sqrt(var)
                t_val = t_critical_95(n)
                ci = t_val * (s / math.sqrt(n))
            else:
                ci = 0.0
            rate_str = f"{rate:.2f}" if rate is not None else "NA"
            print(f"  {scenario} α={rate_str} | n={n} | PDR*={mean:.4f} ± {ci:.4f}")
    
    print("=" * 70)

if __name__ == "__main__":
    main()
