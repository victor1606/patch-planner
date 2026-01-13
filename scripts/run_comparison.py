"""
PatchPlanner - Comparison Runner Script

Run all strategies across all scenarios and generate comparison reports.

Usage:
    python scripts/run_comparison.py                    # Run all
    python scripts/run_comparison.py --scenario scenario1  # Single scenario
    python scripts/run_comparison.py --strategy hybrid     # Single strategy
"""

import argparse
import csv
import json
import subprocess
import sys
from pathlib import Path

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
RESULTS_DIR = PROJECT_ROOT / "results"

# Available options
SCENARIOS = ["scenario1", "scenario2", "scenario3"]
STRATEGIES = ["bigbang", "rolling", "batch_rolling", "canary", "bluegreen", "dep_greedy", "hybrid"]

# Key metrics to compare
KEY_METRICS = [
    "time_to_full_patch",
    "exposure_window_weighted",
    "mixed_version_time_seconds",
    "number_of_degraded_intervals",
    "number_of_incompatibility_violations",
    "rollback_count",
    "total_downtime_seconds_overall",
    "number_of_guardrail_pauses",
]


def run_simulation(scenario: str, strategy: str, seed: int = 42) -> dict:
    """Run a single simulation and return metrics."""
    out_dir = RESULTS_DIR / scenario / strategy
    out_dir.mkdir(parents=True, exist_ok=True)
    
    cmd = [
        sys.executable, "-m", "patchplanner.cli",
        "--scenario", str(DATA_DIR / f"{scenario}.yaml"),
        "--strategy", strategy,
        "--out", str(out_dir),
        "--seed", str(seed),
    ]
    
    print(f"  Running {strategy} on {scenario}...", end=" ", flush=True)
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=PROJECT_ROOT)
        if result.returncode != 0:
            print(f"FAILED")
            print(f"    Error: {result.stderr.strip()}")
            return {"error": result.stderr.strip()}
        print("OK")
    except Exception as e:
        print(f"ERROR: {e}")
        return {"error": str(e)}
    
    # Read metrics
    metrics_file = out_dir / "metrics.csv"
    if metrics_file.exists():
        metrics = {}
        with open(metrics_file, "r") as f:
            reader = csv.DictReader(f)
            for row in reader:
                metrics[row["metric"]] = row["value"]
        return metrics
    
    return {"error": "No metrics file generated"}


def generate_comparison_table(all_results: dict) -> str:
    """Generate a markdown comparison table."""
    lines = ["# Strategy Comparison Results\n"]
    
    for scenario in all_results:
        lines.append(f"\n## {scenario}\n")
        
        # Header
        header = "| Metric |"
        separator = "|--------|"
        for strategy in STRATEGIES:
            if strategy in all_results[scenario]:
                header += f" {strategy} |"
                separator += "-------:|"
        lines.append(header)
        lines.append(separator)
        
        # Rows
        for metric in KEY_METRICS:
            row = f"| {metric} |"
            for strategy in STRATEGIES:
                if strategy in all_results[scenario]:
                    value = all_results[scenario][strategy].get(metric, "N/A")
                    # Format large numbers
                    try:
                        num = float(value)
                        if num > 10000:
                            value = f"{num:,.0f}"
                        elif num == int(num):
                            value = f"{int(num)}"
                        else:
                            value = f"{num:.2f}"
                    except (ValueError, TypeError):
                        pass
                    row += f" {value} |"
            lines.append(row)
        
        lines.append("")
    
    return "\n".join(lines)


def generate_summary(all_results: dict) -> str:
    """Generate a summary analysis."""
    lines = ["\n# Summary Analysis\n"]
    
    for scenario in all_results:
        lines.append(f"\n## {scenario}\n")
        
        # Find best strategy for each key metric
        for metric in ["time_to_full_patch", "exposure_window_weighted", "total_downtime_seconds_overall"]:
            best_strategy = None
            best_value = float("inf")
            
            for strategy, metrics in all_results[scenario].items():
                if "error" in metrics:
                    continue
                try:
                    value = float(metrics.get(metric, float("inf")))
                    if value < best_value:
                        best_value = value
                        best_strategy = strategy
                except (ValueError, TypeError):
                    continue
            
            if best_strategy:
                lines.append(f"- **Best {metric}**: {best_strategy} ({best_value:,.0f})")
        
        lines.append("")
    
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Run PatchPlanner strategy comparisons")
    parser.add_argument("--scenario", choices=SCENARIOS, help="Run only this scenario")
    parser.add_argument("--strategy", choices=STRATEGIES, help="Run only this strategy")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility")
    args = parser.parse_args()
    
    scenarios = [args.scenario] if args.scenario else SCENARIOS
    strategies = [args.strategy] if args.strategy else STRATEGIES
    
    print("=" * 60)
    print("PatchPlanner Strategy Comparison")
    print("=" * 60)
    
    RESULTS_DIR.mkdir(exist_ok=True)
    all_results = {}
    
    for scenario in scenarios:
        print(f"\n[{scenario}]")
        all_results[scenario] = {}
        
        for strategy in strategies:
            metrics = run_simulation(scenario, strategy, args.seed)
            all_results[scenario][strategy] = metrics
    
    # Save raw results as JSON
    results_json = RESULTS_DIR / "all_results.json"
    with open(results_json, "w") as f:
        json.dump(all_results, f, indent=2)
    print(f"\nRaw results saved to: {results_json}")
    
    # Generate comparison report
    report = generate_comparison_table(all_results)
    report += generate_summary(all_results)
    
    report_file = RESULTS_DIR / "comparison_report.md"
    with open(report_file, "w") as f:
        f.write(report)
    print(f"Comparison report saved to: {report_file}")
    
    print("\n" + "=" * 60)
    print("Done!")
    print("=" * 60)


if __name__ == "__main__":
    main()
