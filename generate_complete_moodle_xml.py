#!/usr/bin/env python3
"""
Complete Moodle XML generator for BioDYM questionnaire
"""

import re

def parse_markdown_questionnaire():
    """Parse the markdown questionnaire and extract questions"""
    
    # Read the markdown file
    with open('docs/BETA_TESTING_QUESTIONNAIRE.md', 'r', encoding='utf-8') as f:
        content = f.read()
    
    questions = []
    lines = content.split('\n')
    i = 0
    
    while i < len(lines):
        line = lines[i].strip()
        
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
                while j < len(lines) and lines[j].strip().startswith('- '):
                    option_text = lines[j].strip()
                    if option_text.startswith('- '):
                        option_text = option_text[2:].strip()
                    if option_text:
                        options.append(option_text)
                    j += 1
                i = j - 1
            
            questions.append({
                'text': question_text,
                'type': question_type,
                'options': options
            })
        
        i += 1
    
    return questions

def generate_complete_moodle_xml():
    """Generate complete Moodle feedback XML"""
    
    questions = parse_markdown_questionnaire()
    
    xml_content = '''<?xml version="1.0" encoding="UTF-8" ?>
<FEEDBACK VERSION="200701" COMMENT="XML-Importfile for mod/feedback">
     <ITEMS>'''
    
    item_id = 111325
    
    # Add section headers and questions
    sections = [
        ("Installation & Setup Experience", 1, 7),
        ("Excel Template & Data Input", 8, 15), 
        ("Core Functionality Testing", 16, 27),
        ("Visualization & Analysis", 29, 36),
        ("Scenario Management & Uncertainty Analysis", 37, 43),
        ("Documentation & Usability", 44, 51),
        ("Bug Reports & Issues", 52, 57),
        ("Feature Evaluation", 58, 60),
        ("Overall Assessment", 61, 68),
        ("Additional Comments", 69, 71)
    ]
    
    question_index = 0
    
    for section_name, start_q, end_q in sections:
        # Add section label
        xml_content += f'''
          <ITEM TYPE="label" REQUIRED="0">
               <ITEMID>
                    <![CDATA[{item_id}]]>
               </ITEMID>
               <ITEMTEXT>
                    <![CDATA[label]]>
               </ITEMTEXT>
               <ITEMLABEL>
                    <![CDATA[]]>
               </ITEMLABEL>
               <PRESENTATION>
                    <![CDATA[<div style="color: #e4e4e4; background-color: #181818; font-family: Consolas, 'Courier New', monospace; font-weight: normal; font-size: 14px; line-height: 19px; white-space: pre;">
<div><span style="color: #f8c762;">**{section_name}**</span></div>
</div>]]>
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
        
        # Add questions for this section
        questions_in_section = end_q - start_q + 1
        for _ in range(questions_in_section):
            if question_index < len(questions):
                q = questions[question_index]
                
                # Determine presentation based on question type
                if q['type'] == 'multichoice':
                    if q['options']:
                        options_str = 'r>>>>>' + '\n'.join(q['options'])
                        presentation = options_str
                    else:
                        # Default rating scale
                        presentation = 'r>>>>>1 (Very poor)\n2 (Poor)\n3 (Neutral)\n4 (Good)\n5 (Excellent)'
                elif q['type'] == 'textfield':
                    presentation = '30|255'
                elif q['type'] == 'textarea':
                    presentation = '30|5'
                else:
                    presentation = ''
                
                xml_content += f'''
          <ITEM TYPE="{q['type']}" REQUIRED="0">
               <ITEMID>
                    <![CDATA[{item_id}]]>
               </ITEMID>
               <ITEMTEXT>
                    <![CDATA[{q['text']}]]>
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
                question_index += 1
    
    xml_content += '''
     </ITEMS>
</FEEDBACK>'''
    
    return xml_content

if __name__ == "__main__":
    xml_output = generate_complete_moodle_xml()
    
    with open("beta_testing_questionnaire_complete_moodle.xml", 'w', encoding='utf-8') as f:
        f.write(xml_output)
    
    questions = parse_markdown_questionnaire()
    print("Complete Moodle XML questionnaire generated: beta_testing_questionnaire_complete_moodle.xml")
    print(f"Generated {len(questions)} questions")
    print("\nFile ready for import into Moodle Feedback module!")
