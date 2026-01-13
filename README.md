# Patch Planner Simulator

Course project: "Security Patch Deployment Strategy for Critical Infrastructures".

This repo provides a reproducible simulator and planner that models patch rollout
strategies over a dependency graph, then compares reliability/security/compatibility
metrics across strategies and scenarios.

## Quick start

```powershell
pip install -e .
python -m patchplanner.cli --scenario data/scenario1.yaml --strategy rolling --out out
python -m patchplanner.cli --scenario data/scenario1.yaml --strategy hybrid --out out
```

## Project layout

```
src/patchplanner/
  models.py
  infra_loader.py
  planner/
  simulator/
  cli.py
data/
tests/
```

## Outputs

- `out/plan.json`
- `out/events.jsonl`
- `out/metrics.csv`
- `out/report.md`

## Notes

- Deterministic runs via `--seed`.
- YAML scenarios live in `data/`.
