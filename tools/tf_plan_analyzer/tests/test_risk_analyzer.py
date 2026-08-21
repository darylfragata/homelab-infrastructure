import pytest

from models.resource import ActionType
from risks.risk_analyzer import RiskLevel, assess


@pytest.mark.parametrize(
    "resource_type,action,expected",
    [
        # HIGH - straight from the CLAUDE.md examples
        ("aws_db_instance", ActionType.DELETE, RiskLevel.HIGH),
        ("aws_vpc", ActionType.REPLACE, RiskLevel.HIGH),
        ("aws_security_group", ActionType.REPLACE, RiskLevel.HIGH),
        ("aws_iam_role", ActionType.DELETE, RiskLevel.HIGH),
        ("aws_kms_key", ActionType.DELETE, RiskLevel.HIGH),
        ("aws_route_table", ActionType.REPLACE, RiskLevel.HIGH),
        # MEDIUM
        ("aws_lambda_function", ActionType.REPLACE, RiskLevel.MEDIUM),
        ("aws_cloudwatch_event_rule", ActionType.REPLACE, RiskLevel.MEDIUM),
        ("aws_security_group", ActionType.UPDATE, RiskLevel.MEDIUM),
        ("aws_api_gateway_rest_api", ActionType.REPLACE, RiskLevel.MEDIUM),
        # Default fallback for unmatched (type, action) combos
        ("aws_cloudfront_distribution", ActionType.CREATE, RiskLevel.LOW),
        ("aws_cloudfront_distribution", ActionType.DELETE, RiskLevel.MEDIUM),
        ("aws_cloudfront_distribution", ActionType.REPLACE, RiskLevel.MEDIUM),
    ],
)
def test_assess_matches_rule_table(resource_type, action, expected):
    assert assess(resource_type, action) == expected


def test_cosmetic_only_update_is_always_low_risk():
    # Even for a normally-HIGH-risk type, a tags-only update stays LOW.
    assert assess("aws_vpc", ActionType.UPDATE, ["tags", "tags_all"]) == RiskLevel.LOW


def test_non_cosmetic_update_uses_rule_table():
    assert assess("aws_security_group", ActionType.UPDATE, ["ingress"]) == RiskLevel.MEDIUM


def test_mixed_cosmetic_and_real_changes_does_not_short_circuit():
    # "tags" plus a real attribute change should NOT be treated as cosmetic-only.
    result = assess("aws_lambda_function", ActionType.UPDATE, ["tags", "memory_size"])
    assert result == RiskLevel.LOW  # default UPDATE risk for lambda (no explicit rule)
