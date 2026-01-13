from __future__ import annotations

from typing import List

from ..models import Plan
from .base import BaseStrategy


class BatchRollingStrategy(BaseStrategy):
    name = "batch_rolling"

    def __init__(self, scenario, graph, batch_size: int = 2):
        super().__init__(scenario, graph)
        self.batch_size = max(1, batch_size)

    def generate(self) -> Plan:
        node_ids = self._node_ids()
        node_ids.sort(
            key=lambda n: (
                -self.graph.nodes[n]["criticality"],
                -self.graph.nodes[n]["spec"].patch.severity,
                n,
            )
        )
        groups = self._group_by_incompatibility(node_ids)
        ordered_groups: List[List[str]] = []
        for _, group_nodes in sorted(groups.items(), key=lambda item: str(item[0])):
            group_nodes.sort()
            ordered_groups.append(group_nodes)

        batches: List[List[str]] = []
        current: List[str] = []
        for group_nodes in ordered_groups:
            if len(current) + len(group_nodes) > self.batch_size and current:
                batches.append(current)
                current = []
            current.extend(group_nodes)
        if current:
            batches.append(current)

        steps = self._make_steps(batches, action="patch")
        return Plan(strategy=self.name, steps=steps)
