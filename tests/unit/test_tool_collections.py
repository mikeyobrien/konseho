"""Tests for tool collections."""


from konseho.tools.collections import code_metrics, search_content, search_files


class TestSearchFiles:
    """Test the search_files tool."""
    
    def test_search_files_returns_list(self, tmp_path):
        """Test that search_files returns a list."""
        # Create test files
        (tmp_path / "test1.py").write_text("print('hello')")
        (tmp_path / "test2.py").write_text("print('world')")
        (tmp_path / "test.txt").write_text("not python")
        
        results = search_files("*.py", str(tmp_path))
        
        assert isinstance(results, list)
        assert len(results) == 2
        assert all(r.endswith(".py") for r in results)
    
    def test_search_files_recursive(self, tmp_path):
        """Test recursive file search."""
        # Create nested structure
        subdir = tmp_path / "subdir"
        subdir.mkdir()
        (tmp_path / "top.py").write_text("top")
        (subdir / "nested.py").write_text("nested")
        
        results = search_files("**/*.py", str(tmp_path))
        
        assert len(results) == 2
        assert any("top.py" in r for r in results)
        assert any("nested.py" in r for r in results)
    
    def test_search_files_sorted(self, tmp_path):
        """Test that results are sorted."""
        # Create files
        (tmp_path / "b.py").write_text("b")
        (tmp_path / "a.py").write_text("a")
        (tmp_path / "c.py").write_text("c")
        
        results = search_files("*.py", str(tmp_path))
        
        assert results == sorted(results)
    
    def test_search_files_no_matches(self, tmp_path):
        """Test when no files match."""
        results = search_files("*.xyz", str(tmp_path))
        assert results == []


class TestSearchContent:
    """Test the search_content tool."""
    
    def test_search_content_basic(self, tmp_path):
        """Test basic content search."""
        test_file = tmp_path / "test.py"
        test_file.write_text("""def hello():
    print("hello world")
    return True
""")
        
        results = search_content("hello", str(test_file))
        
        assert isinstance(results, list)
        assert len(results) == 2  # Found in function name and string
        assert all(isinstance(r, dict) for r in results)
        assert all("line" in r and "content" in r and "file" in r for r in results)
    
    def test_search_content_regex(self, tmp_path):
        """Test regex pattern search."""
        test_file = tmp_path / "test.py"
        test_file.write_text("""import os
import sys
from typing import List

def process_data(data: List[str]) -> bool:
    return True
""")
        
        # Search for import statements
        results = search_content(r"^import\s+\w+", str(test_file))
        
        assert len(results) == 2
        assert results[0]["line"] == 1
        assert results[1]["line"] == 2
    
    def test_search_content_line_numbers(self, tmp_path):
        """Test that line numbers are correct."""
        test_file = tmp_path / "test.py"
        test_file.write_text("""line 1
line 2
target line
line 4
""")
        
        results = search_content("target", str(test_file))
        
        assert len(results) == 1
        assert results[0]["line"] == 3
        assert "target" in results[0]["content"]
    
    def test_search_content_file_not_found(self):
        """Test handling of non-existent file."""
        results = search_content("test", "/nonexistent/file.txt")
        
        assert len(results) == 1
        assert "error" in results[0]


class TestCodeMetrics:
    """Test the code_metrics tool."""
    
    def test_code_metrics_basic(self, tmp_path):
        """Test basic code metrics."""
        test_file = tmp_path / "test.py"
        test_file.write_text("""# This is a comment
def hello():
    \"\"\"Docstring\"\"\"
    print("hello")

class MyClass:
    def method(self):
        pass

# Another comment
""")
        
        metrics = code_metrics(str(test_file))
        
        assert isinstance(metrics, dict)
        assert metrics["total_lines"] == 11  # Including final newline
        assert metrics["functions"] == 2  # hello and method
        assert metrics["classes"] == 1
        assert metrics["comment_lines"] == 2
        assert metrics["blank_lines"] >= 1
    
    def test_code_metrics_empty_file(self, tmp_path):
        """Test metrics for empty file."""
        test_file = tmp_path / "empty.py"
        test_file.write_text("")
        
        metrics = code_metrics(str(test_file))
        
        assert metrics["total_lines"] == 0
        assert metrics["code_lines"] == 0
        assert metrics["functions"] == 0
        assert metrics["classes"] == 0
    
    def test_code_metrics_code_only(self, tmp_path):
        """Test file with only code."""
        test_file = tmp_path / "code.py"
        test_file.write_text("""import os
x = 1
y = 2
print(x + y)""")
        
        metrics = code_metrics(str(test_file))
        
        assert metrics["total_lines"] == 4
        assert metrics["code_lines"] == 4
        assert metrics["comment_lines"] == 0
        assert metrics["blank_lines"] == 0
    
    def test_code_metrics_file_not_found(self):
        """Test handling of non-existent file."""
        metrics = code_metrics("/nonexistent/file.py")
        
        assert "error" in metrics
        assert isinstance(metrics["error"], str)