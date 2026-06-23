# BioDYM — Getting Started From Zero

A complete, no-prior-knowledge guide to installing everything you need and running
BioDYM for the first time. **You do not need to know how to program.** Just follow
the steps in order.

> **What is BioDYM?** A tool that analyses how biological materials (straw, compost,
> organic waste, carbon…) flow and accumulate through a system over time. You give it
> data (an Excel file or a config you build in a visual editor), and it produces
> charts, mass balances, and tables.

**Estimated time:** 30–45 minutes, most of it waiting for downloads.

---

## What you will install

You only need **two** things. One tool (`uv`) automatically handles the rest
(Python, Jupyter, and ~30 scientific libraries) for you — so don't install Python
separately.

| Tool | What it is | Why you need it |
|------|-----------|-----------------|
| **VS Code** | A free code/text editor from Microsoft | To open the project and run a terminal |
| **uv** | A fast Python project manager | It installs the correct Python, Jupyter, and all libraries automatically |

> You may have heard you need to "install Python" and "install Jupyter" yourself.
> With `uv` you **don't** — it downloads the exact Python version BioDYM needs and
> every library, all into a self-contained folder inside the project. Nothing is
> installed system-wide, so it can't break other software on your computer.

---

## Step 1 — Install VS Code

1. Go to **https://code.visualstudio.com**
2. Click the big download button (it auto-detects Windows/Mac).
3. Run the installer. On Windows, **tick "Add to PATH"** if asked (it usually is by
   default). Accept the defaults for everything else.
4. Launch VS Code once to confirm it opens.

### Add the Python & Jupyter extensions (recommended)

Inside VS Code:

1. Click the **Extensions** icon in the left bar (four squares) — or press
   `Ctrl+Shift+X`.
2. Search for **"Python"** (by Microsoft) → click **Install**.
3. Search for **"Jupyter"** (by Microsoft) → click **Install**.

These let you open notebooks directly inside VS Code.

---

## Step 2 — Install uv (this also gives you Python)

`uv` is installed with a single command. You'll use VS Code's built-in terminal.

