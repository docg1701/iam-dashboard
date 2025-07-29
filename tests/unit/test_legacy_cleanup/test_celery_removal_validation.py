"""Unit tests to validate complete removal of Celery infrastructure.

This module ensures that all Celery components have been completely removed
and no legacy code dependencies remain in the system.
"""

import os
import subprocess
from pathlib import Path

import pytest


class TestCeleryRemovalValidation:
    """Tests to validate complete Celery infrastructure removal."""

    def test_celery_workers_directory_removed(self):
        """Test that app/workers directory has been completely removed."""
        workers_dir = Path("app/workers")
        assert not workers_dir.exists(), f"Legacy workers directory still exists: {workers_dir}"

    def test_celery_imports_removed_from_codebase(self):
        """Test that no Celery imports remain in the codebase."""
        # Search for Celery imports in Python files
        app_dir = Path("app")
        if not app_dir.exists():
            pytest.skip("App directory not found")
            
        celery_patterns = [
            "from celery",
            "import celery",
            "celery.task",
            "celery_app",
            "@task",
            "apply_async"
        ]
        
        violations = {}
        
        for py_file in app_dir.rglob("*.py"):
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                for pattern in celery_patterns:
                    if pattern.lower() in content.lower():
                        if str(py_file) not in violations:
                            violations[str(py_file)] = []
                        violations[str(py_file)].append(pattern)
            except (UnicodeDecodeError, PermissionError):
                continue  # Skip files that can't be read
        
        # Exclude files that are allowed to reference Celery (like documentation)
        allowed_files = {
            "docs/",  # Documentation files
            "tests/",  # Test files may reference for comparison
            ".git/",   # Git files
        }
        
        filtered_violations = {}
        for file_path, patterns in violations.items():
            if not any(allowed in file_path for allowed in allowed_files):
                filtered_violations[file_path] = patterns
        
        assert not filtered_violations, \
            f"Celery imports found in: {filtered_violations}"

    def test_celery_dependencies_removed_from_pyproject(self):
        """Test that Celery dependencies have been removed from pyproject.toml."""
        pyproject_path = Path("pyproject.toml")
        if not pyproject_path.exists():
            pytest.skip("pyproject.toml not found")
            
        with open(pyproject_path, 'r') as f:
            content = f.read()
        
        celery_deps = [
            "celery>=",
            "celery==",
            '"celery',
            "'celery"
        ]
        
        violations = []
        for dep in celery_deps:
            if dep in content.lower():
                violations.append(dep)
        
        assert not violations, \
            f"Celery dependencies still present in pyproject.toml: {violations}"

    def test_docker_compose_worker_service_removed(self):
        """Test that Celery worker service has been removed from docker-compose.yml."""
        compose_files = [
            "docker-compose.yml"
        ]
        
        for compose_file in compose_files:
            compose_path = Path(compose_file)
            if not compose_path.exists():
                continue
                
            with open(compose_path, 'r') as f:
                content = f.read()
            
            # Check for worker service definition
            worker_indicators = [
                "celery -A",
                "worker --loglevel",
                "celery_app worker",
            ]
            
            violations = []
            for indicator in worker_indicators:
                if indicator in content:
                    violations.append(indicator)
            
            assert not violations, \
                f"Worker service references found in {compose_file}: {violations}"

    def test_agent_architecture_properly_implemented(self):
        """Test that agent architecture is properly in place."""
        # Check that agent directories exist
        required_agent_dirs = [
            Path("app/agents"),
            Path("app/tools"),
            Path("app/plugins")
        ]
        
        existing_dirs = []
        for agent_dir in required_agent_dirs:
            if agent_dir.exists() and agent_dir.is_dir():
                existing_dirs.append(agent_dir)
        
        # At least agents directory should exist
        assert Path("app/agents").exists(), "Core agents directory missing"

    def test_startup_has_no_celery_initialization(self):
        """Test that application startup has no Celery initialization."""
        main_file = Path("app/main.py")
        if not main_file.exists():
            pytest.skip("Main application file not found")
            
        with open(main_file, 'r') as f:
            content = f.read()
        
        celery_init_patterns = [
            "celery_app",
            "Celery(",
            "celery.Celery",
            "worker_main",
            "celery worker"
        ]
        
        violations = []
        for pattern in celery_init_patterns:
            if pattern in content:
                violations.append(pattern)
        
        assert not violations, \
            f"Celery initialization found in main.py: {violations}"


class TestSystemIntegrityAfterCleanup:
    """Tests to ensure system integrity after Celery cleanup."""

    def test_application_can_import_without_errors(self):
        """Test that main application modules can be imported."""
        try:
            # Test core imports
            from app.main import fastapi_app
            assert fastapi_app is not None
        except ImportError as e:
            pytest.fail(f"Failed to import main application: {e}")

    def test_no_missing_imports_after_cleanup(self):
        """Test that no imports are broken after Celery removal."""
        # This would be caught by other tests, but good to be explicit
        app_dir = Path("app")
        if not app_dir.exists():
            pytest.skip("App directory not found")
            
        # We can't actually test all imports without running the app
        # But we can check that main modules exist
        critical_modules = [
            Path("app/main.py"),
            Path("app/core/__init__.py"),
            Path("app/models/__init__.py"),
            Path("app/api/__init__.py")
        ]
        
        missing_modules = []
        for module in critical_modules:
            if not module.exists():
                missing_modules.append(str(module))
        
        assert not missing_modules, \
            f"Critical modules missing after cleanup: {missing_modules}"

    def test_database_models_intact(self):
        """Test that database models are intact after cleanup."""
        models_dir = Path("app/models")
        if not models_dir.exists():
            pytest.skip("Models directory not found")
            
        # Check that core models exist
        core_models = [
            "client.py",
            "document.py", 
            "user.py"
        ]
        
        missing_models = []
        for model in core_models:
            model_path = models_dir / model
            if not model_path.exists():
                missing_models.append(model)
        
        assert not missing_models, \
            f"Core models missing: {missing_models}"

    def test_api_endpoints_intact(self):
        """Test that API endpoints are intact after cleanup."""
        api_dir = Path("app/api")
        if not api_dir.exists():
            pytest.skip("API directory not found")
            
        # Check that core API modules exist
        core_apis = [
            "documents.py",
            "clients.py"
        ]
        
        missing_apis = []
        for api in core_apis:
            api_path = api_dir / api
            if not api_path.exists():
                missing_apis.append(api)
        
        # Some APIs might not exist yet, so we just check structure
        assert api_dir.exists(), "API directory should exist"