#!/usr/bin/env python3
"""
Convert markdown questionnaire to JSON format
"""

import json
import re

def parse_markdown_to_json(md_file):
    """Parse markdown questionnaire to JSON format"""
    
    with open(md_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    questionnaire = {
        "title": "BioDYM Beta Testing Questionnaire",
        "description": "Comprehensive feedback collection for BioDYM beta testing",
        "sections": [],
        "questions": []
    }
    
    lines = content.split('\n')
    current_section = None
    question_id = 1
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        # Detect sections
        if line.startswith('## ') and not line.startswith('### '):
            section_name = line[3:].strip()
            current_section = {
                "name": section_name,
                "description": "",
                "questions": []
            }
            questionnaire["sections"].append(current_section)
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
            
            question = {
                "id": question_id,
                "text": question_text,
                "type": question_type,
                "options": options,
                "required": True,
                "section": current_section["name"] if current_section else "General"
            }
            
            questionnaire["questions"].append(question)
            if current_section:
                current_section["questions"].append(question_id)
            question_id += 1
        
        i += 1
    
    return questionnaire

if __name__ == "__main__":
    questionnaire = parse_markdown_to_json("../docs/BETA_TESTING_QUESTIONNAIRE.md")
    
    with open("beta_testing_questionnaire.json", 'w', encoding='utf-8') as f:
        json.dump(questionnaire, f, indent=2, ensure_ascii=False)
    
    print(f"JSON questionnaire generated: beta_testing_questionnaire.json")
    print(f"Total questions: {len(questionnaire['questions'])}")
    print(f"Total sections: {len(questionnaire['sections'])}")
