"""Tests for code manipulation tools."""

from konseho.tools.code_ops import code_edit, code_insert


class TestCodeEdit:
    """Test the code_edit tool."""

    def test_edit_simple_replacement(self, tmp_path):
        """Test simple string replacement."""
        test_file = tmp_path / "test.py"
        test_file.write_text(
            """def hello():
    print("Hello, World!")
    return True"""
        )

        result = code_edit(
            str(test_file), 'print("Hello, World!")', 'print("Hello, Universe!")'
        )

        assert "Success" in result
        content = test_file.read_text()
        assert 'print("Hello, Universe!")' in content
        assert 'print("Hello, World!")' not in content

    def test_edit_specific_occurrence(self, tmp_path):
        """Test replacing specific occurrence."""
        test_file = tmp_path / "test.py"
        test_file.write_text(
            """def process():
    value = 10
    value = value + 5
    value = value * 2
    return value"""
        )

        # Replace second occurrence of "value"
        result = code_edit(str(test_file), "value", "result", occurrence=2)

        assert "Success" in result
        content = test_file.read_text()
        lines = content.splitlines()
        assert "value = 10" in lines[1]  # First occurrence unchanged
        assert "result = value + 5" in lines[2]  # Second occurrence changed

    def test_edit_preserves_indentation(self, tmp_path):
        """Test that indentation is preserved."""
        test_file = tmp_path / "test.py"
        test_file.write_text(
            """class MyClass:
    def method(self):
        if True:
            do_something()
            do_another_thing()"""
        )

        result = code_edit(str(test_file), "do_something()", "do_something_else()")

        assert "Success" in result
        content = test_file.read_text()
        assert "            do_something_else()" in content
        # Check indentation is preserved
        lines = content.splitlines()
        for line in lines:
            if "do_something_else()" in line:
                assert line.startswith("            ")  # 12 spaces

    def test_edit_multiline_search(self, tmp_path):
        """Test searching and replacing multiline content."""
        test_file = tmp_path / "test.py"
        test_file.write_text(
            """def old_function():
    # This is old
    pass

def new_function():
    pass"""
        )

        result = code_edit(
            str(test_file),
            """def old_function():
    # This is old
    pass""",
            """def updated_function():
    # This is updated
    return True""",
        )

        assert "Success" in result
        content = test_file.read_text()
        assert "def updated_function():" in content
        assert "# This is updated" in content
        assert "def old_function():" not in content

    def test_edit_not_found(self, tmp_path):
        """Test when search string is not found."""
        test_file = tmp_path / "test.py"
        test_file.write_text("print('hello')")

        result = code_edit(str(test_file), "nonexistent", "replacement")

        assert "Error:" in result
        assert "not found" in result.lower() or "no match" in result.lower()

    def test_edit_file_not_found(self):
        """Test editing non-existent file."""
        result = code_edit("/nonexistent/file.py", "search", "replace")

        assert "Error:" in result
        assert "not found" in result.lower()

    def test_edit_occurrence_out_of_range(self, tmp_path):
        """Test when occurrence number is too high."""
        test_file = tmp_path / "test.py"
        test_file.write_text("x = 1\ny = 2")

        result = code_edit(
            str(test_file), "=", "+=", occurrence=5  # Only 2 occurrences exist
        )

        assert "Error:" in result
        assert "occurrence" in result.lower() or "found only" in result.lower()


class TestCodeInsert:
    """Test the code_insert tool."""

    def test_insert_after_line(self, tmp_path):
        """Test inserting content after a line."""
        test_file = tmp_path / "test.py"
        test_file.write_text(
            """line 1
line 2
line 3"""
        )

        result = code_insert(
            str(test_file), line=2, content="inserted line", position="after"
        )

        assert "Success" in result
        content = test_file.read_text()
        lines = content.splitlines()
        assert lines == ["line 1", "line 2", "inserted line", "line 3"]

    def test_insert_before_line(self, tmp_path):
        """Test inserting content before a line."""
        test_file = tmp_path / "test.py"
        test_file.write_text(
            """line 1
line 2
line 3"""
        )

        result = code_insert(
            str(test_file), line=2, content="inserted line", position="before"
        )

        assert "Success" in result
        content = test_file.read_text()
        lines = content.splitlines()
        assert lines == ["line 1", "inserted line", "line 2", "line 3"]

    def test_insert_preserves_indentation(self, tmp_path):
        """Test that insert matches surrounding indentation."""
        test_file = tmp_path / "test.py"
        test_file.write_text(
            """def function():
    line 1
    line 2
    line 3"""
        )

        result = code_insert(
            str(test_file), line=3, content="new_statement()", position="after"
        )

        assert "Success" in result
        content = test_file.read_text()
        lines = content.splitlines()
        assert lines[3] == "    new_statement()"  # Should have 4 spaces

    def test_insert_at_beginning(self, tmp_path):
        """Test inserting at the beginning of file."""
        test_file = tmp_path / "test.py"
        test_file.write_text("original content")

        result = code_insert(
            str(test_file), line=1, content="# Header comment", position="before"
        )

        assert "Success" in result
        content = test_file.read_text()
        lines = content.splitlines()
        assert lines[0] == "# Header comment"
        assert lines[1] == "original content"

    def test_insert_at_end(self, tmp_path):
        """Test inserting at the end of file."""
        test_file = tmp_path / "test.py"
        test_file.write_text("line 1\nline 2")

        result = code_insert(str(test_file), line=2, content="line 3", position="after")

        assert "Success" in result
        content = test_file.read_text()
        lines = content.splitlines()
        assert lines == ["line 1", "line 2", "line 3"]

    def test_insert_multiline_content(self, tmp_path):
        """Test inserting multiple lines."""
        test_file = tmp_path / "test.py"
        test_file.write_text(
            """def function():
    pass"""
        )

        result = code_insert(
            str(test_file),
            line=1,
            content="""    x = 1
    y = 2
    return x + y""",
            position="after",
        )

        assert "Success" in result
        content = test_file.read_text()
        assert "x = 1" in content
        assert "y = 2" in content
        assert "return x + y" in content

    def test_insert_line_out_of_range(self, tmp_path):
        """Test when line number is out of range."""
        test_file = tmp_path / "test.py"
        test_file.write_text("line 1\nline 2")

        result = code_insert(
            str(test_file), line=10, content="new line", position="after"
        )

        assert "Error:" in result
        assert "line" in result.lower() and (
            "range" in result.lower() or "bounds" in result.lower()
        )

    def test_insert_empty_file(self, tmp_path):
        """Test inserting into empty file."""
        test_file = tmp_path / "empty.py"
        test_file.write_text("")

        result = code_insert(
            str(test_file), line=1, content="first line", position="before"
        )

        assert "Success" in result
        content = test_file.read_text()
        assert content.strip() == "first line"

    def test_insert_file_not_found(self):
        """Test inserting into non-existent file."""
        result = code_insert(
            "/nonexistent/file.py", line=1, content="text", position="after"
        )

        assert "Error:" in result
        assert "not found" in result.lower()
