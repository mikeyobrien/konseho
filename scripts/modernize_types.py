#!/usr/bin/env python3
"""Automated type modernization script for Python 3.12+ codebases."""

from __future__ import annotations

import ast
import re
from pathlib import Path
from typing import Any, TypeAlias

import click


class TypeModernizer(ast.NodeTransformer):
    """AST transformer to modernize type annotations."""
    
    def __init__(self) -> None:
        self.imports_to_remove: set[str] = set()
        self.imports_to_add: set[str] = set()
    
    def visit_Subscript(self, node: ast.Subscript) -> ast.AST:
        """Convert Optional[X] to X | None."""
        self.generic_visit(node)
        
        if isinstance(node.value, ast.Name):
            if node.value.id == 'Optional':
                self.imports_to_remove.add('Optional')
                return ast.BinOp(
                    left=node.slice,
                    op=ast.BitOr(),
                    right=ast.Constant(value=None)
                )
            elif node.value.id in {'List', 'Dict', 'Set', 'Tuple'}:
                self.imports_to_remove.add(node.value.id)
                # Convert List[X] to list[X]
                new_name = node.value.id.lower()
                node.value.id = new_name
        
        return node
    
    def visit_Name(self, node: ast.Name) -> ast.AST:
        """Convert Union[X, Y] to X | Y."""
        if node.id == 'Union' and isinstance(node.ctx, ast.Load):
            self.imports_to_remove.add('Union')
        return node
    
    def visit_ImportFrom(self, node: ast.ImportFrom) -> ast.AST | None:
        """Remove deprecated typing imports."""
        if node.module == 'typing':
            new_names = []
            for alias in node.names:
                if alias.name not in {'List', 'Dict', 'Set', 'Tuple', 'Optional', 'Union'}:
                    new_names.append(alias)
            
            if new_names:
                node.names = new_names
                return node
            else:
                return None
        
        return node


class SyntaxModernizer:
    """Modernize Python syntax patterns."""
    
    @staticmethod
    def add_slots_to_classes(content: str) -> str:
        """Add __slots__ to classes for memory efficiency."""
        # Pattern to find class definitions without __slots__
        class_pattern = re.compile(
            r'^class\s+(\w+)(?:\([^)]*\))?\s*:\s*\n(?!.*__slots__)',
            re.MULTILINE
        )
        
        def replacement(match: re.Match[str]) -> str:
            class_name = match.group(1)
            # Don't add slots to certain class types
            if any(skip in match.group(0) for skip in ['Protocol', 'TypedDict', 'ABC']):
                return match.group(0)
            
            indent = '    '
            return match.group(0) + f'{indent}__slots__ = ()\n'
        
        return class_pattern.sub(replacement, content)
    
    @staticmethod
    def use_walrus_operator(content: str) -> str:
        """Convert simple assignments to walrus operator where appropriate."""
        # Pattern: result = func()\nif result:
        pattern = re.compile(
            r'(\s*)(\w+)\s*=\s*([^\n]+)\n\1if\s+\2\s*:',
            re.MULTILINE
        )
        
        def replacement(match: re.Match[str]) -> str:
            indent, var_name, expression = match.groups()
            return f'{indent}if {var_name} := {expression}:'
        
        return pattern.sub(replacement, content)
    
    @staticmethod
    def modernize_string_formatting(content: str) -> str:
        """Convert % and .format() to f-strings."""
        # Pattern for .format()
        format_pattern = re.compile(
            r'"([^"]*?)"\s*\.format\s*\(([^)]+)\)'
        )
        
        def format_replacement(match: re.Match[str]) -> str:
            template, args = match.groups()
            # Simple conversion for basic cases
            if '{0}' in template or '{1}' in template:
                args_list = [arg.strip() for arg in args.split(',')]
                for i, arg in enumerate(args_list):
                    template = template.replace(f'{{{i}}}', f'{{{arg}}}')
            elif '{}' in template:
                args_list = [arg.strip() for arg in args.split(',')]
                for arg in args_list:
                    template = template.replace('{}', f'{{{arg}}}', 1)
            
            return f'f"{template}"'
        
        content = format_pattern.sub(format_replacement, content)
        
        # Pattern for % formatting
        percent_pattern = re.compile(
            r'"([^"]*?%s[^"]*?)"\s*%\s*\(([^)]+)\)'
        )
        
        def percent_replacement(match: re.Match[str]) -> str:
            template, var = match.groups()
            template = template.replace('%s', f'{{{var.strip()}}}')
            return f'f"{template}"'
        
        return percent_pattern.sub(percent_replacement, content)


