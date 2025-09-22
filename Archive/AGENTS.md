# Repository Guidelines

## Project Structure & Module Organization
- **Core Tool:** `biodym_mfa_tool/`
  - `src/` (Python source: CLI in `main_cli.py`, engines in `src/engine/`, plotting in `src/plotting/`)
  - `test/` (unit/integration tests) and `test_data/` (fixtures)
  - `data/` (project templates and example inputs/outputs)
  - `framework/` (vendor dependencies: ODYM + BioDYM add‑ons)
- **Root:** `pyproject.toml` (Python ≥3.13), `uv.lock`, top‑level `data/01_input` and `02_output`, docs in `README.md`, legacy in `Archive/`.

## Build, Test, and Development Commands
- **Create env:** `uv venv && source .venv/bin/activate`
- **Install deps:** `uv sync`
- **Run tests:** `uv run pytest -q`
- **Run CLI locally:**
  - `uv run python biodym_mfa_tool/src/main_cli.py --input data/01_input/250625_Template_CS0.xlsx --output data/02_output/results.xlsx --summary`

Tip: Manage all dependencies via `uv add …` and `uv sync`. Do not use legacy `uv pip` or `pip`.

## Coding Style & Naming Conventions
- **Language:** Python 3.13+. Use type hints and docstrings.
- **Indentation/line length:** 4 spaces; prefer ≤100 chars.
- **Naming:** modules/functions `snake_case`; classes `PascalCase`; constants `UPPER_SNAKE_CASE`.
- **Imports:** standard → third‑party → local; avoid circular imports across `src/engine` and `src/plotting`.

## Testing Guidelines
- **Framework:** `pytest` (see `biodym_mfa_tool/pytest.ini`).
- **Layout:** put unit tests in `biodym_mfa_tool/test/` (files `test_*.py`); use `test_data/` for fixtures.
- **Running:** `pytest -q` or filter with `-k name`.
- **Coverage focus:** data loading, engine (`solver.py`, `fomp_model.py`), and CLI paths.

## Commit & Pull Request Guidelines
- **Commits:** follow Conventional Commits when possible
  - Examples: `feat(engine): implement 2‑pool FOMP`, `fix(plotting): correct node layout`
- **PR checklist:**
  - Clear description + scope; link issues.
  - Screenshots or exported files for visualization changes (e.g., Sankey outputs).
  - Tests updated/added; `pytest -q` passes locally.
  - Avoid touching `framework/` unless necessary; document rationale if changed.

## Security & Configuration Tips
- Do not commit large outputs or sensitive datasets; keep results in `data/02_output/`.
- Excel paths in CLI should point to `data/01_input/`; validate with `--summary` before exporting.
