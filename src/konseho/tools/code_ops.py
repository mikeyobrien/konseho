"""Code manipulation tools for agents."""
from __future__ import annotations

import os
from konseho.tools.diff_utils import generate_inline_diff, summarize_changes


def code_edit(path: str, search: str, replace: str, occurrence: int=1,
    show_diff: bool=True) ->str:
    """Smart code editing with pattern matching.

    Args:
        path: Path to the file to edit
        search: String to search for
        replace: String to replace with
        occurrence: Which occurrence to replace (1-based, default: 1)
        show_diff: Whether to show a diff of changes (default: True)

    Returns:
        Success message with optional diff, or error message if failed
    """
    try:
        if not os.path.exists(path):
            return f'Error: File not found: {path}'
        with open(path, encoding='utf-8') as f:
            original_content = f.read()
        count = original_content.count(search)
        if count == 0:
            return 'Error: Search string not found in file'
        if occurrence > count:
            return (
                f'Error: Only found {count} occurrences, but occurrence {occurrence} was requested'
                )
        parts = original_content.split(search, occurrence)
        if len(parts) <= occurrence:
            return 'Error: Could not split content properly'
        new_content = search.join(parts[:occurrence]) + replace + parts[
            occurrence]
        with open(path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        result = (
            f'Success: Replaced occurrence {occurrence} of search string in {path}'
            )
        if show_diff:
            diff = generate_inline_diff(original_content, new_content, path)
            summary = summarize_changes(original_content, new_content)
            result += f'\n\n{summary}\n\n{diff}'
        return result
    except Exception as e:
        return f'Error: Failed to edit file: {str(e)}'


def code_insert(path: str, line: int, content: str, position: str='after',
    show_diff: bool=True) ->str:
    """Insert code at specific line number with smart indentation.

    Args:
        path: Path to the file to edit
        line: Line number to insert at (1-based)
        content: Content to insert
        position: Where to insert relative to line ("before" or "after")
        show_diff: Whether to show a diff of changes (default: True)

    Returns:
        Success message with optional diff, or error message if failed
    """
    try:
        if not os.path.exists(path):
            return f'Error: File not found: {path}'
        with open(path, encoding='utf-8') as f:
            original_content = f.read()
            lines = original_content.splitlines(keepends=True)
        if not lines and line == 1:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(content + '\n')
            result = 'Success: Inserted content into empty file'
            if show_diff:
                diff = generate_inline_diff('', content + '\n', path)
                result += f'\n\n{diff}'
            return result
        if line < 1 or lines and line > len(lines):
            return (
                f'Error: Line {line} is out of bounds (file has {len(lines)} lines)'
                )
        indent = ''
        if lines:
            ref_line_idx = line - 1 if position == 'after' else max(0, line - 2
                )
            if ref_line_idx < len(lines):
                ref_line = lines[ref_line_idx]
                indent = ref_line[:len(ref_line) - len(ref_line.lstrip())]
        if content_lines := content.splitlines():
            if content_lines[0] and not content_lines[0][0].isspace():
                indented_content = []
                for content_line in content_lines:
                    if content_line:
                        indented_content.append(indent + content_line)
                    else:
                        indented_content.append(content_line)
            else:
                indented_content = content_lines
        else:
            indented_content = [indent + content]
        content_to_insert = '\n'.join(indented_content) + '\n'
        if position == 'before':
            if line == 1:
                lines.insert(0, content_to_insert)
            else:
                lines.insert(line - 1, content_to_insert)
        elif line <= len(lines):
            lines.insert(line, content_to_insert)
        else:
            lines.append(content_to_insert)
        new_content = ''.join(lines)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        result = (
            f'Success: Inserted {len(content_lines)} line(s) {position} line {line}'
            )
        if show_diff:
            diff = generate_inline_diff(original_content, new_content, path)
            summary = summarize_changes(original_content, new_content)
            result += f'\n\n{summary}\n\n{diff}'
        return result
    except Exception as e:
        return f'Error: Failed to insert code: {str(e)}'
