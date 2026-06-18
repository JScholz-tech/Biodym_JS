# -*- coding: utf-8 -*-
"""
Age Cohort Utilities for Initial Stock Distribution.

This module provides functions to generate age-cohort distributions for
initial stocks in Dynamic Stock Models (DSM).
"""

import numpy as np


def generate_age_cohorts(
    total_stock, distribution_type, max_age, decay_constant=None,
    mean_age=None, std_age=None,
):
    """Generate age-cohort distribution for initial stock.

    Distributes a total initial stock quantity across age cohorts (0 … max_age-1).

    Parameters
    ----------
    total_stock : float
        Total quantity of initial stock to distribute across ages.
    distribution_type : str
        Type of age distribution:
        - "uniform"     : Equal amounts at each age
        - "exponential" : Exponentially decreasing with age (more recent items)
        - "normal"      : Normal (Gaussian) distribution; requires mean_age, std_age
        - "lognormal"   : Log-normal distribution; requires mean_age, std_age
    max_age : int
        Maximum age of items in the initial stock (in years).
        For normal/lognormal this is the cutoff — set to mean + 3*std or higher.
    decay_constant : float, optional
        Decay constant for "exponential" (years). Defaults to max_age/3.
    mean_age : float, optional
        Mean age of items in the existing stock. Required for "normal"/"lognormal".
    std_age : float, optional
        Std dev of ages. Required for "normal"/"lognormal".

    Returns
    -------
    np.ndarray
        1D array of length max_age containing the stock quantity at each age.
        Index 0 = age 0-1 years, Index 1 = age 1-2 years, etc.
    """
    if total_stock <= 0:
        raise ValueError(f"total_stock must be positive, got {total_stock}")
    if max_age <= 0:
        raise ValueError(f"max_age must be positive, got {max_age}")

    distribution_type = distribution_type.lower()
    ages = np.arange(max_age, dtype=float)

    if distribution_type == "uniform":
        cohorts = np.ones(max_age) * (total_stock / max_age)

    elif distribution_type == "exponential":
        if decay_constant is None:
            decay_constant = max_age / 3
        if decay_constant <= 0:
            raise ValueError(f"decay_constant must be positive, got {decay_constant}")
        weights = np.exp(-ages / decay_constant)
        cohorts = total_stock * weights / weights.sum()

    elif distribution_type == "normal":
        if mean_age is None or std_age is None:
            raise ValueError("Normal distribution requires mean_age and std_age")
        if std_age <= 0:
            raise ValueError(f"std_age must be positive, got {std_age}")
        weights = np.exp(-0.5 * ((ages - float(mean_age)) / float(std_age)) ** 2)
        if weights.sum() == 0:
            raise ValueError(
                f"Normal distribution with mean_age={mean_age}, std_age={std_age}, "
                f"max_age={max_age} produced zero weights — increase max_age"
            )
        cohorts = total_stock * weights / weights.sum()

    elif distribution_type == "lognormal":
        if mean_age is None or std_age is None:
            raise ValueError("LogNormal distribution requires mean_age and std_age")
        if std_age <= 0:
            raise ValueError(f"std_age must be positive, got {std_age}")
        mean_a, std_a = float(mean_age), float(std_age)
        # Convert normal-space mean/std to log-space parameters
        sigma_ln = np.sqrt(np.log(1.0 + (std_a / mean_a) ** 2))
        mu_ln = np.log(mean_a) - 0.5 * sigma_ln ** 2
        ages_pos = np.maximum(ages, 0.5)  # avoid log(0) for age-0 cohort
        weights = (
            np.exp(-0.5 * ((np.log(ages_pos) - mu_ln) / sigma_ln) ** 2) / ages_pos
        )
        if weights.sum() == 0:
            raise ValueError(
                f"LogNormal distribution produced zero weights — check mean_age/std_age/max_age"
            )
        cohorts = total_stock * weights / weights.sum()

    else:
        raise ValueError(
            f"Unknown distribution type: '{distribution_type}'. "
            f"Must be 'uniform', 'exponential', 'normal', or 'lognormal'."
        )

    return cohorts


