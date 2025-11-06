# BioDYM Documentation

This directory contains all documentation for the BioDYM Material Flow Analysis tool.

## 📁 Documentation Structure

### User Documentation (This Folder)

- **[USER_GUIDE.md](USER_GUIDE.md)** - Comprehensive user guide with tutorials and examples
- **[TESTING_GUIDE.md](TESTING_GUIDE.md)** - Quick testing guide for testers and new users

### Development Documentation (`development/`)

Core development resources for contributors and maintainers:

- **[CLAUDE.md](development/CLAUDE.md)** - Comprehensive development guide for Claude Code
- **[CODING_STANDARDS.md](development/CODING_STANDARDS.md)** - Code quality standards and conventions
- **[TECHNICAL_DEEP_DIVE.md](development/TECHNICAL_DEEP_DIVE.md)** - In-depth technical documentation
- **[TROUBLESHOOTING.md](development/TROUBLESHOOTING.md)** - Common issues and solutions
- **[TECHNICAL_DEBT.md](development/TECHNICAL_DEBT.md)** - Known technical debt and future improvements
- **[ROADMAP.md](development/ROADMAP.md)** - Development roadmap and planned features
- **[PRE_PUBLICATION_CHECKLIST.md](development/PRE_PUBLICATION_CHECKLIST.md)** - Publication readiness checklist
- **[BioDYM_Publication_TODO.md](development/BioDYM_Publication_TODO.md)** - Publication tasks and tracking

### Design Documentation (`development/design/`)

Implementation plans and design decisions:

- **[ELEMENT_HIERARCHY_DESIGN.md](development/design/ELEMENT_HIERARCHY_DESIGN.md)** - Element hierarchy system design
- **[FLEXIBLE_ELEMENT_IMPLEMENTATION_PLAN.md](development/design/FLEXIBLE_ELEMENT_IMPLEMENTATION_PLAN.md)** - Element-agnostic architecture plan
- **[IMPLEMENTATION_PLAN_DATA_RECONCILIATION.md](development/design/IMPLEMENTATION_PLAN_DATA_RECONCILIATION.md)** - Data reconciliation module (v2.0)
- **[DYNAMIC_EXCEL_HEADERS_SOLUTION.md](development/design/DYNAMIC_EXCEL_HEADERS_SOLUTION.md)** - Excel header parsing solution
- **[EXCEL_ELEMENT_NAMING_DISCUSSION.md](development/design/EXCEL_ELEMENT_NAMING_DISCUSSION.md)** - Element naming conventions
- **[E_NAMING_COMPATIBILITY_REPORT.md](development/design/E_NAMING_COMPATIBILITY_REPORT.md)** - Process logic compatibility analysis
- **[PHASE_5B_COMPLETE_SUMMARY.md](development/design/PHASE_5B_COMPLETE_SUMMARY.md)** - Phase 5b implementation summary

### Feature Documentation (`features/`)

Specific feature guides and overviews:

- **[VISUALIZATION_SYSTEM_OVERVIEW.md](features/VISUALIZATION_SYSTEM_OVERVIEW.md)** - Complete visualization system overview
- **[VISUALIZATION_IMPROVEMENTS_SUMMARY.md](features/VISUALIZATION_IMPROVEMENTS_SUMMARY.md)** - Recent visualization updates
- **[PUBLICATION_STYLE_USAGE_GUIDE.md](features/PUBLICATION_STYLE_USAGE_GUIDE.md)** - Publication-quality plotting guide
- **[MULTIPLOT_SANKEY_USAGE.md](features/MULTIPLOT_SANKEY_USAGE.md)** - Multi-element Sankey diagrams
- **[METALS_EXTENSION_QUICKSTART.md](features/METALS_EXTENSION_QUICKSTART.md)** - Extending BioDYM for metal systems
- **[00_BioDYM_Workflow_Improved_Structure.md](features/00_BioDYM_Workflow_Improved_Structure.md)** - Workflow notebook structure

### Additional Resources

