"""Analyzer for S3 buckets and their sub-resource configurations."""

from __future__ import annotations

from analyzers.base import ResourceAnalyzer
from models.resource import ActionType

SUPPORTED_TYPES = frozenset(
    {
        "aws_s3_bucket",
        "aws_s3_bucket_versioning",
        "aws_s3_bucket_public_access_block",
        "aws_s3_bucket_server_side_encryption_configuration",
        "aws_s3_bucket_policy",
    }
)


class S3Analyzer(ResourceAnalyzer):
    SERVICE_KEY = "s3"
    IMPORTANT_ATTRIBUTES = frozenset(
        {
            "bucket",
            "versioning_configuration",
            "block_public_acls",
            "block_public_policy",
            "ignore_public_acls",
            "restrict_public_buckets",
            "rule",
            "policy",
        }
    )
    IMPACT_TEMPLATES = {
        ActionType.CREATE: "A new S3 bucket or bucket configuration will be created.",
        ActionType.UPDATE: "The S3 bucket's configuration will be updated.",
        ActionType.DELETE: "The S3 bucket or its configuration will be deleted.",
        ActionType.REPLACE: (
            "The S3 bucket will be replaced; if it is not empty, replacement can fail "
            "or result in data loss."
        ),
    }


ANALYZER = S3Analyzer()