def apply_element_composition_to_cohorts(cohorts, element_fractions):
    """Apply element composition to age cohorts.

    Takes age cohorts (material only) and applies element fractions to create
    a full cohort matrix with all elements.

    Parameters
    ----------
    cohorts : np.ndarray
        1D array of material quantities by age cohort (length = max_age).
    element_fractions : np.ndarray
        1D array of element fractions (length = num_elements).
        element_fractions[0] should be 1.0 (material itself).
        element_fractions[1:] are the fractions of each element in the material.

    Returns
    -------
    np.ndarray
        2D array of shape (max_age, num_elements) where:
        - cohorts[:, 0] = material quantities by age
        - cohorts[:, i] = element i quantities by age

    Examples
    --------
    >>> cohorts = np.array([10, 10, 10])  # 3 age cohorts, 10 Mg each
    >>> fractions = np.array([1.0, 0.6, 0.4, 0.18])  # Material, WC, DM, CC
    >>> cohort_matrix = apply_element_composition_to_cohorts(cohorts, fractions)
    >>> cohort_matrix.shape
    (3, 4)
    >>> cohort_matrix[:, 0]  # Material
    array([10., 10., 10.])
    >>> cohort_matrix[:, 3]  # Carbon (18% of material)
    array([1.8, 1.8, 1.8])
    """
    max_age = len(cohorts)
    num_elements = len(element_fractions)

    # Initialize cohort matrix
    cohort_matrix = np.zeros((max_age, num_elements))

    # Material column (element 0)
    cohort_matrix[:, 0] = cohorts

    # Element columns (elements 1+)
    for elem_idx in range(1, num_elements):
        cohort_matrix[:, elem_idx] = cohorts * element_fractions[elem_idx]

    return cohort_matrix


def validate_age_cohort_parameters(config, process_id):
    """Validate age cohort parameters from initial stock configuration.

    Parameters
    ----------
    config : dict
        Initial stock configuration dictionary for a process.
        Should contain:
        - "initial_stock_values" dict with element fractions
        - Cohort parameters if applicable
    process_id : int
        Process ID for error messages.

    Returns
    -------
    dict or None
        Dictionary with validated parameters:
        {
            "total_stock": float,
            "distribution_type": str,
            "max_age": int,
            "decay_constant": float or None,
            "element_fractions": np.ndarray
        }
        Returns None if validation fails.

    Raises
    ------
    ValueError
        If required parameters are missing or invalid.
    """
    stock_values = config.get("initial_stock_values", {})

    # Check for required material quantity
    total_stock = stock_values.get("Initial_Stock_material", 0.0)
    if total_stock <= 0:
        raise ValueError(
            f"Process {process_id}: Initial stock material quantity must be positive, got {total_stock}"
        )

    # Check for cohort-specific parameters
    distribution_type = config.get("cohort_age_distribution_type")
    max_age = config.get("cohort_max_age")

    if distribution_type is None or max_age is None:
        raise ValueError(
            f"Process {process_id}: Missing required cohort parameters. "
            f"Need 'Cohort_Age_Distribution_Type' and 'Cohort_Max_Age[years]'."
        )

    # Validate distribution type
    distribution_type = str(distribution_type).lower()
    _supported = ["uniform", "exponential", "normal", "lognormal"]
    if distribution_type not in _supported:
        raise ValueError(
            f"Process {process_id}: Invalid age distribution type '{distribution_type}'. "
            f"Must be one of: {', '.join(_supported)}."
        )

    # Validate max age
    try:
        max_age = int(max_age)
        if max_age <= 0:
            raise ValueError("max_age must be positive")
    except (ValueError, TypeError) as e:
        raise ValueError(
            f"Process {process_id}: Invalid max_age '{max_age}'. Must be a positive integer."
        ) from e

    # Get decay constant (optional, exponential only)
    decay_constant = config.get("cohort_decay_constant")
    if decay_constant is not None:
        try:
            decay_constant = float(decay_constant)
        except (ValueError, TypeError):
            print(
                f"  -> WARNING: Invalid decay_constant for Process {process_id}, using default (max_age/3)"
            )
            decay_constant = None

    # Get mean/std age (required for normal/lognormal)
    mean_age = config.get("cohort_mean_age")
    std_age = config.get("cohort_std_age")
    if mean_age is not None:
        try:
            mean_age = float(mean_age)
        except (ValueError, TypeError):
            mean_age = None
    if std_age is not None:
        try:
            std_age = float(std_age)
        except (ValueError, TypeError):
            std_age = None

    # Build element fractions array from config
    elements = config.get("elements", ["material", "WC", "DM", "CC"])
    element_fractions = np.zeros(len(elements))
    element_fractions[0] = 1.0  # Material itself

    for idx, element in enumerate(elements[1:], start=1):
        fraction_key = f"Initial_Stock_{element}[%]"
        element_fractions[idx] = stock_values.get(fraction_key, 0.0)

    return {
        "total_stock": total_stock,
        "distribution_type": distribution_type,
        "max_age": max_age,
        "decay_constant": decay_constant,
        "mean_age": mean_age,
        "std_age": std_age,
        "element_fractions": element_fractions,
    }
