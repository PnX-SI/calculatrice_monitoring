from ..utils import extract_variable_names


class TestExtractVariableNames:
    def test_it_with_one_variable(self):
        code = "foo=1"
        names = extract_variable_names(code)
        assert len(names) == 1
        name = names[0]
        assert name == "foo"

    def test_it_with_multiple_variables(self):
        code = """
foo=1
bar=2
"""
        names = extract_variable_names(code)
        assert len(names) == 2
        assert "foo" in names
        assert "bar" in names

    def test_it_with_no_variable(self):
        code = """
def foo():
    print("bar")
        """
        names = extract_variable_names(code)
        assert len(names) == 0

    def test_it_with_syntactically_incorrect_code(self):
        code = "foo bar"
        names = extract_variable_names(code)
        assert len(names) == 0
