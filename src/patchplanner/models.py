from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


class NodeType(str, Enum):
    HOST = "HOST"
    SERVICE_INSTANCE = "SERVICE_INSTANCE"
    DATABASE = "DATABASE"


class HealthState(str, Enum):
    HEALTHY = "HEALTHY"
    DOWN = "DOWN"
    FAILED = "FAILED"


class CompatibilityLevel(str, Enum):
    COMPATIBLE = "COMPATIBLE"
    DEGRADED = "DEGRADED"
    INCOMPATIBLE = "INCOMPATIBLE"


class PatchSpec(BaseModel):
    patch_duration_seconds: int = 0
    requires_restart: bool = False
    requires_reboot: bool = False
    failure_probability: float = 0.0
    rollback_supported: bool = True
    severity: float = 0.0

    @field_validator("patch_duration_seconds")
    @classmethod
    def _duration_non_negative(cls, v: int) -> int:
        if v < 0:
            raise ValueError("patch_duration_seconds must be >= 0")
        return v

    @field_validator("failure_probability")
    @classmethod
    def _failure_probability_range(cls, v: float) -> float:
        if not (0.0 <= v <= 1.0):
            raise ValueError("failure_probability must be in [0, 1]")
        return v

    @field_validator("severity")
    @classmethod
    def _severity_range(cls, v: float) -> float:
        if not (0.0 <= v <= 10.0):
            raise ValueError("severity must be in [0, 10]")
        return v


class NodeSpec(BaseModel):
    id: str
    type: NodeType
    service: Optional[str] = None
    criticality: int = 1
    redundancy: int = 1
    min_up: Optional[int] = None
    patchable: bool = True
    group: Optional[str] = None
    version: str = "v_old"
    health: HealthState = HealthState.HEALTHY
    patch: PatchSpec = Field(default_factory=PatchSpec)

    @field_validator("criticality")
    @classmethod
    def _criticality_range(cls, v: int) -> int:
        if not (1 <= v <= 5):
            raise ValueError("criticality must be in [1, 5]")
        return v

    @field_validator("redundancy")
    @classmethod
    def _redundancy_min(cls, v: int) -> int:
        if v < 1:
            raise ValueError("redundancy must be >= 1")
        return v


class EdgeSpec(BaseModel):
    source: str
    target: str
    compatibility: CompatibilityLevel = CompatibilityLevel.COMPATIBLE
    mixed_max_duration_seconds: Optional[int] = None

    @field_validator("mixed_max_duration_seconds")
    @classmethod
    def _mixed_duration_non_negative(cls, v: Optional[int]) -> Optional[int]:
        if v is not None and v < 0:
            raise ValueError("mixed_max_duration_seconds must be >= 0")
        return v


class ScenarioSpec(BaseModel):
    name: str
    seed: int = 0
    incompatible_max_duration_seconds: int = 0
    min_up_default: int = 1
    nodes: List[NodeSpec]
    edges: List[EdgeSpec] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class PlanStep(BaseModel):
    step_id: str
    action: str
    node_ids: List[str] = Field(default_factory=list)
    pause_seconds: int = 0
    strategy: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class Plan(BaseModel):
    strategy: str
    steps: List[PlanStep]
    metadata: Dict[str, Any] = Field(default_factory=dict)


class SimulationResult(BaseModel):
    plan: Plan
    events: List[Dict[str, Any]]
    metrics: Dict[str, Any]
