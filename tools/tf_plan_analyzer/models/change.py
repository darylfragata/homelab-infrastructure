"""Models representing analyzed, human-readable results derived from a ResourceChange."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from models.resource import ActionType
from risks.risk_analyzer import RiskLevel


@dataclass(frozen=True)
class AttributeChange:
    """A single before/after attribute difference.

    `before`/`after` are usually scalars but may be lists (e.g. a security group's
    port list) - reporters render list-valued changes as nested Before/After bullets.
    `display` is an optional analyzer-formatted label (e.g. "memory = 256 MB");
    reporters fall back to "{path} = {after}" when it is not set.
    """

    path: str
    before: Any
    after: Any
    display: Optional[str] = None


@dataclass
class AnalyzedResource:
    """The output of a service analyzer for one resource change."""

    address: str
    resource_type: str
    name: str
    service: str
    action: ActionType
    attribute_changes: List[AttributeChange]
    impacts: List[str]
    dependencies: List[str]
    risk: Optional[RiskLevel] = None


@dataclass
class ChangeSummary:
    """Aggregate counts of resources by action, for the report header."""

    create: int = 0
    update: int = 0
    delete: int = 0
    replace: int = 0
    no_op: int = 0

    @classmethod
    def from_resources(cls, resources: List[AnalyzedResource]) -> "ChangeSummary":
        summary = cls()
        for resource in resources:
            if resource.action == ActionType.CREATE:
                summary.create += 1
            elif resource.action == ActionType.UPDATE:
                summary.update += 1
            elif resource.action == ActionType.DELETE:
                summary.delete += 1
            elif resource.action == ActionType.REPLACE:
                summary.replace += 1
            else:
                summary.no_op += 1
        return summary


@dataclass
class PlanAnalysis:
    """Top-level aggregate consumed by every reporter."""

    source_path: str
    terraform_version: Optional[str]
    resources: List[AnalyzedResource]
    summary: ChangeSummary
    skipped_count: int = 0

    @property
    def high_risk(self) -> List[AnalyzedResource]:
        return [r for r in self.resources if r.risk == RiskLevel.HIGH]
