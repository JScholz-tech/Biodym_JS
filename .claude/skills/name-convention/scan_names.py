#!/usr/bin/env python
"""Scan (and optionally fix) flow/process `name:` fields in a study config.yaml
against the BioDYM naming convention (see CONVENTION.md in this folder).

Touches ONLY the human-readable `name:` scalars of flows and processes. IDs,
parameter names, endpoints, and every other field are left byte-for-byte
untouched — apply mode does targeted single-line replacement, not a YAML
round-trip, so diffs stay minimal.

Usage
    # scan + report (no writes)
    uv run python .claude/skills/name-convention/scan_names.py <study>
    # machine-readable findings
    uv run python .claude/skills/name-convention/scan_names.py <study> --json
    # apply explicit approved renames (repeatable)
    uv run python .claude/skills/name-convention/scan_names.py <study> \
        --set F_00_01="Printer (new)" --set P11="HDD/Motherboard"
    # apply every deterministic auto-fix (strip ID prefix, spacing, trim);
    # skips findings whose fix needs a human (placeholder / missing material)
    uv run python .claude/skills/name-convention/scan_names.py <study> --apply-suggested

`<study>` is a folder name under 01_data/01_input/case_studies/, a path to that
folder, or a path to a config.yaml.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

import yaml

CASE_STUDIES = Path("01_data/01_input/case_studies")

FLOW_ID_FRAGMENT = re.compile(r"F_\d+_\d+(?:_\d+)?")
FLOW_ID_PREFIX = re.compile(r"^F_\d+_\d+(?:_\d+)?_")
PROCESS_DEFAULT = re.compile(r"^Process \d+$")
FLOW_DEFAULT = re.compile(r"^Flow \d+$")
BAD_PAREN_SPACE = re.compile(r"\S\(|\(\s|\s\)")  # no-space-before / space-after-open / space-before-close


# --------------------------------------------------------------------------- #
# Locate + load
# --------------------------------------------------------------------------- #
def resolve_config(study: str) -> Path:
    p = Path(study)
    candidates = [
        p if p.name == "config.yaml" else p / "config.yaml",
        CASE_STUDIES / study / "config.yaml",
    ]
    for c in candidates:
        if c.is_file():
            return c
    sys.exit(f"error: no config.yaml found for study '{study}'")


def brackets_balanced(s: str) -> bool:
    depth_round = depth_square = 0
    for ch in s:
        if ch == "(":
            depth_round += 1
        elif ch == ")":
            depth_round -= 1
        elif ch == "[":
            depth_square += 1
        elif ch == "]":
            depth_square -= 1
        if depth_round < 0 or depth_square < 0:
            return False
    return depth_round == 0 and depth_square == 0


def spacing_fixed(name: str) -> str:
    """Normalise `Foo(Bar)` / `Foo ( Bar )` -> `Foo (Bar)` and trim."""
    n = (name or "").strip()
    n = re.sub(r"\s*\(\s*", " (", n)
    n = re.sub(r"\s*\)", ")", n)
    return n


# --------------------------------------------------------------------------- #
# Rule engine
# --------------------------------------------------------------------------- #
def finding(kind, ident, severity, current, reason, suggestion=None, auto=True):
    return {
        "kind": kind,          # "flow" | "process"
        "id": ident,
        "severity": severity,  # "ERROR" | "WARN"
        "current": current,
        "reason": reason,
        "suggestion": suggestion,  # str, or None when a human must decide
        # auto=True  -> a safe mechanical fix (prefix strip, spacing, trim,
        #               casing) that --apply-suggested may apply unattended.
        # auto=False -> a semantic reshape or a guess that needs human sign-off
        #               (fold status into core, add a destination); shown in the
        #               report but never bulk-applied.
        "auto": auto,
    }


def has_destination(name: str) -> bool:
    """True when the name carries a `(to …)` destination qualifier."""
    return bool(re.search(r"\(\s*to\b", name or "", re.I))


def core_with_status(name: str) -> str:
    """Reduce a name to its `Material_Status` core: strip any ID prefix, drop a
    `(to …)` destination, and fold a non-destination status paren into the
    underscore core. `Printer (Reman)` -> `Printer_Reman`;
    `F_05_03_Straw (to WEEE)` -> `Straw`."""
    n = FLOW_ID_PREFIX.sub("", name or "").strip()
    m = re.search(r"^(.*?)\s*\(([^)]*)\)\s*$", n)
    if m:
        head, inside = m.group(1).strip(), m.group(2).strip()
        if inside.lower().startswith("to "):
            return spacing_fixed(head)                       # destination -> drop
        return (head + "_" + inside.replace(" ", "_")).strip("_")  # status -> fold
    return spacing_fixed(n)


def scan(cfg: dict) -> list[dict]:
    pname = {p["id"]: (p.get("name") or "") for p in cfg.get("processes", [])}
    findings: list[dict] = []

    # ---- processes ----
    for p in cfg.get("processes", []):
        pid, name = p["id"], (p.get("name") or "")
        tag = f"P{pid}"
        if not name.strip():
            findings.append(finding("process", tag, "ERROR", name,
                            "empty name", suggestion=None))
            continue
        if PROCESS_DEFAULT.match(name) or name == tag:
            findings.append(finding("process", tag, "ERROR", name,
                            "placeholder default name", suggestion=None))
        if not brackets_balanced(name):
            findings.append(finding("process", tag, "ERROR", name,
                            "unbalanced brackets", suggestion=None))
        fixed = spacing_fixed(name)
        if fixed != name:
            findings.append(finding("process", tag, "WARN", name,
                            "spacing / trim", suggestion=fixed))
        if name[:1].islower():
            findings.append(finding("process", tag, "WARN", name,
                            "not Title Case", suggestion=name[:1].upper() + name[1:]))

    # ---- flows ----
    # group outflows by (from_process, Material_Status core) to catch splits
    # where two flows share a core and can't be told apart without a destination
    by_split: dict[tuple, list] = {}
    for f in cfg.get("flows", []):
        key = (f["from_process"], core_with_status(f.get("name", "")).lower())
        by_split.setdefault(key, []).append(f)

    for f in cfg.get("flows", []):
        fid = str(f["id"])
        name = f.get("name") or ""
        frm, to = f["from_process"], f["to_process"]
        default_join = f"{pname.get(frm, '')}_{pname.get(to, '')}"
        dest = pname.get(to, f"P{to}")
        core = core_with_status(name)

        if not name.strip():
            findings.append(finding("flow", fid, "ERROR", name, "empty name",
                            suggestion=f"⟨Material_Status⟩ (to {dest})", auto=False))
            continue
        if FLOW_DEFAULT.match(name) or name == default_join:
            findings.append(finding("flow", fid, "ERROR", name,
                            "placeholder default name",
                            suggestion=f"⟨Material_Status⟩ (to {dest})", auto=False))
        if name == fid:
            findings.append(finding("flow", fid, "ERROR", name,
                            "name equals the flow ID", suggestion=None, auto=False))
        m = FLOW_ID_PREFIX.match(name)
        if m:
            # strip the F_x_x_ prefix, then collapse the author's `_` separator
            # that sat between material and qualifier (`Foo_(bar)` -> `Foo (bar)`)
            stripped = re.sub(r"_+\(", " (", FLOW_ID_PREFIX.sub("", name))
            stripped = spacing_fixed(stripped)
            findings.append(finding("flow", fid, "ERROR", name,
                            "name echoes the flow ID (drifts on rewire)",
                            suggestion=stripped))
        elif FLOW_ID_FRAGMENT.search(name):
            findings.append(finding("flow", fid, "ERROR", name,
                            "name contains an F_x_x ID fragment",
                            suggestion=None, auto=False))
        if not brackets_balanced(name):
            findings.append(finding("flow", fid, "ERROR", name,
                            "unbalanced brackets", suggestion=None, auto=False))

        # body = name minus any ID prefix, for status/spacing checks. A status
        # paren is a *trailing* `(…)` that isn't a destination — a mid-name paren
        # (e.g. `Lithosphere(P&I)_Emissions`) is part of the material token.
        body = FLOW_ID_PREFIX.sub("", name).strip()
        status_paren = bool(re.search(r"\([^)]*\)\s*$", body)) and not has_destination(body)
        siblings = by_split.get((frm, core.lower()), [])

        if len(siblings) > 1 and not has_destination(name):
            # ambiguous split: same Material_Status core out of one process,
            # this flow has no (to …) to tell it apart
            findings.append(finding("flow", fid, "ERROR", name,
                            f"ambiguous split: {len(siblings)} flows share core "
                            f"'{core}' out of P{frm} — add a (to Destination)",
                            suggestion=f"{core} (to {dest})", auto=False))
        elif status_paren:
            # a paren that isn't a destination is a status → fold into the core
            findings.append(finding("flow", fid, "WARN", name,
                            "status in parentheses — fold into the Material_Status core",
                            suggestion=core, auto=False))

        if not m and not status_paren:
            fixed = spacing_fixed(name)
            if fixed != name:
                findings.append(finding("flow", fid, "WARN", name,
                                "spacing / trim", suggestion=fixed))
        if name[:1].islower():
            findings.append(finding("flow", fid, "WARN", name,
                            "not Title Case", suggestion=name[:1].upper() + name[1:]))

    # duplicate names within a kind
    for kind, items in (("flow", cfg.get("flows", [])), ("process", cfg.get("processes", []))):
        seen: dict[str, list] = {}
        for it in items:
            ident = str(it["id"]) if kind == "flow" else f"P{it['id']}"
            seen.setdefault((it.get("name") or "").strip(), []).append(ident)
        for nm, ids in seen.items():
            if nm and len(ids) > 1:
                for ident in ids:
                    findings.append(finding(kind, ident, "WARN", nm,
                                    f"duplicate name shared with {', '.join(i for i in ids if i != ident)}",
                                    suggestion=None))
    return findings


# --------------------------------------------------------------------------- #
# Report
# --------------------------------------------------------------------------- #
def print_report(cfg: dict, findings: list[dict]) -> None:
    errs = [f for f in findings if f["severity"] == "ERROR"]
    warns = [f for f in findings if f["severity"] == "WARN"]
    print(f"\n{cfg.get('name', '?')}: {len(cfg.get('processes', []))} processes, "
          f"{len(cfg.get('flows', []))} flows")
    print(f"  {len(errs)} ERROR, {len(warns)} WARN\n")
    if not findings:
        print("  ✓ all names conform.")
        return
    order = {"ERROR": 0, "WARN": 1}
    for f in sorted(findings, key=lambda x: (order[x["severity"]], x["kind"], x["id"])):
        sug = f"  →  {f['suggestion']!r}" if f["suggestion"] else "  →  (needs a human)"
        print(f"  [{f['severity']:<5}] {f['kind']:<7} {f['id']:<14} {f['current']!r}")
        print(f"          {f['reason']}{sug}")
    print("\n  Apply a fix:  --set <ID>=\"New name\"   (ID = flow id like F_05_06, or P<n>)")
    print("  Auto-fix all deterministic suggestions:  --apply-suggested")


# --------------------------------------------------------------------------- #
# Apply — targeted single-line replacement (no YAML round-trip)
# --------------------------------------------------------------------------- #
def yaml_scalar(value: str) -> str:
    """Render a string as pyyaml would after `name: ` (handles quoting)."""
    dumped = yaml.safe_dump({"name": value}, default_flow_style=False,
                            allow_unicode=True, sort_keys=False).rstrip("\n")
    return dumped[len("name:"):].strip()


def apply_sets(path: Path, renames: dict[str, str]) -> list[tuple[str, str, str]]:
    """Replace the `name:` line of each flow/process item whose id is a key in
    `renames`. Returns list of (id, old, new) actually changed."""
    lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
    section = None            # "processes" | "flows" | other
    cur_id = None             # id of the item currently open
    changed: list[tuple[str, str, str]] = []
    pending = dict(renames)

    top = re.compile(r"^(\w[\w_]*):")
    item_id = re.compile(r"^- id:\s*(.+?)\s*$")
    name_line = re.compile(r"^  name:\s*(.*)$")

    for i, line in enumerate(lines):
        mt = top.match(line)
        if mt:
            section = mt.group(1)
            cur_id = None
            continue
        if section not in ("processes", "flows"):
            continue
        mi = item_id.match(line)
        if mi:
            raw = mi.group(1).strip()
            cur_id = ("P" + raw) if section == "processes" else raw.strip("'\"")
            continue
        mn = name_line.match(line)
        if mn and cur_id is not None and cur_id in pending:
            new = pending.pop(cur_id)
            old_val = mn.group(1)
            newline = f"  name: {yaml_scalar(new)}\n" if line.endswith("\n") else f"  name: {yaml_scalar(new)}"
            lines[i] = newline
            changed.append((cur_id, old_val, new))
            cur_id = None  # only the item's own name (2-space) can match

    if pending:
        sys.exit(f"error: id(s) not found in {path.name}: {', '.join(pending)}")
    path.write_text("".join(lines), encoding="utf-8")
    return changed


def suggested_map(findings: list[dict]) -> dict[str, str]:
    """Safe mechanical auto-fixes only: `auto` findings with a concrete
    suggestion. Semantic reshapes (fold status, add destination) and ⟨…⟩
    placeholders are excluded — those go through explicit --set."""
    out: dict[str, str] = {}
    for f in findings:
        s = f["suggestion"]
        if f.get("auto") and s and "⟨" not in s:
            out.setdefault(f["id"], s)
    return out


# --------------------------------------------------------------------------- #
def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("study")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--set", action="append", default=[], metavar="ID=NAME")
    ap.add_argument("--apply-suggested", action="store_true")
    args = ap.parse_args()

    try:  # Windows consoles default to cp1252; names/suggestions use →, ⟨⟩, ✓
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

    path = resolve_config(args.study)
    cfg = yaml.safe_load(path.read_text(encoding="utf-8"))
    findings = scan(cfg)

    if args.set or args.apply_suggested:
        renames = {}
        if args.apply_suggested:
            renames.update(suggested_map(findings))
        for pair in args.set:
            if "=" not in pair:
                sys.exit(f"error: --set expects ID=NAME, got '{pair}'")
            k, v = pair.split("=", 1)
            renames[k.strip()] = v.strip()
        changed = apply_sets(path, renames)
        for cid, old, new in changed:
            print(f"  {cid:<14} {old!r}  ->  {new!r}")
        print(f"\n  {len(changed)} name(s) updated in {path}")
        return

    if args.json:
        print(json.dumps(findings, ensure_ascii=False, indent=2))
    else:
        print_report(cfg, findings)


if __name__ == "__main__":
    main()
