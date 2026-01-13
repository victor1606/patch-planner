from __future__ import annotations

from collections import defaultdict
from typing import List

from ..models import Plan
from .base import BaseStrategy


class BatchRollingStrategy(BaseStrategy):
    """Batch rolling strategy that respects service availability constraints."""
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
        
        # Group nodes by service to respect min_up
        by_service = defaultdict(list)
        for node_id in node_ids:
            service = self.graph.nodes[node_id].get("service") or node_id
            by_service[service].append(node_id)
        
        # Calculate how many nodes can be down per service
        max_down_per_service = {}
        for service, nodes in by_service.items():
            min_up = self._get_min_up(nodes)
            max_down_per_service[service] = max(0, len(nodes) - min_up)
        
        # Build batches respecting constraints
        batches: List[List[str]] = []
        remaining = set(node_ids)
        
        while remaining:
            batch = []
            service_down_count = defaultdict(int)
            
            for node_id in list(remaining):
                service = self.graph.nodes[node_id].get("service") or node_id
                # Check if we can add this node to batch
                if service_down_count[service] < max_down_per_service.get(service, 1):
                    if len(batch) < self.batch_size:
                        batch.append(node_id)
                        service_down_count[service] += 1
                        remaining.remove(node_id)
            
            if batch:
                batches.append(sorted(batch))
            else:
                # Safety: if we can't make progress, patch one at a time
                node = remaining.pop()
                batches.append([node])
        
        steps = self._make_steps(batches, action="patch")
        return Plan(strategy=self.name, steps=steps)
    
    def _get_min_up(self, node_ids: List[str]) -> int:
        """Get the min_up requirement for a group of nodes."""
        min_ups = []
        for node_id in node_ids:
            node_min = self.graph.nodes[node_id].get("min_up")
            if node_min is None:
                node_min = self.scenario.min_up_default
            min_ups.append(node_min)
        return max(min_ups) if min_ups else self.scenario.min_up_default
