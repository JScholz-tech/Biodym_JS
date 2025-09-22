import re

def generate_toc_from_py_notebook(file_path):
    """Parses a Jupytext .py light script and prints a markdown Table of Contents."""
    print("### Current Table of Contents\n")
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                # Check for lines that are jupytext markdown headings
                if line.startswith('# #'):
                    content = line[2:].strip()
                    # Match for markdown headings inside the comment
                    match = re.match(r'^(#+)\s*(.*)', content)
                    if match:
                        level = len(match.group(1))
                        title = match.group(2).strip()
                        if title:
                            indent = '  ' * (level - 1)
                            print(f"{indent}- **{title}**")
    except FileNotFoundError:
        print(f"Error: File not found at {file_path}")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    notebook_path = "biodym_mfa_tool/BioDYM_Scientific_Notebook.py"
    generate_toc_from_py_notebook(notebook_path)