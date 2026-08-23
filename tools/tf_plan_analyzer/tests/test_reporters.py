from pathlib import Path

from analyzers.registry import analyze_all
from models.change import ChangeSummary, PlanAnalysis
from parser.tfplan_parser import parse_tfplan
from reporters import html as html_reporter
from reporters import markdown as markdown_reporter
from reporters import pipeline as pipeline_reporter

FIXTURES = Path(__file__).parent / "fixtures"


def _analysis(fixture_name: str) -> PlanAnalysis:
    parsed = parse_tfplan(FIXTURES / fixture_name)
    resources = analyze_all(parsed.resources)
    return PlanAnalysis(
        source_path=fixture_name,
        terraform_version=parsed.terraform_version,
        resources=resources,
        summary=ChangeSummary.from_resources(resources),
        skipped_count=parsed.skipped_count,
    )


def test_markdown_report_matches_expected_structure():
    analysis = _analysis("tfplan_core_mixed.json")
    report = markdown_reporter.render(analysis)

    assert "Terraform Plan Summary" in report
    assert "Resources to Create : 1" in report
    assert "Resources to Update : 1" in report
    assert "Resources to Delete : 1" in report
    assert "Resources to Replace : 2" in report
    assert "Before:" in report
    assert "- Port 80" in report
    assert "After:" in report
    assert "- Port 8080" in report
    assert "HIGH RISK" in report


def test_markdown_report_omits_high_risk_section_when_none_present():
    analysis = _analysis("tfplan_create_web.json")
    report = markdown_reporter.render(analysis)
    assert "HIGH RISK" not in report
    assert "Resources to Create : 4" in report


def test_html_report_is_self_contained_and_escapes_values():
    analysis = _analysis("tfplan_core_mixed.json")
    report = html_reporter.render(analysis)

    assert report.startswith("<!doctype html>")
    assert "<style>" in report
    assert "http://" not in report and "https://" not in report  # no external assets
    assert "HIGH RISK" in report
    # The IAM role's assume_role_policy contains raw JSON with quotes/braces -
    # make sure nothing breaks the HTML and special chars are escaped if present.
    assert "<script" not in report.lower()


def test_pipeline_report_lists_each_resource_and_high_risk_summary():
    analysis = _analysis("tfplan_core_mixed.json")
    report = pipeline_reporter.render(analysis)

    assert "Terraform Plan Summary" in report
    assert "[REPLACE]" in report
    assert "[DELETE]" in report
    assert "[CREATE]" in report
    assert "[UPDATE]" in report
    assert "HIGH RISK:" in report
