from __future__ import annotations

import argparse

from .infra_loader import build_graph, load_scenario
from .planner import (
    BatchRollingStrategy,
    BigBangStrategy,
    BlueGreenStrategy,
    CanaryStrategy,
    DependencyAwareGreedyStrategy,
    HybridRiskAwareStrategy,
    RollingStrategy,
)
from .simulator.engine import SimulationEngine
from .simulator.reporter import write_report


STRATEGIES = {
    "bigbang": BigBangStrategy,
    "rolling": RollingStrategy,
    "batch_rolling": BatchRollingStrategy,
    "canary": CanaryStrategy,
    "bluegreen": BlueGreenStrategy,
    "dep_greedy": DependencyAwareGreedyStrategy,
    "hybrid": HybridRiskAwareStrategy,
}


def main() -> None:
    parser = argparse.ArgumentParser(description="Patch planner simulator")
    parser.add_argument("--scenario", required=True, help="Path to scenario YAML")
    parser.add_argument(
        "--strategy",
        required=True,
        choices=sorted(STRATEGIES.keys()),
    )
    parser.add_argument("--out", required=True, help="Output directory")
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--batch-size", type=int, default=2)
    args = parser.parse_args()

    scenario = load_scenario(args.scenario)
    graph, edges = build_graph(scenario)

    strategy_cls = STRATEGIES[args.strategy]
    if args.strategy == "batch_rolling":
        strategy = strategy_cls(scenario, graph, batch_size=args.batch_size)
    else:
        strategy = strategy_cls(scenario, graph)

    plan = strategy.generate()
    engine = SimulationEngine(scenario, graph, edges)
    result = engine.run(plan, seed=args.seed)
    write_report(args.out, result.plan, result.events, result.metrics)


if __name__ == "__main__":
    main()
