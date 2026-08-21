# analyzers/

This is the folder you'll touch most often when adopting this tool on a new
codebase - it's where per-resource-type coverage lives. Read this before
adding or editing an analyzer.

## The contract for a service analyzer module

Every module in this package (except `base.py`, `registry.py`, and
`generic.py`) is a standalone plugin discovered automatically at import time.
Each one must expose, at module level:

```python
SUPPORTED_TYPES: frozenset[str]      # Terraform resource type strings this module handles
ANALYZER: ResourceAnalyzer           # a singleton instance of your analyzer class
```

And the class itself subclasses `ResourceAnalyzer` (from `base.py`) and sets:

```python
class MyServiceAnalyzer(ResourceAnalyzer):
    SERVICE_KEY = "my_service"                  # report section grouping key
    IMPORTANT_ATTRIBUTES = frozenset({...})      # top-level attrs to show; empty = show everything (generic.py's approach)
    IMPACT_TEMPLATES = {ActionType.CREATE: "...", ActionType.UPDATE: "...", ...}  # plain strings, no AI
```

That's it - `analyzers/registry.py` walks this package with `pkgutil.iter_modules`,
imports every module dynamically via `importlib.import_module`, and merges
`SUPPORTED_TYPES -> ANALYZER` into one dispatch table. **Nothing else needs to
change** to add coverage: not the parser, not `main.py`, not `registry.py`
itself. Drop the file in, and it's live.

## Never set `risk` in an analyzer

`AnalyzedResource.risk` is left `None` by `ResourceAnalyzer.analyze()` and
filled in centrally by `analyzers/registry.py` after your analyzer returns,
by calling `risks.risk_analyzer.assess()`. This guarantees the same
`(resource_type, action)` always gets the same risk level no matter which
analyzer produced it, and keeps analyzers unit-testable without importing the
risk rule table. If a type needs a non-default risk level, add a row to
`risks/risk_analyzer.py`, not logic here.

## The `lambda.py` keyword problem

`lambda` is a reserved Python word, so `analyzers/lambda.py` can never be
imported with `import analyzers.lambda` or `from analyzers import lambda` -
both are `SyntaxError`s. The file is still named `lambda.py` (per the
project's required structure) because `registry.py`'s discovery uses
`importlib.import_module(f"analyzers.{name}")`, and that API takes a plain
string - it doesn't care that the string happens to be a keyword. If you ever
need to import it directly (e.g. in a test), do the same:
`importlib.import_module("analyzers.lambda")`. Never write a static
`from analyzers import lambda` anywhere.

## `generic.py` is the fallback, not "one more analyzer"

It has an empty `SUPPORTED_TYPES` (nothing maps to it explicitly) and empty
`IMPORTANT_ATTRIBUTES` (shows the full, unfiltered diff). `registry.get_analyzer()`
returns it for any type with no dedicated module, and `registry.analyze_all()`
also falls back to it if a real analyzer raises an unexpected exception -
an analyzer bug must never crash the whole run.

## Adding coverage for a new resource type - checklist

1. Run `python main.py <tfplan.json> --coverage-report` to see what's currently
   unmapped in the codebase you care about.
2. Pick a type (or a small related group, like `security_group.py` does for
   both `aws_security_group` and `aws_security_group_rule`). Create
   `analyzers/<name>.py` following the contract above.
3. Only override `_diff()` if the generic attribute-by-attribute diff isn't
   readable enough (see `security_group.py` for an example that reshapes
   port lists into `AttributeChange(before=[...], after=[...])` for the
   reporters' Before:/After: rendering, and `lambda.py` for an example that
   just relabels a couple of scalar values via `display=`).
4. Add a risk rule in `risks/risk_analyzer.py` if the type's risk profile
   isn't well served by the action defaults (see that folder's CLAUDE.md).
5. Add a unit test in `tests/test_analyzers.py` and re-run the suite.

## `base.py` internals worth knowing

- `_diff()` calls `utils.helpers.flatten_diff()` then filters to
  `IMPORTANT_ATTRIBUTES` if that set is non-empty.
- `_impacts()` looks up `IMPACT_TEMPLATES[action]`, falling back to
  `DEFAULT_IMPACT_TEMPLATES[action]` (generic per-action text) if your
  analyzer doesn't override that action.
- `dependencies` is always populated via `utils.helpers.extract_dependency_hints(change.after)`
  - a heuristic based on attribute-name suffixes (`_id`, `_arn`, ...), not a
    real dependency graph. See `utils/CLAUDE.md`.
