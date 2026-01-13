"""Metrics collection for simulation results."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Iterable, Tuple

import networkx as nx

from ..models import CompatibilityLevel, EdgeSpec, ScenarioSpec


@dataclass
class MetricsState:
    """State tracking for all simulation metrics during execution."""
    time_seconds: int = 0
    total_downtime_seconds: Dict[str, int] = field(default_factory=dict)
    max_continuous_downtime_seconds: Dict[str, int] = field(default_factory=dict)
    exposure_window_weighted: float = 0.0
    mixed_version_time_seconds: int = 0
    number_of_degraded_intervals: int = 0
    number_of_incompatibility_violations: int = 0
    rollback_count: int = 0
    plan_abort_count: int = 0
    number_of_guardrail_pauses: int = 0
    # Node unavailability: total time × nodes being patched (node-seconds)
    node_unavailability_seconds: int = 0
    _edge_mixed_time: Dict[Tuple[str, str], int] = field(default_factory=dict)
    _edge_violation_seen: Dict[Tuple[str, str], bool] = field(default_factory=dict)


def update_interval_metrics(
    metrics: MetricsState,
    graph: nx.DiGraph,
    edges: Iterable[EdgeSpec],
    scenario: ScenarioSpec,
    duration: int,
) -> None:
    if duration <= 0:
        return

    metrics.time_seconds += duration
    _update_exposure(metrics, graph, duration)
    _update_mixed_versions(metrics, graph, edges, scenario, duration)


def _update_exposure(metrics: MetricsState, graph: nx.DiGraph, duration: int) -> None:
    """Calculate exposure window: sum of (criticality × severity × time) for unpatched nodes."""
    exposure = 0.0
    for node_id, data in graph.nodes(data=True):
        if data.get("version") != "v_new":
            criticality = data.get("criticality", 1)
            severity = data["spec"].patch.severity
            exposure += criticality * severity
    metrics.exposure_window_weighted += exposure * duration


def _update_mixed_versions(
    metrics: MetricsState,
    graph: nx.DiGraph,
    edges: Iterable[EdgeSpec],
    scenario: ScenarioSpec,
    duration: int,
) -> None:
    degraded_seen = False
    for edge in edges:
        src_version = graph.nodes[edge.source].get("version")
        tgt_version = graph.nodes[edge.target].get("version")
        if src_version == tgt_version:
            continue

        if edge.compatibility in (
            CompatibilityLevel.DEGRADED,
            CompatibilityLevel.INCOMPATIBLE,
        ):
            metrics.mixed_version_time_seconds += duration

        if edge.compatibility == CompatibilityLevel.DEGRADED:
            degraded_seen = True

        if edge.compatibility == CompatibilityLevel.INCOMPATIBLE:
            key = (edge.source, edge.target)
            metrics._edge_mixed_time[key] = metrics._edge_mixed_time.get(key, 0) + duration
            max_allowed = (
                edge.mixed_max_duration_seconds
                if edge.mixed_max_duration_seconds is not None
                else scenario.incompatible_max_duration_seconds
            )
            if metrics._edge_mixed_time[key] > max_allowed and not metrics._edge_violation_seen.get(
                key
            ):
                metrics.number_of_incompatibility_violations += 1
                metrics._edge_violation_seen[key] = True

    if degraded_seen:
        metrics.number_of_degraded_intervals += 1


def finalize_metrics(metrics: MetricsState) -> Dict[str, float | int | Dict[str, int]]:
    total_downtime_overall = sum(metrics.total_downtime_seconds.values())
    max_continuous_overall = (
        max(metrics.max_continuous_downtime_seconds.values(), default=0)
    )
    return {
        "time_to_full_patch": metrics.time_seconds,
        "exposure_window_weighted": metrics.exposure_window_weighted,
        "mixed_version_time_seconds": metrics.mixed_version_time_seconds,
        "number_of_degraded_intervals": metrics.number_of_degraded_intervals,
        "number_of_incompatibility_violations": metrics.number_of_incompatibility_violations,
        "rollback_count": metrics.rollback_count,
        "plan_abort_count": metrics.plan_abort_count,
        "number_of_guardrail_pauses": metrics.number_of_guardrail_pauses,
        "node_unavailability_seconds": metrics.node_unavailability_seconds,
        "total_downtime_seconds": metrics.total_downtime_seconds,
        "total_downtime_seconds_overall": total_downtime_overall,
        "max_continuous_downtime_seconds": metrics.max_continuous_downtime_seconds,
        "max_continuous_downtime_seconds_overall": max_continuous_overall,
    }
