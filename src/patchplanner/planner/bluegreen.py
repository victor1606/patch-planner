from __future__ import annotations

from ..models import Plan, PlanStep
from .base import BaseStrategy


class BlueGreenStrategy(BaseStrategy):
    name = "bluegreen"

    def generate(self) -> Plan:
        node_ids = self._node_ids()
        steps = [
            PlanStep(
                step_id="bluegreen-build",
                action="bluegreen_build",
                node_ids=node_ids,
                strategy=self.name,
                metadata={"extra_capacity": True},
            ),
            PlanStep(
                step_id="bluegreen-switch",
                action="bluegreen_switch",
                node_ids=node_ids,
                strategy=self.name,
            ),
        ]
        return Plan(strategy=self.name, steps=steps)
