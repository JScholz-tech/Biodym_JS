#!/usr/bin/env python3
"""
Master script to convert markdown questionnaire to multiple formats
"""

import os
import sys
import subprocess

def run_conversion_script(script_name, description):
    """Run a conversion script and handle errors"""
    print(f"\n{description}...")
    try:
        result = subprocess.run([sys.executable, script_name], 
                              capture_output=True, text=True, check=True)
        print(f"SUCCESS: {description} completed successfully")
        if result.stdout:
            print(f"   Output: {result.stdout.strip()}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"ERROR: {description} failed")
        print(f"   Error: {e.stderr}")
        return False
    except FileNotFoundError:
        print(f"ERROR: {description} failed - script not found: {script_name}")
        return False

def main():
    """Run all conversion scripts"""
    print("BioDYM Questionnaire Conversion Tool")
    print("=" * 50)
    
    # Check if markdown file exists
    md_file = "docs/BETA_TESTING_QUESTIONNAIRE.md"
    if not os.path.exists(md_file):
        print(f"ERROR: Markdown file not found: {md_file}")
        print("   Please ensure the questionnaire file exists in the docs/ directory")
        return
    
    # Change to scripts directory
    scripts_dir = "scripts"
    if not os.path.exists(scripts_dir):
        print(f"ERROR: Scripts directory not found: {scripts_dir}")
        return
    
    os.chdir(scripts_dir)
    
    # Run conversion scripts
    conversions = [
        ("convert_to_html.py", "Converting to HTML form"),
        ("convert_to_json.py", "Converting to JSON format"),
        ("convert_to_csv.py", "Converting to CSV format")
    ]
    
    successful_conversions = 0
    total_conversions = len(conversions)
    
    for script, description in conversions:
        if run_conversion_script(script, description):
            successful_conversions += 1
    
    # Summary
    print("\n" + "=" * 50)
    print(f"Conversion Summary: {successful_conversions}/{total_conversions} successful")
    
    if successful_conversions == total_conversions:
        print("SUCCESS: All conversions completed successfully!")
        print("\nGenerated files:")
        print("   - beta_testing_questionnaire.html (HTML form)")
        print("   - beta_testing_questionnaire.json (JSON format)")
        print("   - beta_testing_questionnaire.csv (CSV format)")
        
        print("\nNext steps:")
        print("   1. Review generated files")
        print("   2. Upload HTML form to web server")
        print("   3. Import CSV to Google Forms/Microsoft Forms")
        print("   4. Use JSON for API integration")
        
    else:
        print("WARNING: Some conversions failed. Check error messages above.")
    
    print("\nFor detailed instructions, see: docs/QUESTIONNAIRE_CONVERSION_GUIDE.md")

if __name__ == "__main__":
    main()
