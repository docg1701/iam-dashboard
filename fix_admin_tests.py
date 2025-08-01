#!/usr/bin/env python3
"""Script to fix async mock issues in admin API tests."""

import re


def fix_admin_tests():
    """Fix async mock issues in admin API tests."""
    with open('tests/unit/test_api/test_admin_api.py') as f:
        content = f.read()

    # Pattern to match mock assignments for async methods
    patterns = [
        (r'mock_agent_manager\.enable_agent\.return_value = (True|False)',
         r'mock_agent_manager.enable_agent = AsyncMock(return_value=\1)'),
        (r'mock_agent_manager\.disable_agent\.return_value = (True|False)',
         r'mock_agent_manager.disable_agent = AsyncMock(return_value=\1)'),
        (r'mock_agent_manager\.health_check\.return_value = (True|False)',
         r'mock_agent_manager.health_check = AsyncMock(return_value=\1)'),
    ]

    for pattern, replacement in patterns:
        content = re.sub(pattern, replacement, content)

    # Add AsyncMock import at the top if not present
    if 'from unittest.mock import AsyncMock' not in content:
        content = content.replace(
            'from unittest.mock import MagicMock',
            'from unittest.mock import AsyncMock, MagicMock'
        )

    with open('tests/unit/test_api/test_admin_api.py', 'w') as f:
        f.write(content)

    print("Fixed async mock issues in admin API tests")

if __name__ == "__main__":
    fix_admin_tests()
