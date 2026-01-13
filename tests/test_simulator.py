import pytest

from patchplanner.infra_loader import build_graph, load_scenario
from patchplanner.models import HealthState, NodeSpec, NodeType, PatchSpec, ScenarioSpec
from patchplanner.planner import RollingStrategy
from patchplanner.simulator.engine import SimulationEngine


def test_simulation_runs_and_metrics():
    scenario = load_scenario("data/scenario3.yaml")
    graph, edges = build_graph(scenario)
    plan = RollingStrategy(scenario, graph).generate()
    engine = SimulationEngine(scenario, graph, edges)
    with pytest.raises(RuntimeError, match="Availability constraint violated"):
        engine.run(plan, seed=1)


def test_simulation_rolls_back_on_failure():
    scenario = ScenarioSpec(
        name="rollback",
        min_up_default=0,
        nodes=[
            NodeSpec(
                id="node-1",
                type=NodeType.HOST,
                patch=PatchSpec(
                    requires_reboot=True,
                    failure_probability=1.0,
                    rollback_supported=True,
                ),
            )
        ],
        edges=[],
    )
    graph, edges = build_graph(scenario)
    plan = RollingStrategy(scenario, graph).generate()
    engine = SimulationEngine(scenario, graph, edges)
    result = engine.run(plan, seed=1)

    assert result.metrics["rollback_count"] == 1
    assert graph.nodes["node-1"]["version"] == "v_old"


def test_simulation_marks_failed_without_rollback():
    scenario = ScenarioSpec(
        name="failure-no-rollback",
        min_up_default=0,
        nodes=[
            NodeSpec(
                id="node-1",
                type=NodeType.HOST,
                patch=PatchSpec(
                    requires_reboot=True,
                    failure_probability=1.0,
                    rollback_supported=False,
                ),
            )
        ],
        edges=[],
    )
    graph, edges = build_graph(scenario)
    plan = RollingStrategy(scenario, graph).generate()
    engine = SimulationEngine(scenario, graph, edges)
    engine.run(plan, seed=1)

    assert graph.nodes["node-1"]["health"] == HealthState.FAILED
