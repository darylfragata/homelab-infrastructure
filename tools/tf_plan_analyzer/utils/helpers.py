"""Shared, deterministic helpers used by analyzers: attribute diffing, dependency
hints, and service grouping/display-name lookup for reporters.
"""

from __future__ import annotations

from typing import Any, Dict, FrozenSet, List, Optional

from models.change import AnalyzedResource, AttributeChange

# Terraform attribute-name suffixes that typically reference another resource.
# Best-effort, deterministic string matching only - not a resolved dependency
# graph (that would require parsing the plan's `configuration` block, which is
# out of scope for v1).
_DEPENDENCY_HINT_SUFFIXES = ("_id", "_arn", "_ids", "_arns")

SERVICE_DISPLAY_NAMES: Dict[str, str] = {
    "lambda": "Lambda",
    "sqs": "SQS",
    "eventbridge": "EventBridge",
    "iam": "IAM",
    "security_group": "Security Group",
    "s3": "S3",
    "vpc": "VPC",
    "subnet": "Subnet",
    "dynamodb": "DynamoDB",
    "generic": "Other",
}


def flatten_diff(
    before: Optional[Dict[str, Any]],
    after: Optional[Dict[str, Any]],
    ignore_keys: FrozenSet[str] = frozenset(),
    _prefix: str = "",
) -> List[AttributeChange]:
    """Recursively diff two attribute dicts into a flat list of AttributeChange.

    Nested dicts are recursed into with a dotted path. Same-length lists of dicts
    are compared elementwise by index. Everything else (scalars, mismatched-length
    lists, lists of scalars) is compared as a whole value. This is a deliberate
    simplification: no reordering/set-aware list diffing is attempted.
    """
    before = before or {}
    after = after or {}
    changes: List[AttributeChange] = []

    for key in sorted(set(before) | set(after)):
        if not _prefix and key in ignore_keys:
            continue
        b, a = before.get(key), after.get(key)
        if b == a:
            continue
        path = f"{_prefix}{key}"
        if isinstance(b, dict) and isinstance(a, dict):
            changes.extend(flatten_diff(b, a, _prefix=f"{path}."))
        elif (
            isinstance(b, list)
            and isinstance(a, list)
            and len(b) == len(a)
            and all(isinstance(item, dict) for item in b + a)
        ):
            for index, (b_item, a_item) in enumerate(zip(b, a)):
                changes.extend(flatten_diff(b_item, a_item, _prefix=f"{path}[{index}]."))
        else:
            changes.append(AttributeChange(path=path, before=b, after=a))

    return changes


def extract_dependency_hints(after: Optional[Dict[str, Any]]) -> List[str]:
    """Best-effort list of "attribute -> value" hints pointing at other resources.

    Matches top-level attribute names ending in _id/_arn/_ids/_arns (e.g. vpc_id,
    role_arn, security_group_ids). This is a heuristic placeholder, not a real
    dependency graph.
    """
    if not after:
        return []

    hints: List[str] = []
    for key in sorted(after):
        if not key.endswith(_DEPENDENCY_HINT_SUFFIXES):
            continue
        value = after[key]
        if value in (None, "", []):
            continue
        if isinstance(value, list):
            hints.extend(f"{key} -> {item}" for item in value if item)
        else:
            hints.append(f"{key} -> {value}")
    return hints


def group_by_service(resources: List[AnalyzedResource]) -> Dict[str, List[AnalyzedResource]]:
    """Group analyzed resources by service key, ordered by display name."""
    groups: Dict[str, List[AnalyzedResource]] = {}
    for resource in resources:
        groups.setdefault(resource.service, []).append(resource)
    return dict(
        sorted(groups.items(), key=lambda item: SERVICE_DISPLAY_NAMES.get(item[0], item[0]))
    )
