from __future__ import annotations

from collections import defaultdict
from typing import List

from ..models import Plan, PlanStep
from .base import BaseStrategy


class CanaryStrategy(BaseStrategy):
    name = "canary"

    def generate(self) -> Plan:
        node_ids = self._node_ids()
        incompat_groups = self._group_by_incompatibility(node_ids)
        group_lookup = {
            node_id: group_id for group_id, nodes in incompat_groups.items() for node_id in nodes
        }

        by_service = defaultdict(list)
        for node_id in node_ids:
            service = self.graph.nodes[node_id].get("service") or node_id
            by_service[service].append(node_id)

        canary_nodes: List[str] = []
        remaining: List[str] = []
        used_groups = set()
        for service, ids in sorted(by_service.items()):
            ids.sort()
            for node_id in ids:
                group_id = group_lookup.get(node_id, -1)
                if group_id in used_groups:
                    continue
                group_nodes = incompat_groups.get(group_id, [node_id])
                if group_nodes and len(group_nodes) > 1:
                    canary_nodes.extend(group_nodes)
                    used_groups.add(group_id)
                    remaining.extend([n for n in ids if n not in group_nodes])
                else:
                    canary_nodes.append(node_id)
                    used_groups.add(group_id)
                    remaining.extend([n for n in ids if n != node_id])
                break

        steps: List[PlanStep] = []
        if canary_nodes:
            steps.extend(self._make_steps([canary_nodes], action="patch_canary"))
            steps.append(
                PlanStep(
                    step_id="pause-canary",
                    action="pause",
                    pause_seconds=60,
                    strategy=self.name,
                )
            )
        if remaining:
            steps.extend(self._make_steps([sorted(set(remaining))], action="patch"))

        return Plan(strategy=self.name, steps=steps)
