from patchplanner.infra_loader import build_graph, load_scenario
from patchplanner.planner import RollingStrategy


def test_rolling_groups_incompatible_nodes():
    scenario = load_scenario("data/scenario2.yaml")
    graph, _ = build_graph(scenario)
    plan = RollingStrategy(scenario, graph).generate()

    first_step_nodes = set(plan.steps[0].node_ids)
    assert {"edge-a", "control-1"}.issubset(first_step_nodes) or {
        "edge-b",
        "control-2",
    }.issubset(first_step_nodes)
