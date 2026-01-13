"""
Quick runner for single simulations.

Usage:
    python scripts/run.py scenario1 hybrid
    python scripts/run.py scenario2 rolling --seed 123
"""

import argparse
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent


def main():
    parser = argparse.ArgumentParser(description="Run a single PatchPlanner simulation")
    parser.add_argument("scenario", help="Scenario name (e.g., scenario1)")
    parser.add_argument("strategy", help="Strategy name (e.g., hybrid)")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--out", default="out", help="Output directory")
    args = parser.parse_args()
    
    scenario_file = PROJECT_ROOT / "data" / f"{args.scenario}.yaml"
    if not scenario_file.exists():
        print(f"Error: Scenario file not found: {scenario_file}")
        sys.exit(1)
    
    cmd = [
        sys.executable, "-m", "patchplanner.cli",
        "--scenario", str(scenario_file),
        "--strategy", args.strategy,
        "--out", args.out,
        "--seed", str(args.seed),
    ]
    
    print(f"Running: {args.strategy} on {args.scenario}")
    print(f"Output: {args.out}/")
    print("-" * 40)
    
    result = subprocess.run(cmd, cwd=PROJECT_ROOT)
    sys.exit(result.returncode)


if __name__ == "__main__":
    main()
