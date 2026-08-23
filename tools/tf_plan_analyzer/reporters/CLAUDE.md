# reporters/

Dumb renderers only. Every reporter takes the exact same input - a single
`models.change.PlanAnalysis` - and returns a string. No business logic: no
risk computation, no impact-text generation, no filtering of which resources
to show. All of that already happened upstream in `analyzers/` and `risks/`
by the time a reporter sees the data.

## Contract

```python
def render(result: PlanAnalysis) -> str: ...
```

- **markdown.py** - produces the plain-text/Markdown report structure
  described in the top-level CLAUDE.md (header counts, per-service
  Create/Update/Delete/Replace sections, trailing HIGH RISK callout).
- **html.py** - same structure as HTML, self-contained (inline `<style>`,
  no external stylesheets/scripts/CDN references - consistent with this
  project's no-network constraint). Every resource-supplied value goes
  through `html.escape()` before being written, since Terraform attribute
  values (IAM policy JSON, descriptions, etc.) can contain `<`, `>`, `&`.
- **pipeline.py** - condensed CI/pipeline-log summary: one line per resource,
  a trailing HIGH RISK list, and a note if any `resource_changes` entries
  were skipped during parsing.

## The one shared rendering rule to know

`AttributeChange.before`/`.after` are normally scalars, rendered as a single
bullet (`display` if the analyzer set one, else `"{path} = {value}"` -
preferring `after`, falling back to `before` when `after` is `None`, which is
the case for deletes). When an analyzer instead sets them to **lists**
(security groups' rendered port lists are the only current example), every
reporter switches to a nested Before:/After: block instead of a single
bullet. If you add a new list-valued `AttributeChange` in an analyzer, no
reporter changes are needed - this branch already handles it generically.
Don't add a new special case per resource type in a reporter; reshape the
data in the analyzer instead so it fits one of these two existing shapes.

## Adding a new output format

Add `reporters/<name>.py` with a `render(result) -> str` function, then wire
it into `main.py`'s `_FILE_REPORTERS` dict (or `_ALL_FORMATS`/pipeline
handling, if it's a stdout-only format like `pipeline.py`).
