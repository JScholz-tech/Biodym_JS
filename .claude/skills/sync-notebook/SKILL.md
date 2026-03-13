---
name: sync-notebook
description: Sync a Jupytext .py notebook to its .ipynb counterpart
argument-hint: <filename.py>
---

Sync the given `.py` file to its `.ipynb` counterpart using Jupytext.

Steps:
1. If `$ARGUMENTS` is provided, use that as the file path. Otherwise, look at recent file edits in the conversation to determine which `.py` notebook was last modified.
2. Run: `uv run jupytext --to notebook $ARGUMENTS`
3. Confirm success by reporting the output.
4. Remind the user to restart the kernel if any `02_src/` modules were also changed.

If no argument is given and no recent `.py` notebook edit is obvious, ask the user which file to sync.
