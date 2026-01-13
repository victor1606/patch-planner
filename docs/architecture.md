# PatchPlanner: System Architecture Document

**Project:** Security Patch Deployment Strategy Simulator for Critical Infrastructures  

## 1. Summary

PatchPlanner is a discrete-event simulation framework designed to model, plan, and evaluate security patch deployment strategies across distributed critical infrastructure systems. The system addresses a fundamental challenge in dependable systems: how to apply security patches quickly (to minimize vulnerability exposure) while maintaining service availability and respecting component compatibility constraints.

The framework enables infrastructure operators to:
- Model their infrastructure as a dependency graph with availability constraints
- Generate patch deployment plans using various strategies
- Simulate plan execution with realistic failure injection
- Compare strategies using quantifiable reliability and security metrics

---

## 2. System Context

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         External Environment                            │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│   ┌──────────────┐                              ┌──────────────────┐    │
│   │   Operator   │                              │  Infrastructure  │    │
│   │   (User)     │                              │  (Real System)   │    │
│   └──────┬───────┘                              └────────▲─────────┘    │
│          │                                               │              │
│          │ Defines scenarios                             │ Informs      │
│          │ Selects strategy                              │ model design │
│          ▼                                               │              │
│   ┌──────────────────────────────────────────────────────┴───────┐      │
│   │                                                              │      │
│   │                    PatchPlanner System                       │      │
│   │                                                              │      │
│   │   ┌─────────────┐   ┌─────────────┐   ┌─────────────────┐    │      │
│   │   │  Scenario   │ → │   Planner   │ → │    Simulator    │    │      │
│   │   │   Loader    │   │  Strategies │   │     Engine      │    │      │
│   │   └─────────────┘   └─────────────┘   └────────┬────────┘    │      │
│   │                                                │             │      │
│   │                                                ▼             │      │
│   │                                       ┌─────────────────┐    │      │
│   │                                       │    Reporter     │    │      │
│   │                                       │  (Metrics/Logs) │    │      │
│   │                                       └─────────────────┘    │      │
│   └──────────────────────────────────────────────────────────────┘      │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Architectural Overview

### 3.1 High-Level Architecture

The system follows a **pipeline architecture** with four main processing stages:

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   INPUT     │    │  PLANNING   │    │ SIMULATION  │    │   OUTPUT    │
│             │    │             │    │             │    │             │
│  Scenario   │ -> │  Strategy   │ -> │   Engine    │ -> │   Reports   │
│  (YAML)     │    │  Selection  │    │  Execution  │    │  (Metrics)  │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
```

### 3.2 Component Diagram

```
┌────────────────────────────────────────────────────────────────────────────┐
│                              PatchPlanner                                  │
├────────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                         CLI Interface                               │   │
│  │  - Command-line argument parsing                                    │   │
│  │  - Strategy selection                                               │   │
│  │  - Output directory management                                      │   │
│  └───────────────────────────────┬─────────────────────────────────────┘   │
│                                  │                                         │
│  ┌───────────────────────────────▼─────────────────────────────────────┐   │
│  │                       Core Domain Models                            │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌────────────┐  │   │
│  │  │ Scenario    │  │    Node     │  │    Edge     │  │   Plan     │  │   │
│  │  │ Spec        │  │    Spec     │  │    Spec     │  │   Step     │  │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └────────────┘  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                  │                                         │
│         ┌────────────────────────┼────────────────────────┐                │
│         │                        │                        │                │
│         ▼                        ▼                        ▼                │
│  ┌─────────────────┐   ┌─────────────────┐   ┌─────────────────────────┐   │
│  │ Infrastructure  │   │    Planner      │   │      Simulator          │   │
│  │    Loader       │   │    Module       │   │       Module            │   │
│  │                 │   │                 │   │                         │   │
│  │ - YAML parsing  │   │ ┌─────────────┐ │   │  ┌─────────────────┐    │   │
│  │ - Graph builder │   │ │ Base        │ │   │  │ Simulation      │    │   │
│  │ - Compatibility │   │ │ Strategy    │ │   │  │ Engine          │    │   │
│  │   grouping      │   │ └──────┬──────┘ │   │  └────────┬────────┘    │   │
│  │                 │   │        │        │   │           │             │   │
│  └─────────────────┘   │ ┌──────▼──────┐ │   │  ┌────────▼────────┐    │   │
│                        │ │ Concrete    │ │   │  │ Constraint      │    │   │
│                        │ │ Strategies  │ │   │  │ Checker         │    │   │
│                        │ │             │ │   │  └─────────────────┘    │   │
│                        │ │ - BigBang   │ │   │                         │   │
│                        │ │ - Rolling   │ │   │  ┌─────────────────┐    │   │
│                        │ │ - BlueGreen │ │   │  │ Metrics         │    │   │
│                        │ │ - Canary    │ │   │  │ Collector       │    │   │
│                        │ │ - DepGreedy │ │   │  └─────────────────┘    │   │
│                        │ │ - Hybrid    │ │   │                         │   │
│                        │ └─────────────┘ │   │  ┌─────────────────┐    │   │
│                        │                 │   │  │ Reporter        │    │   │
│                        └─────────────────┘   │  └─────────────────┘    │   │
│                                              └─────────────────────────┘   │
│                                                                            │
└────────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Core Components

