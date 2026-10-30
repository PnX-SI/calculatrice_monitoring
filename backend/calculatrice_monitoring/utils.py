import ast


def extract_variable_names(code: str) -> list[str]:
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return []

    names = set()
    for node in ast.walk(tree):
        if type(node) is ast.Assign:
            try:
                try:
                    names.add(node.targets[0].id)
                except AttributeError:
                    for d in node.targets[0].dims:
                        names.add(d.id)
            except Exception:
                pass
    return sorted(list(names))
