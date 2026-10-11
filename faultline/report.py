"""Build final demo reports for Faultline runs."""

from __future__ import annotations

from pathlib import Path
from typing import Any


def _bullet(items: list[str]) -> list[str]:
    return [f"- {item}" for item in items] if items else ["- None"]


def _case_summary(analysis: dict[str, Any]) -> list[str]:
    lines = [
        f"- Cases: {analysis.get('cases', 0)}",
        f"- Attempted: {analysis.get('attempted', 0)}",
        f"- Correct: {analysis.get('correct', 0)}",
        f"- Accuracy on attempted: {analysis.get('accuracy_on_attempted')}",
    ]
    misses = analysis.get("misses", [])
    if misses:
        lines.extend(["", "Misses:"])
        for miss in misses:
            lines.append(
                "- "
                f"{miss.get('case_id')}: expected `{miss.get('expected_root_service')}`, "
                f"predicted `{miss.get('predicted_root_service')}`"
            )
    return lines


def _patch_summary(analysis: dict[str, Any]) -> list[str]:
    plans = analysis.get("patch_plan", {}).get("plans", [])
    lines = [f"- Patch plans: {len(plans)}"]
    for plan in plans:
        lines.append(
            "- "
            f"{plan.get('kind')} for `{plan.get('service')}` "
            f"({', '.join(plan.get('target_files', [])) or 'no target files'})"
        )
    return lines


def render_demo_report(
    analysis: dict[str, Any],
    patch_bundle_dir: Path | None = None,
    aws_handoff_dir: Path | None = None,
) -> str:
    """Render a final markdown demo report for a Faultline evaluation run."""
    run_dir = Path(analysis.get("run_dir", "."))
    patch_dir = patch_bundle_dir or run_dir / "patch-bundle"
    aws_dir = aws_handoff_dir or run_dir / "aws-handoff"
    verification = [
        "python3 -m unittest discover -s tests",
        "python3 -m py_compile scripts/flags.py scripts/cases.py scripts/telemetry.py scripts/diagnose.py scripts/evaluate.py scripts/run_eval.py scripts/analyze_eval.py scripts/write_patch_plan.py scripts/write_patch_bundle.py scripts/write_aws_handoff.py scripts/write_demo_report.py faultline/scrubber.py faultline/telemetry.py faultline/agent.py faultline/verifier.py faultline/eval.py faultline/harness.py faultline/analysis.py faultline/blindspots.py faultline/patches.py faultline/artifacts.py faultline/aws.py faultline/report.py",
        f"python3 scripts/analyze_eval.py {run_dir}",
        f"python3 scripts/write_patch_bundle.py {run_dir}",
        f"python3 scripts/write_aws_handoff.py {run_dir}",
    ]
    blockers = [
        "Live Docker/OpenTelemetry Demo verification still depends on Docker being available locally.",
        "Direct git push is blocked on this machine by missing GitHub HTTPS credentials.",
        "AWS is optional for the MVP; the handoff files prepare S3 archival but do not provision cloud resources.",
    ]
    lines = [
        "# Faultline Final Demo Report",
        "",
        f"Run: `{run_dir}`",
        "",
        "## MVP Loop",
        "",
        "Faultline now demonstrates the loop: inject a known fault, diagnose from telemetry, score the result, identify blind spots, create patch plans, package patch bundles, and prepare an optional AWS handoff.",
        "",
        "## Evaluation Summary",
        "",
        *_case_summary(analysis),
        "",
        "## Patch Evidence",
        "",
        *_patch_summary(analysis),
        "",
        "Patch bundle:",
        f"- `{patch_dir / 'patch-plan.md'}`",
        f"- `{patch_dir / 'patch-manifest.json'}`",
        f"- `{patch_dir / 'validation.sh'}`",
        "",
        "## AWS Status",
        "",
        "AWS is not required for the local MVP. The project is AWS-ready through handoff artifacts:",
        f"- `{aws_dir / 'aws-manifest.json'}`",
        f"- `{aws_dir / 'upload-to-s3.sh'}`",
        f"- `{aws_dir / 'README.md'}`",
        "",
        "## Verification Commands",
        "",
        *_bullet([f"`{command}`" for command in verification]),
        "",
        "## Remaining Blockers",
        "",
        *_bullet(blockers),
        "",
        "## Demo Script",
        "",
        "1. Show `cases/day2_feature_flags.json` as the ground-truth fault catalog.",
        "2. Show `scripts/run_eval.py` as the end-to-end fault and diagnosis harness.",
        "3. Show the saved evaluation summary and diagnosis JSON under the run directory.",
        "4. Run `scripts/analyze_eval.py` to explain the miss and blind spots.",
        "5. Show `patch-bundle/patch-plan.md` as the next engineering action.",
        "6. Explain that AWS is optional and represented by `aws-handoff/` for S3 archival.",
        "",
    ]
    return "\n".join(lines)


def write_demo_report(
    analysis: dict[str, Any],
    output_dir: Path | None = None,
    patch_bundle_dir: Path | None = None,
    aws_handoff_dir: Path | None = None,
) -> Path:
    """Write final-demo-report.md for a saved evaluation run."""
    run_dir = Path(analysis.get("run_dir", "."))
    destination = output_dir or run_dir / "final-report"
    destination.mkdir(parents=True, exist_ok=True)
    path = destination / "final-demo-report.md"
    path.write_text(render_demo_report(analysis, patch_bundle_dir, aws_handoff_dir), encoding="utf-8")
    return path
