"""
Helper functions for handling 3D arrays in Material Flow Analysis.

These functions abstract the difference between 2D (Time, Element) and 
3D (Time, Material, Element) array structures.
"""

import numpy as np


def get_element_values(flow_or_stock, element_index, aggregate_materials=True):
    """
    Get time series values for a specific element, handling both 2D and 3D arrays.
    
    Parameters
    ----------
    flow_or_stock : Flow or Stock object
        The flow or stock object containing Values attribute
    element_index : int
        Index of the element in the Elements list
    aggregate_materials : bool, optional
        If True (default), sum over materials dimension for 3D arrays.
        If False, return 2D array (time, materials) for element values.
    
    Returns
    -------
    np.ndarray
        Time series of element values.
        - For 2D arrays: Shape (n_years,)
        - For 3D arrays with aggregation: Shape (n_years,)
        - For 3D arrays without aggregation: Shape (n_years, n_materials)
    
    Examples
    --------
    >>> # 2D array (current system)
    >>> values = get_element_values(flow, element_index=0)  # (26,)
    
    >>> # 3D array with aggregation (new system - default)
    >>> values = get_element_values(flow, element_index=0)  # (26,) - summed over materials
    
    >>> # 3D array without aggregation
    >>> values = get_element_values(flow, element_index=0, aggregate_materials=False)  # (26, 2)
    """
    if flow_or_stock.Values is None:
        return np.array([])
    
    values = flow_or_stock.Values
    
    if values.ndim == 2:
        # 2D: (time, elements)
        return values[:, element_index]
    
    elif values.ndim == 3:
        # 3D: (time, materials, elements)
        if aggregate_materials:
            # Sum over materials dimension
            return np.sum(values[:, :, element_index], axis=1)
        else:
            # Return full 2D array (time, materials)
            return values[:, :, element_index]
    
    else:
        raise ValueError(
            f"Unexpected array dimension: {values.ndim}. "
            f"Expected 2D (time, elements) or 3D (time, materials, elements)"
        )


def get_material_values(flow_or_stock, material_index):
    """
    Get all element values for a specific material.
    
    Parameters
    ----------
    flow_or_stock : Flow or Stock object
        The flow or stock object containing Values attribute
    material_index : int
        Index of the material in the Materials list
    
    Returns
    -------
    np.ndarray
        Element values over time for the specified material.
        Shape: (n_years, n_elements)
    
    Examples
    --------
    >>> # Get all elements for WC (material 0)
    >>> wc_values = get_material_values(flow, material_index=0)  # (26, 2)
    
    >>> # Get all elements for DM (material 1)
    >>> dm_values = get_material_values(flow, material_index=1)  # (26, 2)
    """
    if flow_or_stock.Values is None:
        return np.array([])
    
    values = flow_or_stock.Values
    
    if values.ndim == 2:
        raise ValueError(
            "Cannot select material from 2D array. "
            "Material dimension not present in this system."
        )
    
    elif values.ndim == 3:
        # 3D: (time, materials, elements)
        return values[:, material_index, :]
    
    else:
        raise ValueError(
            f"Unexpected array dimension: {values.ndim}. "
            f"Expected 3D (time, materials, elements)"
        )


def get_element_by_material(flow_or_stock, element_index, material_index):
    """
    Get element values for a specific element within a specific material.
    
    Parameters
    ----------
    flow_or_stock : Flow or Stock object
        The flow or stock object containing Values attribute
    element_index : int
        Index of the element in the Elements list
    material_index : int
        Index of the material in the Materials list
    
    Returns
    -------
    np.ndarray
        Time series of element values for the specified element in the specified material.
        Shape: (n_years,)
    
    Examples
    --------
    >>> # Get CC (element 1) for WC (material 0)
    >>> cc_in_wc = get_element_by_material(flow, element_index=1, material_index=0)
    
    >>> # Get material (element 0) for DM (material 1)
    >>> mass_in_dm = get_element_by_material(flow, element_index=0, material_index=1)
    """
    if flow_or_stock.Values is None:
        return np.array([])
    
    values = flow_or_stock.Values
    
    if values.ndim == 2:
        raise ValueError(
            "Cannot select material from 2D array. "
            "Material dimension not present in this system."
        )
    
    elif values.ndim == 3:
        # 3D: (time, materials, elements)
        return values[:, material_index, element_index]
    
    else:
        raise ValueError(
            f"Unexpected array dimension: {values.ndim}. "
            f"Expected 3D (time, materials, elements)"
        )


def has_material_dimension(flow_or_stock):
    """
    Check if a flow or stock has a material dimension (3D array).
    
    Parameters
    ----------
    flow_or_stock : Flow or Stock object
        The flow or stock object containing Values attribute
    
    Returns
    -------
    bool
        True if the array is 3D (has material dimension), False if 2D
    """
    if flow_or_stock.Values is None:
        return False
    
    return flow_or_stock.Values.ndim == 3


def get_array_info(flow_or_stock):
    """
    Get information about the array structure of a flow or stock.
    
    Parameters
    ----------
    flow_or_stock : Flow or Stock object
        The flow or stock object containing Values attribute
    
    Returns
    -------
    dict
        Dictionary with shape information and dimension names
    
    Examples
    --------
    >>> info = get_array_info(flow)
    >>> print(info)
    {'shape': (26, 2, 2), 'ndim': 3, 'has_materials': True, 'n_years': 26, 'n_materials': 2, 'n_elements': 2}
    """
    if flow_or_stock.Values is None:
        return {'shape': None, 'ndim': 0, 'has_materials': False}
    
    values = flow_or_stock.Values
    info = {'shape': values.shape, 'ndim': values.ndim}
    
    if values.ndim == 2:
        # 2D: (time, elements)
        info['has_materials'] = False
        info['n_years'] = values.shape[0]
        info['n_elements'] = values.shape[1]
        info['dimensions'] = 'Time × Element'
    
    elif values.ndim == 3:
        # 3D: (time, materials, elements)
        info['has_materials'] = True
        info['n_years'] = values.shape[0]
        info['n_materials'] = values.shape[1]
        info['n_elements'] = values.shape[2]
        info['dimensions'] = 'Time × Material × Element'
    
    return info

