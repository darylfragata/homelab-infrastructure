"""Renders a condensed, CI-friendly plain-text summary of a PlanAnalysis -
suitable for a pipeline log or step-summary output.
"""

from __future__ import annotations

from models.change import PlanAnalysis
from utils.helpers import SERVICE_DISPLAY_NAMES


def render(result: PlanAnalysis) -> str:
    """Render the condensed pipeline summary for `result`."""
    lines = [
        "Terraform Plan Summary",
        (
            f"Create: {result.summary.create}  Update: {result.summary.update}  "
            f"Delete: {result.summary.delete}  Replace: {result.summary.replace}"
        ),
        "",
    ]

    for resource in result.resources:
        action_label = resource.action.value.upper()
        risk = resource.risk.value if resource.risk else "UNKNOWN"
        service = SERVICE_DISPLAY_NAMES.get(resource.service, resource.service)
        lines.append(f"[{action_label}] {service}: {resource.address} - {risk}")

    if result.high_risk:
        lines.append("")
        lines.append("HIGH RISK:")
        lines.extend(f"- {resource.address}" for resource in result.high_risk)

    if result.skipped_count:
        plural = "y" if result.skipped_count == 1 else "ies"
        lines.append("")
        lines.append(
            f"Note: {result.skipped_count} resource_changes entr{plural} could not be "
            "parsed and were skipped."
        )

    return "\n".join(lines) + "\n"
