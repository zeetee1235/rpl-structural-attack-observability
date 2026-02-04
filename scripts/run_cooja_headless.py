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
            alt_jar = cooja_path / "build" / "libs" / "cooja.jar"
            if alt_jar.exists():
                self.cooja_jar = alt_jar
        
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

        simulation_file = simulation_file.resolve()
        
        output_dir.mkdir(parents=True, exist_ok=True)
        output_dir = output_dir.resolve()
        
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
            "--enable-preview",
            "-jar", str(self.cooja_jar),
            "--no-gui",
            "--contiki=" + str(self.contiki_path),
            "--cooja=" + str(self.cooja_path),
            "--logdir=" + str(output_dir),
        ]
        cmd.append(str(simulation_file))
        
        if random_seed is not None:
            cmd.append(f"-random-seed={random_seed}")
        
        # Pre-build firmware with specified parameters
        firmware_dir = self.contiki_path / "simulations" / "firmware"
        if not firmware_dir.exists():
            firmware_dir = simulation_file.parent.parent / "firmware"
        
        if firmware_dir.exists():
            print(f"[INFO] Pre-building firmware with parameters...")
            print(f"[INFO]   ATTACKER_ID={attacker_id or 6}")
            print(f"[INFO]   ATTACK_RATE={attack_rate or 0.0}")
            print(f"[INFO]   ROOT_ID={root_id or 1}")
            
            build_env = dict(**os.environ)
            build_env["CONTIKI"] = str(self.contiki_path)
            if attacker_id is not None:
                build_env["ATTACKER_ID"] = str(attacker_id)
            if attack_rate is not None:
                build_env["ATTACK_RATE"] = str(attack_rate)
            if root_id is not None:
                build_env["ROOT_ID"] = str(root_id)
            if routing:
                routing_map = {
                    "rpl-lite": "MAKE_ROUTING_RPL_LITE",
                    "rpl-classic": "MAKE_ROUTING_RPL_CLASSIC",
                    "rpl": "MAKE_ROUTING_RPL_CLASSIC",
                    "brpl": "MAKE_ROUTING_RPL_CLASSIC",
                }
                build_env["MAKE_ROUTING"] = routing_map.get(routing, routing)
                if routing == "brpl":
                    build_env["BRPL"] = "1"
            
            # Clean and rebuild
            build_cmd = ["make", "clean", "TARGET=cooja"]
            subprocess.run(build_cmd, cwd=str(firmware_dir), env=build_env, 
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            build_cmd = ["make", "rpl-node.cooja", "TARGET=cooja"]
            if attacker_id is not None:
                build_cmd.append(f"ATTACKER_ID={attacker_id}")
            if attack_rate is not None:
                build_cmd.append(f"ATTACK_RATE={attack_rate}")
            if root_id is not None:
                build_cmd.append(f"ROOT_ID={root_id}")
            
            build_result = subprocess.run(build_cmd, cwd=str(firmware_dir), env=build_env,
                                        capture_output=True, text=True)
            if build_result.returncode != 0:
                print(f"[ERROR] Firmware build failed!")
                print(build_result.stderr)
                return {
                    "success": False,
                    "error": "firmware_build_failed",
                    "log_file": None,
                    "testlog_file": None
                }
            print(f"[INFO] Firmware built successfully")
        
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
                    cwd=str(output_dir),
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
