#!/usr/bin/env python3
"""
Kalshi Influence Network - Revolving Doors, Lobbying & Regulatory Ties (June 2026)
====================================================================================
Renders data/*.json into a single, self-contained, hostable HTML file:
kalshi_influence_network.html

The data is the source of truth (data/nodes.json, data/edges.json, data/meta.json);
this script only turns it into an interactive graph. To change the graph, edit the
JSON and run `python validate.py` then this script. See CONTRIBUTING.md.

Methodology: every node and edge is drawn from primary sources (Kalshi official
announcements, OpenSecrets lobbying disclosures, the 2024 KalshiEX LLC v. CFTC
ruling, CFTC/SEC public records, reputable reporting). Anything not directly
supported is omitted or explicitly tagged "inferred - requires verification".

Requirements:  pip install -r requirements.txt
Tested with:   pyvis 0.3.2, networkx 3.x, Python 3.10+
"""

import csv
import json
import os
import re

import networkx as nx
from pyvis.network import Network

OUTPUT_FILE = "kalshi_influence_network.html"

# ---------------------------------------------------------------------------
# 1. Load data (SOURCE OF TRUTH lives in data/*.json -- see CONTRIBUTING.md).
#    Editing prose in JSON is collaborator-safe: a stray quote is a localized,
#    immediately-flagged parse error instead of corrupting this whole module.
# ---------------------------------------------------------------------------
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")


def _load(name):
    with open(os.path.join(DATA_DIR, name), encoding="utf-8") as fh:
        return json.load(fh)


NODES = _load("nodes.json")
EDGES = _load("edges.json")
_meta = _load("meta.json")
COLORS = _meta["colors"]
CATEGORY_LABELS = _meta["category_labels"]
SUBGRAPH_IDS = _meta["subgraph_ids"]
NEXUS_IDS = _meta["nexus_ids"]

# ---------------------------------------------------------------------------
# 2. Export flattened CSV views (nodes.csv, edges.csv) for portable/auditable
#    analysis outside this script. Generated artifacts; not the source of truth.
# ---------------------------------------------------------------------------
def _flatten_sources(sources):
    return " | ".join("%s (%s)" % (s["text"], s["url"]) for s in sources)


with open("nodes.csv", "w", encoding="utf-8", newline="") as f:
    w = csv.writer(f)
    w.writerow(["id", "label", "category", "color", "size", "role", "bio", "verification", "sources"])
    for n in NODES:
        w.writerow([
            n["id"], n["label"].replace("\n", " "), n["category"], COLORS[n["category"]],
            n["size"], n["role"], n["bio"], n["verification"], _flatten_sources(n["sources"]),
        ])

with open("edges.csv", "w", encoding="utf-8", newline="") as f:
    w = csv.writer(f)
    w.writerow(["source", "target", "label", "details", "width", "revolving_door_dashed"])
    for e in EDGES:
        w.writerow([
            e["src"], e["dst"], e["label"].replace("\n", " "), e["title"],
            e.get("width", 2), "yes" if e.get("dashes") else "no",
        ])

print("Wrote nodes.csv (%d rows) and edges.csv (%d rows)." % (len(NODES), len(EDGES)))

# ---------------------------------------------------------------------------
# 4. Build graph (networkx -> pyvis)
# ---------------------------------------------------------------------------
G = nx.DiGraph()
for n in NODES:
    G.add_node(
        n["id"],
        label=n["label"],
        category=n["category"],
        color=COLORS[n["category"]],
        size=n["size"],
        title=n["role"],
        borderWidth=2,
    )
for e in EDGES:
    G.add_edge(
        e["src"], e["dst"],
        label=e["label"],
        title=e["title"],
        width=e.get("width", 2),
        dashes=e.get("dashes", False),
        color="#9aa5b1",
        arrows="to",
    )

net = Network(
    height="720px", width="100%", directed=True,
    bgcolor="#ffffff", font_color="#1a202c",
    cdn_resources="remote", notebook=False,
)
net.from_nx(G)

html = net.generate_html(OUTPUT_FILE)

