from __future__ import annotations

from ..models import Plan
from .base import BaseStrategy


class BigBangStrategy(BaseStrategy):
    name = "bigbang"

    def generate(self) -> Plan:
        node_ids = self._node_ids()
        steps = self._make_steps([node_ids], action="patch")
        return Plan(strategy=self.name, steps=steps)
