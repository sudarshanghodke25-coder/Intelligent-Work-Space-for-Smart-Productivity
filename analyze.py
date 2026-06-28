import os
import ast

def analyze_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        try:
            content = f.read()
            tree = ast.parse(content, filename=filepath)
        except Exception as e:
            return

    imports = []
    used_names = set()
    
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(alias.asname or alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.names:
                for alias in node.names:
                    imports.append(alias.asname or alias.name)
        elif isinstance(node, ast.Name):
            if isinstance(node.ctx, ast.Load):
                used_names.add(node.id)
                
    unused = []
    for imp in imports:
        # Very simple heuristic: if the name doesn't appear in Load context, might be unused.
        # But this is not 100% accurate because of dynamic imports or star imports.
        # So we'll just check if it's completely missing from file text (except import line).
        pass

# A better way is just to regex search for common redundant patterns or use pylint.
