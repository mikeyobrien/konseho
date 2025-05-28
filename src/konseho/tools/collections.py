"""Core tool collections for Konseho agents."""
from __future__ import annotations

import glob
import os
import re
from typing import Any


def search_files(pattern: str, directory: str='.') ->list[str]:
    """Search for files matching a glob pattern.

    Args:
        pattern: Glob pattern (e.g., "**/*.py")
        directory: Directory to search in

    Returns:
        List of matching file paths
    """
    if not os.path.exists(directory):
        return []
    full_pattern = os.path.join(directory, pattern)
    matches = glob.glob(full_pattern, recursive=True)
    return sorted(matches)


def search_content(regex: str, file_path: str) ->list[dict[str, Any]]:
    """Search file content with regex.

    Args:
        regex: Regular expression pattern
        file_path: Path to file to search

    Returns:
        List of matches with line numbers and content
    """
    matches = []
    try:
        with open(file_path, encoding='utf-8') as f:
            for i, line in enumerate(f, 1):
                if re.search(regex, line):
                    matches.append({'line': i, 'content': line.strip(),
                        'file': file_path})
    except Exception as e:
        return [{'error': str(e)}]
    return matches


def code_metrics(file_path: str) ->dict[str, Any]:
    """Calculate basic code metrics for a file.

    Args:
        file_path: Path to code file

    Returns:
        Dictionary with metrics (lines, functions, classes, etc.)
    """
    metrics = {'total_lines': 0, 'code_lines': 0, 'comment_lines': 0,
        'blank_lines': 0, 'functions': 0, 'classes': 0}
    try:
        with open(file_path, encoding='utf-8') as f:
            for line in f:
                metrics['total_lines'] += 1
                stripped = line.strip()
                if not stripped:
                    metrics['blank_lines'] += 1
                elif stripped.startswith('#'):
                    metrics['comment_lines'] += 1
                else:
                    metrics['code_lines'] += 1
                    if stripped.startswith('def '):
                        metrics['functions'] += 1
                    elif stripped.startswith('class '):
                        metrics['classes'] += 1
    except Exception as e:
        metrics['error'] = str(e)
    return metrics
