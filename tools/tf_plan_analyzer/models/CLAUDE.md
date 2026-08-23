# models/

Plain dataclasses only. No parsing, no analysis, no risk logic, no formatting.
If you're about to add a method that computes something (a diff, an impact
string, a risk level), it belongs in `analyzers/`, `risks/`, or `reporters/`
instead - this folder just defines the shapes those layers pass around.

## Files

- **resource.py** - `ActionType` enum and `ResourceChange`, the parser's only
  output type. Purely structural: address, mode, resource_type, name,
  provider_name, action, before/after dicts. Nothing derived lives here.
- **change.py** - `AttributeChange`, `AnalyzedResource`, `ChangeSummary`,
  `PlanAnalysis`. These are what analyzers/risk/reporters produce and consume.

## Dependency direction

`models/change.py` imports `RiskLevel` from `risks/risk_analyzer.py` (for the
`AnalyzedResource.risk` field's type) and `ActionType` from `models/resource.py`.
That's the only outward dependency this package has. Nothing in `models/`
imports from `parser/`, `analyzers/`, or `reporters/` - keep it that way, or
you'll create an import cycle (those packages depend on `models/`, not the
other way around).

## Notes on the existing shapes

- `AttributeChange.before`/`after` are usually scalars but can be **lists**
  (e.g. a security group's rendered port list) - reporters branch on
  `isinstance(x, list)` to decide whether to render a scalar bullet or a
  nested Before:/After: block. If you add a new field that can hold a list,
  document it the same way.
- `AnalyzedResource.risk` starts as `None` and is filled in centrally by
  `analyzers/registry.py`, never by an individual analyzer. Don't set it
  inside a new analyzer.
- `PlanAnalysis.high_risk` is a computed property, not a stored field - it
  filters `resources` by `risk == RiskLevel.HIGH` on access.
