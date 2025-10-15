# Converting Beta Testing Questionnaire to Different Formats

## 🎯 **Overview**
This guide shows how to convert the markdown questionnaire into various formats for easier distribution and data collection.

---

## 📊 **Format Options**

### **1. Microsoft Forms**
- **Best for**: Easy distribution, automatic data collection, Excel export
- **Pros**: No coding required, built-in analytics, mobile-friendly
- **Cons**: Requires Microsoft account, limited customization

### **2. Google Forms**
- **Best for**: Free distribution, Google Sheets integration, wide accessibility
- **Pros**: Free, easy sharing, automatic data collection, Google Sheets export
- **Cons**: Requires Google account, limited advanced features

### **3. SurveyMonkey**
- **Best for**: Professional surveys, advanced analytics, custom branding
- **Pros**: Professional appearance, advanced question types, detailed analytics
- **Cons**: Paid service for full features, learning curve

### **4. Typeform**
- **Best for**: Beautiful, interactive surveys, great user experience
- **Pros**: Excellent UX, mobile-optimized, engaging interface
- **Cons**: Paid service, limited free responses

### **5. HTML Form**
- **Best for**: Custom hosting, full control, integration with existing systems
- **Pros**: Complete customization, can integrate with databases, free hosting
- **Cons**: Requires web development knowledge

---

## 🚀 **Quick Conversion Methods**

### **Method 1: Manual Copy-Paste (Fastest)**

