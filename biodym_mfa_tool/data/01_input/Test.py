# -*- coding: utf-8 -*-
"""
Configuration File for the BioDYM MFA Model.

This file contains all the high-level settings and switches to control
a model run. Users can define the input data, model scope, and
calculation modes (e.g., deterministic vs. Monte Carlo) here.
"""

# ==============================================================================
# FILE PATHS
# ==============================================================================
# Path to the primary Excel input file containing all model definitions
# and data.
EXCEL_FILE_PATH = '250625_Template_CS0.xlsx'

# ==============================================================================
# MODEL SCOPE
# ==============================================================================
# The first year of the analysis.
START_YEAR = 2025
# The last year of the analysis.
END_YEAR = 2050
# List of elements/substances to be tracked throughout the system.
ELEMENTS = ['material', 'WC', 'DM', 'CC']

# ==============================================================================
# CALCULATION SWITCHES
# ==============================================================================
# Master switch to run a full Monte Carlo simulation.
RUN_MONTE_CARLO = False  # Set to True for uncertainty analysis.

# Number of iterations for the Monte Carlo simulation.
MC_ITERATIONS = 100

# Individual model component switches.
RUN_DSM_CALCULATION = True
RUN_FOMP_CALCULATION = True