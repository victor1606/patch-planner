# Patch Planner Simulator

Course project: "Security Patch Deployment Strategy for Critical Infrastructures".

This repo provides a reproducible simulator and planner that models patch rollout
strategies over a dependency graph, then compares reliability/security/compatibility
metrics across strategies and scenarios.

---

## Setup

### Prerequisites
- Python 3.11 or higher
- pip

### Installation

1. **Clone the repository** (if not already done):
   ```bash
   git clone <repository-url>
   cd ds_project
   ```

2. **Create a virtual environment** (recommended):
   ```bash
   python -m venv .venv
   
   # On Linux/macOS:
   source .venv/bin/activate
   
   # On Windows PowerShell:
   .venv\Scripts\Activate.ps1
   ```

3. **Install the package in development mode**:
   ```bash
   pip install -e .
   ```

4. **Install development dependencies** (for testing):
   ```bash
   pip install pytest
   ```

5. **Verify installation**:
   ```bash
   python -m patchplanner.cli --help
   ```

---

## Quick Start

### Run a single simulation

```bash
# Using the CLI directly
python -m patchplanner.cli \
  --scenario data/scenario1.yaml \
  --strategy hybrid \
  --out out

# Or use the convenience script
python scripts/run.py scenario1 hybrid
```

### Available strategies
- `bigbang` - Patch all nodes at once
- `rolling` - Patch nodes one-by-one
- `batch_rolling` - Patch in configurable batches
- `canary` - Test on subset first, then rollout
- `bluegreen` - Build new environment, instant switch
- `dep_greedy` - Dependency-aware topological order
- `hybrid` - Risk-aware adaptive strategy (recommended)

### Run comprehensive comparison

Compare all strategies across all scenarios:

```bash
python scripts/run_comparison.py
```

This generates:
- `results/all_results.json` - Raw metrics for all runs
- `results/comparison_report.md` - Comparison tables and analysis
- `results/<scenario>/<strategy>/` - Individual outputs per run

Filter by scenario or strategy:
```bash
python scripts/run_comparison.py --scenario scenario1
python scripts/run_comparison.py --strategy hybrid
```

---

## Project Structure

```
ds_project/
├── data/                   # Scenario definitions (YAML)
│   ├── scenario1.yaml      # HA microservices
│   ├── scenario2.yaml      # Compatibility constraints
│   └── scenario3.yaml      # High-risk patching
│
├── src/patchplanner/       # Main package
│   ├── cli.py              # Command-line interface
│   ├── models.py           # Domain models (Pydantic)
│   ├── infra_loader.py     # YAML parsing and graph construction
│   ├── planner/            # Strategy implementations
│   │   ├── base.py         # Abstract base strategy
│   │   ├── bigbang.py
│   │   ├── rolling.py
│   │   ├── batch_rolling.py
│   │   ├── canary.py
│   │   ├── bluegreen.py
│   │   ├── dep_greedy.py
│   │   └── hybrid.py       # Risk-aware adaptive
│   └── simulator/          # Simulation engine
│       ├── engine.py       # Main simulation loop
│       ├── constraints.py  # Availability checking
│       ├── metrics.py      # Metric collection
│       └── reporter.py     # Output generation
│
├── scripts/                # Utility scripts
│   ├── run.py              # Single simulation runner
│   └── run_comparison.py   # Batch comparison runner
│
├── tests/                  # Test suite
│   ├── test_simulator.py
│   ├── test_constraints.py
│   ├── test_strategies.py
│   └── test_planner.py
│
├── docs/                   # Documentation
│   ├── architecture.md     # Detailed architecture
│   └── architecture_summary.md  # High-level overview
│
└── out/                    # Default output directory (generated)
    ├── plan.json
    ├── events.jsonl
    ├── metrics.csv
    └── report.md
```

---

## Output Files

Each simulation generates four files:

1. **`plan.json`** - Complete deployment plan with all steps
2. **`events.jsonl`** - Chronological event log (one event per line)
3. **`metrics.csv`** - Key metrics in tabular format
4. **`report.md`** - Human-readable summary

### Key Metrics

| Metric | Description |
|--------|-------------|
| `time_to_full_patch` | Total seconds to complete all patches |
| `exposure_window_weighted` | Security exposure (criticality × severity × time) |
| `mixed_version_time_seconds` | Time with different versions coexisting |
| `number_of_degraded_intervals` | Count of degraded performance periods |
| `number_of_incompatibility_violations` | Hard constraint violations |
| `rollback_count` | Number of failed patches that were rolled back |
| `total_downtime_seconds_overall` | Total service unavailability |
| `number_of_guardrail_pauses` | Safety pause count |

---

## Testing

Run the test suite:

```bash
# All tests
python -m pytest tests/ -v

# Specific test file
python -m pytest tests/test_simulator.py -v

# With coverage
python -m pytest tests/ --cov=patchplanner --cov-report=html
```

---

## Creating Custom Scenarios

Create a YAML file in `data/`:

```yaml
name: my-scenario
seed: 42
min_up_default: 1
incompatible_max_duration_seconds: 0

nodes:
  - id: api-1
    type: SERVICE_INSTANCE
    service: api
    criticality: 4
    redundancy: 2
    min_up: 1
    patch:
      patch_duration_seconds: 60
      requires_restart: true
      failure_probability: 0.02
      rollback_supported: true
      severity: 7.0

edges:
  - source: web-1
    target: api-1
    compatibility: COMPATIBLE  # or DEGRADED, INCOMPATIBLE
```

Then run:
```bash
python scripts/run.py my-scenario hybrid
```

---

## Advanced Usage

### Custom seed for reproducibility
```bash
python scripts/run.py scenario1 hybrid --seed 123
```

### Batch rolling with custom batch size
```bash
python -m patchplanner.cli \
  --scenario data/scenario1.yaml \
  --strategy batch_rolling \
  --batch-size 3 \
  --out out
```

### Output to custom directory
```bash
python scripts/run.py scenario1 hybrid --out results/my-experiment
```

---

## Documentation

- **Architecture Overview**: `docs/architecture_summary.md`
- **Detailed Architecture**: `docs/architecture.md`

---

## Course Context

**Dependable Systems Project** - Evaluates patch deployment strategies considering:
- **Availability**: Maintaining service uptime during updates
- **Security**: Minimizing vulnerability exposure window
- **Reliability**: Handling failures and rollbacks
- **Compatibility**: Managing mixed-version dependencies

For academic evaluation criteria, see project requirements in documentation.
