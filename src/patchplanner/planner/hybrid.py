"""Hybrid strategy that adapts between blue-green and rolling based on constraints."""
from __future__ import annotations

from typing import Dict, List, Tuple

from ..models import Plan, PlanStep
from .base import BaseStrategy


class HybridRiskAwareStrategy(BaseStrategy):
    """Risk-aware adaptive strategy: patches high-risk nodes first, chooses optimal sub-strategy per group."""
    name = "hybrid"

    def generate(self) -> Plan:
        node_ids = self._node_ids()
        risk_scores = self._risk_scores(node_ids)
        groups = self._group_by_incompatibility(node_ids)
        # Order groups by highest risk first
        ordered_groups = sorted(
            groups.values(),
            key=lambda nodes: (-max(risk_scores[n] for n in nodes), sorted(nodes)[0]),
        )

        steps: List[PlanStep] = []
        cooldown = 30
        for idx, group_nodes in enumerate(ordered_groups, start=1):
            # Choose blue-green if possible (zero downtime), otherwise rolling
            if self._use_bluegreen(group_nodes):
                steps.append(
                    PlanStep(
                        step_id=f"group-{idx}-bluegreen-build",
                        action="bluegreen_build",
                        node_ids=group_nodes,
                        strategy=self.name,
                    )
                )
                steps.append(
                    PlanStep(
                        step_id=f"group-{idx}-bluegreen-switch",
                        action="bluegreen_switch",
                        node_ids=group_nodes,
                        strategy=self.name,
                    )
                )
            else:
                steps.append(
                    PlanStep(
                        step_id=f"group-{idx}-rolling",
                        action="patch",
                        node_ids=group_nodes,
                        strategy=self.name,
                    )
                )
            steps.append(
                PlanStep(
                    step_id=f"group-{idx}-cooldown",
                    action="pause",
                    pause_seconds=cooldown,
                    strategy=self.name,
                    metadata={"guardrail": "cooldown"},
                )
            )

        return Plan(strategy=self.name, steps=steps)

    def _risk_scores(self, node_ids: List[str]) -> Dict[str, float]:
        scores: Dict[str, float] = {}
        for node_id in node_ids:
            data = self.graph.nodes[node_id]
            severity = data["spec"].patch.severity
            criticality = data["criticality"]
            exposure = 1.0 + self.graph.in_degree(node_id) + self.graph.out_degree(node_id)
            scores[node_id] = severity * criticality * exposure
        return scores

    def _use_bluegreen(self, group_nodes: List[str]) -> bool:
        min_up = self._min_up_for_group(group_nodes)
        return min_up >= len(group_nodes)

    def _min_up_for_group(self, group_nodes: List[str]) -> int:
        if not group_nodes:
            return 0
        min_ups = []
        for node_id in group_nodes:
            node_min = self.graph.nodes[node_id].get("min_up")
            node_min = node_min if node_min is not None else self.scenario.min_up_default
            min_ups.append(node_min)
        return max(min_ups)
