# -*- coding: utf-8 -*-
"""
Unit tests for enhanced Sankey configuration lookup and position handling.
Focus: robust Process_ID/name matching and element-specific position clamping.
"""

import types

from plotting.enhanced_sankey import (
    get_process_visualization,
    calculate_element_specific_positions,
)


def test_get_process_visualization_id_variants():
    # Config simulating 6_1_Visualization_Processes after loader
    cfg = {
        'process_colors': {
            'P_02': {
                'Process_ID': 'P_02',
                'Name(EN)': 'Proc 2',
                'X_Position_Material': 0.25,
                'Y_Position_Material': 0.75,
                'Node_Color': '#112233',
            }
        }
    }

    # Lookup by numeric variants should find 'P_02'
    viz = get_process_visualization(2, 'Proc 2', cfg, element='material')
    assert viz['X_Position'] == 0.25
    assert viz['Y_Position'] == 0.75
    assert viz.get('Node_Color') == '#112233'


def test_get_process_visualization_name_fallback():
    cfg = {
        'process_colors': {
            'P_99': {
                'Process_ID': 'P_03',
                'Name(EN)': 'Fermentation',
                'X_Position_Material': 0.4,
                'Y_Position_Material': 0.6,
            }
        }
    }

    # Pass an ID that won't match keys but a matching name
    viz = get_process_visualization(12345, 'Fermentation', cfg, element='material')
    assert viz['X_Position'] == 0.4
    assert viz['Y_Position'] == 0.6


def test_calculate_element_specific_positions_clamps():
    # Two dummy processes with element-specific positions out of bounds
    class P:
        def __init__(self, ID, Name):
            self.ID = ID
            self.Name = Name

    processes = [P(1, 'A'), P(2, 'B')]

    cfg = {
        'process_colors': {
            'P_1': {
                'Process_ID': 'P_1', 'Name(EN)': 'A',
                'X_Position_Material': 1.2, 'Y_Position_Material': -0.2,
            },
            'P_2': {
                'Process_ID': 'P_2', 'Name(EN)': 'B',
                'X_Position_Material': '0,8', 'Y_Position_Material': '0,3',
            },
        }
    }

    positions = calculate_element_specific_positions(processes, cfg, 'material')

    # Process 1 gets clamped to [1.0, 0.0]
    assert positions[1][0] == 1.0
    assert positions[1][1] == 0.0

    # Process 2 gets comma-decimal parsed correctly
    assert positions[2][0] == 0.8
    assert positions[2][1] == 0.3
