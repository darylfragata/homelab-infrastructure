# tests/

pytest, run from the `tf-plan-analyzer/` root (`python -m pytest -q`). Imports
are absolute top-level (`from models.resource import ...`, `from analyzers.registry
import ...`) - `conftest.py` and `pyproject.toml`'s `pythonpath = ["."]` both
put the project root on `sys.path` so this works regardless of pytest version.

## Layout

- **fixtures/*.json** - hand-authored `terraform show -json`-shaped plan
  files, not real Terraform output (this project must never execute
  Terraform, including in tests). `tfplan_create_web.json` and
  `tfplan_core_mixed.json` are modeled on the real modules in `../../modules`
  (s3, vpc, security groups, iam, lambda, cloudfront/budget via the generic
  fallback) so they exercise realistic attribute shapes, not toy data.
- **test_parser.py** - action-normalization table test, malformed/missing-key
  handling, file-not-found / invalid-JSON error paths.
- **test_risk_analyzer.py** - every HIGH/MEDIUM/LOW example from the
  top-level CLAUDE.md, plus the cosmetic-only-forces-LOW override and the
  default-by-action fallback.
- **test_analyzers.py** - one test per notable analyzer behavior (generic
  fallback, Lambda's memory/runtime formatting, security group port
  rendering), plus `registry.py`'s dispatch/fallback/risk-assignment and
  `uncovered_resource_types()`. Note: `analyzers/lambda.py` is imported here
  via `importlib.import_module("analyzers.lambda")`, never a static
  `from analyzers import lambda` (see `analyzers/CLAUDE.md` for why).
- **test_reporters.py** - structural assertions against rendered output
  (section counts, Before:/After: port rendering, HTML escaping/self-containment).
- **test_main.py** - CLI end-to-end via `main.run(argv) -> int`, including
  `--fail-on-high-risk` exit codes and `--coverage-report`.

## Adding a fixture for a new codebase

If you're extending analyzer coverage for a different Terraform codebase
(see the root README's "Using this on a different codebase" section), add a
new `tests/fixtures/*.json` modeled on that codebase's real resource shapes -
copy the structure of the existing fixtures rather than inventing a new plan
JSON shape. Keep fixtures hand-authored and minimal: only the fields your new
analyzer/test actually reads need real values; everything else can be a
placeholder.
