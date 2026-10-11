"""Render and write human-reviewable Faultline artifacts."""

from __future__ import annotations

from pathlib import Path
from typing import Any


def _line_items(values: list[str]) -> list[str]:
    return [f"  - {value}" for value in values] if values else ["  - None"]


def _format_optional(label: str, value: Any) -> list[str]:
    if value in (None, "", []):
        return []
    return [f"- {label}: {value}"]


def render_patch_plan_markdown(patch_plan: dict[str, Any]) -> str:
    """Render a patch plan as markdown for review before implementation."""
    run_dir = patch_plan.get("run_dir", "unknown run")
    plans = patch_plan.get("plans", [])
    lines = [
        "# Faultline Patch Plan",
        "",
        f"- Run: `{run_dir}`",
        f"- Plans: {len(plans)}",
        "",
    ]
    if not plans:
        lines.extend(
            [
                "No patch plans were generated for this run.",
                "",
            ]
        )
        return "\n".join(lines)

    for index, plan in enumerate(plans, start=1):
        lines.extend(
            [
                f"## {index}. {plan.get('kind', 'patch')}",
                "",
                f"- Case: `{plan.get('case_id', 'unknown')}`",
                f"- Service: `{plan.get('service', 'unknown')}`",
                f"- Priority: {plan.get('priority', 'medium')}",
                f"- Objective: {plan.get('objective', 'No objective provided.')}",
            ]
        )
        lines.extend(_format_optional("Source gap", plan.get("source_gap")))
        lines.extend(
            [
                "",
                "Target files:",
                *_line_items(plan.get("target_files", [])),
                "",
                "Implementation steps:",
                *_line_items(plan.get("steps", [])),
            ]
        )
        validation = plan.get("validation")
        validation_query = plan.get("validation_query")
        if validation or validation_query:
            lines.extend(["", "Validation:"])
            if validation:
                lines.append(f"  - {validation}")
            if validation_query:
                lines.append(f"  - `{validation_query}`")
        lines.append("")

    return "\n".join(lines)


def write_patch_plan_artifact(analysis: dict[str, Any], output_dir: Path | None = None) -> Path:
    """Write patch-plan.md for an analyzed evaluation run."""
    patch_plan = analysis.get("patch_plan", {})
    run_dir = Path(analysis.get("run_dir", "."))
    destination = output_dir or run_dir / "patch-plan"
    destination.mkdir(parents=True, exist_ok=True)
    path = destination / "patch-plan.md"
    path.write_text(render_patch_plan_markdown(patch_plan), encoding="utf-8")
    return path
