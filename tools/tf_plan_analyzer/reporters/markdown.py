"""Renders a PlanAnalysis as a Markdown report."""

from __future__ import annotations

from typing import List

from models.change import AnalyzedResource, AttributeChange, PlanAnalysis
from models.resource import ActionType
from utils.helpers import SERVICE_DISPLAY_NAMES, group_by_service

_SEPARATOR = "-" * 34

_ACTION_HEADINGS = {
    ActionType.CREATE: "Create",
    ActionType.UPDATE: "Update",
    ActionType.DELETE: "Delete",
    ActionType.REPLACE: "Replace",
}


def _attribute_lines(change: AttributeChange) -> List[str]:
    if isinstance(change.before, list) or isinstance(change.after, list):
        lines: List[str] = []
        if change.before:
            lines.append("Before:")
            lines.append("")
            lines.extend(f"- {item}" for item in change.before)
            lines.append("")
        if change.after:
            lines.append("After:")
            lines.append("")
            lines.extend(f"- {item}" for item in change.after)
            lines.append("")
        return lines
    value = change.after if change.after is not None else change.before
    label = change.display or f"{change.path} = {value}"
    return [f"- {label}"]


def _render_resource(resource: AnalyzedResource) -> List[str]:
    heading = _ACTION_HEADINGS.get(resource.action, resource.action.value.title())
    lines = [f"{heading}:", "", f"- {resource.name}", ""]

    if resource.attribute_changes:
        lines.append("Changes:")
        lines.append("")
        for change in resource.attribute_changes:
            lines.extend(_attribute_lines(change))
        if lines[-1] != "":
            lines.append("")

    if resource.impacts:
        lines.append("Impact:")
        lines.append("")
        lines.extend(f"- {impact}" for impact in resource.impacts)
        lines.append("")

    if resource.risk:
        lines.append("Risk:")
        lines.append("")
        lines.append(f"- {resource.risk.value}")
        lines.append("")

    return lines


def render(result: PlanAnalysis) -> str:
    """Render the full Markdown report for `result`."""
    lines = [
        "Terraform Plan Summary",
        "",
        _SEPARATOR,
        "",
        f"Resources to Create : {result.summary.create}",
        f"Resources to Update : {result.summary.update}",
        f"Resources to Delete : {result.summary.delete}",
        f"Resources to Replace : {result.summary.replace}",
        "",
        _SEPARATOR,
        "",
    ]

    for service, resources in group_by_service(result.resources).items():
        lines.append(SERVICE_DISPLAY_NAMES.get(service, service))
        lines.append("")
        for resource in resources:
            lines.extend(_render_resource(resource))
        lines.append(_SEPARATOR)
        lines.append("")

    if result.high_risk:
        lines.append("HIGH RISK")
        lines.append("")
        for resource in result.high_risk:
            lines.extend(f"- {impact}" for impact in resource.impacts)
        lines.append("")
        lines.append(_SEPARATOR)
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"
