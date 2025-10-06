#!/usr/bin/env python3
"""
Generate corrected Moodle XML for BioDYM Beta Testing Questionnaire
This version uses the correct Moodle Feedback module format
"""

import re
import os

def parse_markdown_questionnaire(file_path):
    """Parse the markdown questionnaire and extract questions"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    questions = []
    lines = content.split('\n')
    
    current_question = None
    question_counter = 0
    
    for i, line in enumerate(lines):
        line = line.strip()
        
        # Skip empty lines and headers
        if not line or line.startswith('#') or line.startswith('---'):
            continue
            
        # Check for question patterns
        if re.match(r'^\d+\.\s*\*\*.*\*\*', line):
            question_counter += 1
            # Extract question text
            question_text = re.sub(r'^\d+\.\s*\*\*(.*?)\*\*.*', r'\1', line)
            question_text = question_text.strip()
            
            # Determine question type and options based on content
            if '(1-5 scale)' in line:
                question_type = 'multichoice'
                options = [
                    '1 (Very difficult)',
                    '2 (Difficult)', 
                    '3 (Neutral)',
                    '4 (Easy)',
                    '5 (Very easy)'
                ]
            elif '(Select all that apply)' in line:
                question_type = 'multichoice'
                options = []
            elif '□' in line or '☐' in line:
                question_type = 'multichoice'
                options = []
            else:
                question_type = 'textfield'
                options = []
            
            current_question = {
                'number': question_counter,
                'text': question_text,
                'type': question_type,
                'options': options
            }
            questions.append(current_question)
            
        # Check for options (lines starting with - or □)
        elif current_question and (line.startswith('- ') or line.startswith('□') or line.startswith('☐')):
            if current_question['type'] == 'multichoice':
                # Clean up the option text
                option_text = re.sub(r'^[-□☐]\s*', '', line).strip()
                if option_text and option_text not in current_question['options']:
                    current_question['options'].append(option_text)
    
    return questions

def generate_moodle_xml(questions):
    """Generate Moodle XML in the correct Feedback module format"""
    
    xml_content = '''<?xml version="1.0" encoding="UTF-8" ?>
<FEEDBACK VERSION="200701" COMMENT="XML-Importfile for mod/feedback">
     <ITEMS>'''
    
    item_id = 111325
    
    for question in questions:
        # Add question number to text
        question_text = f"{question['number']}. **{question['text']}**"
        
        if question['type'] == 'multichoice' and question['options']:
            # Generate options string with correct format
            options_str = 'r>>>>>' + '\n||'.join(question['options'])
            
            xml_content += f'''
          <ITEM TYPE="multichoice" REQUIRED="0">
               <ITEMID>
                    <![CDATA[{item_id}]]>
               </ITEMID>
               <ITEMTEXT>
                    <![CDATA[{question_text}]]>
               </ITEMTEXT>
               <ITEMLABEL>
                    <![CDATA[]]>
               </ITEMLABEL>
               <PRESENTATION>
                    <![CDATA[{options_str}]]>
               </PRESENTATION>
               <OPTIONS>
                    <![CDATA[]]>
               </OPTIONS>
               <DEPENDITEM>
                    <![CDATA[0]]>
               </DEPENDITEM>
               <DEPENDVALUE>
                    <![CDATA[]]>
               </DEPENDVALUE>
          </ITEM>'''
        else:
            # Text field or textarea
            field_type = 'textarea' if len(question['text']) > 100 else 'textfield'
            presentation = '30|255' if field_type == 'textfield' else '30|5'
            
            xml_content += f'''
          <ITEM TYPE="{field_type}" REQUIRED="0">
               <ITEMID>
                    <![CDATA[{item_id}]]>
               </ITEMID>
               <ITEMTEXT>
                    <![CDATA[{question_text}]]>
               </ITEMTEXT>
               <ITEMLABEL>
                    <![CDATA[]]>
               </ITEMLABEL>
               <PRESENTATION>
                    <![CDATA[{presentation}]]>
               </PRESENTATION>
               <OPTIONS>
                    <![CDATA[]]>
               </OPTIONS>
               <DEPENDITEM>
                    <![CDATA[0]]>
               </DEPENDITEM>
               <DEPENDVALUE>
                    <![CDATA[]]>
               </DEPENDVALUE>
          </ITEM>'''
        
        item_id += 1
    
    xml_content += '''
     </ITEMS>
</FEEDBACK>'''
    
    return xml_content

def main():
    # Change to scripts directory
    os.chdir('scripts')
    
    # Parse the markdown questionnaire
    questions = parse_markdown_questionnaire('../docs/BETA_TESTING_QUESTIONNAIRE.md')
    
    print(f"Parsed {len(questions)} questions")
    
    # Generate XML
    xml_content = generate_moodle_xml(questions)
    
    # Write to file
    with open('../beta_testing_questionnaire_corrected_moodle.xml', 'w', encoding='utf-8') as f:
        f.write(xml_content)
    
    print("Generated corrected Moodle XML file: beta_testing_questionnaire_corrected_moodle.xml")
    
    # Show sample of first few questions
    print("\nSample questions:")
    for i, q in enumerate(questions[:5]):
        print(f"{q['number']}. {q['text']} ({q['type']})")
        if q['options']:
            print(f"   Options: {q['options']}")

if __name__ == "__main__":
    main()