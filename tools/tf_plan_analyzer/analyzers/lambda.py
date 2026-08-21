"""Analyzer for aws_lambda_function resources.

Note: this file is named lambda.py per the project's required structure, even
though `lambda` is a Python keyword. It is never imported with a normal
`import`/`from...import` statement - analyzers/registry.py loads it via
importlib.import_module("analyzers.lambda"), which works fine since that API
takes a plain string.
"""

from __future__ import annotations

from typing import List

from analyzers.base import ResourceAnalyzer
from models.change import AttributeChange
from models.resource import ActionType, ResourceChange

SUPPORTED_TYPES = frozenset({"aws_lambda_function"})


class LambdaAnalyzer(ResourceAnalyzer):
    SERVICE_KEY = "lambda"
    IMPORTANT_ATTRIBUTES = frozenset(
        {"runtime", "memory_size", "timeout", "handler", "environment", "layers"}
    )
    IMPACT_TEMPLATES = {
        ActionType.CREATE: "A new Lambda function will be created.",
        ActionType.UPDATE: "The Lambda function's configuration will be updated.",
        ActionType.DELETE: (
            "The Lambda function will be deleted and will stop processing invocations."
        ),
        ActionType.REPLACE: (
            "The Lambda function will be replaced, causing a brief gap in availability "
            "during recreation."
        ),
    }

    def _diff(self, change: ResourceChange) -> List[AttributeChange]:
        return [self._format(c) for c in super()._diff(change)]

    @staticmethod
    def _format(change: AttributeChange) -> AttributeChange:
        if change.path == "memory_size" and change.after is not None:
            return AttributeChange(
                path=change.path,
                before=change.before,
                after=change.after,
                display=f"memory = {change.after} MB",
            )
        if change.path == "runtime" and change.after is not None:
            return AttributeChange(
                path=change.path,
                before=change.before,
                after=change.after,
                display=f"runtime = {change.after}",
            )
        return change


ANALYZER = LambdaAnalyzer()
