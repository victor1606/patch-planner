"""Infrastructure loading utilities: YAML parsing and graph construction."""
from __future__ import annotations

from pathlib import Path
from typing import Dict, Iterable, List

import networkx as nx
import yaml

from .models import (
    CompatibilityLevel,
    EdgeSpec,
    NodeSpec,
    ScenarioSpec,
)


def load_scenario(path: str | Path) -> ScenarioSpec:
    """Load scenario from YAML file and parse into structured objects."""
    raw = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    if raw is None:
        raise ValueError(f"Empty scenario file: {path}")

    # Support optional global patches section
    patches = raw.get("patches", {})
    nodes = []
    for node_data in raw.get("nodes", []):
        node_id = node_data.get("id")
        patch_data = patches.get(node_id)
        if patch_data and "patch" not in node_data:
            node_data = dict(node_data)
            node_data["patch"] = patch_data
        nodes.append(NodeSpec(**node_data))

    edges = [EdgeSpec(**edge) for edge in raw.get("edges", [])]

    return ScenarioSpec(
        name=raw.get("name", Path(path).stem),
        seed=raw.get("seed", 0),
        incompatible_max_duration_seconds=raw.get(
            "incompatible_max_duration_seconds", 0
        ),
        min_up_default=raw.get("min_up_default", 1),
        nodes=nodes,
        edges=edges,
        metadata=raw.get("metadata", {}),
    )


def build_graph(
    scenario: ScenarioSpec,
) -> tuple[nx.DiGraph, List[EdgeSpec]]:
    graph = nx.DiGraph()
    for node in scenario.nodes:
        graph.add_node(
            node.id,
            spec=node,
            type=node.type,
            service=node.service,
            criticality=node.criticality,
            redundancy=node.redundancy,
            min_up=node.min_up,
            patchable=node.patchable,
            group=node.group,
            version=node.version,
            health=node.health,
        )

    for edge in scenario.edges:
        graph.add_edge(edge.source, edge.target, compatibility=edge.compatibility)

    return graph, list(scenario.edges)


def incompatible_components(
    graph: nx.DiGraph, edges: Iterable[EdgeSpec]
) -> Dict[str, int]:
    undirected = nx.Graph()
    undirected.add_nodes_from(graph.nodes)
    for edge in edges:
        if edge.compatibility == CompatibilityLevel.INCOMPATIBLE:
            undirected.add_edge(edge.source, edge.target)
    components = {}
    for idx, comp in enumerate(nx.connected_components(undirected)):
        for node_id in comp:
            components[node_id] = idx
    return components
