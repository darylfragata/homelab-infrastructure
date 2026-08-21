"""Renders a PlanAnalysis as a single, self-contained HTML report.

No external stylesheets, scripts, or CDN references - everything is inlined,
consistent with this project's no-network, stdlib-only constraint. All
resource-supplied values are HTML-escaped since Terraform attribute values can
contain characters like <, >, and & (e.g. in IAM policy JSON).
"""

from __future__ import annotations

from html import escape
from typing import List

from models.change import AnalyzedResource, AttributeChange, PlanAnalysis
from models.resource import ActionType
from utils.helpers import SERVICE_DISPLAY_NAMES, group_by_service

_ACTION_HEADINGS = {
    ActionType.CREATE: "Create",
    ActionType.UPDATE: "Update",
    ActionType.DELETE: "Delete",
    ActionType.REPLACE: "Replace",
}

_RISK_CLASS = {"LOW": "risk-low", "MEDIUM": "risk-medium", "HIGH": "risk-high"}

_STYLE = """
body { font-family: -apple-system, Segoe UI, Arial, sans-serif; margin: 2rem;
  color: #1a1a1a; background: #ffffff; }
h1 { margin-bottom: 0.25rem; }
.summary { display: flex; gap: 1.5rem; margin: 1rem 0 2rem; flex-wrap: wrap; }
.summary div { background: #f3f4f6; border-radius: 6px; padding: 0.5rem 1rem; }
.service { border: 1px solid #e5e7eb; border-radius: 8px; padding: 1rem 1.5rem;
  margin-bottom: 1.5rem; }
.resource { border-top: 1px solid #e5e7eb; padding: 0.75rem 0; }
.resource:first-of-type { border-top: none; }
.badge { display: inline-block; padding: 0.1rem 0.5rem; border-radius: 4px;
  font-size: 0.8rem; font-weight: 600; }
.risk-low { background: #dcfce7; color: #166534; }
.risk-medium { background: #fef9c3; color: #854d0e; }
.risk-high { background: #fee2e2; color: #991b1b; }
.high-risk { border: 2px solid #991b1b; border-radius: 8px; padding: 1rem 1.5rem;
  background: #fef2f2; }
ul { margin: 0.25rem 0; }
"""


def _list_items(values: List) -> str:
    return "".join(f"<li>{escape(str(v))}</li>" for v in values)


def _attribute_html(change: AttributeChange) -> str:
    if isinstance(change.before, list) or isinstance(change.after, list):
        parts = []
        if change.before:
            parts.append(f"<strong>Before:</strong><ul>{_list_items(change.before)}</ul>")
        if change.after:
            parts.append(f"<strong>After:</strong><ul>{_list_items(change.after)}</ul>")
        return "".join(parts)
    value = change.after if change.after is not None else change.before
    label = change.display or f"{change.path} = {value}"
    return f"<li>{escape(str(label))}</li>"


def _resource_html(resource: AnalyzedResource) -> str:
    heading = _ACTION_HEADINGS.get(resource.action, resource.action.value.title())
    risk = resource.risk.value if resource.risk else ""
    risk_class = _RISK_CLASS.get(risk, "")

    html: List[str] = ['<div class="resource">']
    html.append(f"<h3>{escape(heading)}: {escape(resource.name)}</h3>")

    if resource.attribute_changes:
        scalar_changes = [
            c
            for c in resource.attribute_changes
            if not (isinstance(c.before, list) or isinstance(c.after, list))
        ]
        list_changes = [
            c
            for c in resource.attribute_changes
            if isinstance(c.before, list) or isinstance(c.after, list)
        ]
        html.append("<p><strong>Changes:</strong></p>")
        if scalar_changes:
            html.append("<ul>" + "".join(_attribute_html(c) for c in scalar_changes) + "</ul>")
        html.extend(_attribute_html(c) for c in list_changes)

    if resource.impacts:
        html.append("<p><strong>Impact:</strong></p><ul>")
        html.append("".join(f"<li>{escape(i)}</li>" for i in resource.impacts))
        html.append("</ul>")

    if risk:
        html.append(
            f'<p><strong>Risk:</strong> <span class="badge {risk_class}">{escape(risk)}</span></p>'
        )

    html.append("</div>")
    return "".join(html)


def render(result: PlanAnalysis) -> str:
    """Render the full HTML report for `result`."""
    body: List[str] = [
        "<h1>Terraform Plan Summary</h1>",
        '<div class="summary">',
        f"<div>Create: {result.summary.create}</div>",
        f"<div>Update: {result.summary.update}</div>",
        f"<div>Delete: {result.summary.delete}</div>",
        f"<div>Replace: {result.summary.replace}</div>",
        "</div>",
    ]

    for service, resources in group_by_service(result.resources).items():
        display_name = SERVICE_DISPLAY_NAMES.get(service, service)
        body.append('<div class="service">')
        body.append(f"<h2>{escape(display_name)}</h2>")
        body.extend(_resource_html(r) for r in resources)
        body.append("</div>")

    if result.high_risk:
        body.append('<div class="high-risk">')
        body.append("<h2>HIGH RISK</h2><ul>")
        for resource in result.high_risk:
            body.extend(f"<li>{escape(impact)}</li>" for impact in resource.impacts)
        body.append("</ul></div>")

    return (
        '<!doctype html><html><head><meta charset="utf-8">'
        f"<title>Terraform Plan Summary</title><style>{_STYLE}</style></head>"
        f"<body>{''.join(body)}</body></html>"
    )
