#!/usr/bin/env python3
"""
Convert markdown questionnaire to Moodle Feedback XML format
"""

import re
import xml.etree.ElementTree as ET
from xml.dom import minidom

def parse_markdown_questionnaire(md_file):
    """Parse markdown questionnaire into structured data"""
    
    with open(md_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    questions = []
    current_section = None
    
    lines = content.split('\n')
    i = 0
    
    while i < len(lines):
        line = lines[i].strip()
        
        # Detect sections
        if line.startswith('## ') and not line.startswith('### '):
            current_section = line[3:].strip()
            continue
            
        # Detect questions (numbered)
        if re.match(r'^\d+\.', line):
            question_text = line.split('.', 1)[1].strip()
            
            # Determine question type
            question_type = 'textfield'
            if 'scale' in question_text.lower() or 'rating' in question_text.lower():
                question_type = 'multichoice'
            elif 'select all that apply' in question_text.lower():
                question_type = 'multichoice'
            elif '□' in question_text or '☐' in question_text:
                question_type = 'multichoice'
            elif 'describe' in question_text.lower() or 'comments' in question_text.lower():
                question_type = 'textarea'
            
            # Extract options for multiple choice questions
            options = []
            if question_type == 'multichoice':
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
                'section': current_section,
                'text': question_text,
                'type': question_type,
                'options': options
            })
        
        i += 1
    
    return questions

def generate_moodle_xml(questions, output_file):
    """Generate Moodle feedback XML from parsed questions"""
    
    # Create root element
    root = ET.Element('FEEDBACK')
    root.set('VERSION', '200701')
    root.set('COMMENT', 'XML-Importfile for mod/feedback')
    
    items = ET.SubElement(root, 'ITEMS')
    
    item_id = 111325  # Starting ID (following your example pattern)
    
    for i, q in enumerate(questions):
        # Add section labels
        if i == 0 or (i > 0 and questions[i-1]['section'] != q['section']):
            # Add section label
            section_item = ET.SubElement(items, 'ITEM')
            section_item.set('TYPE', 'label')
            section_item.set('REQUIRED', '0')
            
            itemid_elem = ET.SubElement(section_item, 'ITEMID')
            itemid_elem.text = str(item_id)
            item_id += 1
            
            itemtext_elem = ET.SubElement(section_item, 'ITEMTEXT')
            itemtext_elem.text = 'label'
            
            itemlabel_elem = ET.SubElement(section_item, 'ITEMLABEL')
            itemlabel_elem.text = ''
            
            presentation_elem = ET.SubElement(section_item, 'PRESENTATION')
            # Create styled section header
            section_title = q['section'].replace('**', '').replace('## ', '')
            presentation_elem.text = f'''<div style="color: #e4e4e4; background-color: #181818; font-family: Consolas, 'Courier New', monospace; font-weight: normal; font-size: 14px; line-height: 19px; white-space: pre;">
<div><span style="color: #f8c762;">**{section_title}**</span></div>
</div>'''
            
            options_elem = ET.SubElement(section_item, 'OPTIONS')
            options_elem.text = ''
            
            dependitem_elem = ET.SubElement(section_item, 'DEPENDITEM')
            dependitem_elem.text = '0'
            
            dependvalue_elem = ET.SubElement(section_item, 'DEPENDVALUE')
            dependvalue_elem.text = ''
        
        # Add question
        item = ET.SubElement(items, 'ITEM')
        item.set('TYPE', q['type'])
        item.set('REQUIRED', '0')
        
        # Item ID
        itemid_elem = ET.SubElement(item, 'ITEMID')
        itemid_elem.text = str(item_id)
        item_id += 1
        
        # Question text
        itemtext_elem = ET.SubElement(item, 'ITEMTEXT')
        itemtext_elem.text = q['text']
        
        # Item label
        itemlabel_elem = ET.SubElement(item, 'ITEMLABEL')
        itemlabel_elem.text = ''
        
        # Presentation (options for multichoice, size for text fields)
        presentation_elem = ET.SubElement(item, 'PRESENTATION')
        
        if q['type'] == 'multichoice':
            if q['options']:
                # Create options string for multichoice
                options_str = 'r>>>>>' + '|'.join(q['options'])
                presentation_elem.text = options_str
            else:
                # Default rating scale
                presentation_elem.text = 'r>>>>>1 (Very poor)|2 (Poor)|3 (Neutral)|4 (Good)|5 (Excellent)'
        elif q['type'] == 'textfield':
            presentation_elem.text = '30|255'  # width|maxlength
        elif q['type'] == 'textarea':
            presentation_elem.text = '30|5'  # width|height
        
        # Options
        options_elem = ET.SubElement(item, 'OPTIONS')
        options_elem.text = ''
        
        # Dependencies
        dependitem_elem = ET.SubElement(item, 'DEPENDITEM')
        dependitem_elem.text = '0'
        
        dependvalue_elem = ET.SubElement(item, 'DEPENDVALUE')
        dependvalue_elem.text = ''
    
    # Convert to string with proper formatting
    rough_string = ET.tostring(root, encoding='unicode')
    reparsed = minidom.parseString(rough_string)
    
    # Add XML declaration
    xml_string = '<?xml version="1.0" encoding="UTF-8" ?>\n' + reparsed.toprettyxml(indent="     ")[23:]
    
    # Clean up empty lines and fix formatting
    lines = xml_string.split('\n')
    cleaned_lines = []
    for line in lines:
        if line.strip():
            cleaned_lines.append(line)
    
    # Write to file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(cleaned_lines))
    
    print(f"Moodle XML questionnaire generated: {output_file}")

if __name__ == "__main__":
    questions = parse_markdown_questionnaire("docs/BETA_TESTING_QUESTIONNAIRE.md")
    generate_moodle_xml(questions, "beta_testing_questionnaire_moodle.xml")
    print(f"Parsed {len(questions)} questions")
