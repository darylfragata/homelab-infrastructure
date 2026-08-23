from pathlib import Path

import main

FIXTURES = Path(__file__).parent / "fixtures"


def test_run_writes_reports_and_returns_zero(tmp_path):
    output_dir = tmp_path / "out"
    exit_code = main.run(
        [
            str(FIXTURES / "tfplan_create_web.json"),
            "--output-dir",
            str(output_dir),
            "--quiet",
        ]
    )
    assert exit_code == 0
    assert (output_dir / "plan_summary.md").exists()
    assert (output_dir / "plan_summary.html").exists()


def test_run_fail_on_high_risk_returns_two_when_high_risk_present(tmp_path):
    output_dir = tmp_path / "out"
    exit_code = main.run(
        [
            str(FIXTURES / "tfplan_core_mixed.json"),
            "--output-dir",
            str(output_dir),
            "--fail-on-high-risk",
            "--quiet",
        ]
    )
    assert exit_code == 2


def test_run_fail_on_high_risk_returns_zero_when_no_high_risk(tmp_path):
    output_dir = tmp_path / "out"
    exit_code = main.run(
        [
            str(FIXTURES / "tfplan_create_web.json"),
            "--output-dir",
            str(output_dir),
            "--fail-on-high-risk",
            "--quiet",
        ]
    )
    assert exit_code == 0


def test_run_missing_plan_file_returns_one(tmp_path, capsys):
    exit_code = main.run(
        [str(tmp_path / "does-not-exist.json"), "--output-dir", str(tmp_path / "out"), "--quiet"]
    )
    assert exit_code == 1
    captured = capsys.readouterr()
    assert "Error" in captured.err


def test_run_coverage_report_lists_unmapped_types_and_writes_no_files(tmp_path, capsys):
    output_dir = tmp_path / "out"
    exit_code = main.run(
        [str(FIXTURES / "tfplan_create_web.json"), "--output-dir", str(output_dir), "--coverage-report"]
    )
    assert exit_code == 0
    assert not output_dir.exists()
    captured = capsys.readouterr()
    assert "aws_cloudfront_distribution" in captured.out
    assert "aws_budgets_budget" in captured.out
    assert "aws_s3_bucket" not in captured.out  # s3.py already covers this type


def test_run_coverage_report_reports_full_coverage(tmp_path, capsys):
    exit_code = main.run(
        [str(FIXTURES / "tfplan_core_mixed.json"), "--output-dir", str(tmp_path / "out"), "--coverage-report"]
    )
    assert exit_code == 0
    captured = capsys.readouterr()
    assert "Every managed resource type in this plan has a dedicated analyzer." in captured.out


def test_run_only_generates_requested_formats(tmp_path):
    output_dir = tmp_path / "out"
    exit_code = main.run(
        [
            str(FIXTURES / "tfplan_create_web.json"),
            "--output-dir",
            str(output_dir),
            "--format",
            "markdown",
            "--quiet",
        ]
    )
    assert exit_code == 0
    assert (output_dir / "plan_summary.md").exists()
    assert not (output_dir / "plan_summary.html").exists()
