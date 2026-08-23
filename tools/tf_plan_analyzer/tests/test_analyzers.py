import importlib

from analyzers.generic import ANALYZER as GENERIC_ANALYZER
from analyzers.security_group import ANALYZER as SECURITY_GROUP_ANALYZER
from models.resource import ActionType, ResourceChange

# analyzers/lambda.py can't be imported with a normal `from analyzers import lambda`
# statement - `lambda` is a Python keyword - so it's loaded dynamically here, the
# same way analyzers/registry.py loads every analyzer module.
_lambda_module = importlib.import_module("analyzers.lambda")
LAMBDA_ANALYZER = _lambda_module.ANALYZER


def _change(resource_type, action, before=None, after=None, address=None, name="example"):
    return ResourceChange(
        address=address or f"{resource_type}.{name}",
        mode="managed",
        resource_type=resource_type,
        name=name,
        provider_name="registry.terraform.io/hashicorp/aws",
        action=action,
        before=before,
        after=after,
    )


def test_generic_analyzer_handles_unknown_type_without_crashing():
    change = _change(
        "aws_budgets_budget",
        ActionType.CREATE,
        before=None,
        after={"budget_type": "COST", "limit_amount": "50"},
    )
    result = GENERIC_ANALYZER.analyze(change)
    assert result.service == "generic"
    assert result.resource_type == "aws_budgets_budget"
    paths = {c.path for c in result.attribute_changes}
    assert {"budget_type", "limit_amount"} <= paths
    assert result.impacts
    assert result.risk is None  # risk is assigned centrally by the registry, not here


def test_lambda_analyzer_formats_memory_and_runtime():
    change = _change(
        "aws_lambda_function",
        ActionType.REPLACE,
        before={"runtime": "python3.12", "memory_size": 128},
        after={"runtime": "python3.13", "memory_size": 256},
    )
    result = LAMBDA_ANALYZER.analyze(change)
    displays = {c.path: c.display for c in result.attribute_changes}
    assert displays["runtime"] == "runtime = python3.13"
    assert displays["memory_size"] == "memory = 256 MB"


def test_lambda_analyzer_filters_to_important_attributes_only():
    change = _change(
        "aws_lambda_function",
        ActionType.UPDATE,
        before={"memory_size": 128, "role": "arn:aws:iam::123:role/old"},
        after={"memory_size": 256, "role": "arn:aws:iam::123:role/old"},
    )
    result = LAMBDA_ANALYZER.analyze(change)
    paths = {c.path for c in result.attribute_changes}
    assert paths == {"memory_size"}


def test_security_group_analyzer_renders_port_lists():
    change = _change(
        "aws_security_group",
        ActionType.UPDATE,
        before={
            "name": "app-sg",
            "ingress": [
                {"from_port": 80, "to_port": 80},
                {"from_port": 443, "to_port": 443},
            ],
        },
        after={
            "name": "app-sg",
            "ingress": [
                {"from_port": 443, "to_port": 443},
                {"from_port": 8080, "to_port": 8080},
            ],
        },
    )
    result = SECURITY_GROUP_ANALYZER.analyze(change)
    ingress_change = next(c for c in result.attribute_changes if c.path == "ingress")
    assert ingress_change.before == ["Port 80", "Port 443"]
    assert ingress_change.after == ["Port 443", "Port 8080"]
    assert "name" not in {c.path for c in result.attribute_changes}


def test_security_group_rule_analyzer_renders_single_port():
    change = _change(
        "aws_security_group_rule",
        ActionType.UPDATE,
        before={"from_port": 80, "to_port": 80, "type": "ingress"},
        after={"from_port": 8080, "to_port": 8080, "type": "ingress"},
    )
    result = SECURITY_GROUP_ANALYZER.analyze(change)
    port_change = next(c for c in result.attribute_changes if c.path == "port")
    assert port_change.before == "Port 80"
    assert port_change.after == "Port 8080"


def test_registry_dispatches_by_resource_type_and_falls_back_to_generic():
    from analyzers.registry import get_analyzer

    assert type(get_analyzer("aws_lambda_function")).__name__ == "LambdaAnalyzer"
    assert type(get_analyzer("aws_security_group")).__name__ == "SecurityGroupAnalyzer"
    assert get_analyzer("aws_some_unmapped_future_resource") is GENERIC_ANALYZER


def test_registry_analyze_all_assigns_risk_and_skips_data_sources_and_no_ops():
    from analyzers.registry import analyze_all

    resources = [
        _change(
            "aws_vpc",
            ActionType.REPLACE,
            before={"cidr_block": "10.0.0.0/16"},
            after={"cidr_block": "10.1.0.0/16"},
            address="module.vpc.aws_vpc.main",
        ),
        ResourceChange(
            address="data.aws_availability_zones.available",
            mode="data",
            resource_type="aws_availability_zones",
            name="available",
            provider_name="registry.terraform.io/hashicorp/aws",
            action=ActionType.READ,
            before=None,
            after=None,
        ),
        ResourceChange(
            address="aws_s3_bucket.untouched",
            mode="managed",
            resource_type="aws_s3_bucket",
            name="untouched",
            provider_name="registry.terraform.io/hashicorp/aws",
            action=ActionType.NO_OP,
            before={"bucket": "x"},
            after={"bucket": "x"},
        ),
    ]
    analyzed = analyze_all(resources)
    assert len(analyzed) == 1
    assert analyzed[0].resource_type == "aws_vpc"
    from risks.risk_analyzer import RiskLevel

    assert analyzed[0].risk == RiskLevel.HIGH


def test_registry_includes_data_sources_when_requested():
    from analyzers.registry import analyze_all

    data_source = ResourceChange(
        address="data.aws_availability_zones.available",
        mode="data",
        resource_type="aws_availability_zones",
        name="available",
        provider_name="registry.terraform.io/hashicorp/aws",
        action=ActionType.READ,
        before=None,
        after=None,
    )
    analyzed = analyze_all([data_source], include_data_sources=True)
    assert len(analyzed) == 1


def test_uncovered_resource_types_lists_only_unmapped_managed_types():
    from analyzers.registry import uncovered_resource_types

    resources = [
        _change("aws_lambda_function", ActionType.CREATE, after={}),  # covered
        _change("aws_budgets_budget", ActionType.CREATE, after={}),  # not covered
        _change(
            "aws_cloudfront_distribution", ActionType.CREATE, after={}
        ),  # not covered, duplicate type
        _change("aws_cloudfront_distribution", ActionType.UPDATE, after={}),
        ResourceChange(
            address="data.aws_ami.latest",
            mode="data",
            resource_type="aws_ami",
            name="latest",
            provider_name="registry.terraform.io/hashicorp/aws",
            action=ActionType.READ,
            before=None,
            after=None,
        ),  # data source excluded regardless of coverage
    ]
    assert uncovered_resource_types(resources) == [
        "aws_budgets_budget",
        "aws_cloudfront_distribution",
    ]


def test_uncovered_resource_types_empty_when_fully_covered():
    from analyzers.registry import uncovered_resource_types

    resources = [_change("aws_lambda_function", ActionType.CREATE, after={})]
    assert uncovered_resource_types(resources) == []
