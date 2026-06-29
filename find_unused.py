import os
import ast

def get_unused_imports(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        tree = ast.parse(content)
    except Exception:
        return []

    imports = []
    used_names = set()
    
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append((alias.asname or alias.name.split('.')[0], node.lineno))
        elif isinstance(node, ast.ImportFrom):
            if node.names:
                for alias in node.names:
                    if alias.name != '*':
                        imports.append((alias.asname or alias.name, node.lineno))
        elif isinstance(node, ast.Name):
            if isinstance(node.ctx, ast.Load):
                used_names.add(node.id)
                
    unused = []
    for imp_name, lineno in imports:
        if imp_name not in used_names:
            # Check if it's in type hints
            if f"{imp_name}" not in content: # Very basic sanity check
                continue
            unused.append(f"{imp_name} (line {lineno})")
            
    # Also check if it's used in type hints which might not be caught by ast.Name(Load) if stringified
    real_unused = []
    for u in unused:
        name = u.split()[0]
        # count occurrences in content (whole word)
        import re
        count = len(re.findall(r'\b' + re.escape(name) + r'\b', content))
        if count == 1: # Only the import itself
            real_unused.append(u)

    return real_unused

total = 0
for root, dirs, files in os.walk('d:/FLOWSPACE'):
    if '__pycache__' in root or '.venv' in root or '.git' in root:
        continue
    for f in files:
        if f.endswith('.py'):
            path = os.path.join(root, f)
            unused = get_unused_imports(path)
            if unused:
                print(f"{path}: Unused {unused}")
                total += len(unused)
print(f"Total unused imports found: {total}")
