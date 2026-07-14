"""Element list + hierarchy editor routes, and the shared rules→paths helper
used by every hierarchy-matrix page.

Moved verbatim from ``main.py``.
"""
from __future__ import annotations

import re

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import RedirectResponse

from systemdefiner import storage
from systemdefiner.deps import _ctx, templates
from systemdefiner.models.config_schema import ElementHierarchyRule

router = APIRouter()


def _rules_to_paths(rules: list) -> list[list[str]]:
    """Convert ElementHierarchyRule list to path-rows for the matrix editor."""
    parent_to_children: dict[str, list] = {}
    child_to_parent: dict[str, str] = {}
    for rule in rules:
        parent_to_children[rule.parent] = list(rule.children)
        for child in rule.children:
            child_to_parent[child] = rule.parent

    all_elems: set[str] = set(parent_to_children.keys())
    for rule in rules:
        all_elems.update(rule.children)

    leaves = [e for e in all_elems if e not in parent_to_children]
    if not leaves and all_elems:
        leaves = list(all_elems)

    def get_path(elem: str) -> list[str]:
        path: list[str] = []
        cur: str | None = elem
        while cur:
            path.insert(0, cur)
            cur = child_to_parent.get(cur)
        return path

    # Pad all paths to the deepest path present (hierarchy depth is not capped).
    raw_paths = [get_path(leaf) for leaf in sorted(leaves)]
    depth = max((len(p) for p in raw_paths), default=0)
    paths = [p + [""] * (depth - len(p)) for p in raw_paths]
    paths.sort()
    return paths


@router.get("/{name}/elements")
async def elements_form(request: Request, name: str):
    if not storage.case_study_exists(name):
        raise HTTPException(404)
    cfg = storage.load_case_study(name)
    import json as _json

    paths_json = _json.dumps(_rules_to_paths(cfg.element_hierarchy))
    elements_json = _json.dumps(cfg.model.elements)
    return templates.TemplateResponse(
        request,
        "elements.html",
        _ctx(cfg=cfg, paths_json=paths_json, elements_json=elements_json),
    )


@router.post("/{name}/elements")
async def elements_save(request: Request, name: str):
    from collections import defaultdict as _defaultdict

    form = await request.form()
    cfg = storage.load_case_study(name)

    # ── Element list ─────────────────────────────────────────────────────────
    elements: list[str] = []
    idx = 0
    while True:
        key = f"element_{idx}"
        if key not in form:
            break
        val = (form[key] or "").strip()
        if val:
            elements.append(val)
        idx += 1
        if idx > 200:
            break
    if elements:
        # The first element is the conserved total-mass balance / hierarchy root;
        # the engine requires it to be named "material". Enforce it defensively
        # (the editor locks the field, but guard against import/manual edits).
        if elements[0] != "material":
            elements = ["material"] + [e for e in elements if e != "material"]
        cfg.model.elements = elements

    # ── Level names ──────────────────────────────────────────────────────────
    # Hierarchy depth is user-extensible: collect however many level_name_{i}
    # fields the editor submitted (tolerant of gaps), not a fixed 4.
    level_indices = sorted(
        {
            int(m.group(1))
            for key in form.keys()
            if (m := re.fullmatch(r"level_name_(\d+)", key))
        }
    )
    level_names = [(form.get(f"level_name_{i}") or "").strip() for i in level_indices]
    level_names = [n for n in level_names if n]
    if level_names:
        cfg.model.hierarchy_level_names = level_names
    n_levels = len(cfg.model.hierarchy_level_names)

    # ── Path rows → hierarchy rules ──────────────────────────────────────────
    # Collect row indices tolerantly: the client may leave gaps in the
    # path_{i}_* numbering (a removal followed by an add), so never stop at the
    # first missing index — that would silently truncate every row past the gap.
    parent_to_children: dict[str, set] = _defaultdict(set)
    path_indices = sorted(
        {
            int(m.group(1))
            for key in form.keys()
            if (m := re.fullmatch(r"path_(\d+)_l1", key))
        }
    )
    for pidx in path_indices:
        # Read as many level columns as the hierarchy has (l1..l{n_levels}).
        cells = [
            (form.get(f"path_{pidx}_l{level}") or "").strip()
            for level in range(1, n_levels + 1)
        ]
        # Collect consecutive non-empty pairs as parent→child
        for i in range(len(cells) - 1):
            if cells[i] and cells[i + 1]:
                parent_to_children[cells[i]].add(cells[i + 1])

    cfg.element_hierarchy = [
        ElementHierarchyRule(parent=p, children=sorted(ch))
        for p, ch in parent_to_children.items()
    ]

    storage.save_case_study(cfg)
    return RedirectResponse(f"/{name}/elements", status_code=303)


# Keep /hierarchy as alias for backwards compatibility
@router.get("/{name}/hierarchy")
async def hierarchy_redirect(name: str):
    return RedirectResponse(f"/{name}/elements", status_code=301)
