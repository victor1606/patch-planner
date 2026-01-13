"""Constraint checking for availability and compatibility."""
from __future__ import annotations

from collections import defaultdict
from typing import Dict, Iterable, List, Tuple

import networkx as nx

from ..models import CompatibilityLevel, EdgeSpec, HealthState, ScenarioSpec


def service_groups(graph: nx.DiGraph) -> Dict[str, List[str]]:
    """Group nodes by service name for availability checking."""
    groups: Dict[str, List[str]] = defaultdict(list)
    for node_id, data in graph.nodes(data=True):
        service = data.get("service") or node_id
        groups[service].append(node_id)
    return groups


def min_up_for_service(
    graph: nx.DiGraph, scenario: ScenarioSpec, service: str, node_ids: Iterable[str]
) -> int:
    min_values = []
    for node_id in node_ids:
        node_min = graph.nodes[node_id].get("min_up")
        if node_min is None:
            node_min = scenario.min_up_default
        min_values.append(node_min)
    return max(min_values) if min_values else scenario.min_up_default


def availability_ok(
    graph: nx.DiGraph, scenario: ScenarioSpec, down_nodes: Iterable[str]
) -> Tuple[bool, List[str]]:
    """Check if taking down these nodes would violate min_up constraints."""
    down_set = set(down_nodes)
    violations: List[str] = []
    for service, node_ids in service_groups(graph).items():
        min_up = min_up_for_service(graph, scenario, service, node_ids)
        healthy = 0
        for node_id in node_ids:
            health = graph.nodes[node_id].get("health")
            if node_id in down_set:
                continue
            if health == HealthState.HEALTHY:
                healthy += 1
        if healthy < min_up:
            violations.append(
                f"service={service} healthy={healthy} min_up={min_up}"
            )
    return (len(violations) == 0, violations)


def incompatible_mixed_version_edges(
    graph: nx.DiGraph, edges: Iterable[EdgeSpec]
) -> List[Tuple[str, str]]:
    violations: List[Tuple[str, str]] = []
    for edge in edges:
        if edge.compatibility != CompatibilityLevel.INCOMPATIBLE:
            continue
        src_version = graph.nodes[edge.source].get("version")
        tgt_version = graph.nodes[edge.target].get("version")
        if src_version != tgt_version:
            violations.append((edge.source, edge.target))
    return violations
