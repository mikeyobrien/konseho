#!/usr/bin/env python3
"""Orchestrate the complete Python modernization process."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import Any

import click


class ModernizationRunner:
    """Orchestrate Python code modernization."""
    
    def __init__(self, path: Path, verbose: bool = False) -> None:
        self.path = path
        self.verbose = verbose
        self.scripts_dir = Path(__file__).parent
    
    def run_command(self, cmd: list[str], check: bool = True) -> subprocess.CompletedProcess[str]:
        """Run a command and return the result."""
        if self.verbose:
            print(f"Running: {' '.join(cmd)}")
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False
        )
        
        if check and result.returncode != 0:
            print(f"Error running {cmd[0]}:")
            print(result.stderr)
            sys.exit(1)
        
        return result
    
    def phase1_analyze(self) -> dict[str, Any]:
        """Phase 1: Analyze current state."""
        print("\n🔍 Phase 1: Analyzing current codebase...")
        
        # Run type completeness check
        cmd = [sys.executable, str(self.scripts_dir / "check_type_completeness.py"), str(self.path)]
        result = self.run_command(cmd)
        
        if self.verbose:
            print(result.stdout)
        
        # Run modernization analysis
        cmd = [
            sys.executable, 
            str(self.scripts_dir / "modernize_types.py"), 
            str(self.path),
            "--analyze-only"
        ]
        result = self.run_command(cmd)
        
        print(result.stdout)
        
        return {"type_check": result.returncode == 0}
    
    def phase2_configure(self) -> None:
        """Phase 2: Configure tools."""
        print("\n⚙️  Phase 2: Configuring development tools...")
        
        # Install pre-commit hooks
        if (self.path / ".pre-commit-config.yaml").exists():
            print("Installing pre-commit hooks...")
            self.run_command(["pre-commit", "install"])
            
            # Run pre-commit on all files to check
            print("Running initial pre-commit checks...")
            result = self.run_command(["pre-commit", "run", "--all-files"], check=False)
            
            if result.returncode != 0:
                print("⚠️  Some pre-commit checks failed. This is expected before modernization.")
    
    def phase3_modernize(self, dry_run: bool = False) -> None:
        """Phase 3: Run modernization."""
        print(f"\n🚀 Phase 3: {'Planning' if dry_run else 'Running'} modernization...")
        
        cmd = [
            sys.executable,
            str(self.scripts_dir / "modernize_types.py"),
            str(self.path)
        ]
        
        if dry_run:
            cmd.append("--dry-run")
        
        result = self.run_command(cmd)
        print(result.stdout)
    
    def phase4_validate(self) -> bool:
        """Phase 4: Validate results."""
        print("\n✅ Phase 4: Validating modernization...")
        
        # Run mypy
        print("Running mypy type checking...")
        result = self.run_command(["mypy", str(self.path)], check=False)
        
        if result.returncode != 0:
            print("❌ Mypy validation failed:")
            print(result.stdout)
            return False
        else:
            print("✅ Mypy validation passed!")
        
        # Run black formatting
        print("Running black formatter...")
        self.run_command(["black", str(self.path)])
        
        # Run ruff
        print("Running ruff linter...")
        result = self.run_command(["ruff", "check", str(self.path), "--fix"], check=False)
        
        if result.returncode != 0:
            print("⚠️  Ruff found issues that couldn't be auto-fixed")
        
        # Validate docstrings
        print("Validating docstrings...")
        cmd = [sys.executable, str(self.scripts_dir / "validate_docstrings.py"), str(self.path)]
        result = self.run_command(cmd, check=False)
        
        if self.verbose:
            print(result.stdout)
        
        return True
    
    def phase5_report(self) -> None:
        """Phase 5: Generate final report."""
        print("\n📊 Phase 5: Generating final report...")
        
        # Re-run type completeness check
        cmd = [sys.executable, str(self.scripts_dir / "check_type_completeness.py"), str(self.path)]
        result = self.run_command(cmd)
        
        print(result.stdout)
        
        # Summary
        print("\n🎉 Modernization Summary:")
        print("- ✅ Type annotations modernized")
        print("- ✅ Syntax updated to Python 3.12+")
        print("- ✅ Tools configured")
        print("- ✅ Code formatted and linted")
        
        if result.returncode == 0:
            print("- ✅ 100% type coverage achieved!")
        else:
            print("- ⚠️  Some type coverage gaps remain")


@click.command()
@click.argument('path', type=click.Path(exists=True, path_type=Path))
@click.option('--dry-run', is_flag=True, help='Show what would be done without making changes')
@click.option('--verbose', '-v', is_flag=True, help='Show detailed output')
@click.option('--skip-analysis', is_flag=True, help='Skip initial analysis phase')
@click.option('--skip-validation', is_flag=True, help='Skip validation phase')
def main(
    path: Path, 
    dry_run: bool, 
    verbose: bool, 
    skip_analysis: bool,
    skip_validation: bool
) -> None:
    """Run complete Python modernization process.
    
    This tool orchestrates the entire modernization workflow:
    1. Analyze current state
    2. Configure development tools
    3. Modernize code
    4. Validate changes
    5. Generate report
    """
    runner = ModernizationRunner(path, verbose=verbose)
    
    print(f"🎯 Modernizing Python code in: {path}")
    
    # Phase 1: Analysis
    if not skip_analysis:
        runner.phase1_analyze()
    
    # Phase 2: Configuration
    runner.phase2_configure()
    
    # Phase 3: Modernization
    runner.phase3_modernize(dry_run=dry_run)
    
    if not dry_run:
        # Phase 4: Validation
        if not skip_validation:
            if not runner.phase4_validate():
                print("\n❌ Validation failed. Please fix issues before proceeding.")
                sys.exit(1)
        
        # Phase 5: Report
        runner.phase5_report()
    
    print("\n✨ Modernization complete!")


if __name__ == '__main__':
    main()