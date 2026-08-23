"""Analyzer for security groups and security group rules.

Needs bespoke logic (not the generic attribute diff) so port changes render as
readable "Port N" bullets - e.g. Before: Port 80, Port 443 / After: Port 443,
Port 8080 - instead of a raw list-of-dict before/after value.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from analyzers.base import ResourceAnalyzer
from models.change import AttributeChange
from models.resource import ActionType, ResourceChange

SUPPORTED_TYPES = frozenset({"aws_security_group", "aws_security_group_rule"})


def _port_label(rule: Dict[str, Any]) -> Optional[str]:
    from_port = rule.get("from_port")
    to_port = rule.get("to_port")
    if from_port is None and to_port is None:
        return None
    if to_port is None or from_port == to_port:
        return f"Port {from_port}"
    if from_port is None:
        return f"Port {to_port}"
    return f"Port {from_port}-{to_port}"


def _top_level_key(path: str) -> str:
    return path.split(".", 1)[0].split("[", 1)[0]


def _port_labels(rules: Optional[List[Dict[str, Any]]]) -> List[str]:
    if not rules:
        return []
    return [label for label in (_port_label(rule) for rule in rules) if label is not None]


class SecurityGroupAnalyzer(ResourceAnalyzer):
    SERVICE_KEY = "security_group"
    IMPACT_TEMPLATES = {
        ActionType.CREATE: "A new security group will be created.",
        ActionType.UPDATE: "Application traffic rules will change.",
        ActionType.DELETE: (
            "The security group will be deleted; any resource still referencing it "
            "may lose network access."
        ),
        ActionType.REPLACE: (
            "The security group will be replaced; dependent resources may briefly "
            "lose their network rules during recreation."
        ),
    }

    def _diff(self, change: ResourceChange) -> List[AttributeChange]:
        if change.resource_type == "aws_security_group":
            return self._diff_security_group(change)
        return self._diff_security_group_rule(change)

    def _diff_security_group(self, change: ResourceChange) -> List[AttributeChange]:
        before = change.before or {}
        after = change.after or {}
        changes: List[AttributeChange] = []
        for direction in ("ingress", "egress"):
            before_labels = _port_labels(before.get(direction))
            after_labels = _port_labels(after.get(direction))
            if before_labels != after_labels:
                changes.append(
                    AttributeChange(path=direction, before=before_labels, after=after_labels)
                )
        # Fall back to the generic diff for anything besides ingress/egress
        # (name, description, vpc_id, ...) so those changes aren't dropped.
        # super()._diff() recurses into list-of-dict attributes, so "ingress"
        # also shows up as e.g. "ingress[0].from_port" - filter by top-level
        # key, not exact path, to avoid duplicating the port summary above.
        changes.extend(
            c for c in super()._diff(change) if _top_level_key(c.path) not in ("ingress", "egress")
        )
        return changes

    def _diff_security_group_rule(self, change: ResourceChange) -> List[AttributeChange]:
        before = change.before or {}
        after = change.after or {}
        before_label = _port_label(before) if before else None
        after_label = _port_label(after) if after else None
        changes: List[AttributeChange] = []
        if before_label != after_label:
            changes.append(AttributeChange(path="port", before=before_label, after=after_label))
        changes.extend(
            c
            for c in super()._diff(change)
            if _top_level_key(c.path) not in ("from_port", "to_port")
        )
        return changes


ANALYZER = SecurityGroupAnalyzer()
