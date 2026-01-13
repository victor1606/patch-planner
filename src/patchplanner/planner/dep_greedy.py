from __future__ import annotations

from typing import Dict, List, Set

import networkx as nx

from ..models import Plan
from .base import BaseStrategy


class DependencyAwareGreedyStrategy(BaseStrategy):
    name = "dep_greedy"

    def generate(self) -> Plan:
        node_ids = self._node_ids()
        groups = self._group_by_incompatibility(node_ids)
        group_ids = list(groups.keys())
        group_lookup = {
            node_id: group_id for group_id, nodes in groups.items() for node_id in nodes
        }
        group_risk = self._group_risk(groups)

        dep_graph = nx.DiGraph()
        dep_graph.add_nodes_from(group_ids)
        for edge in self.scenario.edges:
            src_group = group_lookup.get(edge.source)
            tgt_group = group_lookup.get(edge.target)
            if src_group is None or tgt_group is None:
                continue
            if src_group == tgt_group:
                continue
            dep_graph.add_edge(tgt_group, src_group)

        steps = []
        remaining: Set[object] = set(group_ids)
        while remaining:
            ready = [
                group_id
                for group_id in remaining
                if dep_graph.in_degree(group_id) == 0
            ]
            if not ready:
                raise RuntimeError(
                    "Dependency cycle detected; cannot build dependency-aware plan."
                )
            ready.sort(
                key=lambda gid: (-group_risk.get(gid, 0.0), str(gid))
            )
            chosen = ready[0]
            batch = sorted(groups[chosen])
            steps.extend(self._make_steps([batch], action="patch"))
            dep_graph.remove_node(chosen)
            remaining.remove(chosen)

        return Plan(strategy=self.name, steps=steps)

    def _group_risk(self, groups: Dict[object, List[str]]) -> Dict[object, float]:
        risk_scores = self._risk_scores(
            [node_id for nodes in groups.values() for node_id in nodes]
        )
        group_risk = {}
        for group_id, nodes in groups.items():
            group_risk[group_id] = max(risk_scores[node] for node in nodes)
        return group_risk

    def _risk_scores(self, node_ids: List[str]) -> Dict[str, float]:
        scores: Dict[str, float] = {}
        for node_id in node_ids:
            data = self.graph.nodes[node_id]
            severity = data["spec"].patch.severity
            criticality = data["criticality"]
            exposure = 1.0 + self.graph.in_degree(node_id) + self.graph.out_degree(node_id)
            scores[node_id] = severity * criticality * exposure
        return scores
