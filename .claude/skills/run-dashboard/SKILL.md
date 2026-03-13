---
name: run-dashboard
description: Sync the dashboard notebook and launch it in Voilà
---

Prepare and launch the BioDYM Voilà dashboard.

Steps:
1. Sync the source file: `uv run jupytext --to notebook 01_BioDYM_Dashboard.py`
2. Launch Voilà in the background: `uv run voila 01_BioDYM_Dashboard.ipynb`
3. Tell the user that Voilà is starting and will open in their browser automatically (usually at http://localhost:8866).
4. Remind the user to set the correct input file path in the text field before clicking Run.
