# risks/

Deterministic risk classification, and nothing else. Given a resource type,
an action, and the list of changed attribute paths, `assess()` always returns
the same `RiskLevel` - no randomness, no AI, no per-run variation.

## Contract

```python
assess(resource_type: str, action: ActionType, changed_attribute_paths: Iterable[str] = ()) -> RiskLevel
```

Precedence, in order:

1. **Cosmetic-only override** - an `UPDATE` where every changed attribute's
   top-level key is in `COSMETIC_ATTRIBUTE_PREFIXES` (`tags`, `tags_all`,
   `description`) is always `LOW`, regardless of resource type. This is
   checked first and short-circuits everything below it.
2. **Explicit rule** - an exact `(resource_type, action)` match in `RISK_RULES`.
3. **Default by action** - `DEFAULT_RISK_BY_ACTION[action]` (create/update →
   LOW, delete/replace → MEDIUM, read/no-op → LOW) when nothing more specific
   applies.

## Adding a new rule

Add a row to `RISK_RULES`. Do not add branching logic to `assess()` itself -
if you find yourself writing an `if resource_type.startswith(...)`, that's a
sign you want either more explicit rows (one per type) or a new cosmetic-style
prefix set, not a new code path. The whole point of this module is that the
full rule set is readable at a glance in one dict.

`risk` on an `AnalyzedResource` is **always** assigned by
`analyzers/registry.py` calling into this module centrally - never by an
individual analyzer - so the same `(type, action)` always yields the same
risk no matter which analyzer produced the result. If you're adding a new
analyzer and thinking about risk, the rule belongs here, not in the analyzer.

## Where `RiskLevel` lives

`RiskLevel` (the LOW/MEDIUM/HIGH enum) is defined in this module, not in
`models/`, so this package stays the single owner of "what does risk mean."
`models/change.py` imports it purely for the `AnalyzedResource.risk` field's
type annotation - that's a one-way dependency (models depends on risks, not
the reverse), so this module must never import from `models/change.py`.