### 4.1 Infrastructure Loader

**Purpose:** Transform declarative infrastructure definitions into executable graph models.

**Responsibilities:**
- Parse YAML scenario files into structured domain objects
- Construct a directed graph (using NetworkX) representing component dependencies
- Identify incompatibility groups (components that must be patched together)

**Key Abstractions:**
- Scenario configuration with global parameters (seed, timing constraints)
- Node specifications (type, criticality, patch requirements)
- Edge specifications (dependency direction, compatibility level)

```
┌─────────────────┐       ┌─────────────────┐       ┌─────────────────┐
│   YAML File     │  -->  │   Scenario      │  -->  │   Dependency    │
│   (scenario)    │       │   Spec Object   │       │   Graph (DAG)   │
└─────────────────┘       └─────────────────┘       └─────────────────┘
```

### 4.2 Domain Models

**Purpose:** Provide a type-safe, validated representation of the problem domain.

**Core Entities:**

| Entity | Description |
|--------|-------------|
| **Scenario** | Complete infrastructure definition with nodes, edges, and global constraints |
| **Node** | A patchable component (host, service instance, database) with properties |
| **Edge** | Dependency relationship with compatibility semantics |
| **Patch** | Patch characteristics (duration, failure risk, severity) |
| **Plan** | Ordered sequence of deployment steps |
| **Step** | Atomic deployment action (patch, pause, switch) |

**Node Type Hierarchy:**
```
                    ┌──────────────┐
                    │     Node     │
                    └──────┬───────┘
                           │
          ┌────────────────┼────────────────┐
          │                │                │
    ┌─────▼─────┐   ┌──────▼──────┐   ┌─────▼─────┐
    │   HOST    │   │  SERVICE    │   │ DATABASE  │
    │           │   │  INSTANCE   │   │           │
    └───────────┘   └─────────────┘   └───────────┘
```

**Compatibility Model:**
```
COMPATIBLE ────────► No restrictions, versions can differ
DEGRADED ──────────► Allowed but tracked (performance impact)
INCOMPATIBLE ──────► Must patch together (hard constraint)
```

### 4.3 Planner Module

**Purpose:** Generate deployment plans using different strategies, each optimizing for different objectives.

**Design Pattern:** Strategy Pattern with a common base class defining the interface.

```
                        ┌───────────────────┐
                        │   BaseStrategy    │
                        │   (Abstract)      │
                        ├───────────────────┤
                        │ + generate(): Plan│
                        │ # _node_ids()     │
                        │ # _group_by_...() │
                        └─────────┬─────────┘
                                  │
        ┌────────────┬────────────┼────────────┬────────────┐
        │            │            │            │            │
   ┌────▼────┐ ┌─────▼─────┐ ┌────▼────┐ ┌─────▼─────┐ ┌────▼────┐
   │ BigBang │ │  Rolling  │ │ Canary  │ │ BlueGreen │ │ Hybrid  │
   └─────────┘ └───────────┘ └─────────┘ └───────────┘ └─────────┘
```

