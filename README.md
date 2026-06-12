# Kalshi Influence Network

An interactive, **source-anchored** network graph mapping the people, firms,
regulators and capital flows around Kalshi and the broader U.S. prediction-market
industry — revolving doors, lobbying, cross-platform venture capital, and the
regulatory-appointment chain.

Built for a HackerNoon investigation. Every node and edge traces to a primary
source (Kalshi announcements, OpenSecrets, CFTC dockets, court filings, reputable
reporting). Speculative links are explicitly tagged **"inferred — requires
verification."**

## How it works

The graph is **generated from data, not hand-coded.** The source of truth is three
JSON files; a Python script renders them into a single self-contained HTML file.

```
data/nodes.json   # every person / firm / institution  (the "what")
data/edges.json   # every relationship between two nodes (the "how")
data/meta.json    # colour palette, category labels, subgraph + nexus membership
        │
        ▼
build_kalshi_network.py   # data → interactive vis.js graph
        │
        ▼
kalshi_influence_network.html   # self-contained, hostable (generated, git-ignored)
```

This separation is deliberate: **100 people can edit prose-heavy JSON safely.** A
stray quote in a JSON file is a localized, immediately-flagged parse error — not a
silent corruption of the whole program, which is what happened when the data lived
inside Python string literals.

## Quick start

```bash
pip install -r requirements.txt

python validate.py                 # check the data is well-formed + sourced
python build_kalshi_network.py     # produce kalshi_influence_network.html
```

Open `kalshi_influence_network.html` in any browser. No server required.

The published version is built and deployed automatically by CI on every push to
`main` (see [`.github/workflows/ci.yml`](.github/workflows/ci.yml)).

## Repository layout

| Path | Purpose |
| --- | --- |
| `data/nodes.json` | Source of truth: nodes. |
| `data/edges.json` | Source of truth: edges. |
| `data/meta.json` | Palette, category labels, subgraph & nexus membership. |
| `build_kalshi_network.py` | Renders the data into the interactive HTML. |
| `validate.py` | Schema + integrity + sourcing gate (run in CI). |
| `CONTRIBUTING.md` | Data schema and how to add a node/edge. |
| `.github/workflows/ci.yml` | Validates, builds, and deploys on every change. |

## Categories

| Category | Meaning |
| --- | --- |
| `company` | Kalshi (the hub). |
| `founders` | Founders / executives. |
| `investors` | Venture & strategic investors. |
| `regulators` | CFTC / SEC / regulators (current and historical). |
| `political` | Political figures, DC hires, lobbying. |
| `legal` | Legal cases, counsel, policy practitioners. |
| `partners` | Brokers, media, sports and platform partners. |

## Contributing

Read [CONTRIBUTING.md](CONTRIBUTING.md). In short: every claim needs a primary
source, edits go in `data/*.json`, and `python validate.py` must pass before you
open a pull request. CI re-runs it and blocks merges that don't.

## License

See [LICENSE](LICENSE). Underlying facts are drawn from public primary sources,
each cited in the node/edge it supports.
