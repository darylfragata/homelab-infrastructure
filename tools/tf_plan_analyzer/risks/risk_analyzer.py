"""Deterministic risk classification for Terraform resource changes.

Risk levels are looked up from a static (resource_type, action) rule table with no
branching heuristics beyond a single cosmetic-only override. Nothing here is
AI-generated or probabilistic - the same inputs always produce the same output.
"""

from __future__ import annotations

from enum import Enum
from typing import Dict, Iterable, Tuple

from models.resource import ActionType


class RiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


# Explicit (resource_type, action) -> risk overrides. Anything not listed here
# falls back to DEFAULT_RISK_BY_ACTION. Add rows here to cover new resource
# types; never add branching logic to `assess()` itself.
RISK_RULES: Dict[Tuple[str, ActionType], RiskLevel] = {
    # HIGH
    ("aws_db_instance", ActionType.DELETE): RiskLevel.HIGH,
    ("aws_rds_cluster", ActionType.DELETE): RiskLevel.HIGH,
    ("aws_vpc", ActionType.REPLACE): RiskLevel.HIGH,
    ("aws_security_group", ActionType.REPLACE): RiskLevel.HIGH,
    ("aws_iam_role", ActionType.DELETE): RiskLevel.HIGH,
    ("aws_kms_key", ActionType.DELETE): RiskLevel.HIGH,
    ("aws_route_table", ActionType.REPLACE): RiskLevel.HIGH,
    # MEDIUM
    ("aws_lambda_function", ActionType.REPLACE): RiskLevel.MEDIUM,
    ("aws_cloudwatch_event_rule", ActionType.REPLACE): RiskLevel.MEDIUM,
    ("aws_security_group", ActionType.UPDATE): RiskLevel.MEDIUM,
    ("aws_security_group_rule", ActionType.UPDATE): RiskLevel.MEDIUM,
    ("aws_api_gateway_rest_api", ActionType.REPLACE): RiskLevel.MEDIUM,
    ("aws_dynamodb_table", ActionType.REPLACE): RiskLevel.MEDIUM,
    ("aws_subnet", ActionType.REPLACE): RiskLevel.MEDIUM,
}

# Fallback when (resource_type, action) has no explicit rule above.
DEFAULT_RISK_BY_ACTION: Dict[ActionType, RiskLevel] = {
    ActionType.CREATE: RiskLevel.LOW,
    ActionType.UPDATE: RiskLevel.LOW,
    ActionType.DELETE: RiskLevel.MEDIUM,
    ActionType.REPLACE: RiskLevel.MEDIUM,
    ActionType.READ: RiskLevel.LOW,
    ActionType.NO_OP: RiskLevel.LOW,
}

# Attribute path prefixes considered purely cosmetic (never risk-elevating on their own).
COSMETIC_ATTRIBUTE_PREFIXES = ("tags", "tags_all", "description")


def _is_cosmetic_only(changed_attribute_paths: Iterable[str]) -> bool:
    paths = list(changed_attribute_paths)
    if not paths:
        return False
    return all(_top_level_key(path) in COSMETIC_ATTRIBUTE_PREFIXES for path in paths)


def _top_level_key(path: str) -> str:
    return path.split(".", 1)[0].split("[", 1)[0]


def assess(
    resource_type: str,
    action: ActionType,
    changed_attribute_paths: Iterable[str] = (),
) -> RiskLevel:
    """Determine the risk level for a resource change.

    Precedence: an update touching only cosmetic attributes (tags/description) is
    always LOW, regardless of resource type. Otherwise an explicit rule for
    (resource_type, action) wins; failing that, the default for the action applies.
    """
    if action == ActionType.UPDATE and _is_cosmetic_only(changed_attribute_paths):
        return RiskLevel.LOW
    if (resource_type, action) in RISK_RULES:
        return RISK_RULES[(resource_type, action)]
    return DEFAULT_RISK_BY_ACTION[action]
