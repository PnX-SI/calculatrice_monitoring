import ast

from weasyprint.css import targets


def extract_variable_names(code: str) -> list[str]:
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return []

    names = []
    for node in ast.walk(tree):
        if type(node) is ast.Assign:
            try:
                try:
                    names.append(node.targets[0].id)
                except AttributeError:
                    names.extend(d.id for d in node.targets[0].dims)
            except Exception:
                pass
    return names
