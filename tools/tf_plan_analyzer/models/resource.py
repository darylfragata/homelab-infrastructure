"""Models representing a single parsed resource change from a Terraform plan."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Optional


class ActionType(str, Enum):
    """Normalized action performed on a resource, derived from the plan's raw action list."""

    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    REPLACE = "replace"
    READ = "read"
    NO_OP = "no-op"


@dataclass(frozen=True)
class ResourceChange:
    """A single resource_changes[] entry from `terraform show -json`, normalized.

    Purely structural: no derived/analyzed data lives here. Resource dependencies,
    attribute diffs, impacts, and risk are all computed later by analyzers/risk_analyzer.
    """

    address: str
    mode: str
    resource_type: str
    name: str
    provider_name: str
    action: ActionType
    before: Optional[Dict[str, Any]]
    after: Optional[Dict[str, Any]]
    after_unknown: Dict[str, Any] = field(default_factory=dict)
