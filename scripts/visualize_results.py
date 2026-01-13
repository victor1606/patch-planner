"""
Visualization script for comparing patch deployment strategies.

Generates comparison charts from simulation results for academic paper inclusion.

Usage:
    python scripts/visualize_results.py results/all_results.json
    python scripts/visualize_results.py results/all_results.json --output figures/
"""

import argparse
import json
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

# Key metrics to visualize
METRICS = {
    "time_to_full_patch": {
        "label": "Time to Complete (seconds)",
        "lower_is_better": True,
    },
    "exposure_window_weighted": {
        "label": "Security Exposure (weighted)",
        "lower_is_better": True,
    },
    "total_downtime_seconds_overall": {
        "label": "Total Downtime (seconds)",
        "lower_is_better": True,
    },
    "mixed_version_time_seconds": {
        "label": "Mixed Version Time (seconds)",
        "lower_is_better": True,
    },
    "rollback_count": {
        "label": "Rollback Count",
        "lower_is_better": True,
    },
    "number_of_guardrail_pauses": {
        "label": "Guardrail Pauses",
        "lower_is_better": False,
    },
}

STRATEGY_COLORS = {
    "bigbang": "#e74c3c",      # Red
    "rolling": "#3498db",       # Blue
    "batch_rolling": "#9b59b6", # Purple
    "canary": "#f39c12",        # Orange
    "bluegreen": "#2ecc71",     # Green
    "dep_greedy": "#1abc9c",    # Teal
    "hybrid": "#e67e22",        # Dark Orange
}


def load_results(results_file: Path) -> dict:
    """Load simulation results from JSON."""
    with open(results_file, "r") as f:
        return json.load(f)


def plot_metric_comparison(all_results: dict, metric: str, config: dict, output_dir: Path):
    """Create bar chart comparing strategies across scenarios for a metric."""
    scenarios = sorted(all_results.keys())
    strategies = sorted(set(
        strategy
        for scenario in all_results.values()
        for strategy in scenario.keys()
        if "error" not in scenario[strategy]
    ))
    
    fig, axes = plt.subplots(1, len(scenarios), figsize=(5 * len(scenarios), 5))
    if len(scenarios) == 1:
        axes = [axes]
    
    for idx, scenario in enumerate(scenarios):
        ax = axes[idx]
        values = []
        labels = []
        colors = []
        
        for strategy in strategies:
            if strategy in all_results[scenario]:
                result = all_results[scenario][strategy]
                if "error" not in result and metric in result:
                    try:
                        value = float(result[metric])
                        values.append(value)
                        labels.append(strategy)
                        colors.append(STRATEGY_COLORS.get(strategy, "#95a5a6"))
                    except (ValueError, TypeError):
                        continue
        
        if values:
            bars = ax.bar(range(len(values)), values, color=colors)
            ax.set_xticks(range(len(labels)))
            ax.set_xticklabels(labels, rotation=45, ha="right")
            ax.set_ylabel(config["label"])
            ax.set_title(f"{scenario}")
            ax.grid(axis="y", alpha=0.3)
            
            # Highlight best value
            if config["lower_is_better"]:
                best_idx = values.index(min(values))
            else:
                best_idx = values.index(max(values))
            bars[best_idx].set_edgecolor("gold")
            bars[best_idx].set_linewidth(3)
    
    fig.suptitle(f"Strategy Comparison: {config['label']}", fontsize=14, fontweight="bold")
    plt.tight_layout()
    
    output_file = output_dir / f"{metric}_comparison.png"
    plt.savefig(output_file, dpi=300, bbox_inches="tight")
    print(f"  Saved: {output_file}")
    plt.close()


