from __future__ import annotations

from typing import List

from ..models import Plan
from .base import BaseStrategy


class RollingStrategy(BaseStrategy):
    name = "rolling"

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
        batches: List[List[str]] = []
        for _, group_nodes in sorted(groups.items(), key=lambda item: str(item[0])):
            group_nodes.sort()
            if len(group_nodes) > 1:
                batches.append(group_nodes)
            else:
                batches.append([group_nodes[0]])
        steps = self._make_steps(batches, action="patch")
        return Plan(strategy=self.name, steps=steps)
