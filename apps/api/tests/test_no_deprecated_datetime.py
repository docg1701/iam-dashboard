"""
Test to ensure no deprecated datetime.utcnow() usage.
Part of architectural fixes - prevents regression of datetime issues.
"""

import ast
import os
from collections.abc import Iterator
from pathlib import Path

import pytest


class DatetimeVisitor(ast.NodeVisitor):
    """AST visitor to find datetime.utcnow() usage."""

    def __init__(self) -> None:
        self.violations: list[tuple[int, str]] = []

    def visit_Attribute(self, node: ast.Attribute) -> None:
        """Visit attribute access nodes."""
        # Check for datetime.utcnow()
        if (
            isinstance(node.value, ast.Name)
            and node.value.id == "datetime"
            and node.attr == "utcnow"
        ):
            self.violations.append((node.lineno, "datetime.utcnow()"))

        # Check for module.datetime.utcnow()
        if (
            isinstance(node.value, ast.Attribute)
            and node.value.attr == "datetime"
            and node.attr == "utcnow"
        ):
            self.violations.append((node.lineno, "module.datetime.utcnow()"))

        self.generic_visit(node)


def find_python_files() -> Iterator[Path]:
    """Find all Python files in source directories."""
    source_dirs = [
        Path("apps/api/src"),
        Path("apps/api/tests"),
    ]

    for source_dir in source_dirs:
        if source_dir.exists():
            yield from source_dir.rglob("*.py")


def check_file_for_datetime_utcnow(file_path: Path) -> list[tuple[int, str]]:
    """
    Check a Python file for deprecated datetime.utcnow() usage.

    Args:
        file_path: Path to the Python file to check

    Returns:
        List of (line_number, violation_description) tuples
    """
    try:
        with open(file_path, encoding="utf-8") as f:
            content = f.read()

        # Parse the file into an AST
        tree = ast.parse(content, filename=str(file_path))

        # Visit all nodes to find datetime.utcnow usage
        visitor = DatetimeVisitor()
        visitor.visit(tree)

        # Add file path to violation descriptions
        violations = [
            (line_no, f"{file_path}:{line_no} - {desc}")
            for line_no, desc in visitor.violations
        ]

        return violations

    except (SyntaxError, UnicodeDecodeError) as e:
        # Skip files that can't be parsed (should not happen in our codebase)
        pytest.fail(f"Could not parse {file_path}: {e}")
        return []


def test_no_deprecated_datetime_utcnow() -> None:
    """
    Test that no Python files use deprecated datetime.utcnow().

    This test prevents regression of the datetime.utcnow() issue.
    All datetime usage should use datetime.now(timezone.utc) instead.
    """
    violations = []

    for file_path in find_python_files():
        file_violations = check_file_for_datetime_utcnow(file_path)
        violations.extend(file_violations)

    if violations:
        violation_messages = [f"  - {desc}" for _, desc in violations]
        error_message = (
            f"Found {len(violations)} usage(s) of deprecated datetime.utcnow():\n"
            + "\n".join(violation_messages)
            + "\n\n"
            + "SOLUTION: Replace datetime.utcnow() with datetime.now(timezone.utc)\n"
            + "See CLAUDE.md section 'CRITICAL DATETIME RULE' for details."
        )
        pytest.fail(error_message)


def test_datetime_check_script_exists() -> None:
    """Test that the datetime validation script exists and is executable."""
    script_path = Path("../../scripts/check-datetime-usage.sh")

    assert script_path.exists(), "check-datetime-usage.sh script should exist"
    assert os.access(script_path, os.X_OK), (
        "check-datetime-usage.sh should be executable"
    )


if __name__ == "__main__":
    # Allow running this test directly for debugging
    test_no_deprecated_datetime_utcnow()
    test_datetime_check_script_exists()
    print("✅ All datetime validation tests passed!")
