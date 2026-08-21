# Terraform Plan Analyzer

A deterministic Python tool that turns a `terraform show -json` plan into a
human-readable report — clearer than scanning raw `~`/`+`/`-` plan output for
faster review, better visibility into infrastructure impact, and early
detection of risky or unintended changes.

It **only** reads an existing `tfplan.json` file. It never executes
`terraform plan`/`apply`/`destroy`/`show`, never touches Terraform state, and
uses no AI/LLM/ML services — every risk level and impact statement comes from
a fixed, deterministic rule table.

## What it does

For every resource in the plan, it identifies:

- The action performed (**Create**, **Update**, **Delete**, **Replace**)
- The important attribute changes (before/after)
- A plain-language impact statement
- A **risk level** (`LOW` / `MEDIUM` / `HIGH`) based on resource type + action
  (e.g. replacing a VPC or security group, or deleting an IAM role/RDS
  instance, is always `HIGH`)

It then produces:

- A **Markdown** report (`plan_summary.md`)
- A self-contained **HTML** report (`plan_summary.html`, no external assets)
- A condensed **pipeline/CI** summary printed to stdout

Resource types without a dedicated analyzer automatically fall back to a
generic analyzer, so an unsupported resource never breaks the tool.

## Project structure

```text
tf-plan-analyzer/
    main.py                  CLI entrypoint
    parser/tfplan_parser.py  JSON -> normalized ResourceChange objects
    analyzers/               one analyzer per service, + generic fallback + registry
    risks/risk_analyzer.py   deterministic (resource_type, action) -> risk level
    reporters/               markdown.py, html.py, pipeline.py
    models/                  ResourceChange / AnalyzedResource / PlanAnalysis dataclasses
    utils/helpers.py         attribute diffing, dependency hints
    tests/                   pytest suite + sample tfplan.json fixtures
```

## Requirements

**To run the analyzer itself:**

- Python 3.9+ — that's it. No third-party runtime dependencies; standard
  library only, no `pip install` needed, no network access required.
- Cross-platform (pure Python, no OS-specific code) — works the same on
  Windows, macOS, and Linux.
- A `tfplan.json` file to point it at (see below for how to produce one).

**To produce the `tfplan.json` input file** (a separate, upstream step —
this tool never does this part itself):

- [Terraform CLI](https://developer.hashicorp.com/terraform/install)
  installed (any version supporting `terraform show -json`, i.e. 0.12+).
- Valid cloud provider credentials configured (e.g. AWS credentials via
  `aws configure`/environment variables) so `terraform plan` can run against
  the target codebase.
- These are only needed to generate the JSON file — once you have
  `tfplan.json`, the analyzer itself needs neither Terraform nor cloud
  credentials to run.

**To run the test suite** (optional, for development):

- `pytest` — install via `pip install -r requirements-dev.txt`

## Usage

Generate a Terraform plan JSON file first (outside the scope of this tool):

```bash
terraform plan -out=tfplan
terraform show -json tfplan > tfplan.json
```

Then run the analyzer against it:

```bash
python main.py tfplan.json
```

By default this writes `plan_summary.md` and `plan_summary.html` to
`./tf-plan-report/`, and prints a condensed summary to stdout.

### CLI options

| Flag | Description |
| --- | --- |
| `plan_path` | Path to the `tfplan.json` file (required, positional) |
| `-o`, `--output-dir` | Directory to write reports into (default: `tf-plan-report`) |
| `--format {markdown,html,pipeline}` | Restrict output to specific format(s); may be repeated (default: all) |
| `--include-data-sources` | Also analyze Terraform data sources (`mode == "data"`); excluded by default |
| `--fail-on-high-risk` | Exit with status code `2` if any `HIGH` risk change is found (useful as a pipeline gate) |
| `--quiet` | Suppress stdout output |
| `--coverage-report` | List distinct resource types in the plan with no dedicated analyzer (falling back to `generic.py`), then exit without generating reports |

### Examples

Only generate the Markdown report:

```bash
python main.py tfplan.json --format markdown --output-dir ./reports
```

Use as a CI gate that fails the build on high-risk changes:

```bash
python main.py tfplan.json --fail-on-high-risk
```

Check analyzer coverage before adopting this tool in a new/unfamiliar codebase
(see [Using this on a different codebase](#using-this-on-a-different-codebase)):

```bash
python main.py tfplan.json --coverage-report
```

## Running the tests

```bash
pip install -r requirements-dev.txt
python -m pytest -q
```

## Extending

Adding support for a new resource type means adding one file to `analyzers/`
with a `SUPPORTED_TYPES` set and an `ANALYZER` instance — `analyzers/registry.py`
discovers it automatically, and neither the parser nor `main.py` need to change.
Unmapped resource types keep working via `analyzers/generic.py` in the meantime.

Each subfolder has its own `CLAUDE.md` describing that layer's contract in
more detail (what belongs there, what doesn't, and the pattern to follow when
adding to it) - start with `analyzers/CLAUDE.md` if you're adding coverage for
a new resource type.

## Using this on a different codebase

The parser, risk engine, and reporters are infra-agnostic - they only consume
Terraform's own plan JSON schema (`type`, `actions`, `before`/`after`), which
is identical regardless of which provider or module structure produced it.
What's specific to this repo's setup (AWS) is the analyzer coverage and the
risk rule table in `risks/risk_analyzer.py`.

To adopt this tool against another Terraform codebase:

1. Generate that codebase's `tfplan.json` (see [Usage](#usage) above).
2. Run `python main.py tfplan.json --coverage-report` to see which resource
   types have no dedicated analyzer yet (they still work, just with the
   generic fallback's unfiltered diff and default-by-action risk level).
3. For any type worth curating, add a small analyzer module under
   `analyzers/` and, if its risk profile differs from the action defaults,
   a rule in `risks/risk_analyzer.py`. See `analyzers/CLAUDE.md` for the
   exact contract.