# ---------------------------------------------------------------------------
# 5. Custom page chrome (header, legend, controls, panel, timeline, footer)
# ---------------------------------------------------------------------------
CUSTOM_CSS = """
<style>
  :root { --ink:#1a202c; --muted:#5b6675; --line:#e3e8ef; --accent:#14315c; }
  * { box-sizing: border-box; }
  html, body { margin:0; padding:0; background:#f7f9fc; color:var(--ink);
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; }
  .wrap { max-width:1280px; margin:0 auto; padding:0 16px; }
  header.kin { background:var(--accent); color:#fff; padding:28px 16px 22px; }
  header.kin h1 { margin:0 0 10px; font-size:clamp(20px,3.2vw,32px); line-height:1.25; font-weight:800; }
  header.kin p.method { margin:0; max-width:980px; font-size:14.5px; line-height:1.55; color:#dbe5f3; }
  .toolbar { display:flex; flex-wrap:wrap; gap:10px; align-items:center;
    padding:12px 0; border-bottom:1px solid var(--line); }
  .toolbar input[type=search], .toolbar select {
    padding:8px 10px; font-size:14px; border:1px solid #c4ccd6; border-radius:8px; background:#fff; color:var(--ink); }
  .toolbar input[type=search] { min-width:200px; flex:1 1 200px; }
  .btn { padding:9px 14px; font-size:14px; font-weight:600; border-radius:8px; cursor:pointer;
    border:1px solid #c4ccd6; background:#fff; color:var(--ink); }
  .btn:hover { background:#eef2f7; }
  .btn.primary { background:#b32030; border-color:#b32030; color:#fff; }
  .btn.primary:hover { background:#971b29; }
  .btn.primary.active { background:#14315c; border-color:#14315c; }
  .legend { display:flex; flex-wrap:wrap; gap:8px 16px; padding:10px 0 4px; font-size:13px; color:var(--muted); }
  .legend .key { display:inline-flex; align-items:center; gap:6px; }
  .legend .dot { width:12px; height:12px; border-radius:50%; display:inline-block; }
  .timeline { display:flex; flex-wrap:wrap; align-items:center; gap:6px;
    margin:10px 0 4px; padding:10px 14px; background:#fff; border:1px solid var(--line);
    border-radius:10px; font-size:13.5px; }
  .timeline .tl { display:inline-flex; align-items:center; gap:7px; font-weight:600; }
  .timeline .tl .yr { background:#14315c; color:#fff; border-radius:6px; padding:2px 8px; font-size:12.5px; }
  .timeline .arrow { color:#9aa5b1; font-weight:700; padding:0 4px; }
  #graphbox { position:relative; background:#fff; border:1px solid var(--line); border-radius:10px;
    margin:10px 0 14px; overflow:hidden; }
  #mynetwork { border:none !important; }
  /* info panel */
  #infoPanel { position:absolute; top:0; right:-380px; width:360px; max-width:92vw; height:100%;
    background:#ffffff; border-left:1px solid var(--line); box-shadow:-6px 0 18px rgba(20,49,92,.12);
    transition:right .25s ease; overflow-y:auto; z-index:50; padding:18px; }
  #infoPanel.open { right:0; }
  #infoPanel .cat { display:inline-block; font-size:11.5px; font-weight:700; letter-spacing:.4px;
    text-transform:uppercase; color:#fff; border-radius:6px; padding:3px 8px; margin-bottom:8px; }
  #infoPanel h2 { margin:0 0 4px; font-size:20px; }
  #infoPanel .role { font-size:13.5px; color:var(--muted); margin:0 0 10px; font-weight:600; }
  #infoPanel .bio { font-size:14px; line-height:1.55; }
  #infoPanel .verif { font-size:12.5px; color:#7a4d00; background:#fff7e8; border:1px solid #f1dcae;
    border-radius:8px; padding:8px 10px; margin:12px 0; line-height:1.45; }
  #infoPanel h3 { font-size:13px; text-transform:uppercase; letter-spacing:.5px; color:var(--muted); margin:14px 0 6px; }
  #infoPanel ul { margin:0; padding-left:18px; font-size:13.5px; line-height:1.6; }
  #infoPanel a { color:#1b5cb8; word-break:break-word; }
  #panelClose { position:absolute; top:10px; right:12px; border:none; background:transparent;
    font-size:22px; cursor:pointer; color:var(--muted); line-height:1; }
  footer.kin { border-top:1px solid var(--line); background:#fff; padding:18px 16px 30px;
    font-size:13.5px; color:var(--muted); }
  footer.kin details { margin-top:10px; }
  footer.kin summary { cursor:pointer; font-weight:700; color:var(--ink); }
  footer.kin ul { line-height:1.7; }
  .hint { font-size:12.5px; color:var(--muted); padding:2px 0 8px; }
  @media (max-width:680px) {
    .toolbar { gap:8px; }
    .btn { flex:1 1 auto; }
    #infoPanel { width:100%; right:-100%; }
    .timeline { font-size:12.5px; }
  }
</style>
"""

