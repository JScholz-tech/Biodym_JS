---
name: name-convention
description: Scan a BioDYM study's flow & process name fields against the naming convention, report violations with suggestions, and apply approved renames. Use when asked to clean up / standardize / rename flows or processes in a study, or when flows are hard to identify in graphs.
argument-hint: <study-name-or-path>
---

Enforce the BioDYM flow & process **naming convention** on a study's
`config.yaml`. Governs the human-readable `name:` fields only — never the
`F_<from>_<to>` IDs or any referenced field, so renames are always safe and
never cascade.

The convention spec is `CONVENTION.md` in this skill folder — read it before
proposing wording so suggestions match the agreed scheme (flow name =
`Material (to <destination>)`; qualifier is the graph disambiguator; names must
never echo the flow ID).

The scanner/applier is `scan_names.py` in this folder. Run everything with
`uv run python`.

## Routine

1. **Resolve the study.** `$ARGUMENTS` is a folder name under
   `01_data/01_input/case_studies/`, a path to that folder, or a path to a
   `config.yaml`. If missing, ask which study.

2. **Scan (read-only).**
   ```
   uv run python .claude/skills/name-convention/scan_names.py <study>
   ```
   Relay the report: ERROR count / WARN count, then the findings table
   (id, current name, reason, suggestion). ERRORs are hard violations
   (placeholder defaults, ID-echoing names, unbalanced brackets, ambiguous
   splits). WARNs are soft (spacing, casing, duplicate labels).

3. **Propose the rename set.** For each finding, decide the new name:
   - Deterministic suggestions (strip ID prefix, fix `(` spacing, trim) — take
     them as-is; they are format-only, they do **not** invent wording.
   - `⟨material⟩` placeholders and `(needs a human)` — you must supply the real
     material and a `(to <destination>)` qualifier, using the process names and
     the study description for context. Read the config's `description` and
     surrounding topology first.
   - **Duplicate-label WARNs** are the flows that are impossible to tell apart
     in a graph — give each a distinct `(to <destination>)` qualifier. This is
     usually the whole point of the exercise.
   Present the proposed old→new table to the user and get confirmation. Do not
   apply before the user approves the wording.

4. **Apply on confirmation.** Either explicit renames:
   ```
   uv run python .claude/skills/name-convention/scan_names.py <study> \
       --set F_05_06="Printer (to storage)" --set P11="HDD/Motherboard"
   ```
   (flow id like `F_05_06`, or `P<n>` for a process), or, to take every
   deterministic auto-fix in one shot (skips placeholders / human-needed):
   ```
   uv run python .claude/skills/name-convention/scan_names.py <study> --apply-suggested
   ```
   A common flow: run `--apply-suggested` first to clear all the mechanical
   fixes, then rescan and hand-resolve the remaining ERRORs (needs-a-human) and
   duplicate-label WARNs with explicit `--set`.

5. **Verify.** Rescan; confirm the remaining findings are only ones the user
   consciously accepted. Apply mode edits only the `name:` line of each item, so
   the rest of the file is byte-for-byte unchanged — a `git diff` should show
   only name lines.

## Notes

- Names are not referenced anywhere else in the config (unlike IDs), so no
  cascade is needed — this is why the skill can edit them directly instead of
  going through the SystemDefiner cascade machinery.
- Stocks have no name field; they are labelled by their owning process's name,
  so the process-name rules cover them. The scanner lists stock-bearing
  processes implicitly (they are just processes).
- `--json` emits machine-readable findings if you need to script the decisions.
