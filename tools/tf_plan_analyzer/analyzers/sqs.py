"""Analyzer for aws_sqs_queue resources."""

from __future__ import annotations

from analyzers.base import ResourceAnalyzer
from models.resource import ActionType

SUPPORTED_TYPES = frozenset({"aws_sqs_queue"})


class SqsAnalyzer(ResourceAnalyzer):
    SERVICE_KEY = "sqs"
    IMPORTANT_ATTRIBUTES = frozenset(
        {
            "visibility_timeout_seconds",
            "message_retention_seconds",
            "fifo_queue",
            "redrive_policy",
            "delay_seconds",
        }
    )
    IMPACT_TEMPLATES = {
        ActionType.CREATE: "A new SQS queue will be created.",
        ActionType.UPDATE: "The SQS queue's configuration will be updated.",
        ActionType.DELETE: (
            "The SQS queue will be deleted; any queued or in-flight messages will be lost."
        ),
        ActionType.REPLACE: (
            "The SQS queue will be replaced under a new identity; queued messages will be lost."
        ),
    }


ANALYZER = SqsAnalyzer()
