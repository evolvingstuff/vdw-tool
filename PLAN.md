# Plan: Fix tag links and DIV parsing

## Goals
- Tag links use trailing slash: `/tags/<slug>/` (no `.html`).
- Preserve `[text](...)` markdown link format everywhere.
- Tag slug generation replaces `/` with `-` (e.g., `.../ALS` → `...-als`).
- Parse and remove `{DIV(...)}...{DIV}` wrappers reliably, including stacked and inline variants, so no stray `{DIV...}` appears in output.

## Scope of Changes
- Update tag link rendering to use `/tags/<slug>/`:
  - `utils/parsing/parser.py` in:
    - `LinkNode.render()`
    - `LocalLinkNode.render()`
    - `AliasedLocalLinkNode.render()`
    - HTML rendering helpers: `_render_link_node_html`, `_render_local_link_node_html`, `_render_aliased_local_link_node_html`.
  - Replace hard-coded `"/tags/{slug}.html"` with `"/tags/{slug}/"`.
  - Ensure output remains `[text](href)` (markdown), and `<a href="...">text</a>` in HTML fragments.
- Update tag link generator:
  - `utils/slugs.generate_tag_link()` → return `[name](/tags/<slug>/)`.
  - Mirror the same in `utils/vitd_utils/slugs.py` for consistency.
- Improve tag slug creation for `/`:
  - `utils/slugs.generate_hugo_tag_slug()` to treat `/` as a separator, replacing with `-` (not dropping it), ensuring `amyotrophic-lateral-sclerosis-als`.

## DIV Parsing Fixes
- Keep `DivPattern` as pass-through, but verify it matches cases without spaces before parentheses, e.g. `{DIV(class="...")}`.
- Confirm nested/stacked `{DIV}{DIV} ... {DIV}{DIV}` sequences are fully consumed.
- Add a final cleanup to remove any stray `{DIV...}` tokens if they occur without matched pairs in edge cases.

## Tests / Validation
- Add tests using the provided sample to verify:
  - All tag links render as `/tags/<slug>/`.
  - Bracketed markdown `[text](...)` is preserved.
  - Slug for `Amyotrophic Lateral Sclerosis/ALS` becomes `amyotrophic-lateral-sclerosis-als`.
  - No `{DIV...}` remains in the output.
- Manual check via `quick-copy-paste-single-page-test.py` with your example.

## Success Criteria
- Sample renders to:
  - `[Amyotrophic Lateral Sclerosis/ALS](/tags/amyotrophic-lateral-sclerosis-als/) (30+)`
  - `[Alzheimer's](/tags/alzheimers/) (81+) [Overview](/tags/overview/)`
  - `[End of Alz.](/tags/end-of-alz/) (15+)`
- No literal `{DIV...}` in final markdown.

## Notes
- We will not introduce Optional fields or soft error handling.
- Changes are minimal and isolated to parsing/link utilities.
