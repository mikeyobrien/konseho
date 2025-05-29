#!/usr/bin/env python3
"""Validate that docstring types match function annotations."""

from __future__ import annotations

import ast
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class DocstringMismatch:
    """Represents a mismatch between docstring and annotation."""
    
    function_name: str
    param_name: str
    docstring_type: str
    annotation_type: str
    line_number: int


@dataclass
class ValidationResult:
    """Results from docstring validation."""
    
    filepath: Path
    mismatches: list[DocstringMismatch] = field(default_factory=list)
    missing_docstrings: list[str] = field(default_factory=list)
    missing_param_docs: list[tuple[str, str]] = field(default_factory=list)
    missing_return_docs: list[str] = field(default_factory=list)


class DocstringValidator(ast.NodeVisitor):
    """Validate docstrings match type annotations."""
    
    def __init__(self, filepath: Path, source_lines: list[str]) -> None:
        self.filepath = filepath
        self.source_lines = source_lines
        self.result = ValidationResult(filepath=filepath)
        self.current_class: str | None = None
    
    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        """Track current class."""
        old_class = self.current_class
        self.current_class = node.name
        self.generic_visit(node)
        self.current_class = old_class
    
    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """Validate function docstring."""
        self._validate_function(node)
        self.generic_visit(node)
    
    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        """Validate async function docstring."""
        self._validate_function(node)
        self.generic_visit(node)
    
    def _validate_function(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
        """Validate a function's docstring against its type annotations."""
        # Skip private methods and properties
        if node.name.startswith('_') and node.name != '__init__':
            return
        
        # Build full function name
        if self.current_class:
            func_name = f"{self.current_class}.{node.name}"
        else:
            func_name = node.name
        
        # Get docstring
        docstring = ast.get_docstring(node)
        if not docstring:
            if node.args.args and len(node.args.args) > 1:  # Has params beyond self
                self.result.missing_docstrings.append(func_name)
            return
        
        # Parse docstring
        parsed_doc = self._parse_docstring(docstring)
        
        # Check parameters
        for arg in node.args.args:
            if arg.arg in ('self', 'cls'):
                continue
            
            if arg.annotation:
                annotation_type = self._annotation_to_string(arg.annotation)
                
                if arg.arg not in parsed_doc['params']:
                    self.result.missing_param_docs.append((func_name, arg.arg))
                else:
                    doc_type = parsed_doc['params'][arg.arg]
                    if not self._types_match(doc_type, annotation_type):
                        self.result.mismatches.append(
                            DocstringMismatch(
                                function_name=func_name,
                                param_name=arg.arg,
                                docstring_type=doc_type,
                                annotation_type=annotation_type,
                                line_number=node.lineno
                            )
                        )
        
        # Check return type
        if node.returns and node.name != '__init__':
            annotation_type = self._annotation_to_string(node.returns)
            if not parsed_doc['returns']:
                self.result.missing_return_docs.append(func_name)
            elif not self._types_match(parsed_doc['returns'], annotation_type):
                self.result.mismatches.append(
                    DocstringMismatch(
                        function_name=func_name,
                        param_name='return',
                        docstring_type=parsed_doc['returns'],
                        annotation_type=annotation_type,
                        line_number=node.lineno
                    )
                )
    
    def _parse_docstring(self, docstring: str) -> dict[str, Any]:
        """Parse docstring to extract parameter and return types."""
        result = {
            'params': {},
            'returns': None
        }
        
        # Common docstring formats
        # Google style: Args: param_name (type): description
        google_param = re.compile(r'^\s*(\w+)\s*\(([^)]+)\)\s*:', re.MULTILINE)
        # NumPy style: param_name : type
        numpy_param = re.compile(r'^\s*(\w+)\s*:\s*([^\n]+)$', re.MULTILINE)
        # Sphinx style: :param type param_name: or :type param_name: type
        sphinx_param = re.compile(r':param\s+(\w+)\s+(\w+):|:type\s+(\w+):\s*([^\n]+)', re.MULTILINE)
        
        # Try Google style
        for match in google_param.finditer(docstring):
            param_name, param_type = match.groups()
            result['params'][param_name] = param_type.strip()
        
        # Try NumPy style if no Google style found
        if not result['params']:
            in_params_section = False
            for line in docstring.split('\n'):
                if 'Parameters' in line or 'Args' in line:
                    in_params_section = True
                    continue
                if 'Returns' in line or 'Raises' in line:
                    in_params_section = False
                
                if in_params_section:
                    match = numpy_param.match(line)
                    if match:
                        param_name, param_type = match.groups()
                        result['params'][param_name] = param_type.strip()
        
        # Try Sphinx style
        for match in sphinx_param.finditer(docstring):
            if match.group(1) and match.group(2):  # :param type name:
                result['params'][match.group(2)] = match.group(1)
            elif match.group(3) and match.group(4):  # :type name: type
                result['params'][match.group(3)] = match.group(4).strip()
        
        # Parse return type
        # Google/NumPy style
        returns_match = re.search(r'Returns?:\s*\n\s*([^\n]+)', docstring, re.IGNORECASE)
        if returns_match:
            result['returns'] = returns_match.group(1).strip()
        
        # Sphinx style
        sphinx_return = re.search(r':returns?:\s*([^\n]+)|:rtype:\s*([^\n]+)', docstring, re.IGNORECASE)
        if sphinx_return:
            result['returns'] = (sphinx_return.group(1) or sphinx_return.group(2)).strip()
        
        return result
    
    def _annotation_to_string(self, annotation: ast.AST) -> str:
        """Convert AST annotation to string representation."""
        if isinstance(annotation, ast.Name):
            return annotation.id
        elif isinstance(annotation, ast.Constant):
            return repr(annotation.value)
        elif isinstance(annotation, ast.Subscript):
            value = self._annotation_to_string(annotation.value)
            slice_val = self._annotation_to_string(annotation.slice)
            return f"{value}[{slice_val}]"
        elif isinstance(annotation, ast.BinOp) and isinstance(annotation.op, ast.BitOr):
            left = self._annotation_to_string(annotation.left)
            right = self._annotation_to_string(annotation.right)
            return f"{left} | {right}"
        elif isinstance(annotation, ast.Tuple):
            elements = [self._annotation_to_string(e) for e in annotation.elts]
            return f"({', '.join(elements)})"
        elif isinstance(annotation, ast.List):
            elements = [self._annotation_to_string(e) for e in annotation.elts]
            return f"[{', '.join(elements)}]"
        else:
            # Fallback to source code
            return ast.unparse(annotation)
    
    def _types_match(self, doc_type: str, annotation_type: str) -> bool:
        """Check if docstring type matches annotation type."""
        # Normalize types
        doc_type = doc_type.strip().replace(' ', '')
        annotation_type = annotation_type.replace(' ', '')
        
        # Direct match
        if doc_type == annotation_type:
            return True
        
        # Common equivalences
        equivalences = {
            'str': ['string', 'text'],
            'int': ['integer', 'number'],
            'bool': ['boolean'],
            'dict': ['dictionary', 'mapping'],
            'list': ['array', 'sequence'],
            'None': ['NoneType'],
        }
        
        for key, values in equivalences.items():
            if key in annotation_type and any(v in doc_type for v in values):
                return True
            if key in doc_type and any(v in annotation_type for v in values):
                return True
        
        # Handle Optional/Union vs |
        if 'Optional[' in doc_type and '|None' in annotation_type:
            core_type = doc_type.replace('Optional[', '').replace(']', '')
            if core_type in annotation_type:
                return True
        
        return False


def validate_file(filepath: Path) -> ValidationResult:
    """Validate docstrings in a single file."""
    content = filepath.read_text()
    lines = content.split('\n')
    tree = ast.parse(content, filename=str(filepath))
    
    validator = DocstringValidator(filepath, lines)
    validator.visit(tree)
    
    return validator.result


def generate_report(results: list[ValidationResult]) -> str:
    """Generate validation report."""
    total_mismatches = sum(len(r.mismatches) for r in results)
    total_missing_docs = sum(len(r.missing_docstrings) for r in results)
    total_missing_params = sum(len(r.missing_param_docs) for r in results)
    total_missing_returns = sum(len(r.missing_return_docs) for r in results)
    
    report = [
        "# Docstring Validation Report",
        "",
        "## Summary",
        f"- Files analyzed: {len(results)}",
        f"- Type mismatches: {total_mismatches}",
        f"- Missing docstrings: {total_missing_docs}",
        f"- Missing parameter docs: {total_missing_params}",
        f"- Missing return docs: {total_missing_returns}",
        "",
    ]
    
    if total_mismatches > 0:
        report.extend([
            "## Type Mismatches",
            "",
        ])
        
        for result in results:
            if result.mismatches:
                report.append(f"### {result.filepath}")
                for mismatch in result.mismatches:
                    report.append(
                        f"- Line {mismatch.line_number}: `{mismatch.function_name}` - "
                        f"parameter `{mismatch.param_name}`: "
                        f"docstring says `{mismatch.docstring_type}` but "
                        f"annotation says `{mismatch.annotation_type}`"
                    )
                report.append("")
    
    if total_missing_docs > 0:
        report.extend([
            "## Missing Docstrings",
            "",
        ])
        
        for result in results:
            if result.missing_docstrings:
                report.append(f"- {result.filepath}: {', '.join(result.missing_docstrings)}")
    
    return "\n".join(report)


def main() -> int:
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: validate_docstrings.py <path> [path2 ...]")
        return 1
    
    all_results: list[ValidationResult] = []
    
    for path_str in sys.argv[1:]:
        path = Path(path_str)
        
        if path.is_file() and path.suffix == '.py':
            result = validate_file(path)
            all_results.append(result)
        elif path.is_dir():
            for py_file in path.rglob('*.py'):
                if '__pycache__' not in str(py_file):
                    result = validate_file(py_file)
                    all_results.append(result)
    
    report = generate_report(all_results)
    print(report)
    
    # Return non-zero if issues found
    total_issues = sum(
        len(r.mismatches) + len(r.missing_docstrings) + 
        len(r.missing_param_docs) + len(r.missing_return_docs)
        for r in all_results
    )
    
    return 1 if total_issues > 0 else 0


if __name__ == '__main__':
    sys.exit(main())