def plot_radar_chart(all_results: dict, scenario: str, output_dir: Path):
    """Create radar chart showing multi-dimensional strategy comparison."""
    import numpy as np
    
    # Select key metrics for radar chart
    radar_metrics = [
        "time_to_full_patch",
        "exposure_window_weighted",
        "total_downtime_seconds_overall",
        "mixed_version_time_seconds",
    ]
    
    if scenario not in all_results:
        return
    
    strategies = [s for s in all_results[scenario].keys() if "error" not in all_results[scenario][s]]
    
    # Prepare data
    num_metrics = len(radar_metrics)
    angles = np.linspace(0, 2 * np.pi, num_metrics, endpoint=False).tolist()
    angles += angles[:1]  # Complete the circle
    
    fig, ax = plt.subplots(figsize=(10, 10), subplot_kw=dict(projection="polar"))
    
    for strategy in strategies:
        values = []
        for metric in radar_metrics:
            try:
                value = float(all_results[scenario][strategy].get(metric, 0))
                values.append(value)
            except (ValueError, TypeError):
                values.append(0)
        
        # Normalize values to 0-1 scale (lower is better for all these metrics)
        max_vals = [max(float(all_results[scenario][s].get(m, 0)) for s in strategies 
                       if "error" not in all_results[scenario][s]) or 1
                   for m in radar_metrics]
        normalized = [1 - (v / mv) if mv > 0 else 0 for v, mv in zip(values, max_vals)]
        normalized += normalized[:1]  # Complete the circle
        
        ax.plot(angles, normalized, "o-", linewidth=2, 
                label=strategy, color=STRATEGY_COLORS.get(strategy, "#95a5a6"))
        ax.fill(angles, normalized, alpha=0.15, color=STRATEGY_COLORS.get(strategy, "#95a5a6"))
    
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels([METRICS[m]["label"].split("(")[0].strip() for m in radar_metrics])
    ax.set_ylim(0, 1)
    ax.set_title(f"Multi-Metric Comparison: {scenario}\n(Outer = Better)", 
                 fontsize=14, fontweight="bold", pad=20)
    ax.legend(loc="upper right", bbox_to_anchor=(1.3, 1.1))
    ax.grid(True)
    
    output_file = output_dir / f"{scenario}_radar.png"
    plt.savefig(output_file, dpi=300, bbox_inches="tight")
    print(f"  Saved: {output_file}")
    plt.close()


def plot_heatmap(all_results: dict, output_dir: Path):
    """Create heatmap showing metric performance across strategies and scenarios."""
    import numpy as np
    
    scenarios = sorted(all_results.keys())
    strategies = sorted(set(
        strategy
        for scenario in all_results.values()
        for strategy in scenario.keys()
        if "error" not in scenario[strategy]
    ))
    
    # Use first 4 key metrics
    metrics_to_show = list(METRICS.keys())[:4]
    
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    axes = axes.flatten()
    
    for idx, metric in enumerate(metrics_to_show):
        ax = axes[idx]
        
        # Build matrix
        matrix = []
        for scenario in scenarios:
            row = []
            for strategy in strategies:
                if strategy in all_results[scenario]:
                    result = all_results[scenario][strategy]
                    if "error" not in result and metric in result:
                        try:
                            value = float(result[metric])
                            row.append(value)
                        except (ValueError, TypeError):
                            row.append(0)
                    else:
                        row.append(0)
                else:
                    row.append(0)
            matrix.append(row)
        
        matrix = np.array(matrix)
        
        # Normalize for coloring (0 = best, 1 = worst)
        if METRICS[metric]["lower_is_better"]:
            max_val = matrix.max() if matrix.max() > 0 else 1
            normalized = matrix / max_val
        else:
            max_val = matrix.max() if matrix.max() > 0 else 1
            normalized = 1 - (matrix / max_val)
        
        im = ax.imshow(normalized, cmap="RdYlGn_r", aspect="auto", vmin=0, vmax=1)
        
        # Set ticks
        ax.set_xticks(range(len(strategies)))
        ax.set_xticklabels(strategies, rotation=45, ha="right")
        ax.set_yticks(range(len(scenarios)))
        ax.set_yticklabels(scenarios)
        ax.set_title(METRICS[metric]["label"])
        
        # Add text annotations
        for i in range(len(scenarios)):
            for j in range(len(strategies)):
                value = matrix[i, j]
                if value > 0:
                    text_color = "white" if normalized[i, j] > 0.5 else "black"
                    ax.text(j, i, f"{value:.0f}", ha="center", va="center",
                           color=text_color, fontsize=8)
    
    fig.suptitle("Strategy Performance Heatmap\n(Green = Better, Red = Worse)", 
                 fontsize=14, fontweight="bold")
    plt.tight_layout()
    
    output_file = output_dir / "performance_heatmap.png"
    plt.savefig(output_file, dpi=300, bbox_inches="tight")
    print(f"  Saved: {output_file}")
    plt.close()