HEADER_HTML = """
<header class="kin">
  <div class="wrap">
    <h1>Kalshi Influence Network &ndash; Revolving Doors, Lobbying &amp; Regulatory Ties (June 2026)</h1>
    <p class="method"><strong>Methodology.</strong> Every connection in this graph is drawn from primary
    sources: Kalshi&rsquo;s official announcements, OpenSecrets federal lobbying disclosures, the
    <em>KalshiEX LLC v. CFTC</em> (2024) court ruling, and CFTC public records. No speculative edges were
    added without sourcing; where a detail is approximate (e.g., a hire date or a per-firm lobbying split),
    it is explicitly marked &ldquo;inferred &ndash; requires verification&rdquo; in the node panel.</p>
  </div>
</header>
<div class="wrap">
  <div class="toolbar">
    <button id="subgraphToggle" class="btn primary">Show Lobbying &amp; Revolving Door Subgraph only</button>
    <select id="categoryFilter" aria-label="Filter by category">
      <option value="all">All categories</option>
      __CATEGORY_OPTIONS__
    </select>
    <input id="searchBox" type="search" placeholder="Search nodes (e.g. Quintenz, a16z)&hellip;" aria-label="Search nodes" />
    <button id="physicsToggle" class="btn">Pause physics</button>
    <button id="resetView" class="btn">Reset view</button>
  </div>
  <div class="legend">__LEGEND_ITEMS__</div>
  <div class="timeline" role="note" aria-label="Key timeline">
    <span class="tl"><span class="yr">2021</span> Quintenz joins Kalshi board (16&nbsp;Nov)</span>
    <span class="arrow">&rarr;</span>
    <span class="tl"><span class="yr">2024</span> Court win in <em>&nbsp;KalshiEX LLC v. CFTC</em></span>
    <span class="arrow">&rarr;</span>
    <span class="tl"><span class="yr">2025&ndash;26</span> DC hiring &amp; lobbying surge (Trump&nbsp;Jr., Bivona, Cutter; &asymp;$490k Q1&nbsp;2026)</span>
  </div>
  <p class="hint">Click any node for its role, bio and primary sources. Hover edges for full sourcing.
  Dashed edges = prior (revolving-door) roles. Drag to rearrange; scroll to zoom.</p>
</div>
"""

PANEL_HTML = """
<aside id="infoPanel" aria-live="polite">
  <button id="panelClose" aria-label="Close panel">&times;</button>
  <div id="panelBody"><p class="role">Click a node to see details and sources.</p></div>
</aside>
"""

