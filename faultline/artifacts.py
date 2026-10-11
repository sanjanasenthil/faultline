"""Render and write human-reviewable Faultline artifacts."""

from __future__ import annotations

import json
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


def build_patch_manifest(analysis: dict[str, Any]) -> dict[str, Any]:
    """Build a compact manifest for applying and validating patch plans."""
    patch_plan = analysis.get("patch_plan", {})
    plans = patch_plan.get("plans", [])
    return {
        "run_dir": patch_plan.get("run_dir") or analysis.get("run_dir"),
        "plan_count": len(plans),
        "plans": [
            {
                "case_id": plan.get("case_id"),
                "service": plan.get("service"),
                "kind": plan.get("kind"),
                "priority": plan.get("priority"),
                "target_files": plan.get("target_files", []),
                "validation": plan.get("validation"),
                "validation_query": plan.get("validation_query"),
            }
            for plan in plans
        ],
    }


def render_validation_script(patch_plan: dict[str, Any]) -> str:
    """Render validation commands from a patch plan."""
    lines = [
        "#!/usr/bin/env sh",
        "set -eu",
        "",
        "# Run these checks after applying the patch bundle.",
        "python3 -m unittest discover -s tests",
    ]
    for plan in patch_plan.get("plans", []):
        query = plan.get("validation_query")
        if query:
            lines.append(query)
    lines.append("python3 scripts/analyze_eval.py results/eval-runs/<timestamp>")
    lines.append("")
    return "\n".join(lines)


def write_patch_bundle(analysis: dict[str, Any], output_dir: Path | None = None) -> dict[str, Path]:
    """Write a patch-plan bundle with human, machine, and validation files."""
    run_dir = Path(analysis.get("run_dir", "."))
    destination = output_dir or run_dir / "patch-bundle"
    destination.mkdir(parents=True, exist_ok=True)

    plan_path = write_patch_plan_artifact(analysis, destination)
    manifest_path = destination / "patch-manifest.json"
    validation_path = destination / "validation.sh"

    manifest_path.write_text(
        json.dumps(build_patch_manifest(analysis), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    validation_path.write_text(render_validation_script(analysis.get("patch_plan", {})), encoding="utf-8")
    validation_path.chmod(0o755)

    return {
        "plan": plan_path,
        "manifest": manifest_path,
        "validation": validation_path,
    }