def plot_summary_scores(all_results: dict, output_dir: Path):
    """Create summary score chart ranking strategies overall."""
    import numpy as np
    
    # Calculate composite scores for each strategy
    strategies = sorted(set(
        strategy
        for scenario in all_results.values()
        for strategy in scenario.keys()
        if "error" not in scenario[strategy]
    ))
    
    strategy_scores = {s: [] for s in strategies}
    
    for scenario in all_results.values():
        # Normalize and score each metric
        for metric, config in list(METRICS.items())[:4]:  # Top 4 metrics
            values = {}
            for strategy in strategies:
                if strategy in scenario and metric in scenario[strategy]:
                    try:
                        values[strategy] = float(scenario[strategy][metric])
                    except (ValueError, TypeError):
                        continue
            
            if not values:
                continue
            
            max_val = max(values.values()) if values else 1
            if max_val == 0:
                continue
            
            # Score: 1.0 = best, 0.0 = worst
            for strategy in strategies:
                if strategy in values:
                    if config["lower_is_better"]:
                        score = 1 - (values[strategy] / max_val)
                    else:
                        score = values[strategy] / max_val
                    strategy_scores[strategy].append(score)
    
    # Average scores
    avg_scores = {s: np.mean(scores) if scores else 0 
                  for s, scores in strategy_scores.items()}
    
    # Sort by score
    sorted_strategies = sorted(avg_scores.items(), key=lambda x: x[1], reverse=True)
    
    fig, ax = plt.subplots(figsize=(10, 6))
    
    strategies_sorted = [s[0] for s in sorted_strategies]
    scores_sorted = [s[1] for s in sorted_strategies]
    colors = [STRATEGY_COLORS.get(s, "#95a5a6") for s in strategies_sorted]
    
    bars = ax.barh(strategies_sorted, scores_sorted, color=colors)
    ax.set_xlabel("Composite Score (1.0 = Best)")
    ax.set_title("Overall Strategy Ranking\n(Based on Time, Exposure, Downtime, Mixed Version)", 
                 fontsize=14, fontweight="bold")
    ax.set_xlim(0, 1)
    ax.grid(axis="x", alpha=0.3)
    
    # Add value labels
    for i, (strategy, score) in enumerate(sorted_strategies):
        ax.text(score + 0.02, i, f"{score:.3f}", va="center")
    
    plt.tight_layout()
    
    output_file = output_dir / "overall_ranking.png"
    plt.savefig(output_file, dpi=300, bbox_inches="tight")
    print(f"  Saved: {output_file}")
    plt.close()


def main():
    parser = argparse.ArgumentParser(description="Visualize patch planner comparison results")
    parser.add_argument("results_file", help="Path to all_results.json")
    parser.add_argument("--output", default="figures", help="Output directory for figures")
    args = parser.parse_args()
    
    results_file = Path(args.results_file)
    if not results_file.exists():
        print(f"Error: Results file not found: {results_file}")
        sys.exit(1)
    
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"Loading results from: {results_file}")
    all_results = load_results(results_file)
    
    print("\nGenerating visualizations...")
    
    # 1. Bar charts for each metric
    print("\n[1/5] Metric comparison charts...")
    for metric, config in METRICS.items():
        plot_metric_comparison(all_results, metric, config, output_dir)
    
    # 2. Radar charts per scenario
    print("\n[2/5] Radar charts...")
    for scenario in all_results.keys():
        plot_radar_chart(all_results, scenario, output_dir)
    
    # 3. Heatmap
    print("\n[3/5] Performance heatmap...")
    plot_heatmap(all_results, output_dir)
    
    # 4. Overall ranking
    print("\n[4/5] Overall ranking chart...")
    plot_summary_scores(all_results, output_dir)
    
    print(f"\n✓ All visualizations saved to: {output_dir}/")
    print("\nGenerated files:")
    for f in sorted(output_dir.glob("*.png")):
        print(f"  - {f.name}")


if __name__ == "__main__":
    main()
