#!/usr/bin/env python3
"""
Simple Moodle XML generator for BioDYM questionnaire
"""

# Sample questions from the questionnaire
questions = [
    {
        'section': 'Installation & Setup Experience',
        'text': 'How easy was the installation process?',
        'type': 'multichoice',
        'options': ['1 (Very difficult)', '2 (Difficult)', '3 (Neutral)', '4 (Easy)', '5 (Very easy)']
    },
    {
        'section': 'Installation & Setup Experience', 
        'text': 'Did you encounter any installation issues?',
        'type': 'multichoice',
        'options': ['No issues', 'Minor issues (resolved quickly)', 'Major issues (took significant time to resolve)', 'Could not complete installation']
    },
    {
        'section': 'Excel Template & Data Input',
        'text': 'Rate the clarity of the Excel template structure',
        'type': 'multichoice', 
        'options': ['1 (Very unclear)', '2 (Unclear)', '3 (Neutral)', '4 (Clear)', '5 (Very clear)']
    },
    {
        'section': 'Excel Template & Data Input',
        'text': 'Which sheets did you find most/least intuitive?',
        'type': 'textfield',
        'options': []
    },
    {
        'section': 'Core Functionality Testing',
        'text': 'Rate the accuracy of MFA calculations',
        'type': 'multichoice',
        'options': ['1 (Very inaccurate)', '2 (Inaccurate)', '3 (Neutral)', '4 (Accurate)', '5 (Very accurate)']
    },
    {
        'section': 'Core Functionality Testing',
        'text': 'Did mass balance checks work correctly?',
        'type': 'multichoice',
        'options': ['Always correct', 'Mostly correct', 'Sometimes incorrect', 'Often incorrect', 'Never worked']
    }
]

def generate_moodle_xml():
    """Generate Moodle feedback XML"""
    
    xml_content = '''<?xml version="1.0" encoding="UTF-8" ?>
<FEEDBACK VERSION="200701" COMMENT="XML-Importfile for mod/feedback">
     <ITEMS>'''
    
    item_id = 111325
    current_section = None
    
    for q in questions:
        # Add section label if new section
        if current_section != q['section']:
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
<div><span style="color: #f8c762;">**{q['section']}**</span></div>
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
            current_section = q['section']
        
        # Add question
        if q['type'] == 'multichoice':
            options_str = 'r>>>>>' + '\n'.join(q['options'])
            presentation = options_str
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
    
    xml_content += '''
     </ITEMS>
</FEEDBACK>'''
    
    return xml_content

if __name__ == "__main__":
    xml_output = generate_moodle_xml()
    
    with open("beta_testing_questionnaire_moodle.xml", 'w', encoding='utf-8') as f:
        f.write(xml_output)
    
    print("Moodle XML questionnaire generated: beta_testing_questionnaire_moodle.xml")
    print(f"Generated {len(questions)} questions")
    print("\nSample XML structure:")
    print(xml_output[:500] + "...")
