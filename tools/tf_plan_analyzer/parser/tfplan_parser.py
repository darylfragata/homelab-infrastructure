"""Parses `terraform show -json` plan output into normalized ResourceChange objects.

This module ONLY converts JSON into typed objects - no analysis, risk, or
reporting logic. Malformed individual resource_changes entries are skipped
(and counted) rather than aborting the whole parse, since unsupported or
malformed resources must never fail the application. This module never reads
Terraform state and never executes Terraform - it only reads the given file.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, FrozenSet, List, Optional, Tuple, Union

from models.resource import ActionType, ResourceChange

logger = logging.getLogger(__name__)


class TfPlanParseError(Exception):
    """Raised when the plan file cannot be read or is not valid JSON."""


@dataclass
class ParsedPlan:
    """The parser's full output: plan metadata plus every normalized resource change."""

    terraform_version: Optional[str]
    format_version: Optional[str]
    resources: List[ResourceChange]
    skipped_count: int


# Every action combination a `terraform show -json` plan can emit. Both create+delete
# orderings mean "replace" - the order only reflects create_before_destroy.
_ACTION_MAP: Dict[FrozenSet[str], ActionType] = {
    frozenset(): ActionType.NO_OP,
    frozenset({"no-op"}): ActionType.NO_OP,
    frozenset({"create"}): ActionType.CREATE,
    frozenset({"update"}): ActionType.UPDATE,
    frozenset({"delete"}): ActionType.DELETE,
    frozenset({"read"}): ActionType.READ,
    frozenset({"create", "delete"}): ActionType.REPLACE,
}


def determine_action(actions: List[str]) -> ActionType:
    """Normalize a plan's raw `change.actions` list into a single ActionType.

    Falls back to NO_OP with a logged warning for anything unrecognized, rather
    than raising, so one odd entry can never abort the whole analysis.
    """
    key = frozenset(actions or [])
    if key in _ACTION_MAP:
        return _ACTION_MAP[key]
    logger.warning("Unrecognized plan actions %r; treating as no-op", actions)
    return ActionType.NO_OP


def load_plan(path: Union[str, Path]) -> Dict[str, Any]:
    """Read and JSON-decode the tfplan.json file at `path`."""
    try:
        with open(path, "r", encoding="utf-8") as handle:
            return json.load(handle)
    except FileNotFoundError as exc:
        raise TfPlanParseError(f"Plan file not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise TfPlanParseError(f"Plan file is not valid JSON: {path} ({exc})") from exc


def _parse_resource_change(raw: Dict[str, Any]) -> ResourceChange:
    change = raw["change"]
    return ResourceChange(
        address=raw["address"],
        mode=raw.get("mode", "managed"),
        resource_type=raw["type"],
        name=raw["name"],
        provider_name=raw.get("provider_name", ""),
        action=determine_action(change.get("actions", [])),
        before=change.get("before"),
        after=change.get("after"),
        after_unknown=change.get("after_unknown") or {},
    )


def parse_resource_changes(plan: Dict[str, Any]) -> Tuple[List[ResourceChange], int]:
    """Parse the `resource_changes` array, skipping (and counting) malformed entries."""
    resources: List[ResourceChange] = []
    skipped = 0
    for raw in plan.get("resource_changes", []) or []:
        try:
            resources.append(_parse_resource_change(raw))
        except (KeyError, TypeError) as exc:
            logger.warning("Skipping malformed resource_changes entry: %s", exc)
            skipped += 1
    return resources, skipped


def parse_tfplan(path: Union[str, Path]) -> ParsedPlan:
    """Load and parse a tfplan.json file into normalized ResourceChange objects."""
    plan = load_plan(path)
    resources, skipped = parse_resource_changes(plan)
    return ParsedPlan(
        terraform_version=plan.get("terraform_version"),
        format_version=plan.get("format_version"),
        resources=resources,
        skipped_count=skipped,
    )
