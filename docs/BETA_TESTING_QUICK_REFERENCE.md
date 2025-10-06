# BioDYM Beta Testing Quick Reference

## 🎯 **Quick Testing Checklist**

### **Essential Tests (Must Complete)**
- [ ] **Installation**: Can install BioDYM without errors
- [ ] **First Run**: Can run baseline analysis successfully
- [ ] **Mass Balance**: Mass balance validation passes
- [ ] **Excel Template**: Can modify Excel template
- [ ] **Visualizations**: Sankey diagrams and plots work
- [ ] **Export**: Can export results to Excel

### **Important Tests (Should Complete)**
- [ ] **Scenario Management**: Can create and compare scenarios
- [ ] **Monte Carlo**: Can run uncertainty analysis
- [ ] **Custom Data**: Can input own data successfully
- [ ] **Error Handling**: Error messages are helpful
- [ ] **Documentation**: Documentation is clear and complete

### **Advanced Tests (Nice to Complete)**
- [ ] **DSM Features**: Dynamic Stock Modeling works
- [ ] **FOMP Features**: First-Order Mineralization works
- [ ] **Performance**: Acceptable speed for typical use cases
- [ ] **Large Datasets**: Can handle complex systems
- [ ] **Edge Cases**: Handles unusual inputs gracefully

---

## 🚀 **Quick Test Scenarios**

### **Scenario 1: First-Time User (30 minutes)**
1. Install BioDYM using `uv sync`
2. Open `BioDYM_Scientific_Notebook.ipynb`
3. Run all cells with example data
4. Check mass balance results
5. View Sankey diagram
6. Export results

**Success**: Analysis completes without errors, visualizations appear

### **Scenario 2: Custom Analysis (60 minutes)**
1. Copy example Excel file to `my_test.xlsx`
2. Modify process names in `2_1_Definition_Processes`
3. Change flow values in `1_2_Data_Flows`
4. Run analysis with modified data
5. Verify mass balance still passes
6. Compare results with original

**Success**: Custom analysis works, mass balance maintained

### **Scenario 3: Scenario Comparison (45 minutes)**
1. Create two scenarios in `5_1_Scenario_Manager`
2. Modify transfer coefficients between scenarios
3. Run scenario comparison analysis
4. View comparative visualizations
5. Export scenario results

**Success**: Scenarios can be compared, differences are visible

### **Scenario 4: Monte Carlo (30 minutes)**
1. Define uncertainty parameters in `4_1_Uncertainty_Parameters`
2. Run Monte Carlo simulation (50 iterations)
3. View uncertainty results
4. Check confidence intervals
5. Export MC results

**Success**: MC simulation runs, uncertainty measures are reasonable

---

## 🐛 **Common Issues & Solutions**

### **Installation Issues**
- **Problem**: `uv sync` fails
- **Solution**: Check Python version (3.12+), try `uv python install 3.12`
- **Problem**: Import errors
- **Solution**: Ensure you're in project directory, check `PYTHONPATH`

### **Excel Template Issues**
- **Problem**: "Required column missing" error
- **Solution**: Check column names match template exactly
- **Problem**: Process ID errors
- **Solution**: Ensure process IDs start from 0, are sequential

### **Calculation Issues**
- **Problem**: Mass balance violations
- **Solution**: Check transfer coefficients sum to 1.0, verify flow directions
- **Problem**: Negative flow values
- **Solution**: Check input data for negative values, verify TC ranges

### **Visualization Issues**
- **Problem**: Sankey diagram doesn't appear
- **Solution**: Check browser compatibility, try different browser
- **Problem**: Plot labels unclear
- **Solution**: Check flow/process names in Excel template

### **Performance Issues**
- **Problem**: Analysis runs slowly
- **Solution**: Reduce time series length, simplify system
- **Problem**: Memory errors
- **Solution**: Close other applications, reduce MC iterations

---

## 📊 **Testing Metrics**

### **Quick Metrics to Track**
- **Installation Time**: Should be <10 minutes
- **First Analysis Time**: Should be <5 minutes
- **Mass Balance Tolerance**: Should be <0.01
- **Visualization Load Time**: Should be <30 seconds
- **Export Time**: Should be <1 minute

### **User Experience Metrics**
- **Ease of Use**: 1-5 scale (target: ≥4)
- **Documentation Quality**: 1-5 scale (target: ≥4)
- **Error Message Helpfulness**: 1-5 scale (target: ≥3)
- **Overall Satisfaction**: 1-5 scale (target: ≥4)

---

## 📝 **Bug Report Template**

### **Critical Bug Report**
```
**Severity**: Critical
**Feature**: [MFA/DSM/FOMP/Monte Carlo/Visualization]
**Steps to Reproduce**:
1. 
2. 
3. 
**Expected Result**: 
**Actual Result**: 
**Error Message**: 
**System Info**: OS, Python version, BioDYM version
**Workaround**: 
```

### **Feature Request**
```
**Feature**: [Feature name]
**Priority**: High/Medium/Low
**Use Case**: 
**Current Workaround**: 
**Proposed Solution**: 
```

---

## 🎯 **Testing Focus Areas**

### **For Technical Users**
- Focus on: Installation, core calculations, performance
- Test: Edge cases, error handling, system integration
- Report: Technical issues, performance bottlenecks

### **For Domain Experts**
- Focus on: Excel template, scenario management, visualizations
- Test: Real-world use cases, data input, result interpretation
- Report: Usability issues, missing features, documentation gaps

### **For End Users**
- Focus on: Overall workflow, ease of use, documentation
- Test: Complete analysis workflow, common tasks
- Report: User experience issues, learning curve, satisfaction

---

## 📈 **Success Indicators**

### **Green Flags (Everything Working)**
- ✅ Installation completes in <10 minutes
- ✅ First analysis runs without errors
- ✅ Mass balance validation passes
- ✅ Visualizations are clear and interactive
- ✅ Results can be exported successfully
- ✅ User feels confident to proceed

### **Yellow Flags (Minor Issues)**
- ⚠️ Installation requires manual steps
- ⚠️ Some error messages are unclear
- ⚠️ Visualizations are slow to load
- ⚠️ Documentation has minor gaps
- ⚠️ Some features are confusing

### **Red Flags (Major Issues)**
- ❌ Installation fails completely
- ❌ Analysis crashes or produces errors
- ❌ Mass balance violations
- ❌ Visualizations don't work
- ❌ Results are incorrect or unrealistic
- ❌ User cannot complete basic tasks

---

## 🚀 **Quick Start for Beta Testers**

### **Step 1: Setup (5 minutes)**
```bash
git clone -b beta-publication https://github.com/JScholz-tech/Biodym_JS.git
cd Biodym_JS
uv sync
```

### **Step 2: First Test (10 minutes)**
```bash
uv run jupyter lab
# Open BioDYM_Scientific_Notebook.ipynb
# Run all cells
```

### **Step 3: Report Results (5 minutes)**
- Complete the beta testing questionnaire
- Report any issues on GitHub
- Provide feedback on user experience

### **Step 4: Advanced Testing (Optional)**
- Try custom scenarios
- Test Monte Carlo simulation
- Explore advanced features

---

*This quick reference provides essential information for beta testers to efficiently test BioDYM and provide valuable feedback.*
