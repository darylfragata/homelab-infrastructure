"""Analyzer for aws_subnet resources."""

from __future__ import annotations

from analyzers.base import ResourceAnalyzer
from models.resource import ActionType

SUPPORTED_TYPES = frozenset({"aws_subnet"})


class SubnetAnalyzer(ResourceAnalyzer):
    SERVICE_KEY = "subnet"
    IMPORTANT_ATTRIBUTES = frozenset(
        {"cidr_block", "availability_zone", "map_public_ip_on_launch"}
    )
    IMPACT_TEMPLATES = {
        ActionType.CREATE: "A new subnet will be created.",
        ActionType.UPDATE: "The subnet's configuration will be updated.",
        ActionType.DELETE: (
            "The subnet will be deleted; resources placed in it may become unreachable."
        ),
        ActionType.REPLACE: (
            "The subnet will be replaced; resources placed in it will need to be "
            "recreated or reattached."
        ),
    }


ANALYZER = SubnetAnalyzer()
