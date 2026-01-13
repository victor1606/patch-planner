from __future__ import annotations

from collections import defaultdict
from typing import List

from ..models import Plan, PlanStep
from .base import BaseStrategy


class CanaryStrategy(BaseStrategy):
    """Canary strategy that respects service availability constraints.
    
    Patches one 'canary' node per service first (with a pause for observation),
    then patches remaining nodes in batches that respect min_up constraints.
    """
    name = "canary"

    def generate(self) -> Plan:
        node_ids = self._node_ids()
        
        # Group nodes by service
        by_service = defaultdict(list)
        for node_id in node_ids:
            service = self.graph.nodes[node_id].get("service") or node_id
            by_service[service].append(node_id)
        
        # Calculate how many nodes can be down per service
        max_down_per_service = {}
        for service, nodes in by_service.items():
            min_up = self._get_min_up(nodes)
            max_down_per_service[service] = max(0, len(nodes) - min_up)
        
        # Select canaries - one per service (if service can have at least one down)
        canaries = []
        remaining_by_service = defaultdict(list)
        
        for service, nodes in by_service.items():
            if max_down_per_service[service] > 0:
                # Pick lowest criticality node as canary
                nodes_sorted = sorted(
                    nodes,
                    key=lambda n: (
                        self.graph.nodes[n]["criticality"],
                        self.graph.nodes[n]["spec"].patch.severity,
                        n,
                    )
                )
                canaries.append(nodes_sorted[0])
                remaining_by_service[service] = nodes_sorted[1:]
            else:
                # Can't take any node down - still need to patch somehow
                # This will fail at runtime, but we try anyway
                remaining_by_service[service] = nodes
        
        # Build canary batches respecting min_up (only 1 per service at a time)
        canary_batches = self._build_safe_batches(canaries, max_down_per_service)
        
        # Flatten remaining nodes
        remaining = []
        for nodes in remaining_by_service.values():
            remaining.extend(nodes)
        
        remaining.sort(
            key=lambda n: (
                -self.graph.nodes[n]["criticality"],
                -self.graph.nodes[n]["spec"].patch.severity,
                n,
            )
        )
        
        # Build remaining batches respecting min_up
        remaining_batches = self._build_safe_batches(remaining, max_down_per_service)
        
        # Build steps
        steps: List[PlanStep] = []
        
        # Add canary steps
        for batch in canary_batches:
            steps.extend(self._make_steps([batch], action="patch_canary"))
        
        # Add pause after canaries
        if canary_batches:
            steps.append(
                PlanStep(
                    step_id="pause-canary",
                    action="pause",
                    pause_seconds=60,
                    strategy=self.name,
                )
            )
        
        # Add remaining steps
        for batch in remaining_batches:
            steps.extend(self._make_steps([batch], action="patch"))
        
        return Plan(strategy=self.name, steps=steps)
    
    def _build_safe_batches(self, nodes: List[str], max_down: dict) -> List[List[str]]:
        """Build batches that respect per-service max_down limits."""
        batches = []
        remaining = list(nodes)
        
        while remaining:
            batch = []
            service_down_count = defaultdict(int)
            
            for node_id in list(remaining):
                service = self.graph.nodes[node_id].get("service") or node_id
                if service_down_count[service] < max_down.get(service, 1):
                    batch.append(node_id)
                    service_down_count[service] += 1
                    remaining.remove(node_id)
            
            if batch:
                batches.append(sorted(batch))
            else:
                # Safety: if we can't make progress, patch one at a time
                if remaining:
                    batches.append([remaining.pop(0)])
        
        return batches
    
    def _get_min_up(self, node_ids: List[str]) -> int:
        """Get the min_up requirement for a group of nodes."""
        min_ups = []
        for node_id in node_ids:
            node_min = self.graph.nodes[node_id].get("min_up")
            if node_min is None:
                node_min = self.scenario.min_up_default
            min_ups.append(node_min)
        return max(min_ups) if min_ups else self.scenario.min_up_default
