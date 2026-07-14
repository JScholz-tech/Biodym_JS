"""Element list + hierarchy editor routes, and the shared rules→paths helper
used by every hierarchy-matrix page.

Moved verbatim from ``main.py``.
"""
from __future__ import annotations

import re

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import RedirectResponse

from systemdefiner import storage
from systemdefiner.consistency import _element_key_sites
from systemdefiner.deps import _ctx, templates
from systemdefiner.models.config_schema import ElementHierarchyRule

router = APIRouter()

# Scenario/MC parameter names that embed a 1-based element position: the
# transformer TC names and the initial-stock fraction names.
_TC_E_NAME = re.compile(r"TC_E(\d+)_(\d+)_(\d+)")
_IS_E_NAME = re.compile(r"P(\d+)_IS_E(\d+)_\[%\]\((.*)\)")


def _remap_element_positions(name: str, e_map: dict, rename_map: dict) -> str:
    """Rewrite the E{n} element position (and, for IS names, the embedded
    element name) in a scenario/MC parameter name after the element list was
    reordered or renamed. Names whose position has no mapping (element
    removed) are returned unchanged — the consistency checker reports them."""
    name = (name or "").strip()
    m = _TC_E_NAME.fullmatch(name)
    if m and int(m.group(1)) in e_map:
        return f"TC_E{e_map[int(m.group(1))]}_{m.group(2)}_{m.group(3)}"
    m = _IS_E_NAME.fullmatch(name)
    if m and int(m.group(2)) in e_map:
        elem = rename_map.get(m.group(3), m.group(3))
        return f"P{m.group(1)}_IS_E{e_map[int(m.group(2))]}_[%]({elem})"
    return name


def _apply_element_edits(cfg, rename_map: dict, removed: set, e_map: dict) -> None:
    """Cascade element renames/removals through every element-keyed value and
    remap positional E{n} references in scenario/MC parameter names."""

    def _rewrite(d: dict) -> None:
        for old, new in rename_map.items():
            if old in d:
                d[new] = d.pop(old)
        for gone in removed:
            d.pop(gone, None)

    for _label, d in _element_key_sites(cfg):
        _rewrite(d)
    for fd in cfg.flow_data:
        if fd.element in rename_map:
            fd.element = rename_map[fd.element]
    for p in cfg.processes:
        if p.dsm:
            for comp in p.dsm.components:
                if comp.element in rename_map:
                    comp.element = rename_map[comp.element]
            # a component whose element was removed has nothing to track
            p.dsm.components = [
                c for c in p.dsm.components if c.element not in removed
            ]
    if e_map or rename_map:
        for sc in cfg.scenarios:
            for mod in sc.modifications:
                mod.parameter_name = _remap_element_positions(
                    mod.parameter_name, e_map, rename_map
                )
        for mc in cfg.mc_parameters:
            mc.parameter_id = _remap_element_positions(
                mc.parameter_id, e_map, rename_map
            )


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
        seen: set[str] = set()
        while cur and cur not in seen:
            # `seen` guards against a cyclic hierarchy (e.g. A→B and B→A),
            # which would otherwise hang every page that renders the matrix;
            # the consistency checker reports the cycle itself.
            seen.add(cur)
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
    # Gap-tolerant index scan (a client-side row removal may leave holes) with
    # the row's original name carried in element_{i}_orig, so renames can be
    # cascaded instead of orphaning every value keyed by the old name.
    old_elements = list(cfg.model.elements)
    row_indices = sorted(
        {
            int(m.group(1))
            for key in form.keys()
            if (m := re.fullmatch(r"element_(\d+)", key))
        }
    )
    rows: list[tuple[str, str]] = []  # (original name, submitted name)
    for i in row_indices:
        new_name = (form.get(f"element_{i}") or "").strip()
        orig = (form.get(f"element_{i}_orig") or "").strip()
        if new_name:
            rows.append((orig, new_name))
    # Renames are only detectable when the form carries the _orig fields
    # (legacy/scripted posts without them get the old replace-only behavior).
    has_orig = any(re.fullmatch(r"element_\d+_orig", k) for k in form.keys())

    elements = [n for _, n in rows]
    if elements:
        # The first element is the conserved total-mass balance / hierarchy root;
        # the engine requires it to be named "material". Enforce it defensively
        # (the editor locks the field, but guard against import/manual edits).
        if elements[0] != "material":
            mat_row = next(
                ((o, n) for o, n in rows if n == "material"), ("material", "material")
            )
            rows = [mat_row] + [(o, n) for o, n in rows if n != "material"]
            elements = [n for _, n in rows]
        cfg.model.elements = elements

    rename_map: dict[str, str] = {}
    removed: set[str] = set()
    e_map: dict[int, int] = {}
    if has_orig and elements:
        rename_map = {
            o: n
            for o, n in rows
            if o and n and o != n and o in old_elements
        }
        removed = set(old_elements) - {o for o, _ in rows if o}
        # 1-based old→new positions for names like TC_E{n}_… / P.._IS_E{n}_…
        # (identity entries stay in the map so IS names with an unmoved
        # position still get their embedded element name renamed).
        for new_pos, (o, _n) in enumerate(rows):
            if o and o in old_elements:
                e_map[old_elements.index(o) + 1] = new_pos + 1
        _apply_element_edits(cfg, rename_map, removed, e_map)

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
        # Path cells are submitted alongside the element list, so apply the
        # same rename/removal mapping — a renamed element keeps its hierarchy
        # position, a removed one breaks the chain at that cell.
        cells = [
            (form.get(f"path_{pidx}_l{level}") or "").strip()
            for level in range(1, n_levels + 1)
        ]
        cells = [
            "" if c in removed else rename_map.get(c, c) for c in cells
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