FOOTER_HTML = """
<footer class="kin">
  <div class="wrap">
    <div><strong>Last updated: June 2026.</strong> Built for a HackerNoon investigation into prediction-market
    influence, revolving doors and lobbying. Interactive graph rendered with Pyvis / vis-network.</div>
    <details>
      <summary>Sources &amp; Citations</summary>
      <ul>
        <li>Kalshi official announcement &ndash; <em>&ldquo;Former CFTC Commissioner Brian Quintenz Joins Our Board&rdquo;</em> (16 Nov 2021):
          <a href="https://news.kalshi.com/p/former-cftc-commissioner-brian-quintenz-joins-our-board" target="_blank" rel="noopener">news.kalshi.com/p/former-cftc-commissioner-brian-quintenz-joins-our-board</a></li>
        <li>Kalshi official news &amp; hiring / funding announcements:
          <a href="https://news.kalshi.com" target="_blank" rel="noopener">news.kalshi.com</a></li>
        <li>OpenSecrets &ndash; federal lobbying database (client: KalshiEX LLC; &asymp;$490k Q1 2026, $615k&ndash;$1M in 2025;
          firms incl. Miller Strategies, Lincoln Policy Group):
          <a href="https://www.opensecrets.org/federal-lobbying" target="_blank" rel="noopener">opensecrets.org/federal-lobbying</a></li>
        <li><em>KalshiEX LLC v. CFTC</em> (2024) &ndash; ruling narrowing &ldquo;gaming&rdquo; and &ldquo;involve&rdquo; under CEA &sect;5c(c)(5)(C);
          docket search: <a href="https://www.courtlistener.com/?q=KalshiEX+LLC+v.+CFTC" target="_blank" rel="noopener">courtlistener.com</a></li>
        <li>U.S. Commodity Futures Trading Commission &ndash; registration records, dockets, staff &amp; commissioner records:
          <a href="https://www.cftc.gov" target="_blank" rel="noopener">cftc.gov</a></li>
        <li>Gambling Insider &ndash; <em>&ldquo;Who Owns Kalshi in 2026?&rdquo;</em> (28 Jan 2026), naming directors
          Alfred Lin (Sequoia), Matt Huang (Paradigm), Michael Seibel (Y Combinator) and oversight member
          Timothy McDermott: <a href="https://www.gamblinginsider.com" target="_blank" rel="noopener">gamblinginsider.com</a></li>
        <li>Sportico (Mar 2026) &ndash; Kalshi lobbying spend breakdown (Miller Strategies &asymp;$430k for CFTC
          rule-proposal work; Lincoln Policy Group on event-contract regulation &amp; sports betting):
          <a href="https://www.sportico.com" target="_blank" rel="noopener">sportico.com</a></li>
        <li>LegiStorm &ndash; lobbying registrations &amp; filings (Lincoln Policy Group / Blanche Lincoln; &ge;$180k in 2024):
          <a href="https://www.legistorm.com" target="_blank" rel="noopener">legistorm.com</a></li>
      </ul>
      <p>Items marked &ldquo;inferred &ndash; requires verification&rdquo; in node panels (approximate hire dates,
      per-firm lobbying splits, exact directorship classes) reflect aggregate reporting where primary documents
      do not break out the detail.</p>
    </details>
  </div>
</footer>
"""

