"""Analyzer for VPC-level networking resources (VPC, gateways, route tables)."""

from __future__ import annotations

from analyzers.base import ResourceAnalyzer
from models.resource import ActionType

SUPPORTED_TYPES = frozenset(
    {
        "aws_vpc",
        "aws_internet_gateway",
        "aws_route_table",
        "aws_route",
        "aws_route_table_association",
        "aws_nat_gateway",
    }
)


class VpcAnalyzer(ResourceAnalyzer):
    SERVICE_KEY = "vpc"
    IMPORTANT_ATTRIBUTES = frozenset(
        {
            "cidr_block",
            "enable_dns_hostnames",
            "enable_dns_support",
            "destination_cidr_block",
            "gateway_id",
        }
    )
    IMPACT_TEMPLATES = {
        ActionType.CREATE: "A new VPC networking resource will be created.",
        ActionType.UPDATE: "The VPC networking configuration will be updated.",
        ActionType.DELETE: (
            "The VPC networking resource will be deleted, which may disconnect "
            "dependent resources."
        ),
        ActionType.REPLACE: (
            "The VPC networking resource will be replaced; dependent resources may "
            "experience network downtime."
        ),
    }


ANALYZER = VpcAnalyzer()
