"""CLI entrypoint for the Terraform Plan Analyzer.

Reads an existing tfplan.json (produced upstream by `terraform show -json`)
and writes human-readable reports. This tool never executes Terraform and
never touches Terraform state directly - its only input is the given JSON
file path.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import List, Optional, Sequence

from analyzers.registry import analyze_all, uncovered_resource_types
from models.change import ChangeSummary, PlanAnalysis
from parser.tfplan_parser import TfPlanParseError, parse_tfplan
from reporters import html as html_reporter
from reporters import markdown as markdown_reporter
from reporters import pipeline as pipeline_reporter

_FILE_REPORTERS = {
    "markdown": (markdown_reporter, "plan_summary.md"),
    "html": (html_reporter, "plan_summary.html"),
}

_ALL_FORMATS = ("markdown", "html", "pipeline")


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="tf-plan-analyzer",
        description="Convert a Terraform plan JSON file into a human-readable report.",
    )
    parser.add_argument("plan_path", help="Path to an existing tfplan.json file.")
    parser.add_argument(
        "-o",
        "--output-dir",
        default="tf-plan-report",
        help="Directory to write markdown/html reports into (default: %(default)s).",
    )
    parser.add_argument(
        "--format",
        dest="formats",
        action="append",
        choices=_ALL_FORMATS,
        help="Output format to generate; may be repeated. Default: all formats.",
    )
    parser.add_argument(
        "--include-data-sources",
        action="store_true",
        help="Include Terraform data sources (mode=data) in the analysis.",
    )
    parser.add_argument(
        "--fail-on-high-risk",
        action="store_true",
        help="Exit with status 2 if any HIGH risk resource changes are found.",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress the pipeline summary and file-written messages printed to stdout.",
    )
    parser.add_argument(
        "--coverage-report",
        action="store_true",
        help=(
            "List distinct resource types in the plan with no dedicated analyzer "
            "(i.e. falling back to generic.py), then exit without generating reports. "
            "Useful when pointing this tool at a new/unfamiliar codebase."
        ),
    )
    return parser


def _build_plan_analysis(plan_path: str, include_data_sources: bool) -> PlanAnalysis:
    parsed = parse_tfplan(plan_path)
    analyzed_resources = analyze_all(parsed.resources, include_data_sources=include_data_sources)
    summary = ChangeSummary.from_resources(analyzed_resources)
    return PlanAnalysis(
        source_path=str(plan_path),
        terraform_version=parsed.terraform_version,
        resources=analyzed_resources,
        summary=summary,
        skipped_count=parsed.skipped_count,
    )


def run(argv: Optional[Sequence[str]] = None) -> int:
    args = build_arg_parser().parse_args(argv)
    formats = args.formats or list(_ALL_FORMATS)

    if args.coverage_report:
        try:
            parsed = parse_tfplan(args.plan_path)
        except TfPlanParseError as exc:
            print(f"Error: {exc}", file=sys.stderr)
            return 1
        uncovered = uncovered_resource_types(parsed.resources)
        if uncovered:
            print(
                f"{len(uncovered)} resource type(s) with no dedicated analyzer "
                "(using generic.py):"
            )
            for resource_type in uncovered:
                print(f"- {resource_type}")
        else:
            print("Every managed resource type in this plan has a dedicated analyzer.")
        return 0

    try:
        analysis = _build_plan_analysis(args.plan_path, args.include_data_sources)
    except TfPlanParseError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    output_dir = Path(args.output_dir)
    written: List[Path] = []
    for name in formats:
        if name not in _FILE_REPORTERS:
            continue
        reporter, filename = _FILE_REPORTERS[name]
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / filename
        output_path.write_text(reporter.render(analysis), encoding="utf-8")
        written.append(output_path)

    if not args.quiet:
        if "pipeline" in formats:
            print(pipeline_reporter.render(analysis))
        for path in written:
            print(f"Wrote {path}")

    if args.fail_on_high_risk and analysis.high_risk:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