#### **For Microsoft Forms:**
1. Go to [forms.microsoft.com](https://forms.microsoft.com)
2. Create new form
3. Copy questions from markdown file
4. Paste into form fields
5. Set question types (multiple choice, rating scale, text)

#### **For Google Forms:**
1. Go to [forms.google.com](https://forms.google.com)
2. Create new form
3. Copy questions from markdown file
4. Paste into form fields
5. Set question types and validation rules

### **Method 2: Automated Conversion Scripts**

I'll create Python scripts to help automate the conversion process.

---

## 🐍 **Python Conversion Scripts**

### **Script 1: Markdown to HTML Form**

```python
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
    for q in questions:
        if q['section'] != current_section:
            if current_section is not None:
                html += "    </div>\n"
            html += f'    <div class="section">\n'
            html += f'        <h2>{q["section"]}</h2>\n'
            current_section = q['section']
        
        html += f'        <div class="question">\n'
        html += f'            <div class="question-text">{q["text"]}</div>\n'
        
        if q['type'] == 'text':
            html += f'            <textarea name="q_{len(questions)}" placeholder="Your answer..."></textarea>\n'
        elif q['type'] == 'rating':
            html += f'            <div class="rating-scale">\n'
            for i in range(1, 6):
                html += f'                <div class="rating-option">\n'
                html += f'                    <input type="radio" name="q_{len(questions)}" value="{i}" id="q_{len(questions)}_{i}">\n'
                html += f'                    <label for="q_{len(questions)}_{i}">{i}</label>\n'
                html += f'                </div>\n'
            html += f'            </div>\n'
        elif q['type'] in ['radio', 'checkbox']:
            html += f'            <div class="options">\n'
            for i, option in enumerate(q['options']):
                input_type = 'checkbox' if q['type'] == 'checkbox' else 'radio'
                html += f'                <div class="option">\n'
                html += f'                    <input type="{input_type}" name="q_{len(questions)}" value="{option}" id="q_{len(questions)}_{i}">\n'
                html += f'                    <label for="q_{len(questions)}_{i}">{option}</label>\n'
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
    questions = parse_markdown_questionnaire("docs/BETA_TESTING_QUESTIONNAIRE.md")
    generate_html_form(questions, "beta_testing_questionnaire.html")
    print(f"Parsed {len(questions)} questions")
```

### **Script 2: Markdown to JSON (for API integration)**

```python
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
    questionnaire = parse_markdown_to_json("docs/BETA_TESTING_QUESTIONNAIRE.md")
    
    with open("beta_testing_questionnaire.json", 'w', encoding='utf-8') as f:
        json.dump(questionnaire, f, indent=2, ensure_ascii=False)
    
    print(f"JSON questionnaire generated: beta_testing_questionnaire.json")
    print(f"Total questions: {len(questionnaire['questions'])}")
    print(f"Total sections: {len(questionnaire['sections'])}")
```

### **Script 3: Markdown to CSV (for spreadsheet import)**

```python
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
    questions = parse_markdown_to_csv("docs/BETA_TESTING_QUESTIONNAIRE.md")
    
    with open("beta_testing_questionnaire.csv", 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['section', 'question', 'type', 'options', 'required'])
        writer.writeheader()
        writer.writerows(questions)
    
    print(f"CSV questionnaire generated: beta_testing_questionnaire.csv")
    print(f"Total questions: {len(questions)}")
```

---

## 🔧 **Step-by-Step Conversion Guides**

### **Microsoft Forms Conversion**

1. **Go to Microsoft Forms**: Visit [forms.microsoft.com](https://forms.microsoft.com)
2. **Create New Form**: Click "New Form"
3. **Add Questions**: For each question in the markdown:
   - Copy the question text
   - Paste into form
   - Set appropriate question type:
     - **Rating questions**: Use "Rating" question type
     - **Multiple choice**: Use "Choice" question type
     - **Text responses**: Use "Text" question type
     - **Checkboxes**: Use "Choice" with "Multiple answers" enabled

4. **Configure Settings**:
   - Set form title: "BioDYM Beta Testing Questionnaire"
   - Enable "Collect email addresses"
   - Set "One response per person" if desired

5. **Share Form**: Get shareable link or embed code

### **Google Forms Conversion**

1. **Go to Google Forms**: Visit [forms.google.com](https://forms.google.com)
2. **Create New Form**: Click "Blank" form
3. **Add Questions**: Similar to Microsoft Forms process
4. **Configure Settings**:
   - Set form title and description
   - Enable "Collect email addresses"
   - Set response collection preferences

5. **Share Form**: Get shareable link or embed code

### **SurveyMonkey Conversion**

1. **Go to SurveyMonkey**: Visit [surveymonkey.com](https://surveymonkey.com)
2. **Create New Survey**: Click "Create Survey"
3. **Import Questions**: Use the CSV format generated by the script
4. **Customize Design**: Apply branding and styling
5. **Configure Settings**: Set collection preferences and analytics

---

## 📊 **Data Collection Strategies**

### **Strategy 1: Direct Form Distribution**
- **Pros**: Easy setup, automatic data collection
- **Cons**: Limited customization, platform dependency
- **Best for**: Quick deployment, basic data collection

### **Strategy 2: Hybrid Approach**
- **Pros**: Combines ease of use with customization
- **Cons**: Requires multiple tools, more complex setup
- **Best for**: Professional surveys with custom branding

### **Strategy 3: Custom Solution**
- **Pros**: Complete control, integration with existing systems
- **Cons**: Requires development, maintenance overhead
- **Best for**: Long-term use, specific requirements

---

## 🚀 **Quick Start Recommendations**

### **For Immediate Use (Today)**
1. **Use Google Forms**: Free, easy, quick setup
2. **Manual copy-paste**: Copy questions from markdown
3. **Set up basic form**: Title, questions, sharing settings
4. **Test form**: Send to yourself first

### **For Professional Use (This Week)**
1. **Use SurveyMonkey**: Professional appearance, better analytics
2. **Use conversion scripts**: Automate question import
3. **Customize branding**: Add logo, colors, styling
4. **Set up analytics**: Track responses, completion rates

### **For Long-term Use (This Month)**
1. **Develop custom solution**: HTML form with database
2. **Integrate with existing systems**: CRM, project management
3. **Set up automated reporting**: Regular analysis and summaries
4. **Create feedback loop**: Continuous improvement process

---

## 📈 **Analytics and Reporting**

### **Built-in Analytics**
- **Response rates**: Track completion rates
- **Question analysis**: Identify problematic questions
- **User feedback**: Collect qualitative insights
- **Trend analysis**: Track changes over time

### **Custom Analytics**
- **Response patterns**: Identify common issues
- **User segmentation**: Analyze by user type
- **Feature prioritization**: Rank issues by importance
- **ROI measurement**: Track improvement impact

---

*This guide provides multiple options for converting your markdown questionnaire into various formats for easier distribution and data collection.*
