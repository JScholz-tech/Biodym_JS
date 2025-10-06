#!/usr/bin/env python3
"""
Generate corrected Moodle XML for BioDYM Beta Testing Questionnaire
Manual approach with correct format
"""

def create_sample_xml():
    """Create a sample XML with correct format"""
    
    xml_content = '''<?xml version="1.0" encoding="UTF-8" ?>
<FEEDBACK VERSION="200701" COMMENT="XML-Importfile for mod/feedback">
     <ITEMS>
          <ITEM TYPE="multichoice" REQUIRED="0">
               <ITEMID>
                    <![CDATA[111325]]>
               </ITEMID>
               <ITEMTEXT>
                    <![CDATA[1. **How easy was the installation process?** (1-5 scale)]]>
               </ITEMTEXT>
               <ITEMLABEL>
                    <![CDATA[]]>
               </ITEMLABEL>
               <PRESENTATION>
                    <![CDATA[r>>>>>1 (Very difficult)
||2 (Difficult)
||3 (Neutral)
||4 (Easy)
||5 (Very easy)]]>
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
          </ITEM>
          <ITEM TYPE="multichoice" REQUIRED="0">
               <ITEMID>
                    <![CDATA[111326]]>
               </ITEMID>
               <ITEMTEXT>
                    <![CDATA[2. **Did you encounter any installation issues?**]]>
               </ITEMTEXT>
               <ITEMLABEL>
                    <![CDATA[]]>
               </ITEMLABEL>
               <PRESENTATION>
                    <![CDATA[r>>>>>No issues
||Minor issues (resolved quickly)
||Major issues (took significant time to resolve)
||Could not complete installation]]>
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
          </ITEM>
          <ITEM TYPE="multichoice" REQUIRED="0">
               <ITEMID>
                    <![CDATA[111327]]>
               </ITEMID>
               <ITEMTEXT>
                    <![CDATA[4. **Rate the clarity of installation instructions** (1-5 scale)]]>
               </ITEMTEXT>
               <ITEMLABEL>
                    <![CDATA[]]>
               </ITEMLABEL>
               <PRESENTATION>
                    <![CDATA[r>>>>>1 (Very unclear)
||2 (Unclear)
||3 (Neutral)
||4 (Clear)
||5 (Very clear)]]>
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
          </ITEM>
          <ITEM TYPE="multichoice" REQUIRED="0">
               <ITEMID>
                    <![CDATA[111328]]>
               </ITEMID>
               <ITEMTEXT>
                    <![CDATA[5. **How easy was it to run your first analysis?** (1-5 scale)]]>
               </ITEMTEXT>
               <ITEMLABEL>
                    <![CDATA[]]>
               </ITEMLABEL>
               <PRESENTATION>
                    <![CDATA[r>>>>>1 (Very difficult)
||2 (Difficult)
||3 (Neutral)
||4 (Easy)
||5 (Very easy)]]>
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
          </ITEM>
          <ITEM TYPE="multichoice" REQUIRED="0">
               <ITEMID>
                    <![CDATA[111329]]>
               </ITEMID>
               <ITEMTEXT>
                    <![CDATA[7. **Did you successfully complete a baseline analysis?**]]>
               </ITEMTEXT>
               <ITEMLABEL>
                    <![CDATA[]]>
               </ITEMLABEL>
               <PRESENTATION>
                    <![CDATA[r>>>>>Yes, without issues
||Yes, with minor issues
||Yes, with major issues
||No, could not complete]]>
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
          </ITEM>
          <ITEM TYPE="multichoice" REQUIRED="0">
               <ITEMID>
                    <![CDATA[111330]]>
               </ITEMID>
               <ITEMTEXT>
                    <![CDATA[29. **Rate the quality of Sankey diagrams** (1-5 scale)]]>
               </ITEMTEXT>
               <ITEMLABEL>
                    <![CDATA[]]>
               </ITEMLABEL>
               <PRESENTATION>
                    <![CDATA[r>>>>>1 (Very poor)
||2 (Poor)
||3 (Neutral)
||4 (Good)
||5 (Excellent)]]>
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
          </ITEM>
     </ITEMS>
</FEEDBACK>'''
    
    return xml_content

def main():
    xml_content = create_sample_xml()
    
    with open('beta_testing_sample_corrected.xml', 'w', encoding='utf-8') as f:
        f.write(xml_content)
    
    print("Generated sample corrected Moodle XML file: beta_testing_sample_corrected.xml")
    print("This file contains 6 sample questions with the correct format")

if __name__ == "__main__":
    main()
