"""Diff utilities for showing changes in a reviewable format."""

import difflib
from typing import List, Optional


def generate_diff(
    original: str, 
    modified: str, 
    filename: str = "file",
    context_lines: int = 3
) -> str:
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
    
    diff = difflib.unified_diff(
        original_lines,
        modified_lines,
        fromfile=f"{filename} (original)",
        tofile=f"{filename} (modified)",
        n=context_lines
    )
    
    return ''.join(diff)


def generate_inline_diff(
    original: str,
    modified: str,
    filename: str = "file",
    max_width: int = 80
) -> str:
    """Generate an inline diff with color formatting for terminal display.
    
    Args:
        original: Original content
        modified: Modified content
        filename: Name of the file
        max_width: Maximum width for side-by-side display
        
    Returns:
        Formatted inline diff with ANSI color codes
    """
    # ANSI color codes
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'
    
    original_lines = original.splitlines()
    modified_lines = modified.splitlines()
    
    # Use difflib to get detailed differences
    differ = difflib.Differ()
    diff = list(differ.compare(original_lines, modified_lines))
    
    output = []
    output.append(f"{BOLD}{BLUE}--- Diff for {filename} ---{RESET}")
    output.append("")
    
    line_num = 0
    for i, line in enumerate(diff):
        if line.startswith('  '):  # Unchanged line
            line_num += 1
            output.append(f"{YELLOW}{line_num:4d}{RESET} {line[2:]}")
        elif line.startswith('- '):  # Line removed
            line_num += 1
            output.append(f"{YELLOW}{line_num:4d}{RESET} {RED}- {line[2:]}{RESET}")
        elif line.startswith('+ '):  # Line added
            output.append(f"     {GREEN}+ {line[2:]}{RESET}")
        elif line.startswith('? '):  # Inline diff indicator
            # Skip these for cleaner output
            continue
    
    output.append("")
    output.append(f"{BOLD}{BLUE}--- End of diff ---{RESET}")
    
    return '\n'.join(output)


def summarize_changes(original: str, modified: str) -> str:
    """Generate a summary of changes made.
    
    Args:
        original: Original content
        modified: Modified content
        
    Returns:
        Summary string
    """
    original_lines = original.splitlines()
    modified_lines = modified.splitlines()
    
    # Calculate statistics
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
    
    return (f"Changes: {added} lines added, {removed} lines removed, "
            f"{unchanged} lines unchanged")