# utils/

Shared, deterministic helpers used by analyzers. No domain-specific
(per-resource-type) knowledge lives here - if a helper needs to know "this is
a security group," it belongs in `analyzers/security_group.py`, not here.

## `helpers.py`

- **`flatten_diff(before, after, ignore_keys=...) -> list[AttributeChange]`**
  - the shared diffing engine every analyzer's default `_diff()` uses (via
  `analyzers.base.ResourceAnalyzer._diff()`). Recurses into nested dicts with
  dotted paths (`"ingress.description"`), and compares same-length lists of
  dicts elementwise by index (`"ingress[0].from_port"`). Everything else
  (scalars, mismatched-length lists, lists of scalars) is compared as a whole
  value. This is a **deliberate simplification** - no reordering/set-aware
  list diffing - documented here so it isn't "discovered" as a bug later.
  If an analyzer needs smarter list handling (matching by some ID rather than
  index), that logic belongs in the analyzer's own `_diff()` override, as
  `security_group.py` does for ports.

- **`extract_dependency_hints(after) -> list[str]`** - best-effort
  `"attribute -> value"` strings for top-level attributes ending in `_id`,
  `_arn`, `_ids`, or `_arns` (e.g. `vpc_id`, `role_arn`). This is a **heuristic
  placeholder**, not a resolved dependency graph - a real one would require
  parsing the plan's `configuration` block (out of scope for this parser, see
  `parser/CLAUDE.md`). Don't present this as more authoritative than it is
  when extending it.

- **`SERVICE_DISPLAY_NAMES`** - maps an analyzer's `SERVICE_KEY` (e.g.
  `"security_group"`) to its report section heading (`"Security Group"`).
  When you add a new analyzer with a new `SERVICE_KEY`, add its display name
  here too, or it'll fall back to the raw key.

- **`group_by_service(resources) -> dict[str, list[AnalyzedResource]]`** -
  groups analyzed resources by `SERVICE_KEY`, ordered by display name, for
  reporters to iterate over. Used by both `markdown.py` and `html.py`.

## Adding a helper here

Ask first: does this logic depend on knowing a specific Terraform resource
type? If yes, it belongs in the relevant `analyzers/*.py` module instead.
This folder is for logic that's useful across *any* analyzer.
