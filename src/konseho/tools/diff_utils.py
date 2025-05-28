"""Diff utilities for showing changes in a reviewable format."""
from __future__ import annotations

import difflib


def generate_diff(original: str, modified: str, filename: str='file',
    context_lines: int=3) ->str:
    """Generate a unified diff between original and modified content.

    Args:
        original: Original file content
        modified: Modified file content
        filename: Name of the file for diff header
        context_lines: Number of context lines to show

    Returns:
        Formatted diff string
    """
    original_lines = original.splitlines(keepends=True)
    modified_lines = modified.splitlines(keepends=True)
    diff = difflib.unified_diff(original_lines, modified_lines, fromfile=
        f'{filename} (original)', tofile=f'{filename} (modified)', n=
        context_lines)
    return ''.join(diff)


def generate_inline_diff(original: str, modified: str, filename: str='file',
    max_width: int=80) ->str:
    """Generate an inline diff with color formatting for terminal display.

    Args:
        original: Original content
        modified: Modified content
        filename: Name of the file
        max_width: Maximum width for side-by-side display

    Returns:
        Formatted inline diff with ANSI color codes
    """
    RED = '\x1b[91m'
    GREEN = '\x1b[92m'
    YELLOW = '\x1b[93m'
    BLUE = '\x1b[94m'
    RESET = '\x1b[0m'
    BOLD = '\x1b[1m'
    original_lines = original.splitlines()
    modified_lines = modified.splitlines()
    differ = difflib.Differ()
    diff = list(differ.compare(original_lines, modified_lines))
    output = []
    output.append(f'{BOLD}{BLUE}--- Diff for {filename} ---{RESET}')
    output.append('')
    line_num = 0
    for i, line in enumerate(diff):
        if line.startswith('  '):
            line_num += 1
            output.append(f'{YELLOW}{line_num:4d}{RESET} {line[2:]}')
        elif line.startswith('- '):
            line_num += 1
            output.append(
                f'{YELLOW}{line_num:4d}{RESET} {RED}- {line[2:]}{RESET}')
        elif line.startswith('+ '):
            output.append(f'     {GREEN}+ {line[2:]}{RESET}')
        elif line.startswith('? '):
            continue
    output.append('')
    output.append(f'{BOLD}{BLUE}--- End of diff ---{RESET}')
    return '\n'.join(output)


def summarize_changes(original: str, modified: str) ->str:
    """Generate a summary of changes made.

    Args:
        original: Original content
        modified: Modified content

    Returns:
        Summary string
    """
    original_lines = original.splitlines()
    modified_lines = modified.splitlines()
    matcher = difflib.SequenceMatcher(None, original_lines, modified_lines)
    added = 0
    removed = 0
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == 'delete':
            removed += i2 - i1
        elif tag == 'insert':
            added += j2 - j1
        elif tag == 'replace':
            removed += i2 - i1
            added += j2 - j1
    unchanged = len(original_lines) - removed
    return (
        f'Changes: {added} lines added, {removed} lines removed, {unchanged} lines unchanged'
        )
