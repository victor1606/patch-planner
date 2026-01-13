from patchplanner.infra_loader import build_graph
from patchplanner.models import (
    CompatibilityLevel,
    EdgeSpec,
    NodeSpec,
    NodeType,
    PatchSpec,
    ScenarioSpec,
)
from patchplanner.planner import DependencyAwareGreedyStrategy


def test_dep_greedy_respects_dependency_order():
    scenario = ScenarioSpec(
        name="dep-order",
        min_up_default=0,
        nodes=[
            NodeSpec(
                id="db",
                type=NodeType.DATABASE,
                service="db",
                criticality=1,
                patch=PatchSpec(severity=1.0),
            ),
            NodeSpec(
                id="api",
                type=NodeType.SERVICE_INSTANCE,
                service="api",
                criticality=1,
                patch=PatchSpec(severity=1.0),
            ),
            NodeSpec(
                id="web",
                type=NodeType.SERVICE_INSTANCE,
                service="web",
                criticality=5,
                patch=PatchSpec(severity=10.0),
            ),
        ],
        edges=[
            EdgeSpec(
                source="web",
                target="api",
                compatibility=CompatibilityLevel.COMPATIBLE,
            ),
            EdgeSpec(
                source="api",
                target="db",
                compatibility=CompatibilityLevel.COMPATIBLE,
            ),
        ],
    )
    graph, edges = build_graph(scenario)
    plan = DependencyAwareGreedyStrategy(scenario, graph).generate()

    order = [step.node_ids[0] for step in plan.steps]
    assert order == ["db", "api", "web"]


def test_dep_greedy_groups_incompatible_nodes():
    scenario = ScenarioSpec(
        name="dep-incompat",
        min_up_default=0,
        nodes=[
            NodeSpec(
                id="a",
                type=NodeType.SERVICE_INSTANCE,
                service="svc",
                patch=PatchSpec(),
            ),
            NodeSpec(
                id="b",
                type=NodeType.SERVICE_INSTANCE,
                service="svc",
                patch=PatchSpec(),
            ),
        ],
        edges=[
            EdgeSpec(
                source="a",
                target="b",
                compatibility=CompatibilityLevel.INCOMPATIBLE,
            )
        ],
    )
    graph, _ = build_graph(scenario)
    plan = DependencyAwareGreedyStrategy(scenario, graph).generate()

    assert len(plan.steps) == 1
    assert set(plan.steps[0].node_ids) == {"a", "b"}
