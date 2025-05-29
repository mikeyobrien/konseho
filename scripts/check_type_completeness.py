#!/usr/bin/env python3
"""Check type completeness and generate reports for Python codebases."""

from __future__ import annotations

import ast
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class TypeCheckResult:
    """Results from type completeness check."""
    
    filepath: Path
    total_functions: int = 0
    typed_functions: int = 0
    total_parameters: int = 0
    typed_parameters: int = 0
    missing_return_types: list[str] = field(default_factory=list)
    missing_param_types: list[tuple[str, str]] = field(default_factory=list)
    uses_any: list[str] = field(default_factory=list)
    
    @property
    def function_coverage(self) -> float:
        """Calculate function type coverage percentage."""
        if self.total_functions == 0:
            return 100.0
        return (self.typed_functions / self.total_functions) * 100
    
    @property
    def parameter_coverage(self) -> float:
        """Calculate parameter type coverage percentage."""
        if self.total_parameters == 0:
            return 100.0
        return (self.typed_parameters / self.total_parameters) * 100


class TypeCompletenessChecker(ast.NodeVisitor):
    """AST visitor to check type completeness."""
    
    def __init__(self, filepath: Path) -> None:
        self.result = TypeCheckResult(filepath=filepath)
        self.current_class: str | None = None
    
    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        """Track current class for method names."""
        old_class = self.current_class
        self.current_class = node.name
        self.generic_visit(node)
        self.current_class = old_class
    
    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """Check function definition for type completeness."""
        self._check_function(node)
        self.generic_visit(node)
    
    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        """Check async function definition for type completeness."""
        self._check_function(node)
        self.generic_visit(node)
    
    def _check_function(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
        """Check a function for type annotations."""
        # Skip dunder methods except __init__
        if node.name.startswith('__') and node.name != '__init__':
            return
        
        self.result.total_functions += 1
        
        # Build function name with class if applicable
        if self.current_class:
            func_name = f"{self.current_class}.{node.name}"
        else:
            func_name = node.name
        
        # Check return type
        has_return_type = node.returns is not None
        if node.name != '__init__' and not has_return_type:
            self.result.missing_return_types.append(func_name)
        
        # Check parameters
        all_params_typed = True
        for arg in node.args.args:
            # Skip 'self' and 'cls'
            if arg.arg in ('self', 'cls'):
                continue
            
            self.result.total_parameters += 1
            if arg.annotation is None:
                all_params_typed = False
                self.result.missing_param_types.append((func_name, arg.arg))
            else:
                self.result.typed_parameters += 1
                # Check for Any usage
                if self._contains_any(arg.annotation):
                    self.result.uses_any.append(f"{func_name}({arg.arg})")
        
        # Check return annotation for Any
        if has_return_type and self._contains_any(node.returns):
            self.result.uses_any.append(f"{func_name} -> return")
        
        # Count as typed if has return type and all params typed
        if has_return_type and all_params_typed:
            self.result.typed_functions += 1
    
    def _contains_any(self, annotation: ast.AST | None) -> bool:
        """Check if annotation contains Any."""
        if annotation is None:
            return False
        
        if isinstance(annotation, ast.Name) and annotation.id == 'Any':
            return True
        
        # Check in subscripts like Optional[Any], list[Any], etc.
        for node in ast.walk(annotation):
            if isinstance(node, ast.Name) and node.id == 'Any':
                return True
        
        return False


def check_file(filepath: Path) -> TypeCheckResult:
    """Check a single file for type completeness."""
    content = filepath.read_text()
    tree = ast.parse(content, filename=str(filepath))
    
    checker = TypeCompletenessChecker(filepath)
    checker.visit(tree)
    
    return checker.result


def generate_report(results: list[TypeCheckResult]) -> str:
    """Generate a comprehensive type completeness report."""
    total_files = len(results)
    total_functions = sum(r.total_functions for r in results)
    total_typed_functions = sum(r.typed_functions for r in results)
    total_parameters = sum(r.total_parameters for r in results)
    total_typed_parameters = sum(r.typed_parameters for r in results)
    total_any_uses = sum(len(r.uses_any) for r in results)
    
    # Calculate overall coverage
    overall_function_coverage = (
        (total_typed_functions / total_functions * 100) if total_functions > 0 else 100
    )
    overall_parameter_coverage = (
        (total_typed_parameters / total_parameters * 100) if total_parameters > 0 else 100
    )
    
    report = [
        "# Type Completeness Report",
        "",
        "## Summary",
        f"- Files analyzed: {total_files}",
        f"- Total functions: {total_functions}",
        f"- Typed functions: {total_typed_functions} ({overall_function_coverage:.1f}%)",
        f"- Total parameters: {total_parameters}",
        f"- Typed parameters: {total_typed_parameters} ({overall_parameter_coverage:.1f}%)",
        f"- Uses of Any: {total_any_uses}",
        "",
        "## Files Needing Attention",
        "",
    ]
    
    # Sort by worst coverage first
    results.sort(key=lambda r: r.function_coverage)
    
    for result in results:
        if result.function_coverage < 100 or result.uses_any:
            report.append(f"### {result.filepath}")
            report.append(f"- Function coverage: {result.function_coverage:.1f}%")
            report.append(f"- Parameter coverage: {result.parameter_coverage:.1f}%")
            
            if result.missing_return_types:
                report.append("- Missing return types:")
                for func in result.missing_return_types[:5]:  # Show first 5
                    report.append(f"  - `{func}`")
                if len(result.missing_return_types) > 5:
                    report.append(f"  - ... and {len(result.missing_return_types) - 5} more")
            
            if result.missing_param_types:
                report.append("- Missing parameter types:")
                for func, param in result.missing_param_types[:5]:
                    report.append(f"  - `{func}({param})`")
                if len(result.missing_param_types) > 5:
                    report.append(f"  - ... and {len(result.missing_param_types) - 5} more")
            
            if result.uses_any:
                report.append("- Uses of Any:")
                for usage in result.uses_any[:5]:
                    report.append(f"  - `{usage}`")
                if len(result.uses_any) > 5:
                    report.append(f"  - ... and {len(result.uses_any) - 5} more")
            
            report.append("")
    
    return "\n".join(report)


def main() -> int:
    """Main entry point for type completeness checking."""
    if len(sys.argv) < 2:
        print("Usage: check_type_completeness.py <path> [path2 ...]")
        return 1
    
    all_results: list[TypeCheckResult] = []
    
    for path_str in sys.argv[1:]:
        path = Path(path_str)
        
        if path.is_file() and path.suffix == '.py':
            result = check_file(path)
            all_results.append(result)
        elif path.is_dir():
            for py_file in path.rglob('*.py'):
                # Skip test files and __pycache__
                if '__pycache__' not in str(py_file) and 'test_' not in py_file.name:
                    result = check_file(py_file)
                    all_results.append(result)
    
    # Generate and print report
    report = generate_report(all_results)
    print(report)
    
    # Return non-zero if coverage is not 100%
    total_functions = sum(r.total_functions for r in all_results)
    total_typed = sum(r.typed_functions for r in all_results)
    
    if total_functions > 0 and total_typed < total_functions:
        return 1
    
    return 0


if __name__ == '__main__':
    sys.exit(main())