1. In VS Code, open the terminal: menu **Terminal → New Terminal**
   (or press `` Ctrl+` `` — the backtick key, top-left of most keyboards).
2. Copy the command for your system, paste it into the terminal, and press **Enter**.

**On Windows** (PowerShell — this is what VS Code opens by default on Windows):

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

**On macOS / Linux:**

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

3. **Close the terminal and open a new one** (Terminal → New Terminal). This is
   important — it lets your computer "find" the newly installed `uv`.
4. Verify it worked by typing:

```powershell
uv --version
```

You should see something like `uv 0.5.x`. If you get "command not found", restart
VS Code completely and try again.

> You never have to install Python yourself. When you run `uv sync` in Step 4, `uv`
> reads BioDYM's requirements, downloads the right Python version automatically, and
> sets everything up.

---

## Step 3 — Get the BioDYM project onto your computer

Pick **one** of the two options below.

> **Which should I choose?** If you expect to receive updates to BioDYM (almost
> everyone does), use **Option A (Git)**. Updating then takes two commands instead of
> re-downloading and re-unzipping the whole project — and you won't lose any data or
> config you added to the folder. Only use the ZIP (Option B) for a quick one-time
> look.

### Option A — Use Git (recommended — makes updates painless)

First install Git (a small tool that downloads the project and later fetches updates):

1. Go to **https://git-scm.com/downloads** and download Git for your system.
2. Run the installer. **Accept every default** — there are several screens, just keep
   clicking *Next*. (The defaults are correct for BioDYM; you don't need to understand
   the options.)
3. **Fully close and reopen VS Code** so it can find the newly installed Git.

Then download the project. In a VS Code terminal (**Terminal → New Terminal**), run:

```powershell
git clone https://github.com/JScholz-tech/Biodym_JS.git
```

This creates a `Biodym_JS` folder in whatever location the terminal is pointing at
(by default your user folder). Then in VS Code: **File → Open Folder…** → select that
new `Biodym_JS` folder.

> **Verify Git works:** run `git --version` in the terminal. If you see a version
> number, you're good. "command not found" usually means you need to fully restart
> VS Code.

### Option B — Download as a ZIP (quick one-time look, no updates)

1. Go to the project page: **https://github.com/JScholz-tech/Biodym_JS**
2. Click the green **`< > Code`** button → **Download ZIP**.
3. Unzip it somewhere easy to find, e.g. your **Documents** folder.
4. In VS Code: **File → Open Folder…** and select the unzipped `Biodym_JS` folder.

> A ZIP is a frozen snapshot. To get a newer version later you'd download and unzip
> again from scratch — which is exactly why Option A is recommended.

---

> **You're "in" the project when** the VS Code title bar / Explorer panel shows the
> project files (`00_BioDYM_Workflow.ipynb`, `pyproject.toml`, the `02_src` folder,
> etc.) and the terminal prompt is inside that folder.

---

## Step 4 — Install BioDYM's environment

With the project folder open in VS Code, open a terminal
(**Terminal → New Terminal**) and run:

```powershell
uv sync
```

**What this does:** downloads the correct Python, creates a private `.venv` folder
inside the project, and installs Jupyter plus every scientific library BioDYM needs.

**This is the longest step** — it downloads a few hundred MB the first time. Wait
until you get your terminal prompt back. (Future runs are nearly instant because
everything is cached.)

> **Golden rule:** From now on, always start your commands with **`uv run`**.
> That prefix tells your computer to use the project's private environment instead of
> hunting for a system Python that may not exist. `uv run jupyter …`,
> `uv run python …`, and so on.

---

## Step 5 — Run BioDYM

There are three ways to use BioDYM. If you're brand new, start with **A**.

### A) The dashboard — point-and-click, zero coding (best first experience)

```powershell
uv run voila 01_BioDYM_Dashboard.ipynb
```

A tab opens in your web browser with interactive charts and controls. When you're
done, return to the terminal and press `Ctrl+C` to stop it.

### B) The analysis notebook — the full, guided workflow

```powershell
uv run jupyter lab
```

Your browser opens **Jupyter Lab**. In the file list on the left, double-click
**`00_BioDYM_Workflow.ipynb`**. Then in the top menu choose
**Kernel → Restart Kernel and Run All Cells**. The notebook runs top to bottom and
produces all the charts and tables.

- It already points at a working example file, so it runs out of the box.
- To use your own data, find the cell near the top that sets `input_file = ...` and
  change it to your own Excel file or `config.yaml`, then run all cells again.

When finished, go back to the terminal and press `Ctrl+C` to shut Jupyter down.

### C) The SystemDefiner — build your own system visually (optional)

If you want to design your own system without editing Excel by hand:

```powershell
uv run python -m systemdefiner
```

Then open **http://localhost:8001** in your browser. Lay out your processes and
flows, and export a `config.yaml` that you can feed into the notebook (option B).
Press `Ctrl+C` in the terminal to stop it.

---

## Updating BioDYM later

> This works only if you got the project with **Git** (Step 3, Option A). ZIP users
> have to download a fresh ZIP instead.

When a newer version of BioDYM is released, open the project folder in VS Code, open
a terminal, and run these **two** commands:

```powershell
git pull
uv sync
```

- `git pull` downloads the latest code changes.
- `uv sync` installs any new or updated libraries the new version needs.

That's the whole update. Your own files in `01_data/` (Excel inputs, outputs, your
`config.yaml`) are left untouched.

> **If `git pull` reports a conflict** (because you edited a tracked file), the
> simplest fix is to copy your changed file somewhere safe, run
> `git checkout -- <that file>` to discard the local change, then `git pull` again.
> If unsure, ask whoever maintains the project rather than guessing.

---

## Everyday cheat sheet

Once installed, this is all you need day to day. Open the project folder in VS Code,
open a terminal, and run:

| I want to… | Command |
|------------|---------|
| Open the click-through dashboard | `uv run voila 01_BioDYM_Dashboard.ipynb` |
| Open the full analysis notebook | `uv run jupyter lab` |
| Build a system visually | `uv run python -m systemdefiner` → http://localhost:8001 |
| Update BioDYM to the latest version (Git only) | `git pull` then `uv sync` |
| Stop any running tool | Press `Ctrl+C` in the terminal |

---

## Troubleshooting

**`uv` is not recognized / "command not found"**
You opened the terminal before installing `uv`, or didn't restart it. Fully close
VS Code, reopen it, open a new terminal, and try `uv --version` again.

**`uv sync` fails or seems stuck**
Check your internet connection (it downloads a lot the first time). If it errored,
just run `uv sync` again — it safely resumes.

**A command "can't find" Python or a library**
You probably forgot the `uv run` prefix. `python xyz` won't work; `uv run python xyz`
will.

**The browser tab didn't open by itself**
Look in the terminal output for a line with a web address (e.g.
`http://localhost:8888/...` or `http://localhost:8001`) and paste it into your
browser manually.

**"Port already in use"**
A previous run is still going. Find that terminal and press `Ctrl+C`, or just close
all terminals and start fresh.

**I edited a `.py` file in `02_src/` but the notebook didn't change**
Restart the notebook's kernel: **Kernel → Restart Kernel and Run All Cells**.
BioDYM does not auto-reload changed code.

**`git` is not recognized**
You ran a `git` command before installing Git, or didn't restart VS Code afterward.
Install Git (Step 3, Option A), fully close and reopen VS Code, then try
`git --version`.

**Still stuck?** See the detailed [README](README.md), or open an issue at
https://github.com/JScholz-tech/Biodym_JS/issues.

---

## Quick recap

1. Install **VS Code** → add **Python** + **Jupyter** extensions.
2. Install **uv** (one command) — it brings Python with it.
3. Install **Git**, then `git clone` the project and open the folder in VS Code.
   *(Or download a ZIP for a one-time look.)*
4. Run **`uv sync`** once.
5. Run **`uv run voila 01_BioDYM_Dashboard.ipynb`** (or `uv run jupyter lab`).
6. Later, update anytime with **`git pull`** then **`uv sync`**.

That's it — you're running BioDYM.
