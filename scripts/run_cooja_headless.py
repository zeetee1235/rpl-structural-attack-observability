#!/usr/bin/env python3
"""
Headless Cooja simulation runner for RPL observability experiments.
Automatically runs Cooja simulations and extracts logs.
"""

import argparse
import subprocess
import sys
import os
from pathlib import Path
from datetime import datetime


class CoojaRunner:
    """Runs Cooja simulations in headless mode and collects output."""
    
    def __init__(self, cooja_path: Path, contiki_path: Path):
        """
        Initialize the Cooja runner.
        
        Args:
            cooja_path: Path to Cooja installation (containing cooja.jar)
            contiki_path: Path to Contiki-NG root directory
        """
        self.cooja_path = cooja_path
        self.contiki_path = contiki_path
        self.cooja_jar = cooja_path / "cooja.jar"
        
        if not self.cooja_jar.exists():
            raise FileNotFoundError(f"Cooja JAR not found at {self.cooja_jar}")
    
    def run_simulation(
        self,
        simulation_file: Path,
        output_dir: Path,
        timeout_minutes: int = 20,
        random_seed: int = None,
        attacker_id: int | None = None,
        attack_rate: float | None = None,
        root_id: int | None = None,
        routing: str | None = None,
    ) -> dict:
        """
        Run a Cooja simulation in headless mode.
        
        Args:
            simulation_file: Path to .csc simulation file
            output_dir: Directory to save output logs
            timeout_minutes: Maximum simulation runtime
            random_seed: Optional random seed override
            
        Returns:
            Dictionary with status and output paths
        """
        if not simulation_file.exists():
            raise FileNotFoundError(f"Simulation file not found: {simulation_file}")
        
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate output filenames
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        sim_name = simulation_file.stem
        log_file = output_dir / f"{sim_name}_{timestamp}.log"
        testlog_file = output_dir / f"{sim_name}_{timestamp}_COOJA.testlog"
        
        # Build command
        cmd = [
            "java",
            "-Xms512m",
            "-Xmx4096m",
            "-jar", str(self.cooja_jar),
            "-nogui=" + str(simulation_file),
            "-contiki=" + str(self.contiki_path),
        ]
        
        if random_seed is not None:
            cmd.append(f"-random-seed={random_seed}")
        
        print(f"[INFO] Starting simulation: {sim_name}")
        print(f"[INFO] Command: {' '.join(cmd)}")
        print(f"[INFO] Log output: {log_file}")
        print(f"[INFO] Test log: {testlog_file}")
        
        try:
            # Run Cooja with output capture
            with open(log_file, 'w') as log_fh:
                env = dict(**os.environ)
                env["CONTIKI"] = str(self.contiki_path)
                if routing:
                    routing_map = {
                        "rpl-lite": "MAKE_ROUTING_RPL_LITE",
                        "rpl-classic": "MAKE_ROUTING_RPL_CLASSIC",
                        "rpl": "MAKE_ROUTING_RPL_CLASSIC",
                        "brpl": "MAKE_ROUTING_RPL_CLASSIC",
                    }
                    env["MAKE_ROUTING"] = routing_map.get(routing, routing)
                    if routing == "brpl":
                        env["BRPL"] = "1"
                if attacker_id is not None:
                    env["ATTACKER_ID"] = str(attacker_id)
                if attack_rate is not None:
                    env["ATTACK_RATE"] = str(attack_rate)
                if root_id is not None:
                    env["ROOT_ID"] = str(root_id)
                result = subprocess.run(
                    cmd,
                    stdout=log_fh,
                    stderr=subprocess.STDOUT,
                    timeout=timeout_minutes * 60,
                    cwd=str(self.cooja_path),
                    env=env,
                )
            
            # Check if simulation succeeded
            success = result.returncode == 0
            
            if success:
                print(f"[SUCCESS] Simulation completed successfully")
            else:
                print(f"[ERROR] Simulation failed with return code {result.returncode}")
            
            return {
                "success": success,
                "log_file": log_file,
                "testlog_file": testlog_file,
                "return_code": result.returncode
            }
            
        except subprocess.TimeoutExpired:
            print(f"[ERROR] Simulation timed out after {timeout_minutes} minutes")
            return {
                "success": False,
                "log_file": log_file,
                "testlog_file": None,
                "error": "timeout"
            }
        except Exception as e:
            print(f"[ERROR] Failed to run simulation: {e}")
            return {
                "success": False,
                "error": str(e)
            }


def main():
    """Main entry point for the Cooja runner."""
    parser = argparse.ArgumentParser(
        description="Run Cooja simulations in headless mode"
    )
    parser.add_argument(
        "--cooja-path",
        type=Path,
        required=True,
        help="Path to Cooja installation directory (containing cooja.jar)"
    )
    parser.add_argument(
        "--contiki-path",
        type=Path,
        required=True,
        help="Path to Contiki-NG root directory"
    )
    parser.add_argument(
        "--simulation",
        type=Path,
        required=True,
        help="Path to .csc simulation file"
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("./simulations/output"),
        help="Directory to save output logs (default: ./simulations/output)"
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=20,
        help="Simulation timeout in minutes (default: 20)"
    )
    parser.add_argument(
        "--random-seed",
        type=int,
        help="Random seed for simulation (optional)"
    )
    parser.add_argument(
        "--attacker-id",
        type=int,
        help="Attacker node ID (optional, passed to firmware build)"
    )
    parser.add_argument(
        "--attack-rate",
        type=float,
        help="Attack rate alpha in [0,1] (optional, passed to firmware build)"
    )
    parser.add_argument(
        "--root-id",
        type=int,
        help="Root node ID (optional, passed to firmware build)"
    )
    parser.add_argument(
        "--routing",
        type=str,
        help="Routing mode: rpl-lite or rpl-classic (optional, passed to firmware build)"
    )
    
    args = parser.parse_args()
    
    try:
        runner = CoojaRunner(args.cooja_path, args.contiki_path)
        result = runner.run_simulation(
            args.simulation,
            args.output_dir,
            timeout_minutes=args.timeout,
            random_seed=args.random_seed,
            attacker_id=args.attacker_id,
            attack_rate=args.attack_rate,
            root_id=args.root_id,
            routing=args.routing,
        )
        
        if result["success"]:
            print(f"\n✓ Simulation completed successfully")
            print(f"  Log file: {result['log_file']}")
            sys.exit(0)
        else:
            print(f"\n✗ Simulation failed")
            if "error" in result:
                print(f"  Error: {result['error']}")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n✗ Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