CUSTOM_JS = """
<script type="text/javascript">
(function () {
  var DETAILS = __NODE_DETAILS__;
  var SUBGRAPH = __SUBGRAPH_IDS__;
  var COLORS = __COLORS__;
  var CAT_LABELS = __CAT_LABELS__;
  var NEXUS = __NEXUS_IDS__;   // Investor-Board Nexus cluster members

  // Refine rendering after pyvis draws the graph (globals: network, nodes, edges)
  network.setOptions({
    interaction: { hover: true, tooltipDelay: 120, navigationButtons: true, keyboard: false },
    physics: {
      solver: "barnesHut",
      barnesHut: { gravitationalConstant: -16000, springLength: 260, springConstant: 0.02,
                   damping: 0.30, avoidOverlap: 0.7 },
      stabilization: { iterations: 300, fit: true }
    },
    edges: {
      font: { size: 9, color: "#4a5568", strokeWidth: 5, strokeColor: "#ffffff", align: "horizontal" },
      smooth: { type: "dynamic" },
      hoverWidth: 1.5
    },
    nodes: {
      shape: "dot",
      font: { size: 14, color: "#1a202c", strokeWidth: 4, strokeColor: "#ffffff", multi: false }
    }
  });

  var state = { subgraph: false, category: "all", search: "" };

  function isVisible(id, label) {
    if (id === "kalshi") return true; // hub always anchors the view
    if (state.subgraph && SUBGRAPH.indexOf(id) === -1) return false;
    var cat = (DETAILS[id] || {}).category || "";
    if (state.category !== "all" && cat !== state.category) return false;
    if (state.search && String(label).toLowerCase().indexOf(state.search) === -1) return false;
    return true;
  }

  function applyFilters() {
    var updates = nodes.get().map(function (n) {
      return { id: n.id, hidden: !isVisible(n.id, n.label) };
    });
    nodes.update(updates);
    network.fit({ animation: { duration: 400, easingFunction: "easeInOutQuad" } });
  }

  document.getElementById("subgraphToggle").addEventListener("click", function () {
    state.subgraph = !state.subgraph;
    this.classList.toggle("active", state.subgraph);
    this.innerHTML = state.subgraph
      ? "Show Full Network"
      : "Show Lobbying &amp; Revolving Door Subgraph only";
    applyFilters();
  });

  document.getElementById("categoryFilter").addEventListener("change", function () {
    state.category = this.value;
    applyFilters();
  });

  document.getElementById("searchBox").addEventListener("input", function () {
    state.search = this.value.trim().toLowerCase();
    applyFilters();
  });

  var physicsOn = true;
  document.getElementById("physicsToggle").addEventListener("click", function () {
    physicsOn = !physicsOn;
    network.setOptions({ physics: { enabled: physicsOn } });
    this.textContent = physicsOn ? "Pause physics" : "Resume physics";
  });

  document.getElementById("resetView").addEventListener("click", function () {
    state.subgraph = false; state.category = "all"; state.search = "";
    var t = document.getElementById("subgraphToggle");
    t.classList.remove("active");
    t.innerHTML = "Show Lobbying &amp; Revolving Door Subgraph only";
    document.getElementById("categoryFilter").value = "all";
    document.getElementById("searchBox").value = "";
    applyFilters();
  });

  // ---- node detail panel ----
  var panel = document.getElementById("infoPanel");
  var body = document.getElementById("panelBody");

  function esc(s) {
    return String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  }

  function renderPanel(id) {
    var d = DETAILS[id];
    if (!d) return;
    var html = '<span class="cat" style="background:' + COLORS[d.category] + '">' +
               esc(CAT_LABELS[d.category]) + "</span>";
    html += "<h2>" + esc(d.name) + "</h2>";
    html += '<p class="role">' + esc(d.role) + "</p>";
    html += '<div class="bio">' + esc(d.bio) + "</div>";
    html += '<div class="verif">' + esc(d.verification) + "</div>";
    html += "<h3>Primary sources</h3><ul>";
    d.sources.forEach(function (s) {
      html += '<li><a href="' + s.url + '" target="_blank" rel="noopener">' + esc(s.text) + "</a></li>";
    });
    html += "</ul>";
    body.innerHTML = html;
    panel.classList.add("open");
  }

  network.on("click", function (params) {
    if (params.nodes.length) renderPanel(params.nodes[0]);
    else panel.classList.remove("open");
  });
  document.getElementById("panelClose").addEventListener("click", function () {
    panel.classList.remove("open");
  });

  // ---- "Investor-Board Nexus" cluster highlight ----
  // Drawn under the nodes each frame as a rounded, translucent hull around the
  // Sequoia / Paradigm / Y Combinator board reps + Brian Quintenz.
  function roundedRect(ctx, x, y, w, h, r) {
    ctx.beginPath();
    ctx.moveTo(x + r, y);
    ctx.arcTo(x + w, y, x + w, y + h, r);
    ctx.arcTo(x + w, y + h, x, y + h, r);
    ctx.arcTo(x, y + h, x, y, r);
    ctx.arcTo(x, y, x + w, y, r);
    ctx.closePath();
  }

  network.on("beforeDrawing", function (ctx) {
    var pts = [];
    var positions = network.getPositions(NEXUS);
    NEXUS.forEach(function (id) {
      var n = nodes.get(id);
      if (n && n.hidden) return;          // respect filters/subgraph toggle
      if (positions[id]) pts.push(positions[id]);
    });
    if (pts.length < 2) return;           // need at least a couple of members

    var pad = 70;
    var minX = Math.min.apply(null, pts.map(function (p) { return p.x; })) - pad;
    var maxX = Math.max.apply(null, pts.map(function (p) { return p.x; })) + pad;
    var minY = Math.min.apply(null, pts.map(function (p) { return p.y; })) - pad;
    var maxY = Math.max.apply(null, pts.map(function (p) { return p.y; })) + pad;

    ctx.save();
    roundedRect(ctx, minX, minY, maxX - minX, maxY - minY, 28);
    ctx.fillStyle = "rgba(46, 164, 79, 0.08)";     // green tint (investor cluster)
    ctx.fill();
    ctx.setLineDash([8, 6]);
    ctx.lineWidth = 2;
    ctx.strokeStyle = "rgba(20, 49, 92, 0.55)";
    ctx.stroke();
    ctx.setLineDash([]);
    // label
    ctx.font = "600 15px -apple-system, Segoe UI, Roboto, sans-serif";
    ctx.fillStyle = "#14315c";
    ctx.textBaseline = "bottom";
    ctx.fillText("Investor-Board Nexus", minX + 14, minY - 6);
    ctx.restore();
  });

  // settle then stop jitter
  network.once("stabilizationIterationsDone", function () {
    network.setOptions({ physics: { barnesHut: { damping: 0.5 } } });
  });
})();
</script>
"""

