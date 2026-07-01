import ast


def extract_variable_names(code: str) -> list[str]:
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return []

    names = []
    for node in ast.walk(tree):
        if type(node) is ast.Assign:
            names.append(node.targets[0].id)
    return names