**Strategy Characteristics:**

| Strategy | Ordering Logic | Batching | Zero-Downtime |
|----------|---------------|----------|---------------|
| Big Bang | None (all at once) | Single batch | No |
| Rolling | Criticality × Severity | One-by-one | Partial |
| Batch Rolling | Same as Rolling | Configurable size | Partial |
| Canary | Service-based selection | 2 phases | Partial |
| Blue-Green | None | All (parallel build) | Yes |
| Dependency-Aware | Topological order | By dependency level | Partial |
| Hybrid | Risk score + adaptive | Dynamic | Adaptive |

### 4.4 Simulator Module

**Purpose:** Execute deployment plans in a discrete-event simulation, modeling real-world behaviors including failures, timing, and constraint violations.

**Architecture:**

```
┌─────────────────────────────────────────────────────────────────┐
│                     Simulation Engine                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────────┐   │
│  │    Plan      │    │   Current    │    │   Random         │   │
│  │   (Input)    │    │   State      │    │   Generator      │   │
│  └──────┬───────┘    └──────────────┘    │   (Failures)     │   │
│         │                   ▲            └──────────────────┘   │
│         ▼                   │                                   │
│  ┌──────────────────────────┴───────────────────────────────┐   │
│  │                    Event Loop                            │   │
│  │                                                          │   │
│  │   for each step in plan:                                 │   │
│  │       1. Check availability constraints                  │   │
│  │       2. Execute action (patch/pause/switch)             │   │
│  │       3. Inject failures probabilistically               │   │
│  │       4. Update node states                              │   │
│  │       5. Advance simulation clock                        │   │
│  │       6. Collect metrics                                 │   │
│  │       7. Record events                                   │   │
│  │                                                          │   │
│  └──────────────────────────────────────────────────────────┘   │
│                              │                                  │
│         ┌────────────────────┼────────────────────┐             │
│         ▼                    ▼                    ▼             │
│  ┌─────────────┐     ┌─────────────┐     ┌─────────────────┐    │
│  │  Metrics    │     │   Events    │     │  Final State    │    │
│  │  Summary    │     │   Log       │     │  (Graph)        │    │
│  └─────────────┘     └─────────────┘     └─────────────────┘    │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**State Machine for Nodes:**

```
                   patch_start
        ┌───────────────────────────────┐
        │                               ▼
   ┌────┴────┐    patch_success    ┌──────────┐
   │ HEALTHY │ <───────────────────│   DOWN   │
   └────┬────┘                     └────┬─────┘
        │                               │
        │    failure                    │ failure
        │    (no rollback)              │ (with rollback)
        │                               │
        ▼                               ▼
   ┌─────────┐                     ┌───────────┐
   │ FAILED  │                     │  HEALTHY  │
   │         │                     │ (v_old)   │
   └─────────┘                     └───────────┘
