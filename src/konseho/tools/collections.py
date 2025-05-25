"""Core tool collections for Konseho agents."""

from typing import List, Dict, Any
import glob
import re
import os


def search_files(pattern: str, directory: str = ".") -> List[str]:
    """Search for files matching a glob pattern.
    
    Args:
        pattern: Glob pattern (e.g., "**/*.py")
        directory: Directory to search in
        
    Returns:
        List of matching file paths
    """
    # Ensure directory exists
    if not os.path.exists(directory):
        return []
    
    # Join pattern with directory
    full_pattern = os.path.join(directory, pattern)
    
    # Use glob to find matches
    matches = glob.glob(full_pattern, recursive=True)
    
    # Return sorted list
    return sorted(matches)


def search_content(regex: str, file_path: str) -> List[Dict[str, Any]]:
    """Search file content with regex.
    
    Args:
        regex: Regular expression pattern
        file_path: Path to file to search
        
    Returns:
        List of matches with line numbers and content
    """
    matches = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for i, line in enumerate(f, 1):
                if re.search(regex, line):
                    matches.append({
                        "line": i,
                        "content": line.strip(),
                        "file": file_path
                    })
    except Exception as e:
        return [{"error": str(e)}]
    
    return matches


def code_metrics(file_path: str) -> Dict[str, Any]:
    """Calculate basic code metrics for a file.
    
    Args:
        file_path: Path to code file
        
    Returns:
        Dictionary with metrics (lines, functions, classes, etc.)
    """
    metrics = {
        "total_lines": 0,
        "code_lines": 0,
        "comment_lines": 0,
        "blank_lines": 0,
        "functions": 0,
        "classes": 0
    }
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                metrics["total_lines"] += 1
                stripped = line.strip()
                
                if not stripped:
                    metrics["blank_lines"] += 1
                elif stripped.startswith('#'):
                    metrics["comment_lines"] += 1
                else:
                    metrics["code_lines"] += 1
                    
                    # Count function and class definitions
                    if stripped.startswith('def '):
                        metrics["functions"] += 1
                    elif stripped.startswith('class '):
                        metrics["classes"] += 1
                        
    except Exception as e:
        metrics["error"] = str(e)
    
    return metrics