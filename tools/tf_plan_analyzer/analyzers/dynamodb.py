"""Analyzer for aws_dynamodb_table resources."""

from __future__ import annotations

from analyzers.base import ResourceAnalyzer
from models.resource import ActionType

SUPPORTED_TYPES = frozenset({"aws_dynamodb_table"})


class DynamoDbAnalyzer(ResourceAnalyzer):
    SERVICE_KEY = "dynamodb"
    IMPORTANT_ATTRIBUTES = frozenset(
        {
            "billing_mode",
            "read_capacity",
            "write_capacity",
            "stream_enabled",
            "stream_view_type",
            "attribute",
            "hash_key",
            "range_key",
        }
    )
    IMPACT_TEMPLATES = {
        ActionType.CREATE: "A new DynamoDB table will be created.",
        ActionType.UPDATE: "The DynamoDB table's configuration will be updated.",
        ActionType.DELETE: "The DynamoDB table will be deleted, permanently removing its data.",
        ActionType.REPLACE: (
            "The DynamoDB table will be replaced, which recreates it and can result "
            "in data loss."
        ),
    }


ANALYZER = DynamoDbAnalyzer()