```

**Constraint Checking:**
- **Availability Constraint:** For each service, count healthy instances ≥ min_up
- **Compatibility Constraint:** Track mixed-version edges, flag violations

### 4.5 Metrics Collector

**Purpose:** Accumulate quantitative measurements throughout simulation execution.

**Metric Categories:**

```
┌─────────────────────────────────────────────────────────────────┐
│                         Metrics                                 │
├────────────────────┬────────────────────┬───────────────────────┤
│      Timing        │    Reliability     │      Security         │
├────────────────────┼────────────────────┼───────────────────────┤
│ • Time to complete │ • Rollback count   │ • Exposure window     │
│ • Total downtime   │ • Abort count      │   (weighted)          │
│ • Max continuous   │ • Guardrail pauses │ • Mixed-version time  │
│   downtime         │                    │ • Incompatibility     │
│                    │                    │   violations          │
└────────────────────┴────────────────────┴───────────────────────┘
```

**Exposure Window Calculation:**

$$E = \sum_{t=0}^{T} \sum_{n \in U_t} C_n \times S_n \times \Delta t$$

Where:
- $U_t$ = set of unpatched nodes at time $t$
- $C_n$ = criticality of node $n$
- $S_n$ = patch severity for node $n$
- $\Delta t$ = time interval

### 4.6 Reporter

**Purpose:** Generate human-readable and machine-processable output artifacts.

**Output Formats:**

| File | Format | Purpose |
|------|--------|---------|
| `plan.json` | JSON | Complete deployment plan with all steps |
| `events.jsonl` | JSON Lines | Chronological event log (one event per line) |
| `metrics.csv` | CSV | Key metrics in tabular format |
| `report.md` | Markdown | Human-readable summary report |

---

## 5. Data Flow

### 5.1 End-to-End Data Flow

```
┌──────────────────────────────────────────────────────────────────────────┐
│                                                                          │
│  scenario.yaml                                                           │
│       │                                                                  │
│       ▼                                                                  │
│  ┌─────────────┐                                                         │
│  │   LOADER    │ ──────────────────────────────────────┐                 │
│  └─────────────┘                                       │                 │
│       │                                                │                 │
│       │ ScenarioSpec                                   │                 │
│       │ + Graph                                        │                 │
│       ▼                                                │                 │
│  ┌─────────────┐                                       │                 │
│  │   PLANNER   │                                       │                 │
│  └─────────────┘                                       │                 │
│       │                                                │                 │
│       │ Plan                                           │ ScenarioSpec    │
│       │                                                │ + Graph         │
│       ▼                                                ▼                 │
│  ┌─────────────────────────────────────────────────────────────────┐     │
│  │                        SIMULATOR                                │     │
│  │                                                                 │     │
│  │   Plan ──► Event Loop ──► State Updates ──► Metric Collection   │     │
│  │                                                                 │     │
│  └───────────────────────────────┬─────────────────────────────────┘     │
│                                  │                                       │
│                                  │ SimulationResult                      │
│                                  │ (Plan + Events + Metrics)             │
│                                  ▼                                       │
│                         ┌─────────────┐                                  │
│                         │  REPORTER   │                                  │
│                         └─────────────┘                                  │
│                                │                                         │
│              ┌─────────────────┼─────────────────┐                       │
│              ▼                 ▼                 ▼                       │
│         plan.json        metrics.csv       report.md                     │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

### 5.2 Simulation Event Sequence

```
Time ──────────────────────────────────────────────────────────────────►

     ┌─────┐   ┌─────┐   ┌─────┐   ┌─────┐   ┌─────┐   ┌─────┐
     │Build│   │Switch│  │Pause│   │Build│   │Switch│  │Pause│
     │ N1  │   │ N1   │  │     │   │ N2  │   │ N2   │  │     │
     └──┬──┘   └──┬───┘  └──┬──┘   └──┬──┘   └──┬───┘  └──┬──┘
        │         │         │         │         │         │
        ▼         ▼         ▼         ▼         ▼         ▼
     ┌──────────────────────────────────────────────────────────┐
     │                    Metrics Updated                       │
     │  • exposure_window += unpatched_risk × Δt                │
     │  • mixed_version_time += Δt (if edges are mixed)         │
     │  • degraded_intervals++ (if DEGRADED edges active)       │
     └──────────────────────────────────────────────────────────┘
```

---

## 6. Deployment Strategies: Detailed Design

### 6.1 Strategy Selection Logic (Hybrid)

The Hybrid strategy demonstrates adaptive decision-making:

```
┌─────────────────────────────────────────────────────────────────┐
│                    Hybrid Strategy Flow                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   1. Calculate risk score for each node:                        │
│    risk = severity × criticality × (1 + in_degree + out_degree) │
│                                                                 │
│   2. Group nodes by incompatibility (must-patch-together)       │
│                                                                 │
│   3. Sort groups by maximum risk (descending)                   │
│                                                                 │
│   4. For each group:                                            │
│      ┌────────────────────────────────────────────┐             │
│      │  IF min_up ≥ group_size:                   │             │
│      │      → Use Blue-Green (zero downtime)      │             │
│      │  ELSE:                                     │             │
│      │      → Use Rolling (maintains availability)│             │
│      └────────────────────────────────────────────┘             │
│                                                                 │
│   5. Add guardrail pause (30s) after each group                 │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 6.2 Dependency-Aware Ordering

```
    Original Dependencies              Patch Order (Reverse Topological)
    
         ┌─────┐                              Step 1: db
         │ web │                              Step 2: api
         └──┬──┘                              Step 3: web
            │
            ▼                            Rationale: Patch dependencies first,
         ┌─────┐                         then dependents. This minimizes
         │ api │                         mixed-version edge time.
         └──┬──┘
            │
            ▼
         ┌─────┐
         │ db  │
         └─────┘
