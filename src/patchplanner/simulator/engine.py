"""Discrete-event simulation engine for patch deployment."""
from __future__ import annotations

import random
from typing import Dict, Iterable, List

import networkx as nx

from ..models import EdgeSpec, HealthState, Plan, PlanStep, ScenarioSpec, SimulationResult
from .constraints import availability_ok, min_up_for_service, service_groups
from .metrics import MetricsState, finalize_metrics, update_interval_metrics


class SimulationEngine:
    """Executes deployment plans with failure injection and constraint checking."""
    def __init__(self, scenario: ScenarioSpec, graph: nx.DiGraph, edges):
        self.scenario = scenario
        self.graph = graph
        self.edges = self._normalize_edges(edges)

    def _normalize_edges(self, edges):
        normalized = []
        for edge in edges:
            if isinstance(edge, EdgeSpec):
                normalized.append(edge)
                continue
            if isinstance(edge, tuple) and len(edge) >= 2:
                src, tgt = edge[0], edge[1]
                compatibility = self.graph.edges[src, tgt].get("compatibility")
                normalized.append(
                    EdgeSpec(source=src, target=tgt, compatibility=compatibility)
                )
                continue
            raise TypeError(f"Unsupported edge type: {type(edge)}")
        return normalized

    def run(self, plan: Plan, seed: int | None = None) -> SimulationResult:
        """Execute plan and return simulation results with metrics."""
        rng = random.Random(seed if seed is not None else self.scenario.seed)
        metrics = MetricsState()
        events: List[Dict[str, object]] = []
        current_downtime: Dict[str, int] = {}

        # Process each step in the plan
        for step in plan.steps:
            if step.action == "pause":
                if step.metadata.get("guardrail"):
                    metrics.number_of_guardrail_pauses += 1
                self._advance_time(metrics, step.pause_seconds)
                events.append(
                    {
                        "time": metrics.time_seconds,
                        "event": "pause",
                        "step_id": step.step_id,
                        "duration": step.pause_seconds,
                    }
                )
                continue

            if step.action in ("bluegreen_build", "bluegreen_switch"):
                self._execute_bluegreen_step(metrics, events, step)
                continue

            if step.action.startswith("patch"):
                self._execute_patch_step(
                    metrics,
                    events,
                    current_downtime,
                    step,
                    rng,
                )
                continue

            raise ValueError(f"Unknown step action: {step.action}")

        metrics_data = finalize_metrics(metrics)
        return SimulationResult(plan=plan, events=events, metrics=metrics_data)

    def _advance_time(self, metrics: MetricsState, duration: int) -> None:
        update_interval_metrics(metrics, self.graph, self.edges, self.scenario, duration)

    def _execute_bluegreen_step(
        self, metrics: MetricsState, events: List[Dict[str, object]], step: PlanStep
    ) -> None:
        duration = 0
        if step.action == "bluegreen_build":
            durations = [
                self.graph.nodes[node_id]["spec"].patch.patch_duration_seconds
                for node_id in step.node_ids
            ]
            duration = max(durations, default=0)
            self._advance_time(metrics, duration)
        elif step.action == "bluegreen_switch":
            for node_id in step.node_ids:
                self.graph.nodes[node_id]["version"] = "v_new"
            duration = 0

        events.append(
            {
                "time": metrics.time_seconds,
                "event": step.action,
                "step_id": step.step_id,
                "node_ids": step.node_ids,
                "duration": duration,
            }
        )

    def _execute_patch_step(
        self,
        metrics: MetricsState,
        events: List[Dict[str, object]],
        current_downtime: Dict[str, int],
        step: PlanStep,
        rng: random.Random,
    ) -> None:
        down_nodes = [
            node_id
            for node_id in step.node_ids
            if self.graph.nodes[node_id]["spec"].patch.requires_restart
            or self.graph.nodes[node_id]["spec"].patch.requires_reboot
        ]
        ok, violations = availability_ok(self.graph, self.scenario, down_nodes)
        if not ok:
            raise RuntimeError(
                f"Availability constraint violated before step {step.step_id}: {violations}"
            )

        for node_id in down_nodes:
            self.graph.nodes[node_id]["health"] = HealthState.DOWN

        duration = max(
            [
                self.graph.nodes[node_id]["spec"].patch.patch_duration_seconds
                for node_id in step.node_ids
            ],
            default=0,
        )
        
        # Track node unavailability: nodes × duration (node-seconds)
        metrics.node_unavailability_seconds += len(down_nodes) * duration
        
        self._apply_downtime(metrics, current_downtime, down_nodes, duration)
        self._advance_time(metrics, duration)

        for node_id in down_nodes:
            self.graph.nodes[node_id]["health"] = HealthState.HEALTHY

        for node_id in step.node_ids:
            if rng.random() < self.graph.nodes[node_id]["spec"].patch.failure_probability:
                if self.graph.nodes[node_id]["spec"].patch.rollback_supported:
                    metrics.rollback_count += 1
                    self.graph.nodes[node_id]["version"] = "v_old"
                    events.append(
                        {
                            "time": metrics.time_seconds,
                            "event": "rollback",
                            "node_id": node_id,
                            "step_id": step.step_id,
                        }
                    )
                else:
                    self.graph.nodes[node_id]["health"] = HealthState.FAILED
                    events.append(
                        {
                            "time": metrics.time_seconds,
                            "event": "patch_failed",
                            "node_id": node_id,
                            "step_id": step.step_id,
                        }
                    )
            else:
                self.graph.nodes[node_id]["version"] = "v_new"
                events.append(
                    {
                        "time": metrics.time_seconds,
                        "event": "patched",
                        "node_id": node_id,
                        "step_id": step.step_id,
                    }
                )

        events.append(
            {
                "time": metrics.time_seconds,
                "event": "patch_step_complete",
                "step_id": step.step_id,
                "node_ids": step.node_ids,
                "duration": duration,
            }
        )

    def _apply_downtime(
        self,
        metrics: MetricsState,
        current_downtime: Dict[str, int],
        down_nodes: Iterable[str],
        duration: int,
    ) -> None:
        if duration <= 0:
            return

        down_set = set(down_nodes)
        for service, node_ids in service_groups(self.graph).items():
            min_up = min_up_for_service(self.graph, self.scenario, service, node_ids)
            healthy = 0
            for node_id in node_ids:
                health = self.graph.nodes[node_id].get("health")
                if node_id in down_set:
                    continue
                if health == HealthState.HEALTHY:
                    healthy += 1
            if healthy < min_up:
                metrics.total_downtime_seconds[service] = (
                    metrics.total_downtime_seconds.get(service, 0) + duration
                )
                current_downtime[service] = current_downtime.get(service, 0) + duration
                metrics.max_continuous_downtime_seconds[service] = max(
                    metrics.max_continuous_downtime_seconds.get(service, 0),
                    current_downtime[service],
                )
            else:
                current_downtime[service] = 0
