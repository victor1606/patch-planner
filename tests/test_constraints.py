"""Tests for constraint checking and availability logic."""
import pytest

from patchplanner.infra_loader import build_graph
from patchplanner.models import (
    CompatibilityLevel,
    EdgeSpec,
    HealthState,
    NodeSpec,
    NodeType,
    PatchSpec,
    ScenarioSpec,
)
from patchplanner.simulator.constraints import (
    availability_ok,
    incompatible_mixed_version_edges,
    min_up_for_service,
    service_groups,
)


def test_service_groups_clusters_by_service():
    """Verify nodes are grouped by service name."""
    scenario = ScenarioSpec(
        name="grouping",
        nodes=[
            NodeSpec(id="api-1", type=NodeType.SERVICE_INSTANCE, service="api"),
            NodeSpec(id="api-2", type=NodeType.SERVICE_INSTANCE, service="api"),
            NodeSpec(id="db-1", type=NodeType.DATABASE, service="db"),
        ],
        edges=[],
    )
    graph, _ = build_graph(scenario)
    groups = service_groups(graph)

    assert set(groups["api"]) == {"api-1", "api-2"}
    assert set(groups["db"]) == {"db-1"}


def test_min_up_uses_node_specific_value():
    """Verify min_up_for_service uses node-specific min_up when available."""
    scenario = ScenarioSpec(
        name="min_up",
        min_up_default=1,
        nodes=[
            NodeSpec(
                id="api-1",
                type=NodeType.SERVICE_INSTANCE,
                service="api",
                min_up=3,
            ),
            NodeSpec(
                id="api-2",
                type=NodeType.SERVICE_INSTANCE,
                service="api",
                min_up=2,
            ),
        ],
        edges=[],
    )
    graph, _ = build_graph(scenario)

    min_up = min_up_for_service(graph, scenario, "api", ["api-1", "api-2"])
    # Should take maximum of node-specific values
    assert min_up == 3


def test_min_up_uses_default_when_not_specified():
    """Verify min_up_for_service falls back to scenario default."""
    scenario = ScenarioSpec(
        name="min_up_default",
        min_up_default=2,
        nodes=[
            NodeSpec(id="api-1", type=NodeType.SERVICE_INSTANCE, service="api"),
        ],
        edges=[],
    )
    graph, _ = build_graph(scenario)

    min_up = min_up_for_service(graph, scenario, "api", ["api-1"])
    assert min_up == 2


def test_availability_ok_with_sufficient_healthy_nodes():
    """Verify availability check passes when min_up is satisfied."""
    scenario = ScenarioSpec(
        name="sufficient",
        min_up_default=2,
        nodes=[
            NodeSpec(
                id="api-1",
                type=NodeType.SERVICE_INSTANCE,
                service="api",
                min_up=2,
            ),
            NodeSpec(
                id="api-2",
                type=NodeType.SERVICE_INSTANCE,
                service="api",
                min_up=2,
            ),
            NodeSpec(
                id="api-3",
                type=NodeType.SERVICE_INSTANCE,
                service="api",
                min_up=2,
            ),
        ],
        edges=[],
    )
    graph, _ = build_graph(scenario)

    # Taking down one node should be OK (2 remain healthy)
    ok, violations = availability_ok(graph, scenario, ["api-1"])
    assert ok is True
    assert len(violations) == 0


def test_availability_fails_with_insufficient_healthy_nodes():
    """Verify availability check fails when min_up would be violated."""
    scenario = ScenarioSpec(
        name="insufficient",
        min_up_default=2,
        nodes=[
            NodeSpec(
                id="api-1",
                type=NodeType.SERVICE_INSTANCE,
                service="api",
                min_up=2,
            ),
            NodeSpec(
                id="api-2",
                type=NodeType.SERVICE_INSTANCE,
                service="api",
                min_up=2,
            ),
        ],
        edges=[],
    )
    graph, _ = build_graph(scenario)

    # Taking down both should fail
    ok, violations = availability_ok(graph, scenario, ["api-1", "api-2"])
    assert ok is False
    assert len(violations) == 1
    assert "service=api" in violations[0]


def test_availability_ignores_already_failed_nodes():
    """Verify availability check accounts for nodes that are already down."""
    scenario = ScenarioSpec(
        name="already_down",
        min_up_default=1,
        nodes=[
            NodeSpec(
                id="api-1",
                type=NodeType.SERVICE_INSTANCE,
                service="api",
                min_up=1,
            ),
            NodeSpec(
                id="api-2",
                type=NodeType.SERVICE_INSTANCE,
                service="api",
                min_up=1,
            ),
        ],
        edges=[],
    )
    graph, _ = build_graph(scenario)
    # Mark one node as already failed
    graph.nodes["api-1"]["health"] = HealthState.FAILED

    # Taking down the second should fail (none remain healthy)
    ok, violations = availability_ok(graph, scenario, ["api-2"])
    assert ok is False


def test_incompatible_mixed_version_edges_detects_violations():
    """Verify detection of incompatible edges with mixed versions."""
    scenario = ScenarioSpec(
        name="incompatible",
        nodes=[
            NodeSpec(id="edge", type=NodeType.SERVICE_INSTANCE),
            NodeSpec(id="control", type=NodeType.SERVICE_INSTANCE),
        ],
        edges=[
            EdgeSpec(
                source="edge",
                target="control",
                compatibility=CompatibilityLevel.INCOMPATIBLE,
            )
        ],
    )
    graph, edges = build_graph(scenario)
    # Set different versions
    graph.nodes["edge"]["version"] = "v_new"
    graph.nodes["control"]["version"] = "v_old"

    violations = incompatible_mixed_version_edges(graph, edges)
    assert len(violations) == 1
    assert violations[0] == ("edge", "control")


def test_incompatible_mixed_version_edges_allows_same_version():
    """Verify no violation when incompatible nodes have same version."""
    scenario = ScenarioSpec(
        name="same_version",
        nodes=[
            NodeSpec(id="edge", type=NodeType.SERVICE_INSTANCE),
            NodeSpec(id="control", type=NodeType.SERVICE_INSTANCE),
        ],
        edges=[
            EdgeSpec(
                source="edge",
                target="control",
                compatibility=CompatibilityLevel.INCOMPATIBLE,
            )
        ],
    )
    graph, edges = build_graph(scenario)
    # Set same version
    graph.nodes["edge"]["version"] = "v_new"
    graph.nodes["control"]["version"] = "v_new"

    violations = incompatible_mixed_version_edges(graph, edges)
    assert len(violations) == 0


def test_incompatible_ignores_compatible_edges():
    """Verify COMPATIBLE edges don't trigger violations."""
    scenario = ScenarioSpec(
        name="compatible",
        nodes=[
            NodeSpec(id="api", type=NodeType.SERVICE_INSTANCE),
            NodeSpec(id="db", type=NodeType.DATABASE),
        ],
        edges=[
            EdgeSpec(
                source="api",
                target="db",
                compatibility=CompatibilityLevel.COMPATIBLE,
            )
        ],
    )
    graph, edges = build_graph(scenario)
    # Set different versions
    graph.nodes["api"]["version"] = "v_new"
    graph.nodes["db"]["version"] = "v_old"

    violations = incompatible_mixed_version_edges(graph, edges)
    assert len(violations) == 0
