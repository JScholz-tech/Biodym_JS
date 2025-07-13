# -*- coding: utf-8 -*-
"""
Test Runner for Enhanced Plotting Functionality

This script runs all the plotting tests and provides a comprehensive report.
"""

import os
import sys
import subprocess
import time
from pathlib import Path

def run_tests():
    """Run all plotting tests and provide a comprehensive report."""
    
    print("🧪" + "="*58)
    print("🧪 ENHANCED PLOTTING FUNCTIONALITY TEST SUITE")
    print("🧪" + "="*58)
    
    # Get the test directory
    test_dir = Path(__file__).parent
    biodym_dir = test_dir.parent
    
    # Change to the biodym directory
    os.chdir(biodym_dir)
    
    print(f"\n📁 Working directory: {os.getcwd()}")
    print(f"📁 Test directory: {test_dir}")
    
    # Test results
    results = {}
    
    # 1. Run unit tests
    print("\n" + "-"*60)
    print("🔬 UNIT TESTS")
    print("-"*60)
    
    try:
        start_time = time.time()
        result = subprocess.run([
            sys.executable, "-m", "pytest", 
            str(test_dir / "unit" / "test_plotting.py"),
            "-v", "--tb=short"
        ], capture_output=True, text=True, timeout=300)
        end_time = time.time()
        
        results['unit_tests'] = {
            'success': result.returncode == 0,
            'output': result.stdout,
            'errors': result.stderr,
            'duration': end_time - start_time
        }
        
        if result.returncode == 0:
            print("✅ Unit tests passed")
        else:
            print("❌ Unit tests failed")
            print(result.stderr)
            
    except subprocess.TimeoutExpired:
        print("⏰ Unit tests timed out")
        results['unit_tests'] = {'success': False, 'error': 'Timeout'}
    except Exception as e:
        print(f"❌ Error running unit tests: {e}")
        results['unit_tests'] = {'success': False, 'error': str(e)}
    
    # 2. Run integration tests
    print("\n" + "-"*60)
    print("🔗 INTEGRATION TESTS")
    print("-"*60)
    
    try:
        start_time = time.time()
        result = subprocess.run([
            sys.executable, "-m", "pytest", 
            str(test_dir / "integration" / "test_enhanced_plotting.py"),
            "-v", "--tb=short"
        ], capture_output=True, text=True, timeout=600)
        end_time = time.time()
        
        results['integration_tests'] = {
            'success': result.returncode == 0,
            'output': result.stdout,
            'errors': result.stderr,
            'duration': end_time - start_time
        }
        
        if result.returncode == 0:
            print("✅ Integration tests passed")
        else:
            print("❌ Integration tests failed")
            print(result.stderr)
            
    except subprocess.TimeoutExpired:
        print("⏰ Integration tests timed out")
        results['integration_tests'] = {'success': False, 'error': 'Timeout'}
    except Exception as e:
        print(f"❌ Error running integration tests: {e}")
        results['integration_tests'] = {'success': False, 'error': str(e)}
    
    # 3. Run comprehensive tests
    print("\n" + "-"*60)
    print("🎯 COMPREHENSIVE TESTS")
    print("-"*60)
    
    try:
        start_time = time.time()
        result = subprocess.run([
            sys.executable, str(test_dir / "integration" / "test_comprehensive_features.py")
        ], capture_output=True, text=True, timeout=900)
        end_time = time.time()
        
        results['comprehensive_tests'] = {
            'success': result.returncode == 0,
            'output': result.stdout,
            'errors': result.stderr,
            'duration': end_time - start_time
        }
        
        if result.returncode == 0:
            print("✅ Comprehensive tests passed")
        else:
            print("❌ Comprehensive tests failed")
            print(result.stderr)
            
    except subprocess.TimeoutExpired:
        print("⏰ Comprehensive tests timed out")
        results['comprehensive_tests'] = {'success': False, 'error': 'Timeout'}
    except Exception as e:
        print(f"❌ Error running comprehensive tests: {e}")
        results['comprehensive_tests'] = {'success': False, 'error': str(e)}
    
    # 4. Generate test report
    print("\n" + "="*60)
    print("📊 TEST REPORT")
    print("="*60)
    
    total_tests = len(results)
    passed_tests = sum(1 for r in results.values() if r.get('success', False))
    failed_tests = total_tests - passed_tests
    
    print(f"\n📈 Overall Results:")
    print(f"   Total test suites: {total_tests}")
    print(f"   ✅ Passed: {passed_tests}")
    print(f"   ❌ Failed: {failed_tests}")
    print(f"   📊 Success rate: {passed_tests/total_tests*100:.1f}%")
    
    print(f"\n⏱️  Test Durations:")
    for test_name, result in results.items():
        duration = result.get('duration', 0)
        status = "✅ PASS" if result.get('success', False) else "❌ FAIL"
        print(f"   {test_name.replace('_', ' ').title()}: {duration:.2f}s {status}")
    
    # Detailed results
    print(f"\n📋 Detailed Results:")
    for test_name, result in results.items():
        print(f"\n{test_name.replace('_', ' ').title()}:")
        if result.get('success', False):
            print(f"   ✅ Status: PASSED")
        else:
            print(f"   ❌ Status: FAILED")
            if 'error' in result:
                print(f"   🔍 Error: {result['error']}")
        
        if 'duration' in result:
            print(f"   ⏱️  Duration: {result['duration']:.2f}s")
    
    # Summary
    print(f"\n" + "="*60)
    if failed_tests == 0:
        print("🎉 ALL TESTS PASSED!")
        print("✅ Enhanced plotting functionality is working correctly.")
    else:
        print("⚠️  SOME TESTS FAILED!")
        print("🔧 Please check the error messages above and fix any issues.")
    print("="*60)
    
    return failed_tests == 0


