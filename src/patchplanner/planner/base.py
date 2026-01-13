from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Dict, Iterable, List

import networkx as nx

from ..infra_loader import incompatible_components
from ..models import Plan, PlanStep, ScenarioSpec


class BaseStrategy(ABC):
    name = "base"

    def __init__(self, scenario: ScenarioSpec, graph: nx.DiGraph):
        self.scenario = scenario
        self.graph = graph
        self._incompat_groups = incompatible_components(graph, scenario.edges)

    @abstractmethod
    def generate(self) -> Plan:
        raise NotImplementedError

    def _node_ids(self) -> List[str]:
        return [n for n, data in self.graph.nodes(data=True) if data["patchable"]]

    def _group_by_incompatibility(self, node_ids: Iterable[str]) -> Dict[str | int, List[str]]:
        groups: Dict[str | int, List[str]] = {}
        for node_id in node_ids:
            group_id = self._incompat_groups.get(node_id, node_id)
            groups.setdefault(group_id, []).append(node_id)
        return groups

    def _make_steps(self, batches: List[List[str]], action: str) -> List[PlanStep]:
        steps = []
        for idx, batch in enumerate(batches, start=1):
            steps.append(
                PlanStep(
                    step_id=f"{action}-{idx}",
                    action=action,
                    node_ids=batch,
                    strategy=self.name,
                )
            )
        return steps
