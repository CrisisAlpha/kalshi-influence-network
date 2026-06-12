#!/usr/bin/env python3
"""
Validate data/*.json for the Kalshi Influence Network.

This is the contribution gate. CI runs it on every pull request; a non-zero
exit blocks the merge. It enforces three things 100 collaborators must respect:

  1. Schema      - every node/edge has the required, correctly-typed fields.
  2. Integrity   - every edge endpoint and every meta id references a real node;
                   ids are unique and well-formed.
  3. No fabrication - every node carries at least one primary source (text+url)
                   and a non-empty verification note. Anything speculative must
                   say "inferred" AND "requires verification".

Run locally before opening a PR:  python validate.py
"""
import json
import os
import re
import sys

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")

ID_RE = re.compile(r"^[a-z0-9_]+$")
URL_RE = re.compile(r"^https?://", re.IGNORECASE)

errors = []
warnings = []


def err(msg):
    errors.append(msg)


def warn(msg):
    warnings.append(msg)


def load(name):
    path = os.path.join(DATA_DIR, name)
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        err(f"{name}: file not found at {path}")
    except json.JSONDecodeError as e:
        err(f"{name}: invalid JSON - {e}")
    return None


def main():
    nodes = load("nodes.json")
    edges = load("edges.json")
    meta = load("meta.json")
    if nodes is None or edges is None or meta is None:
        return report()

    colors = meta.get("colors", {})
    category_labels = meta.get("category_labels", {})
    valid_categories = set(colors)

    # ---- meta: colors and category_labels must agree ----
    if set(category_labels) != valid_categories:
        err("meta.json: 'colors' and 'category_labels' must define the same "
            f"category keys (colors={sorted(valid_categories)}, "
            f"labels={sorted(category_labels)})")

    # ---- nodes ----
    node_ids = set()
    required_node_fields = {
        "id": str, "label": str, "category": str, "size": (int, float),
        "role": str, "bio": str, "sources": list, "verification": str,
    }
    for i, n in enumerate(nodes):
        where = f"nodes[{i}]"
        if not isinstance(n, dict):
            err(f"{where}: must be an object")
            continue
        nid = n.get("id", "")
        where = f"node '{nid}'" if nid else where

        for field, typ in required_node_fields.items():
            if field not in n:
                err(f"{where}: missing required field '{field}'")
            elif not isinstance(n[field], typ):
                err(f"{where}: field '{field}' must be {typ}")

        if nid:
            if not ID_RE.match(nid):
                err(f"{where}: id must match [a-z0-9_]+ (snake_case)")
            if nid in node_ids:
                err(f"{where}: duplicate node id")
            node_ids.add(nid)

        cat = n.get("category")
        if cat and cat not in valid_categories:
            err(f"{where}: category '{cat}' not in meta.json colors "
                f"{sorted(valid_categories)}")

        size = n.get("size")
        if isinstance(size, (int, float)) and size <= 0:
            err(f"{where}: size must be positive")

        # no-fabrication: sources must exist and be well-formed
        sources = n.get("sources")
        if isinstance(sources, list):
            if not sources:
                err(f"{where}: every node needs at least one primary source")
            for j, s in enumerate(sources):
                if not isinstance(s, dict):
                    err(f"{where}: sources[{j}] must be an object")
                    continue
                if not s.get("text"):
                    err(f"{where}: sources[{j}] missing 'text'")
                url = s.get("url", "")
                if not url:
                    err(f"{where}: sources[{j}] missing 'url'")
                elif not URL_RE.match(url):
                    err(f"{where}: sources[{j}] url should start with http(s):// "
                        f"(got '{url}')")

        # no-fabrication: speculative claims must be self-labelled
        verif = (n.get("verification") or "").lower()
        if not verif:
            err(f"{where}: verification note must not be empty")
        elif "inferred" in verif and "requires verification" not in verif:
            warn(f"{where}: verification says 'inferred' but not 'requires "
                 f"verification' - please make the caveat explicit")

    # ---- edges ----
    edge_pairs = set()
    for i, e in enumerate(edges):
        where = f"edges[{i}]"
        if not isinstance(e, dict):
            err(f"{where}: must be an object")
            continue
        src, dst = e.get("src"), e.get("dst")
        where = f"edge {src}->{dst}" if src and dst else where
        for field in ("src", "dst", "label", "title"):
            if field not in e:
                err(f"{where}: missing required field '{field}'")
        if src and src not in node_ids:
            err(f"{where}: src '{src}' is not a defined node id")
        if dst and dst not in node_ids:
            err(f"{where}: dst '{dst}' is not a defined node id")
        if "width" in e and not isinstance(e["width"], (int, float)):
            err(f"{where}: width must be a number")
        if "dashes" in e and not isinstance(e["dashes"], bool):
            err(f"{where}: dashes must be true/false")
        if src and dst:
            if (src, dst) in edge_pairs:
                warn(f"{where}: duplicate edge (same src/dst pair)")
            edge_pairs.add((src, dst))

    # ---- meta id references ----
    for key in ("subgraph_ids", "nexus_ids"):
        for ref in meta.get(key, []):
            if ref not in node_ids:
                err(f"meta.json: {key} references unknown node id '{ref}'")

    return report()


def report():
    for w in warnings:
        print(f"WARNING: {w}")
    for e in errors:
        print(f"ERROR:   {e}")
    if errors:
        print(f"\nFAILED: {len(errors)} error(s), {len(warnings)} warning(s).")
        return 1
    print(f"OK: data is valid ({len(warnings)} warning(s)).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
