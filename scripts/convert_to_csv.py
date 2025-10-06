#!/usr/bin/env python3
"""
Convert markdown questionnaire to CSV format
"""

import csv
import re

def parse_markdown_to_csv(md_file):
    """Parse markdown questionnaire to CSV format"""
    
    with open(md_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    questions = []
    lines = content.split('\n')
    current_section = None
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        # Detect sections
        if line.startswith('## ') and not line.startswith('### '):
            current_section = line[3:].strip()
            continue
            
        # Detect questions
        if re.match(r'^\d+\.', line):
            question_text = line.split('.', 1)[1].strip()
            
            # Determine question type
            question_type = 'text'
            if 'scale' in question_text.lower() or 'rating' in question_text.lower():
                question_type = 'rating'
            elif 'select all that apply' in question_text.lower():
                question_type = 'checkbox'
            elif '□' in question_text or '☐' in question_text:
                question_type = 'radio'
            
            # Extract options
            options = []
            if question_type in ['radio', 'checkbox', 'rating']:
                j = i + 1
                while j < len(lines) and (lines[j].strip().startswith('- □') or 
                                        lines[j].strip().startswith('- ☐') or
                                        lines[j].strip().startswith('□') or
                                        lines[j].strip().startswith('☐')):
                    option_text = lines[j].strip()
                    if option_text.startswith('- '):
                        option_text = option_text[2:]
                    if option_text.startswith('□') or option_text.startswith('☐'):
                        option_text = option_text[1:].strip()
                    if option_text:
                        options.append(option_text)
                    j += 1
                i = j - 1
            
            questions.append({
                'section': current_section or 'General',
                'question': question_text,
                'type': question_type,
                'options': '; '.join(options) if options else '',
                'required': 'Yes'
            })
        
        i += 1
    
    return questions

if __name__ == "__main__":
    questions = parse_markdown_to_csv("../docs/BETA_TESTING_QUESTIONNAIRE.md")
    
    with open("beta_testing_questionnaire.csv", 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['section', 'question', 'type', 'options', 'required'])
        writer.writeheader()
        writer.writerows(questions)
    
    print(f"CSV questionnaire generated: beta_testing_questionnaire.csv")
    print(f"Total questions: {len(questions)}")