def run_quick_test():
    """Run a quick test to verify basic functionality."""
    print("🚀 Running quick functionality test...")
    
    try:
        # Test basic imports
        import sys
        import os
        
        # Add paths
        current_dir = os.getcwd()
        src_path = os.path.join(current_dir, "src")
        sys.path.insert(0, src_path)
        
        # Test imports
        import plotting
        print("✅ Plotting module imported successfully")
        
        # Test basic function existence
        required_functions = [
            'plot_monte_carlo_integrated_dashboard',
            'plot_enhanced_export_options',
            'plot_optimized_mass_balance_error',
            'plot_interactive_sankey',
            'plot_individual_flows',
            'plot_individual_stocks'
        ]
        
        for func_name in required_functions:
            if hasattr(plotting, func_name):
                print(f"✅ {func_name} function found")
            else:
                print(f"❌ {func_name} function missing")
                return False
        
        print("✅ Quick test passed - basic functionality is available")
        return True
        
    except Exception as e:
        print(f"❌ Quick test failed: {e}")
        return False


def main():
    """Main function to run tests."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run enhanced plotting tests")
    parser.add_argument("--quick", action="store_true", help="Run quick test only")
    parser.add_argument("--unit", action="store_true", help="Run unit tests only")
    parser.add_argument("--integration", action="store_true", help="Run integration tests only")
    
    args = parser.parse_args()
    
    if args.quick:
        success = run_quick_test()
    elif args.unit:
        # Run only unit tests
        test_dir = Path(__file__).parent
        result = subprocess.run([
            sys.executable, "-m", "pytest", 
            str(test_dir / "unit" / "test_plotting.py"),
            "-v"
        ])
        success = result.returncode == 0
    elif args.integration:
        # Run only integration tests
        test_dir = Path(__file__).parent
        result = subprocess.run([
            sys.executable, "-m", "pytest", 
            str(test_dir / "integration" / "test_enhanced_plotting.py"),
            "-v"
        ])
        success = result.returncode == 0
    else:
        # Run all tests
        success = run_tests()
    
    if not success:
        sys.exit(1)


if __name__ == "__main__":
    main() 