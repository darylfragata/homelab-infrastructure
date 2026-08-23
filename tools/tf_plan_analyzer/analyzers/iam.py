"""Analyzer for IAM identities, policies, attachments, and permission grants."""

from __future__ import annotations

from analyzers.base import ResourceAnalyzer
from models.resource import ActionType

SUPPORTED_TYPES = frozenset(
    {
        "aws_iam_role",
        "aws_iam_policy",
        "aws_iam_role_policy",
        "aws_iam_role_policy_attachment",
        "aws_iam_user",
        "aws_iam_user_policy",
        "aws_iam_user_policy_attachment",
        "aws_iam_group",
        "aws_iam_group_policy",
        "aws_iam_group_policy_attachment",
        "aws_iam_instance_profile",
        "aws_iam_access_key",
        "aws_iam_service_linked_role",
        "aws_iam_openid_connect_provider",
        "aws_iam_saml_provider",
        # Resource-based permission grants - conceptually IAM even though they
        # attach to a non-IAM resource (e.g. a Lambda function or S3 bucket).
        "aws_lambda_permission",
    }
)


class IamAnalyzer(ResourceAnalyzer):
    SERVICE_KEY = "iam"
    IMPORTANT_ATTRIBUTES = frozenset(
        {
            "assume_role_policy",
            "policy",
            "managed_policy_arns",
            "policy_arn",
            "name",
            "role",
            "user",
            "group",
            "path",
            "principal",
            "action",
            "function_name",
            "status",
        }
    )
    IMPACT_TEMPLATES = {
        ActionType.CREATE: "A new IAM identity or policy will be created.",
        ActionType.UPDATE: (
            "The IAM permissions will be updated, changing what this identity can access."
        ),
        ActionType.DELETE: (
            "The IAM identity or policy will be deleted; anything relying on it will lose access."
        ),
        ActionType.REPLACE: (
            "The IAM identity or policy will be replaced, temporarily revoking and "
            "reissuing access."
        ),
    }


ANALYZER = IamAnalyzer()
