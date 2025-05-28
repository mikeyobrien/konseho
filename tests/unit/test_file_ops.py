"""Tests for file operation tools."""

from konseho.tools.file_ops import file_append, file_read, file_write


class TestFileRead:
    """Test the file_read tool."""

    def test_read_simple_file(self, tmp_path):
        """Test reading a simple text file."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("Hello, World!")

        result = file_read(str(test_file))
        assert result == "Hello, World!"

    def test_read_with_encoding(self, tmp_path):
        """Test reading with specific encoding."""
        test_file = tmp_path / "test.txt"
        content = "Hello, 世界!"
        test_file.write_text(content, encoding="utf-8")

        result = file_read(str(test_file), encoding="utf-8")
        assert result == content

    def test_read_nonexistent_file(self):
        """Test reading a file that doesn't exist."""
        result = file_read("/nonexistent/file.txt")
        assert "Error:" in result
        assert "not found" in result.lower() or "no such file" in result.lower()

    def test_read_empty_file(self, tmp_path):
        """Test reading an empty file."""
        test_file = tmp_path / "empty.txt"
        test_file.touch()

        result = file_read(str(test_file))
        assert result == ""

    def test_read_large_file(self, tmp_path):
        """Test reading a larger file."""
        test_file = tmp_path / "large.txt"
        content = "Line {}\n" * 1000
        lines = [content.format(i) for i in range(1000)]
        test_file.write_text("".join(lines))

        result = file_read(str(test_file))
        assert len(result.splitlines()) == 1000
        assert result.startswith("Line 0\n")
        assert result.endswith("Line 999\n")

    def test_read_binary_file_protection(self, tmp_path):
        """Test that binary files are handled safely."""
        test_file = tmp_path / "binary.bin"
        test_file.write_bytes(b"\x00\x01\x02\x03\x04")

        result = file_read(str(test_file))
        assert "Error:" in result
        assert "binary" in result.lower() or "decode" in result.lower()


class TestFileWrite:
    """Test the file_write tool."""

    def test_write_simple_file(self, tmp_path):
        """Test writing a simple text file."""
        test_file = tmp_path / "output.txt"
        content = "Hello from write!"

        result = file_write(str(test_file), content)
        assert "Success" in result or "Written" in result
        assert test_file.read_text() == content

    def test_write_creates_directories(self, tmp_path):
        """Test that write creates parent directories."""
        test_file = tmp_path / "nested" / "deep" / "output.txt"
        content = "Nested content"

        result = file_write(str(test_file), content)
        assert "Success" in result or "Written" in result
        assert test_file.exists()
        assert test_file.read_text() == content

    def test_write_overwrites_existing(self, tmp_path):
        """Test that write overwrites existing files."""
        test_file = tmp_path / "existing.txt"
        test_file.write_text("Old content")

        new_content = "New content"
        result = file_write(str(test_file), new_content)
        assert "Success" in result or "Written" in result
        assert test_file.read_text() == new_content

    def test_write_with_encoding(self, tmp_path):
        """Test writing with specific encoding."""
        test_file = tmp_path / "unicode.txt"
        content = "Unicode: 你好世界 🌍"

        result = file_write(str(test_file), content, encoding="utf-8")
        assert "Success" in result or "Written" in result
        assert test_file.read_text(encoding="utf-8") == content

    def test_write_empty_content(self, tmp_path):
        """Test writing empty content."""
        test_file = tmp_path / "empty.txt"

        result = file_write(str(test_file), "")
        assert "Success" in result or "Written" in result
        assert test_file.exists()
        assert test_file.read_text() == ""

    def test_write_permission_error(self, tmp_path):
        """Test handling permission errors."""
        # Create a read-only directory
        read_only_dir = tmp_path / "readonly"
        read_only_dir.mkdir()
        read_only_dir.chmod(0o444)

        test_file = read_only_dir / "forbidden.txt"
        result = file_write(str(test_file), "content")

        assert "Error:" in result
        assert "permission" in result.lower() or "access" in result.lower()

        # Cleanup
        read_only_dir.chmod(0o755)


class TestFileAppend:
    """Test the file_append tool."""

    def test_append_to_existing(self, tmp_path):
        """Test appending to an existing file."""
        test_file = tmp_path / "append.txt"
        test_file.write_text("Line 1\n")

        result = file_append(str(test_file), "Line 2\n")
        assert "Success" in result or "Appended" in result
        assert test_file.read_text() == "Line 1\nLine 2\n"

    def test_append_to_nonexistent(self, tmp_path):
        """Test appending to a file that doesn't exist creates it."""
        test_file = tmp_path / "new.txt"

        result = file_append(str(test_file), "First line\n")
        assert "Success" in result or "Appended" in result or "Created" in result
        assert test_file.exists()
        assert test_file.read_text() == "First line\n"

    def test_append_multiple_times(self, tmp_path):
        """Test appending multiple times."""
        test_file = tmp_path / "multi.txt"
        test_file.write_text("Start\n")

        file_append(str(test_file), "Middle\n")
        file_append(str(test_file), "End\n")

        content = test_file.read_text()
        assert content == "Start\nMiddle\nEnd\n"

    def test_append_with_encoding(self, tmp_path):
        """Test appending with specific encoding."""
        test_file = tmp_path / "unicode_append.txt"
        test_file.write_text("Hello ", encoding="utf-8")

        result = file_append(str(test_file), "世界!", encoding="utf-8")
        assert "Success" in result or "Appended" in result
        assert test_file.read_text(encoding="utf-8") == "Hello 世界!"

    def test_append_empty_content(self, tmp_path):
        """Test appending empty content."""
        test_file = tmp_path / "base.txt"
        original = "Original content"
        test_file.write_text(original)

        result = file_append(str(test_file), "")
        assert "Success" in result or "Appended" in result
        assert test_file.read_text() == original  # No change

    def test_append_creates_parent_dirs(self, tmp_path):
        """Test that append creates parent directories if needed."""
        test_file = tmp_path / "deep" / "nested" / "file.txt"

        result = file_append(str(test_file), "Content in nested file\n")
        assert "Success" in result or "Appended" in result or "Created" in result
        assert test_file.exists()
        assert test_file.read_text() == "Content in nested file\n"
