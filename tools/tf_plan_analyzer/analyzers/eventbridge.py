"""Analyzer for EventBridge (CloudWatch Events) rules and targets."""

from __future__ import annotations

from analyzers.base import ResourceAnalyzer
from models.resource import ActionType

SUPPORTED_TYPES = frozenset({"aws_cloudwatch_event_rule", "aws_cloudwatch_event_target"})


class EventBridgeAnalyzer(ResourceAnalyzer):
    SERVICE_KEY = "eventbridge"
    IMPORTANT_ATTRIBUTES = frozenset({"schedule_expression", "event_pattern", "state", "arn"})
    IMPACT_TEMPLATES = {
        ActionType.CREATE: "A new EventBridge rule will be created.",
        ActionType.UPDATE: "The EventBridge rule's schedule or event pattern will be updated.",
        ActionType.DELETE: (
            "The EventBridge rule will be deleted and will stop triggering its targets."
        ),
        ActionType.REPLACE: (
            "The EventBridge rule will be replaced, briefly interrupting scheduled or "
            "event-driven triggers."
        ),
    }


ANALYZER = EventBridgeAnalyzer()
