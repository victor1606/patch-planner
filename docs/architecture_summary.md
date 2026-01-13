# PatchPlanner: Architecture Overview

**Project:** Security Patch Deployment Simulator for Critical Infrastructures  

---

## 1. System Purpose

PatchPlanner is a simulation framework that models security patch deployment across distributed systems. It addresses the fundamental trade-off between **security** (patching quickly to reduce vulnerability exposure) and **availability** (maintaining service uptime during updates).

---

## 2. High-Level Architecture

The system follows a four-stage pipeline:

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│    INPUT     │     │   PLANNING   │     │  SIMULATION  │     │    OUTPUT    │
│              │ --> │              │ --> │              │ --> │              │
│  Scenario    │     │   Strategy   │     │    Engine    │     │   Reports    │
│  (YAML)      │     │  Generator   │     │   Executor   │     │  & Metrics   │
└──────────────┘     └──────────────┘     └──────────────┘     └──────────────┘
```

---

## 3. Core Components

### 3.1 Infrastructure Model

The infrastructure is represented as a **directed dependency graph**:

- **Nodes**: Patchable components (hosts, services, databases) with properties:
  - Criticality level (1-5)
  - Patch characteristics (duration, failure probability, severity)
  - Availability requirements (minimum instances that must remain healthy)

- **Edges**: Dependencies between components with compatibility semantics:
  - `COMPATIBLE` – versions can safely differ
  - `DEGRADED` – mixed versions cause performance impact
  - `INCOMPATIBLE` – components must be patched together

### 3.2 Planning Module

Implements the **Strategy Pattern** with seven deployment strategies:

| Strategy | Approach | Trade-off |
|----------|----------|-----------|
| Big Bang | All at once | Fast but max downtime |
| Rolling | One-by-one | Safe but slow |
| Blue-Green | Parallel build + switch | Zero downtime, 2x resources |
| Canary | Test on subset first | Early failure detection |
| Dependency-Aware | Topological order | Respects dependencies |
| **Hybrid** | Risk-based + adaptive | Balances all factors |

### 3.3 Simulation Engine

A discrete-event simulator that:
1. Executes plan steps sequentially
2. Enforces availability constraints (min_up requirements)
3. Injects failures probabilistically
4. Tracks node state transitions: `HEALTHY → DOWN → HEALTHY/FAILED`
5. Collects metrics throughout execution

### 3.4 Metrics & Reporting

**Key metrics collected:**

| Category | Metrics |
|----------|---------|
| Timing | Total duration, downtime per service |
| Security | Exposure window (weighted by severity × criticality) |
| Reliability | Rollback count, constraint violations |
| Compatibility | Mixed-version time, degraded intervals |

---

## 4. Data Flow

```
scenario.yaml  ──►  Graph Builder  ──►  Strategy.generate()  ──►  Plan
                                                                    │
                                                                    ▼
reports (JSON/CSV/MD)  ◄──  Reporter  ◄──  SimulationResult  ◄──  Engine.run()
```

---

## 5. Technology Stack

- **Python 3.11+** – Core implementation
- **Pydantic** – Data validation and serialization
- **NetworkX** – Graph operations and algorithms
- **PyYAML** – Configuration parsing

---

## 6. Key Design Decisions

1. **Declarative scenarios**: Infrastructure defined in YAML, not code
2. **Deterministic simulation**: Seeded RNG ensures reproducible results
3. **Extensible strategies**: New strategies require only implementing one method
4. **Separation of concerns**: Planning logic decoupled from simulation execution


