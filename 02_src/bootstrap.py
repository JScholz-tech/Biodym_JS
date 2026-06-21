"""Shared runtime setup for BioDYM entry points.

Top-level folders are number-prefixed (``02_src``, ``06_framework``) for workflow
ordering, but a digit-prefixed directory cannot be a Python import package. So the
source root and the ODYM / bioDYM-add-on framework module directories are added to
``sys.path`` at runtime instead. These helpers centralise that logic so it is not
duplicated across the workflow notebook, ``main.py``, ``main_cli.py``, and the test
``conftest.py``.
"""

import os
import sys


def setup_paths(project_root=None):
    """Add ``02_src`` and the ODYM / bioDYM-add-on module dirs to ``sys.path``.

    Parameters
    ----------
    project_root : str, optional
        Repository root. Defaults to the current working directory.

    Returns
    -------
    str
        The resolved project root.
    """
    if project_root is None:
        project_root = os.getcwd()

    paths = [
        os.path.join(project_root, "02_src"),
        os.path.join(
            project_root, "06_framework", "ODYM-master_20241127", "odym", "modules"
        ),
        os.path.join(project_root, "06_framework", "bioDYM_add-on", "modules"),
    ]
    for path in paths:
        if path not in sys.path:
            sys.path.insert(0, path)
    return project_root


def init_widgets(delay=0.5):
    """Pre-initialise the Plotly / ipywidgets comm channel.

    Creating a throwaway ``FigureWidget`` early forces the widget communication
    channel to be established, which prevents the first real interactive plot from
    occasionally rendering empty in Jupyter / Voilà. Safe to call outside a
    notebook — any failure is swallowed with a warning.

    Returns
    -------
    bool
        ``True`` if initialisation succeeded, ``False`` otherwise.
    """
    try:
        import time

        import plotly.graph_objects as go
        from ipywidgets import IntSlider

        _fig = go.FigureWidget()
        _slider = IntSlider()
        time.sleep(delay)  # allow widget registration to complete
        del _fig, _slider
        return True
    except Exception as exc:  # pragma: no cover - environment dependent
        print(f"Widget initialization had issues: {exc}")
        return False
