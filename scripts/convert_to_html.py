#!/usr/bin/env python3
"""
Convert markdown questionnaire to HTML form
"""

import re
import json

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
            question_type = 'text'
            if 'scale' in question_text.lower() or 'rating' in question_text.lower():
                question_type = 'rating'
            elif 'select all that apply' in question_text.lower():
                question_type = 'checkbox'
            elif '□' in question_text or '☐' in question_text:
                question_type = 'radio'
            
            # Extract options for multiple choice questions
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
                'section': current_section,
                'text': question_text,
                'type': question_type,
                'options': options
            })
        
        i += 1
    
    return questions

def generate_html_form(questions, output_file):
    """Generate HTML form from parsed questions"""
    
    html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>BioDYM Beta Testing Questionnaire</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
        .section { margin: 30px 0; padding: 20px; border: 1px solid #ddd; border-radius: 5px; }
        .section h2 { color: #333; border-bottom: 2px solid #007acc; padding-bottom: 10px; }
        .question { margin: 20px 0; }
        .question-text { font-weight: bold; margin-bottom: 10px; }
        .options { margin-left: 20px; }
        .option { margin: 5px 0; }
        input[type="text"], textarea { width: 100%; padding: 8px; border: 1px solid #ccc; border-radius: 3px; }
        textarea { height: 100px; resize: vertical; }
        .rating-scale { display: flex; gap: 10px; align-items: center; }
        .rating-option { display: flex; flex-direction: column; align-items: center; }
        .submit-btn { background-color: #007acc; color: white; padding: 15px 30px; border: none; border-radius: 5px; font-size: 16px; cursor: pointer; }
        .submit-btn:hover { background-color: #005a9e; }
    </style>
</head>
<body>
    <h1>BioDYM Beta Testing Questionnaire</h1>
    <form id="questionnaire" action="#" method="post">
"""
    
    current_section = None
    for i, q in enumerate(questions):
        if q['section'] != current_section:
            if current_section is not None:
                html += "    </div>\n"
            html += f'    <div class="section">\n'
            html += f'        <h2>{q["section"]}</h2>\n'
            current_section = q['section']
        
        html += f'        <div class="question">\n'
        html += f'            <div class="question-text">{q["text"]}</div>\n'
        
        if q['type'] == 'text':
            html += f'            <textarea name="q_{i+1}" placeholder="Your answer..."></textarea>\n'
        elif q['type'] == 'rating':
            html += f'            <div class="rating-scale">\n'
            for j in range(1, 6):
                html += f'                <div class="rating-option">\n'
                html += f'                    <input type="radio" name="q_{i+1}" value="{j}" id="q_{i+1}_{j}">\n'
                html += f'                    <label for="q_{i+1}_{j}">{j}</label>\n'
                html += f'                </div>\n'
            html += f'            </div>\n'
        elif q['type'] in ['radio', 'checkbox']:
            html += f'            <div class="options">\n'
            for j, option in enumerate(q['options']):
                input_type = 'checkbox' if q['type'] == 'checkbox' else 'radio'
                html += f'                <div class="option">\n'
                html += f'                    <input type="{input_type}" name="q_{i+1}" value="{option}" id="q_{i+1}_{j}">\n'
                html += f'                    <label for="q_{i+1}_{j}">{option}</label>\n'
                html += f'                </div>\n'
            html += f'            </div>\n'
        
        html += f'        </div>\n'
    
    if current_section is not None:
        html += "    </div>\n"
    
    html += """
        <div style="text-align: center; margin: 40px 0;">
            <button type="submit" class="submit-btn">Submit Questionnaire</button>
        </div>
    </form>
    
    <script>
        document.getElementById('questionnaire').addEventListener('submit', function(e) {
            e.preventDefault();
            alert('Thank you for your feedback! This form is for demonstration purposes.');
        });
    </script>
</body>
</html>"""
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"HTML form generated: {output_file}")

if __name__ == "__main__":
    questions = parse_markdown_questionnaire("../docs/BETA_TESTING_QUESTIONNAIRE.md")
    generate_html_form(questions, "beta_testing_questionnaire.html")
    print(f"Parsed {len(questions)} questions")
