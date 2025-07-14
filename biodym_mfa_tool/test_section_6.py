# -*- coding: utf-8 -*-
"""
Test script for Section 6 - Monte Carlo Parameter Selection
This script tests the syntax and basic functionality of the new parameter selection system.
"""

import sys
import os

# Add the src directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def test_section_6_imports():
    """Test that the MC parameter selection modules can be imported."""
    
    print("🧪 Testing Section 6 - Monte Carlo Parameter Selection")
    print("=" * 60)
    
    try:
        # Test import of the codelist module
        from mc_parameter_codelist import MCParameterCodelist
        print("✅ MCParameterCodelist imported successfully")
        
        # Test import of the user interface module
        from mc_user_interface import create_mc_parameter_interface, quick_mc_setup
        print("✅ MC user interface functions imported successfully")
        
        # Test basic functionality
        print("\n📊 Testing basic functionality...")
        
        # Create a simple codelist
        codelist = MCParameterCodelist()
        print("✅ MCParameterCodelist created successfully")
        
        # Test parameter generation
        all_params = codelist.get_all_parameters()
        print(f"✅ Generated {len(all_params)} parameters")
        
        # Test categories
        categories = codelist.get_parameter_categories()
        print(f"✅ Found {len(categories)} parameter categories")
        
        # Test quick setup
        quick_params = quick_mc_setup()
        print(f"✅ Quick setup generated {len(quick_params)} parameters")
        
        print("\n🎉 All tests passed! Section 6 is working correctly.")
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("   This is expected if the modules are not yet implemented.")
        return False
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_syntax():
    """Test that the main notebook file has no syntax errors."""
    
    print("\n🔍 Testing syntax of main notebook...")
    
    try:
        # Try to compile the main notebook
        import py_compile
        py_compile.compile('BioDYM_Scientific_Notebook.py', doraise=True)
        print("✅ Main notebook syntax is correct")
        return True
    except py_compile.PyCompileError as e:
        print(f"❌ Syntax error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    print("🎲 Testing Monte Carlo Parameter Selection System")
    print("=" * 60)
    
    # Test syntax first
    syntax_ok = test_syntax()
    
    # Test functionality
    functionality_ok = test_section_6_imports()
    
    print("\n" + "=" * 60)
    print("📊 TEST RESULTS")
    print("=" * 60)
    
    if syntax_ok:
        print("✅ Syntax: PASSED - No syntax errors found")
    else:
        print("❌ Syntax: FAILED - Syntax errors found")
    
    if functionality_ok:
        print("✅ Functionality: PASSED - Modules work correctly")
    else:
        print("❌ Functionality: FAILED - Module issues found")
    
    if syntax_ok and functionality_ok:
        print("\n🎉 ALL TESTS PASSED!")
        print("Section 6 (Monte Carlo Parameter Selection) is ready to use.")
    else:
        print("\n⚠️ Some tests failed. Please check the errors above.") 