```

---

## 7. Technology Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| Language | Python 3.11+ | Core implementation |
| Data Validation | Pydantic v2 | Schema validation, serialization |
| Graph Processing | NetworkX | Dependency graph operations |
| Configuration | PyYAML | Scenario file parsing |
| Visualization | Matplotlib | (Optional) Graph/metric visualization |
| Testing | pytest | Unit and integration testing |
| Packaging | setuptools | Distribution and installation |

---

## 8. Quality Attributes

### 8.1 Extensibility

**Adding a new strategy:**
1. Create new class inheriting from `BaseStrategy`
2. Implement `generate() -> Plan` method
3. Register in CLI strategy dictionary

**Adding new metrics:**
1. Add field to `MetricsState` dataclass
2. Update `update_interval_metrics()` or step handlers
3. Include in `finalize_metrics()` output

### 8.2 Testability

- **Unit tests:** Strategy logic, constraint checking, metric calculations
- **Integration tests:** End-to-end simulation with known outcomes
- **Determinism:** Seeded random number generator ensures reproducible runs

### 8.3 Configurability

All scenario parameters externalized to YAML:
- No hardcoded infrastructure definitions
- Strategy-specific parameters via CLI flags
- Seed control for reproducibility

---

## 9. Limitations and Future Extensions

### Current Limitations

1. **Simplified timing model:** No network latency or parallel execution overhead
2. **Binary node states:** No partial degradation modeling
3. **Static dependencies:** Cannot model dynamic service discovery
4. **Single failure mode:** Only patch application failures modeled

### Potential Extensions

1. **Multi-objective optimization:** Pareto-optimal strategy selection
2. **Container orchestration:** Kubernetes-style rolling updates
3. **Machine learning:** Learned failure probability models
4. **Real-time integration:** API for production deployment systems
5. **Visualization dashboard:** Interactive simulation replay

---

## 10. Appendix: Directory Structure

```
patchplanner/
├── pyproject.toml          # Project metadata and dependencies
├── pytest.ini              # Test configuration
├── README.md               # Quick start guide
│
├── data/                   # Scenario definitions
│   ├── scenario1.yaml      # HA microservices scenario
│   ├── scenario2.yaml      # Compatibility constraint scenario
│   └── scenario3.yaml      # High-risk patch scenario
│
├── src/patchplanner/       # Main package
│   ├── __init__.py
│   ├── cli.py              # Command-line interface
│   ├── models.py           # Domain models (Pydantic)
│   ├── infra_loader.py     # YAML parsing and graph construction
│   │
│   ├── planner/            # Strategy implementations
│   │   ├── __init__.py
│   │   ├── base.py         # Abstract base strategy
│   │   ├── bigbang.py
│   │   ├── rolling.py
│   │   ├── batch_rolling.py
│   │   ├── canary.py
│   │   ├── bluegreen.py
│   │   ├── dep_greedy.py
│   │   └── hybrid.py
│   │
│   └── simulator/          # Simulation engine
│       ├── __init__.py
│       ├── engine.py       # Main simulation loop
│       ├── constraints.py  # Availability checking
│       ├── metrics.py      # Metric collection
│       └── reporter.py     # Output generation
│
├── tests/                  # Test suite
│   ├── test_planner.py
│   ├── test_simulator.py
│   └── test_strategies.py
│
└── out/                    # Simulation outputs (generated)
    ├── plan.json
    ├── events.jsonl
    ├── metrics.csv
    └── report.md
```
