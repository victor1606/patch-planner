from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any, Dict, Iterable

from ..models import Plan


def write_report(
    out_dir: str | Path,
    plan: Plan,
    events: Iterable[Dict[str, Any]],
    metrics: Dict[str, Any],
) -> None:
    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    (out_path / "plan.json").write_text(
        json.dumps(plan.model_dump(), indent=2), encoding="utf-8"
    )
    _write_events(out_path / "events.jsonl", events)
    _write_metrics(out_path / "metrics.csv", metrics)
    _write_markdown(out_path / "report.md", metrics)


def _write_events(path: Path, events: Iterable[Dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for event in events:
            handle.write(json.dumps(event))
            handle.write("\n")


def _write_metrics(path: Path, metrics: Dict[str, Any]) -> None:
    flat: Dict[str, Any] = {}
    for key, value in metrics.items():
        if isinstance(value, dict):
            for sub_key, sub_val in value.items():
                flat[f"{key}.{sub_key}"] = sub_val
        else:
            flat[key] = value

    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["metric", "value"])
        for key, value in flat.items():
            writer.writerow([key, value])


def _write_markdown(path: Path, metrics: Dict[str, Any]) -> None:
    lines = ["# Patch Strategy Report", ""]
    lines.append("## Summary")
    lines.append("")
    for key, value in metrics.items():
        if isinstance(value, dict):
            continue
        lines.append(f"- {key}: {value}")
    lines.append("")
    lines.append("## Downtime Breakdown")
    lines.append("")
    for service, downtime in metrics.get("total_downtime_seconds", {}).items():
        lines.append(f"- {service}: {downtime}")
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")
