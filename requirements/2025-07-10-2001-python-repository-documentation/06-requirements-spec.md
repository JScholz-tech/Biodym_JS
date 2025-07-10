# BioDYM Documentation Requirements Specification

## Problem Statement
The BioDYM repository has grown from a beginner's vibe-coded project into a complex Material Flow Analysis tool with both legacy notebook-based and modern modular implementations. The documentation is fragmented across three README files, contains stale content, and lacks clear guidance for domain experts who are not programmers. A comprehensive documentation overhaul is needed to make the tool accessible and usable.

## Solution Overview
Create a unified, comprehensive documentation system that:
- Consolidates all existing documentation into a single, well-organized structure
- Provides clear visual aids and architecture diagrams
- Offers step-by-step tutorials for domain experts
- Documents both legacy and modern workflows to enable smooth migration
- Includes troubleshooting guides for common issues
- Creates a clear roadmap for using the repository

## Functional Requirements

### FR1: Consolidate Documentation
- **FR1.1**: Merge README.md, README2.0.md, and biodym_mfa_tool/README.md into a single comprehensive README at repository root
- **FR1.2**: Remove stale content and outdated references
- **FR1.3**: Create concise, effective documentation focused on user needs
- **FR1.4**: Preserve important content from all three sources

### FR2: Create Visual Documentation
- **FR2.1**: Design system architecture diagram showing both old and new structures
- **FR2.2**: Create data flow diagrams for MFA processes
- **FR2.3**: Update workflow diagrams to reflect current implementation
- **FR2.4**: Include visual guides for Excel template structure

### FR3: Develop User Tutorials
- **FR3.1**: Create QUICKSTART.md tutorial using basic_example_1
- **FR3.2**: Walk through complete workflow: Excel setup → Analysis → Results export
- **FR3.3**: Include screenshots and code snippets
- **FR3.4**: Target domain experts without programming experience

### FR4: Document Excel Templates
- **FR4.1**: Create comprehensive Excel template documentation
- **FR4.2**: Document each sheet's purpose and required fields
- **FR4.3**: Provide examples for each data type
- **FR4.4**: Include validation rules and constraints

### FR5: Create Troubleshooting Guide
- **FR5.1**: Create TROUBLESHOOTING.md file
- **FR5.2**: Document common mass balance errors and solutions
- **FR5.3**: Include debugging steps for each error type
- **FR5.4**: Provide contact information for further help

### FR6: Develop Migration Roadmap
- **FR6.1**: Create clear migration path from notebooks to modular tool
- **FR6.2**: Document benefits of new approach
- **FR6.3**: Provide conversion guides for existing workflows
- **FR6.4**: Include compatibility notes

## Technical Requirements

### TR1: File Structure
- **TR1.1**: Main README.md at repository root
- **TR1.2**: docs/ folder for additional documentation:
  - QUICKSTART.md
  - TROUBLESHOOTING.md
  - EXCEL_TEMPLATE_GUIDE.md
  - MIGRATION_GUIDE.md
- **TR1.3**: Archive old READMEs in docs/archive/
- **TR1.4**: Update all internal links and references

### TR2: Documentation Standards
- **TR2.1**: Use clear, non-technical language for domain experts
- **TR2.2**: Include table of contents in long documents
- **TR2.3**: Use consistent formatting and styling
- **TR2.4**: Include version numbers and last updated dates

### TR3: Visual Elements
- **TR3.1**: Use Mermaid diagrams for architecture (GitHub-compatible)
- **TR3.2**: Include example screenshots where helpful
- **TR3.3**: Create flowcharts for decision processes
- **TR3.4**: Use tables for parameter descriptions

## Implementation Hints

### Documentation Structure
```
Biodym_JS/
├── README.md (consolidated, comprehensive)
├── docs/
│   ├── QUICKSTART.md
│   ├── TROUBLESHOOTING.md
│   ├── EXCEL_TEMPLATE_GUIDE.md
│   ├── MIGRATION_GUIDE.md
│   ├── architecture/
│   │   ├── system_overview.md
│   │   └── data_flow.md
│   └── archive/
│       ├── README_old.md
│       ├── README2.0_old.md
│       └── biodym_mfa_tool_README_old.md
```

### Key Sections for Main README
1. **Overview**: What is BioDYM, what it does, who it's for
2. **Quick Start**: 3-step process to get running
3. **Installation**: Clear setup instructions
4. **Usage**: Links to detailed guides
5. **Features**: Key capabilities with visual examples
6. **Documentation**: Links to all guides
7. **Contributing**: How to help improve
8. **License**: Legal information

### Excel Template Documentation Approach
- One section per sheet
- Required vs optional fields clearly marked
- Example values for each field
- Common mistakes and how to avoid them
- Validation checklist

## Acceptance Criteria
- [ ] All three README files consolidated into one
- [ ] No stale or outdated content remains
- [ ] Domain experts can understand without programming knowledge
- [ ] Visual diagrams clearly show system architecture
- [ ] Quick-start tutorial completes successfully
- [ ] Excel template fully documented with examples
- [ ] Common errors documented with solutions
- [ ] Migration path clearly defined
- [ ] All internal links work correctly
- [ ] Documentation is concise and effective

## Assumptions
- Users are domain experts in material flow analysis but not programmers
- The scientific concepts (MFA, DSM, FOMP) are already understood
- Focus is on tool usage, not extending functionality
- Both old and new workflows need documentation during transition period
- Existing Excel template structure will be maintained