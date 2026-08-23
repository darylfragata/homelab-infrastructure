"""Base interface every service analyzer implements."""

from __future__ import annotations

from abc import ABC
from typing import Dict, FrozenSet, List

from models.change import AnalyzedResource, AttributeChange
from models.resource import ActionType, ResourceChange
from utils.helpers import extract_dependency_hints, flatten_diff

# Generic, resource-type-agnostic impact text used whenever a subclass doesn't
# override IMPACT_TEMPLATES for a given action.
DEFAULT_IMPACT_TEMPLATES: Dict[ActionType, str] = {
    ActionType.CREATE: "A new resource will be created.",
    ActionType.UPDATE: "The resource will be updated in place.",
    ActionType.DELETE: "The resource will be deleted.",
    ActionType.REPLACE: "The resource will be replaced (destroyed and recreated).",
    ActionType.READ: "The data source will be read.",
    ActionType.NO_OP: "No changes will be applied to this resource.",
}


class ResourceAnalyzer(ABC):
    """Turns a raw ResourceChange into a human-readable AnalyzedResource.

    Subclasses declare SERVICE_KEY / IMPORTANT_ATTRIBUTES / IMPACT_TEMPLATES.
    Risk is intentionally never set here - it is assigned centrally by
    analyzers/registry.py so every resource gets the same (type, action) -> risk
    rule regardless of which analyzer produced it.
    """

    SERVICE_KEY: str = "generic"
    # Empty set means "no filtering" (used by generic.py to show the full diff).
    IMPORTANT_ATTRIBUTES: FrozenSet[str] = frozenset()
    IMPACT_TEMPLATES: Dict[ActionType, str] = {}

    def analyze(self, change: ResourceChange) -> AnalyzedResource:
        return AnalyzedResource(
            address=change.address,
            resource_type=change.resource_type,
            name=change.name,
            service=self.SERVICE_KEY,
            action=change.action,
            attribute_changes=self._diff(change),
            impacts=self._impacts(change),
            dependencies=extract_dependency_hints(change.after),
        )

    def _diff(self, change: ResourceChange) -> List[AttributeChange]:
        changes = flatten_diff(change.before, change.after)
        if not self.IMPORTANT_ATTRIBUTES:
            return changes
        return [
            c
            for c in changes
            if c.path.split(".", 1)[0].split("[", 1)[0] in self.IMPORTANT_ATTRIBUTES
        ]

    def _impacts(self, change: ResourceChange) -> List[str]:
        template = self.IMPACT_TEMPLATES.get(change.action) or DEFAULT_IMPACT_TEMPLATES.get(
            change.action
        )
        return [template] if template else []
