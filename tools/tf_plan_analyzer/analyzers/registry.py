"""Maps a Terraform resource type to the analyzer that should handle it.

Uses dynamic module discovery (importlib.import_module by string name) rather
than static `from analyzers import lambda` imports, because `lambda` is a
Python keyword and analyzers/lambda.py could otherwise never be imported with
ordinary import syntax. Dropping a new analyzer module into this package (with
a SUPPORTED_TYPES set and an ANALYZER instance) is enough to register it -
nothing else in this file, or in the parser, needs to change.
"""

from __future__ import annotations

import importlib
import logging
import pkgutil
from typing import Dict, List

import analyzers
from analyzers.base import ResourceAnalyzer
from analyzers.generic import ANALYZER as GENERIC_ANALYZER
from models.change import AnalyzedResource
from models.resource import ActionType, ResourceChange
from risks.risk_analyzer import assess

logger = logging.getLogger(__name__)

_EXCLUDED_MODULES = {"base", "registry", "generic"}


def _discover() -> Dict[str, ResourceAnalyzer]:
    mapping: Dict[str, ResourceAnalyzer] = {}
    for module_info in pkgutil.iter_modules(analyzers.__path__):
        name = module_info.name
        if name in _EXCLUDED_MODULES:
            continue
        module = importlib.import_module(f"analyzers.{name}")
        supported_types = getattr(module, "SUPPORTED_TYPES", frozenset())
        module_analyzer = getattr(module, "ANALYZER", None)
        if not supported_types or module_analyzer is None:
            continue
        for resource_type in supported_types:
            if resource_type in mapping:
                logger.warning(
                    "Resource type %s already mapped to %s; %s overrides it",
                    resource_type,
                    type(mapping[resource_type]).__name__,
                    name,
                )
            mapping[resource_type] = module_analyzer
    return mapping


_ANALYZERS_BY_TYPE: Dict[str, ResourceAnalyzer] = _discover()


def get_analyzer(resource_type: str) -> ResourceAnalyzer:
    """Return the analyzer registered for `resource_type`, or the generic fallback."""
    return _ANALYZERS_BY_TYPE.get(resource_type, GENERIC_ANALYZER)


def uncovered_resource_types(resources: List[ResourceChange]) -> List[str]:
    """Sorted, deduplicated resource types present in `resources` that have no
    dedicated analyzer and would fall back to generic.py.

    Useful when pointing this tool at a new/unfamiliar codebase: run this
    first to see which resource types are worth writing a dedicated analyzer
    (and risk rule) for, versus what's already covered.
    """
    return sorted(
        {
            change.resource_type
            for change in resources
            if change.mode == "managed" and change.resource_type not in _ANALYZERS_BY_TYPE
        }
    )


def analyze_all(
    resources: List[ResourceChange], include_data_sources: bool = False
) -> List[AnalyzedResource]:
    """Analyze every resource change and assign its risk level centrally.

    Risk is assigned here - not inside individual analyzers - so the same
    (resource_type, action) always yields the same risk regardless of which
    analyzer produced the AnalyzedResource. An analyzer raising an unexpected
    error falls back to the generic analyzer rather than aborting the run.
    Data sources (mode == "data") and no-op resources are excluded by default
    since they represent no actual infrastructure change to report.
    """
    analyzed: List[AnalyzedResource] = []
    for change in resources:
        if change.mode != "managed" and not include_data_sources:
            continue
        if change.action == ActionType.NO_OP:
            continue

        analyzer = get_analyzer(change.resource_type)
        try:
            result = analyzer.analyze(change)
        except Exception:
            logger.exception(
                "Analyzer %s failed for %s; falling back to generic",
                type(analyzer).__name__,
                change.address,
            )
            result = GENERIC_ANALYZER.analyze(change)

        result.risk = assess(
            change.resource_type,
            change.action,
            [c.path for c in result.attribute_changes],
        )
        analyzed.append(result)
    return analyzed
