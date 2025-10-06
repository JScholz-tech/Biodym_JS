#!/usr/bin/env python3
"""
Fix markdown questionnaire format for Moodle XML conversion
"""

import re

def fix_markdown_format():
    """Fix markdown format to have each option on separate lines"""
    
    with open('docs/BETA_TESTING_QUESTIONNAIRE.md', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Pattern to match lines with multiple checkboxes on same line
    pattern = r'(\s*-\s*)□\s*([^□\n]+?)\s*□\s*([^□\n]+?)\s*□\s*([^□\n]+?)\s*□\s*([^□\n]+?)\s*□\s*([^□\n]+?)(?:\s*□\s*([^□\n]+?))?'
    
    def replace_multiple_checkboxes(match):
        indent = match.group(1)
        options = [match.group(2), match.group(3), match.group(4), match.group(5), match.group(6)]
        if match.group(7):  # If there's a 6th option
            options.append(match.group(7))
        
        # Clean up each option
        cleaned_options = []
        for option in options:
            cleaned = option.strip()
            if cleaned:
                cleaned_options.append(f"{indent}- {cleaned}")
        
        return '\n'.join(cleaned_options)
    
    # Apply the fix
    fixed_content = re.sub(pattern, replace_multiple_checkboxes, content)
    
    # Also fix single checkbox patterns
    single_pattern = r'(\s*-\s*)□\s*([^-\n]+)'
    def replace_single_checkbox(match):
        indent = match.group(1)
        option = match.group(2).strip()
        return f"{indent}- {option}"
    
    fixed_content = re.sub(single_pattern, replace_single_checkbox, fixed_content)
    
    # Write the fixed content back
    with open('docs/BETA_TESTING_QUESTIONNAIRE.md', 'w', encoding='utf-8') as f:
        f.write(fixed_content)
    
    print("Fixed markdown format - each option now on separate line")

if __name__ == "__main__":
    fix_markdown_format()
