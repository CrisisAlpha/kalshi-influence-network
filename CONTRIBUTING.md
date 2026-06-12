# Contributing

Thanks for helping map the prediction-market influence network. This project has
**one non-negotiable rule** and a simple workflow designed so that many people can
contribute without breaking the build.

## The rule: no fabrication

Every node and every edge must trace to a **primary source** — a Kalshi
announcement, an OpenSecrets/LegiStorm filing, a CFTC docket, a court ruling, an
SEC record, or credible reporting that itself cites such sources.

- If you can't cite it, don't add it.
- If a detail is approximate or deduced (a hire date, a per-firm lobbying split, a
  directorship class, a "same political orbit" link), say so: put **`inferred —
  requires verification`** in the node's `verification` field or the edge's prose,
  and mark inferred edges with `"dashes": true`.

`validate.py` enforces the structural side of this (every node needs ≥1 source with
a URL; verification can't be empty). The factual side is on you and on review.

## Workflow

1. **Fork & branch.** Never edit `main` directly.
2. **Edit only `data/*.json`.** You almost never need to touch Python.
3. **Validate locally:** `python validate.py` — fix every `ERROR:` before pushing.
4. **(Optional) build to preview:** `python build_kalshi_network.py` then open
   `kalshi_influence_network.html`.
5. **Open a pull request.** CI re-runs validation + build. Green check = mergeable.

## Data schema

### Add a node — `data/nodes.json`

Append one object to the array:

```json
{
  "id": "jane_doe",
  "label": "Jane Doe",
  "category": "investors",
  "size": 24,
  "role": "Short one-line title shown on hover.",
  "bio": "A few sentences of sourced narrative. Plain prose. Quotes and commas are fine here — JSON handles them.",
  "sources": [
    { "text": "Outlet / document name (date)", "url": "https://example.com/article" }
  ],
  "verification": "Verified per [source]. Or: inferred - requires verification."
}
```

Field rules (checked by `validate.py`):

| Field | Type | Rules |
| --- | --- | --- |
| `id` | string | Unique. `snake_case`, `[a-z0-9_]+` only. |
| `label` | string | Display name. Use `\n` for a line break in the bubble. |
| `category` | string | One of the keys in `data/meta.json` → `colors`. |
| `size` | number | Positive. Bigger = more central (hub ≈ 46, minor ≈ 20). |
| `role` | string | One-line subtitle. |
| `bio` | string | Sourced narrative. |
| `sources` | array | **≥ 1** object, each with non-empty `text` and an `http(s)://` `url`. |
| `verification` | string | Non-empty. Say "inferred - requires verification" if speculative. |

### Add an edge — `data/edges.json`

```json
{
  "src": "jane_doe",
  "dst": "kalshi",
  "label": "Short edge caption",
  "title": "Full sourced explanation shown on hover. Sources: ...",
  "width": 3,
  "dashes": false
}
```

| Field | Type | Rules |
| --- | --- | --- |
| `src`, `dst` | string | **Must** match an existing node `id`. |
| `label` | string | Short caption on the edge. |
| `title` | string | Full hover explanation; end with `Source: ...`. |
| `width` | number | Optional (default 2). Thicker = stronger/clearer tie. |
| `dashes` | bool | Optional. `true` = prior role, revolving door, or inferred link. |

### Membership lists — `data/meta.json`

- `subgraph_ids` — node ids included in the "Lobbying & Revolving Door" view.
- `nexus_ids` — node ids highlighted in the "Investor-Board Nexus" hull.
- Adding a new id here that isn't a real node will fail validation.
- To add a **new category**, add the same key to both `colors` (a hex value) and
  `category_labels` (a display string).

## What CI checks

Every PR runs [`validate.py`](validate.py):

- JSON parses; every node/edge has required, correctly-typed fields.
- Node ids are unique and well-formed; categories are valid.
- Every edge endpoint and every `meta` id references a real node.
- Every node has at least one sourced `(text, url)` and a verification note.

It then runs `build_kalshi_network.py` as a smoke test. If both pass, the branch is
mergeable; on `main` the graph is rebuilt and published automatically.

## Tips

- Keep one factual claim per source line; multiple sources are encouraged.
- Prefer the most primary source available (the filing over the article about it).
- Use a JSON-aware editor — it will flag a misplaced comma or quote instantly.
