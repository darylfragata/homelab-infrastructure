import json

import pytest

from models.resource import ActionType
from parser.tfplan_parser import (
    TfPlanParseError,
    determine_action,
    load_plan,
    parse_resource_changes,
    parse_tfplan,
)


@pytest.mark.parametrize(
    "actions,expected",
    [
        (["create"], ActionType.CREATE),
        (["update"], ActionType.UPDATE),
        (["delete"], ActionType.DELETE),
        (["read"], ActionType.READ),
        (["no-op"], ActionType.NO_OP),
        ([], ActionType.NO_OP),
        (["create", "delete"], ActionType.REPLACE),
        (["delete", "create"], ActionType.REPLACE),
    ],
)
def test_determine_action(actions, expected):
    assert determine_action(actions) == expected


def test_determine_action_unrecognized_falls_back_to_no_op():
    assert determine_action(["update", "delete"]) == ActionType.NO_OP


def test_load_plan_missing_file_raises_parse_error(tmp_path):
    missing = tmp_path / "does-not-exist.json"
    with pytest.raises(TfPlanParseError):
        load_plan(missing)


def test_load_plan_invalid_json_raises_parse_error(tmp_path):
    bad_file = tmp_path / "tfplan.json"
    bad_file.write_text("{not valid json", encoding="utf-8")
    with pytest.raises(TfPlanParseError):
        load_plan(bad_file)


def test_parse_resource_changes_basic_create():
    plan = {
        "resource_changes": [
            {
                "address": "aws_s3_bucket.site",
                "mode": "managed",
                "type": "aws_s3_bucket",
                "name": "site",
                "provider_name": "registry.terraform.io/hashicorp/aws",
                "change": {
                    "actions": ["create"],
                    "before": None,
                    "after": {"bucket": "my-bucket"},
                    "after_unknown": {"id": True},
                },
            }
        ]
    }
    resources, skipped = parse_resource_changes(plan)
    assert skipped == 0
    assert len(resources) == 1
    resource = resources[0]
    assert resource.address == "aws_s3_bucket.site"
    assert resource.resource_type == "aws_s3_bucket"
    assert resource.action == ActionType.CREATE
    assert resource.before is None
    assert resource.after == {"bucket": "my-bucket"}


def test_parse_resource_changes_skips_malformed_entries_without_crashing():
    plan = {
        "resource_changes": [
            {"address": "missing.change.field"},
            {
                "address": "aws_s3_bucket.site",
                "mode": "managed",
                "type": "aws_s3_bucket",
                "name": "site",
                "provider_name": "registry.terraform.io/hashicorp/aws",
                "change": {"actions": ["create"], "before": None, "after": {}, "after_unknown": {}},
            },
        ]
    }
    resources, skipped = parse_resource_changes(plan)
    assert skipped == 1
    assert len(resources) == 1


def test_parse_resource_changes_missing_key_entirely():
    assert parse_resource_changes({}) == ([], 0)


def test_parse_tfplan_end_to_end(tmp_path):
    plan = {
        "format_version": "1.2",
        "terraform_version": "1.7.5",
        "resource_changes": [
            {
                "address": "aws_s3_bucket.site",
                "mode": "managed",
                "type": "aws_s3_bucket",
                "name": "site",
                "provider_name": "registry.terraform.io/hashicorp/aws",
                "change": {
                    "actions": ["create"],
                    "before": None,
                    "after": {"bucket": "my-bucket"},
                    "after_unknown": {},
                },
            }
        ],
    }
    plan_path = tmp_path / "tfplan.json"
    plan_path.write_text(json.dumps(plan), encoding="utf-8")

    parsed = parse_tfplan(plan_path)
    assert parsed.terraform_version == "1.7.5"
    assert parsed.format_version == "1.2"
    assert parsed.skipped_count == 0
    assert len(parsed.resources) == 1