- **workflow_diagram.drawio** - Editable workflow diagram (DrawIO format)
- **workflow_diagram.pdf** - Workflow diagram (PDF)
- **workflow_explained.pdf** - Detailed workflow explanation

## 🚀 Quick Navigation

### I want to...

**Use BioDYM for the first time:**
→ Start with [TESTING_GUIDE.md](TESTING_GUIDE.md)

**Learn how to use BioDYM:**
→ Read [USER_GUIDE.md](USER_GUIDE.md)

**Contribute code:**
→ Read [CLAUDE.md](development/CLAUDE.md) and [CODING_STANDARDS.md](development/CODING_STANDARDS.md)

**Understand the technical details:**
→ Read [TECHNICAL_DEEP_DIVE.md](development/TECHNICAL_DEEP_DIVE.md)

**Fix a bug or issue:**
→ Check [TROUBLESHOOTING.md](development/TROUBLESHOOTING.md)

**Add a new feature:**
→ Review [ROADMAP.md](development/ROADMAP.md) and design docs in `development/design/`

**Prepare for publication:**
→ Follow [PRE_PUBLICATION_CHECKLIST.md](development/PRE_PUBLICATION_CHECKLIST.md)

**Understand visualizations:**
→ Read [VISUALIZATION_SYSTEM_OVERVIEW.md](features/VISUALIZATION_SYSTEM_OVERVIEW.md)

**Extend BioDYM to other materials:**
→ Read [METALS_EXTENSION_QUICKSTART.md](features/METALS_EXTENSION_QUICKSTART.md)

## 📚 Documentation Categories

### 1. User Guides
For users who want to use BioDYM for their research:
- USER_GUIDE.md
- TESTING_GUIDE.md

### 2. Developer Guides
For developers contributing to BioDYM:
- CLAUDE.md (comprehensive development reference)
- CODING_STANDARDS.md
- TROUBLESHOOTING.md

### 3. Technical Documentation
For understanding BioDYM's architecture and design:
- TECHNICAL_DEEP_DIVE.md
- TECHNICAL_DEBT.md
- All files in `development/design/`

### 4. Project Management
For tracking progress and planning:
- ROADMAP.md
- PRE_PUBLICATION_CHECKLIST.md
- BioDYM_Publication_TODO.md

### 5. Feature Documentation
For understanding specific features:
- All files in `features/`

## 🔄 Documentation Workflow

### When Starting a New Feature:
1. Check [ROADMAP.md](development/ROADMAP.md) for planned features
2. Create a design document in `development/design/` if needed
3. Follow [CODING_STANDARDS.md](development/CODING_STANDARDS.md)
4. Update relevant feature docs in `features/`

### When Fixing a Bug:
1. Check [TROUBLESHOOTING.md](development/TROUBLESHOOTING.md) first
2. Document the solution in TROUBLESHOOTING.md
3. Add test cases to prevent regression

### Before Publishing:
1. Follow [PRE_PUBLICATION_CHECKLIST.md](development/PRE_PUBLICATION_CHECKLIST.md)
2. Update [USER_GUIDE.md](USER_GUIDE.md) with any new features
3. Review and update [TESTING_GUIDE.md](TESTING_GUIDE.md)

## 📝 Contributing to Documentation

When adding or updating documentation:

1. **User-facing docs** → Place in `05_docs/`
2. **Development docs** → Place in `05_docs/development/`
3. **Design documents** → Place in `05_docs/development/design/`
4. **Feature guides** → Place in `05_docs/features/`

Keep documentation:
- ✅ Up-to-date with code changes
- ✅ Clear and concise
- ✅ Well-structured with headings
- ✅ Including examples where helpful
- ✅ Cross-referenced between related docs

## 🔗 External Documentation

- **ODYM Framework**: https://github.com/IndEcol/ODYM
- **GitHub Repository**: https://github.com/JScholz-tech/Biodym_JS
- **Main README**: See [../README.md](../README.md) in the root directory

---

**Last Updated**: 2025-11-06
**BioDYM Version**: 1.0-beta
