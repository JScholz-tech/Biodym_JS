# BioDYM Tool - Test Usage Guide

## 🎯 **Purpose**
This guide explains how to effectively use the comprehensive test suite to validate BioDYM functionality, catch bugs, and ensure quality.

## 🧪 **Test Suite Overview**

### **Test Categories** (counts vary by branch)
- **Unit Tests**: individual functions
- **Integration Tests**: end-to-end workflows
- **Workflow Tests**: user scenarios

### **Test Files Structure:**
```
test/
├── conftest.py                    # Test configuration & setup
├── test_fomp_model.py            # FOMP calculation tests (5 tests)
├── test_data_loader.py           # Data loading tests (4 tests)
├── test_solver.py                # MFA solver tests (2 tests)
├── test_system_setup.py          # System setup tests (7 tests)
├── run_plotting_tests.py         # Plotting test runner
├── unit/                         # Unit test modules
│   ├── test_plotting.py         # Plotting function tests (16 tests)
│   └── test_utils.py            # Utility function tests (7 tests)
├── integration/                  # Integration test modules
│   ├── test_comprehensive_features.py  # Full workflow tests (5 tests)
│   ├── test_enhanced_plotting.py      # Plotting integration (12 tests)
│   └── test_golden_dataset.py         # Real data validation (1 test)
└── workflow/                     # Workflow test modules
    └── 1_setup/
        └── test_setup.py        # Setup workflow tests (7 tests)
```

## 🚀 **How to Use Tests Effectively**

### **1. Comprehensive Testing (All Functions)**
```bash
# Run all tests with verbose output (from the project root)
uv run pytest -v --tb=short

# Run with coverage report
uv run pytest --cov=src --cov-report=html

# Run with detailed failure information
uv run pytest -v -s --tb=long
```

### **2. Category-Based Testing (Targeted)**
```bash
# Test only core calculation functions
uv run pytest test/test_fomp_model.py test/test_data_loader.py test/test_solver.py -v

# Test only plotting functionality
uv run pytest test/unit/test_plotting.py -v

# Test only integration scenarios
uv run pytest test/integration/ -v

# Test only workflow processes
uv run pytest test/workflow/ -v
```

### **3. Specific Function Testing (Debugging)**
```bash
# Test specific test function
uv run pytest test/test_fomp_model.py::test_calculate_fomp_simple_decay -v

# Test with detailed output and no capture
uv run pytest test/test_data_loader.py -v -s

# Test with maximum verbosity
uv run pytest test/test_system_setup.py -vvv
```

### **4. Performance & Debugging Testing**
```bash
# Run tests with timing information
uv run pytest test/ --durations=10

# Run tests and stop on first failure
uv run pytest test/ -x

# Run tests and show local variables on failure
uv run pytest test/ -l

```

## 📊 **Test Categories & When to Use Them**

### **🔬 Unit Tests (35 tests)**
**Purpose**: Test individual functions in isolation
**When to Use**: 
- After making changes to specific functions
- To debug calculation errors
- To validate function behavior

**Key Test Files**:
- **`test_fomp_model.py`** - FOMP calculations (critical for your error fix)
- **`test_data_loader.py`** - Excel data loading (critical for configuration)
- **`test_solver.py`** - MFA calculation engine
- **`test_system_setup.py`** - System initialization

### **🔗 Integration Tests (18 tests)**
**Purpose**: Test how functions work together
**When to Use**:
- After major changes to ensure nothing breaks
- To validate complete workflows
- Before releasing updates

**Key Test Files**:
- **`test_comprehensive_features.py`** - Full workflow validation
- **`test_enhanced_plotting.py`** - Plotting system integration
- **`test_golden_dataset.py`** - Real data validation

### **🔄 Workflow Tests (7 tests)**
**Purpose**: Test user scenarios and setup processes
**When to Use**:
- To validate user workflows
- To ensure setup processes work correctly
- To test configuration integration

## 🎯 **Recommended Testing Strategy**

### **Phase 1: Validate Critical Fixes (Immediate)**
```bash
# Test FOMP fix (your recent error resolution)
uv run pytest test/test_fomp_model.py -v

# Test data loading (Excel configuration integration)
uv run pytest test/test_data_loader.py -v

# Test system setup (core functionality)
uv run pytest test/test_system_setup.py -v
```

### **Phase 2: Validate Core Functions (This Week)**
```bash
# Test all core calculation functions
uv run pytest test/test_fomp_model.py test/test_data_loader.py test/test_solver.py test/test_system_setup.py -v

# Test plotting functions
uv run pytest test/unit/test_plotting.py -v
```

### **Phase 3: Validate Integration (Next Week)**
```bash
# Test complete workflows
uv run pytest test/integration/ -v

# Test user scenarios
uv run pytest test/workflow/ -v
```

### **Phase 4: Full Validation (Before Publication)**
```bash
# Run all tests with coverage
uv run pytest test/ -v --cov=src --cov-report=html

# Generate test report
uv run pytest test/ --html=test_report.html --self-contained-html
```

## 🚨 **Common Test Issues & Solutions**

### **Import Errors**
**Problem**: Tests can't import modules
**Solution**: Check `conftest.py` path configuration

### **Mock Data Issues**
**Problem**: Tests fail due to unrealistic mock data
**Solution**: Use `test_golden_dataset.py` for real data validation

### **ODYM Framework Dependencies**
**Problem**: Tests fail due to missing ODYM framework
**Solution**: Ensure framework paths are correctly set in `conftest.py`

### **Performance Issues**
**Problem**: Tests run slowly
**Solution**: Use `--durations=10` to identify slow tests

## 📈 **Test Results Interpretation**

### **✅ All Tests Passing**
- **Status**: Excellent - All functions working correctly
- **Action**: Ready for production use

### **⚠️ Some Tests Failing**
- **Status**: Issues detected - Need investigation
- **Action**: Focus on failing test categories first

### **❌ Many Tests Failing**
- **Status**: Critical issues - Major problems detected
- **Action**: Start with core function tests, fix issues incrementally

## 🔑 **Key Benefits of Using Tests**

1. **Validate Fixes** - Ensure your FOMP error fix works
2. **Catch Regressions** - Prevent new bugs when making changes
3. **Document Behavior** - Tests show how functions should work
4. **Quality Assurance** - Ensure all 52 functions work correctly
5. **Confidence** - Know your tool works before using it

## 🎉 **Getting Started**

### **Quick Start (5 minutes)**
```bash
# Test your recent FOMP fix
python -m pytest test/test_fomp_model.py -v

# Test configuration integration
python -m pytest test/test_data_loader.py -v
```

### **Full Validation (30 minutes)**
```bash
# Run all tests with progress bar
python -m pytest test/ -v --tb=short
```

---

*Test Usage Guide Created: 2025-08-31*  
*Purpose: Effective test suite utilization*  
*Status: ✅ READY FOR USE*
