# BioDYM Documentation

This folder is the canonical home for BioDYM documentation.

## Start here

| Resource | What it covers |
|----------|----------------|
| [biodym_manual.pdf](biodym_manual.pdf) | Full user manual for the BioDYM tool |
| [../README.md](../README.md) | Install, quick start, project structure, citation |
| [../00_BioDYM_Workflow.ipynb](../00_BioDYM_Workflow.ipynb) | Main, runnable end-to-end analysis workflow (also the integration test) |
| [../CONTRIBUTING.md](../CONTRIBUTING.md) | How to contribute, dev setup, project layout |
| [../CHANGELOG.md](../CHANGELOG.md) | Release history |

## Using the bioDYM SystemDefiner

The SystemDefiner web app (`uv run python -m systemdefiner`, opens at
http://localhost:8001) lets you define a case study visually and export a
`config.yaml` for the workflow notebook. See the README's Quick Start for the
end-to-end path.

## A note on archived material

Older design notes and superseded planning documents may exist locally under
`development/_archive/` but are **not part of the shipped documentation** (they are
not tracked in git). Treat anything under an `_archive/` path as historical, not
current guidance.
