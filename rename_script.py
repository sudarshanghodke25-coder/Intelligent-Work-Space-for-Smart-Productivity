import os
import re

def replace_in_file(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"Skipping {filepath}: {e}")
        return

    # Replace FLOWSPACE -> Flowspace
    # Replace flowspace -> flowspace
    # Replace FLOWSPACE -> FLOWSPACE
    
    # Let's just do exact case replacement first
    new_content = re.sub(r'\bAurex\b', 'FLOWSPACE', content)
    new_content = re.sub(r'\baurex\b', 'flowspace', new_content)
    new_content = re.sub(r'\bAUREX\b', 'FLOWSPACE', new_content)
    
    if new_content != content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"Updated {filepath}")

def process_directory(directory):
    for root, dirs, files in os.walk(directory):
        # skip .git, .env, __pycache__, etc.
        if '.git' in root or '__pycache__' in root:
            continue
        for file in files:
            if file.endswith('.py') or file.endswith('.md') or file.endswith('.json'):
                filepath = os.path.join(root, file)
                replace_in_file(filepath)

if __name__ == '__main__':
    process_directory(r'd:\FLOWSPACE')
