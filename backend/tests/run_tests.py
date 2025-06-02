#!/usr/bin/env python3
"""
Test runner script for the LMA API testing suite.
Provides convenient ways to run different test types and generate reports.
"""
import os
import sys
import subprocess
import argparse
from pathlib import Path


def run_command(cmd, description="Running command"):
    """Run a command and return the result."""
    print(f"\n{'='*60}")
    print(f"{description}...")
    print(f"Command: {' '.join(cmd)}")
    print('='*60)
    
    result = subprocess.run(cmd, capture_output=False)
    
    if result.returncode != 0:
        print(f"\n❌ {description} failed with exit code {result.returncode}")
        return False
    else:
        print(f"\n✅ {description} completed successfully")
        return True


def run_tests(test_type="all", verbose=False, coverage=True, html_report=False):
    """Run tests based on type specification."""
    # Change to backend directory
    backend_dir = Path(__file__).parent.parent
    os.chdir(backend_dir)
    
    # Base pytest command
    cmd = ["python", "-m", "pytest"]
    
    # Add test paths based on type
    if test_type == "unit":
        cmd.append("tests/unit")
        description = "unit tests"
    elif test_type == "integration":
        cmd.append("tests/integration")
        description = "integration tests"
    elif test_type == "all":
        cmd.append("tests")
        description = "all tests"
    else:
        print(f"❌ Unknown test type: {test_type}")
        return False
    
    # Add pytest options
    if verbose:
        cmd.extend(["-v", "-s"])
    
    if coverage:
        cmd.extend([
            "--cov=.",
            "--cov-report=term-missing",
            "--cov-fail-under=80"
        ])
        
        if html_report:
            cmd.append("--cov-report=html:htmlcov")
    
    # Add markers
    cmd.extend([
        "--strict-markers",
        "--strict-config"
    ])
    
    # Run the tests
    success = run_command(cmd, f"Running {description}")
    
    if coverage and html_report and success:
        html_path = backend_dir / "htmlcov" / "index.html"
        if html_path.exists():
            print(f"\n📊 Coverage report generated: {html_path}")
            print(f"   Open in browser: file://{html_path}")
    
    return success


def install_dependencies():
    """Install test dependencies."""
    cmd = ["pip", "install", "-r", "requirements.txt"]
    return run_command(cmd, "Installing dependencies")


def lint_code():
    """Run code linting (if tools are available)."""
    # Try to run basic Python syntax check
    cmd = ["python", "-m", "py_compile"] + [
        str(p) for p in Path(".").rglob("*.py") 
        if not str(p).startswith("__pycache__") and not str(p).startswith(".pytest_cache")
    ]
    return run_command(cmd, "Checking Python syntax")


def main():
    parser = argparse.ArgumentParser(description="Run LMA API tests")
    parser.add_argument(
        "test_type", 
        choices=["unit", "integration", "all"], 
        default="all",
        nargs="?",
        help="Type of tests to run (default: all)"
    )
    parser.add_argument(
        "-v", "--verbose", 
        action="store_true",
        help="Run tests in verbose mode"
    )
    parser.add_argument(
        "--no-coverage", 
        action="store_true",
        help="Skip coverage reporting"
    )
    parser.add_argument(
        "--html-report", 
        action="store_true",
        help="Generate HTML coverage report"
    )
    parser.add_argument(
        "--install-deps", 
        action="store_true",
        help="Install dependencies before running tests"
    )
    parser.add_argument(
        "--lint", 
        action="store_true",
        help="Run code linting before tests"
    )
    
    args = parser.parse_args()
    
    print("🧪 LMA API Test Runner")
    print("=" * 50)
    
    # Install dependencies if requested
    if args.install_deps:
        if not install_dependencies():
            sys.exit(1)
    
    # Run linting if requested
    if args.lint:
        if not lint_code():
            print("⚠️  Linting failed, but continuing with tests...")
    
    # Run tests
    success = run_tests(
        test_type=args.test_type,
        verbose=args.verbose,
        coverage=not args.no_coverage,
        html_report=args.html_report
    )
    
    if success:
        print("\n🎉 All tests completed successfully!")
        sys.exit(0)
    else:
        print("\n❌ Tests failed!")
        sys.exit(1)


if __name__ == "__main__":
    main() 