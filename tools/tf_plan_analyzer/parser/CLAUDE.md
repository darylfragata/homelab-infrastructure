# parser/

One job: turn a `terraform show -json` file into a list of `models.resource.ResourceChange`
objects. Nothing else. No impact text, no risk, no attribute filtering, no
service-specific knowledge - that's all downstream in `analyzers/` and `risks/`.

This is also the only place in the whole project that touches the filesystem
to read Terraform output, and it never executes Terraform or reads state -
it only ever opens the path it's given.

## Contract

- `parse_tfplan(path) -> ParsedPlan` - the public entrypoint. `ParsedPlan`
  bundles `terraform_version`, `format_version`, the parsed `resources`, and
  `skipped_count` (how many malformed entries were dropped).
- `determine_action(actions: list[str]) -> ActionType` - normalizes Terraform's
  raw `change.actions` array. Both `["create","delete"]` and `["delete","create"]`
  mean **replace** (the order just reflects `create_before_destroy`).
- Malformed individual `resource_changes` entries are **skipped and counted**,
  never allowed to crash the whole parse - CLAUDE.md requires unsupported
  resources to never fail the application, and that starts here, before
  analyzers even see the data. Only catch `(KeyError, TypeError)` doing this -
  don't broaden it to bare `except Exception`, or genuine bugs get swallowed
  silently.
- Unrecognized action combinations fall back to `ActionType.NO_OP` with a
  logged warning rather than raising.

## Fields relied upon from the plan JSON

Per `resource_changes[]` entry: `address`, `mode` (`"managed"`/`"data"`),
`type`, `name`, `provider_name`, `change.actions`, `change.before`,
`change.after`, `change.after_unknown`. Everything is accessed defensively
(`.get()`) except the handful of required keys that trigger the skip-on-error
path if missing.

Top-level `configuration` / `planned_values` are intentionally **not**
parsed in v1 - dependency information is derived heuristically downstream
from attribute names instead (see `utils/CLAUDE.md`), not from Terraform's
expression graph.

## If you're porting this to a codebase with a different `format_version`

The shape above is stable across recent Terraform versions. If you hit a
plan where a relied-upon key is missing or shaped differently, prefer adding
defensive `.get()` handling here over loosening the malformed-entry skip
behavior - the goal is "degrade gracefully for that one resource," not
"silently accept anything."