# Build legend + category <option>s
legend_items = "".join(
    '<span class="key"><span class="dot" style="background:%s"></span>%s</span>'
    % (COLORS[c], CATEGORY_LABELS[c])
    for c in ["company", "founders", "investors", "regulators", "political", "legal", "partners"]
)
category_options = "".join(
    '<option value="%s">%s</option>' % (c, CATEGORY_LABELS[c])
    for c in ["founders", "investors", "regulators", "political", "legal", "partners"]
)

node_details = {
    n["id"]: {
        "name": n["label"].replace("\n", " "),
        "category": n["category"],
        "role": n["role"],
        "bio": n["bio"],
        "sources": n["sources"],
        "verification": n["verification"],
    }
    for n in NODES
}

header = HEADER_HTML.replace("__CATEGORY_OPTIONS__", category_options) \
                    .replace("__LEGEND_ITEMS__", legend_items)
custom_js = (CUSTOM_JS
             .replace("__NODE_DETAILS__", json.dumps(node_details, ensure_ascii=False))
             .replace("__SUBGRAPH_IDS__", json.dumps(SUBGRAPH_IDS))
             .replace("__NEXUS_IDS__", json.dumps(NEXUS_IDS))
             .replace("__COLORS__", json.dumps(COLORS))
             .replace("__CAT_LABELS__", json.dumps(CATEGORY_LABELS)))

# ---------------------------------------------------------------------------
# 6. Inject chrome into the pyvis HTML
# ---------------------------------------------------------------------------
html = html.replace("</head>", CUSTOM_CSS + "\n</head>", 1)
html = re.sub(r"<body[^>]*>", lambda m: m.group(0) + header, html, count=1)

# Wrap the network canvas so the slide-in panel can anchor to it
html = html.replace(
    '<div id="mynetwork"',
    '<div class="wrap"><div id="graphbox">' + PANEL_HTML + '<div id="mynetwork"',
    1,
)
# pyvis places a loading bar after #mynetwork; close our wrappers and append
# the footer + custom JS at the end of <body>.
html = html.replace("</body>", "</div></div>" + FOOTER_HTML + custom_js + "\n</body>", 1)

# Give the canvas a clean inline style (full width inside the card)
html = html.replace('width: 100%', "width: 100%", 1)

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    f.write(html)

print("Wrote %s (%d nodes, %d edges)." % (OUTPUT_FILE, G.number_of_nodes(), G.number_of_edges()))
print("Open it locally in a browser, or host it (Netlify Drop / GitHub Pages).")