def analyze_file(filepath: Path) -> dict[str, Any]:
    """Analyze a Python file for modernization opportunities."""
    content = filepath.read_text()
    tree = ast.parse(content)
    
    analysis = {
        'filepath': filepath,
        'has_future_annotations': False,
        'uses_old_typing': False,
        'uses_any': 0,
        'missing_return_types': 0,
        'uses_old_union': False,
        'uses_optional': False,
    }
    
    # Check for future annotations
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            if node.module == '__future__' and any(
                alias.name == 'annotations' for alias in node.names
            ):
                analysis['has_future_annotations'] = True
            
            if node.module == 'typing':
                for alias in node.names:
                    if alias.name in {'List', 'Dict', 'Set', 'Optional', 'Union'}:
                        analysis['uses_old_typing'] = True
                    if alias.name == 'Optional':
                        analysis['uses_optional'] = True
                    if alias.name == 'Union':
                        analysis['uses_old_union'] = True
                    if alias.name == 'Any':
                        analysis['uses_any'] += 1
        
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.returns is None and node.name != '__init__':
                analysis['missing_return_types'] += 1
    
    return analysis


def modernize_file(filepath: Path, dry_run: bool = False) -> None:
    """Modernize a single Python file."""
    print(f"Processing {filepath}")
    
    content = filepath.read_text()
    original_content = content
    
    # Parse and transform AST
    tree = ast.parse(content)
    modernizer = TypeModernizer()
    new_tree = modernizer.visit(tree)
    
    # Convert back to source
    import astor
    content = astor.to_source(new_tree)
    
    # Apply syntax modernizations
    syntax_mod = SyntaxModernizer()
    content = syntax_mod.add_slots_to_classes(content)
    content = syntax_mod.use_walrus_operator(content)
    content = syntax_mod.modernize_string_formatting(content)
    
    # Add future annotations if needed and not present
    if 'from __future__ import annotations' not in content:
        lines = content.split('\n')
        # Find the right place to insert (after module docstring and encoding)
        insert_idx = 0
        for i, line in enumerate(lines):
            if line.strip() and not line.startswith('#') and not line.startswith('"""'):
                insert_idx = i
                break
        
        lines.insert(insert_idx, 'from __future__ import annotations\n')
        content = '\n'.join(lines)
    
    if content != original_content:
        if not dry_run:
            filepath.write_text(content)
            print(f"  ✓ Modernized {filepath}")
        else:
            print(f"  → Would modernize {filepath}")
    else:
        print(f"  - No changes needed for {filepath}")


@click.command()
@click.argument('path', type=click.Path(exists=True, path_type=Path))
@click.option('--dry-run', is_flag=True, help='Show what would be done without making changes')
@click.option('--analyze-only', is_flag=True, help='Only analyze files without making changes')
def main(path: Path, dry_run: bool, analyze_only: bool) -> None:
    """Modernize Python type hints and syntax for Python 3.12+."""
    if path.is_file():
        files = [path]
    else:
        files = list(path.rglob('*.py'))
    
    print(f"Found {len(files)} Python files to process\n")
    
    if analyze_only:
        # Analysis mode
        total_analysis = {
            'total_files': len(files),
            'needs_modernization': 0,
            'uses_old_typing': 0,
            'uses_any_total': 0,
            'missing_return_types_total': 0,
        }
        
        for filepath in files:
            analysis = analyze_file(filepath)
            
            if (analysis['uses_old_typing'] or analysis['uses_optional'] or 
                analysis['uses_old_union'] or analysis['missing_return_types'] > 0):
                total_analysis['needs_modernization'] += 1
            
            if analysis['uses_old_typing']:
                total_analysis['uses_old_typing'] += 1
            
            total_analysis['uses_any_total'] += analysis['uses_any']
            total_analysis['missing_return_types_total'] += analysis['missing_return_types']
        
        print("Analysis Summary:")
        print(f"  Total files: {total_analysis['total_files']}")
        print(f"  Files needing modernization: {total_analysis['needs_modernization']}")
        print(f"  Files using old typing imports: {total_analysis['uses_old_typing']}")
        print(f"  Total uses of Any: {total_analysis['uses_any_total']}")
        print(f"  Total missing return types: {total_analysis['missing_return_types_total']}")
    else:
        # Modernization mode
        for filepath in files:
            try:
                modernize_file(filepath, dry_run=dry_run)
            except Exception as e:
                print(f"  ✗ Error processing {filepath}: {e}")


if __name__ == '__main__':
    main()