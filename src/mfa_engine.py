# -*- coding: utf-8 -*-
"""
MFA Engine Module for the BioDYM Model.

This file contains the core calculation functions for the Material Flow
Analysis, including system setup, the iterative solver, and the specific
implementations for the Dynamic Stock Model (DSM) and First-Order Model
Process (FOMP).
"""

import numpy as np
import pandas as pd

# These are imported by main.py and are available in this namespace
import ODYM_Classes as msc


def define_model_scope(start_year, end_year, elements):
    """
    Defines the temporal and elemental scope of the MFA model.

    Args:
        start_year (int): The first year of the analysis.
        end_year (int): The last year of the analysis.
        elements (list): A list of strings for the elements to be tracked.

    Returns:
        tuple: A tuple containing the ModelClassification dictionary
               and the IndexTable DataFrame, which are core ODYM objects.
    """
    ModelClassification = {}
    MyYears = list(np.arange(start_year, end_year + 1))

    ModelClassification["Time"] = msc.Classification(
        Name="Time", Dimension="Time", ID=1, Items=MyYears
    )
    ModelClassification["Element"] = msc.Classification(
        Name="Elements", Dimension="Element", ID=2, Items=elements
    )

    IndexTable = pd.DataFrame(
        {
            "Aspect": ["Time", "Element"],
            "Description": ['Model aspect "time"', 'Model aspect "Element"'],
            "Dimension": ["Time", "Element"],
            "Classification": [
                ModelClassification[Aspect] for Aspect in ["Time", "Element"]
            ],
            "IndexLetter": ["t", "e"],
        }
    )
    IndexTable.set_index("Aspect", inplace=True)

    print("--> Model scope and classifications defined.")
    return ModelClassification, IndexTable
