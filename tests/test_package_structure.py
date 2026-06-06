"""Tests for package structure and pip installability."""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest


class TestPackageStructure:
    """Test that the package structure is correct for pip install."""

    @pytest.fixture
    def project_root(self):
        """Get project root path."""
        return Path(__file__).parent.parent

    def test_setup_py_exists(self, project_root):
        """Test that setup.py exists in project root."""
        setup_path = project_root / 'setup.py'
        assert setup_path.exists()

    def test_setup_py_valid_python(self, project_root):
        """Test that setup.py is valid Python code."""
        setup_path = project_root / 'setup.py'
        with open(setup_path) as f:
            code = f.read()
        compile(code, 'setup.py', 'exec')

    def test_setup_py_has_entry_points(self, project_root):
        """Test that setup.py has console_scripts entry points."""
        setup_path = project_root / 'setup.py'
        with open(setup_path) as f:
            content = f.read()

        assert 'console_scripts' in content
        assert 'openexec=' in content

    def test_setup_py_has_packages(self, project_root):
        """Test that setup.py has packages defined."""
        setup_path = project_root / 'setup.py'
        with open(setup_path) as f:
            content = f.read()

        assert 'packages=' in content

    def test_setup_py_has_install_requires(self, project_root):
        """Test that setup.py has install_requires."""
        setup_path = project_root / 'setup.py'
        with open(setup_path) as f:
            content = f.read()

        assert 'install_requires=' in content

    def test_requirements_txt_exists(self, project_root):
        """Test that requirements.txt exists."""
        requirements_path = project_root / 'requirements.txt'
        assert requirements_path.exists()

    def test_requirements_txt_not_empty(self, project_root):
        """Test that requirements.txt has dependencies."""
        requirements_path = project_root / 'requirements.txt'
        with open(requirements_path) as f:
            lines = [line.strip() for line in f if line.strip() and not line.startswith('#')]

        assert len(lines) > 0


class TestOpenexecPackage:
    """Test that openexec package exists and is importable."""

    @pytest.fixture
    def project_root(self):
        """Get project root path."""
        return Path(__file__).parent.parent

    def test_openexec_package_directory_exists(self, project_root):
        """Test that openexec package directory exists."""
        openexec_dir = project_root / 'openexec'
        assert openexec_dir.exists()

    def test_openexec_package_init_exists(self, project_root):
        """Test that openexec/__init__.py exists."""
        init_path = project_root / 'openexec' / '__init__.py'
        assert init_path.exists()

    def test_openexec_cli_exists(self, project_root):
        """Test that openexec/cli.py exists."""
        cli_path = project_root / 'openexec' / 'cli.py'
        assert cli_path.exists()

    def test_openexec_cli_importable(self, project_root):
        """Test that openexec.cli can be imported."""
        # Add project root to path
        sys.path.insert(0, str(project_root))
        from openexec.cli import main

        assert callable(main)

    def test_openexec_package_init_exports(self, project_root):
        """Test that openexec/__init__.py exports main."""
        init_path = project_root / 'openexec' / '__init__.py'
        with open(init_path) as f:
            content = f.read()

        assert 'from .cli import main' in content or 'from cli import main' in content


class TestOpenexecModules:
    """Test that openexec package modules exist."""

    @pytest.fixture
    def project_root(self):
        """Get project root path."""
        return Path(__file__).parent.parent

    def test_agents_directory_exists(self, project_root):
        """Test that openexec/agents directory exists."""
        agents_dir = project_root / 'openexec' / 'agents'
        assert agents_dir.exists()

    def test_agents_init_exists(self, project_root):
        """Test that openexec/agents/__init__.py exists."""
        init_path = project_root / 'openexec' / 'agents' / '__init__.py'
        assert init_path.exists()

    def test_agents_interface_exists(self, project_root):
        """Test that openexec/agents/interface.py exists."""
        interface_path = project_root / 'openexec' / 'agents' / 'interface.py'
        assert interface_path.exists()

    def test_agents_templates_exist(self, project_root):
        """Test that agent template files exist."""
        agents_dir = project_root / 'openexec' / 'agents'

        templates = ['templates_ceo.py', 'templates_cfo.py', 'templates_cto.py', 'templates_cmo.py']

        for template in templates:
            template_path = agents_dir / template
            assert template_path.exists(), f"Missing: {template}"

    def test_ai_directory_exists(self, project_root):
        """Test that openexec/ai directory exists."""
        ai_dir = project_root / 'openexec' / 'ai'
        assert ai_dir.exists()

    def test_ai_init_exists(self, project_root):
        """Test that openexec/ai/__init__.py exists."""
        init_path = project_root / 'openexec' / 'ai' / '__init__.py'
        assert init_path.exists()

    def test_ai_provider_exists(self, project_root):
        """Test that openexec/ai/ollama_provider.py exists."""
        provider_path = project_root / 'openexec' / 'ai' / 'ollama_provider.py'
        assert provider_path.exists()

    def test_ai_prompts_exists(self, project_root):
        """Test that openexec/ai/prompts.py exists."""
        prompts_path = project_root / 'openexec' / 'ai' / 'prompts.py'
        assert prompts_path.exists()

    def test_core_modules_exist(self, project_root):
        """Test that core module files exist."""
        core_modules = [
            'cli.py',
            'main.py',
            'orchestrator.py',
            'event_store.py',
            'events.py',
            'decision_tracker.py',
            'memory.py',
            'feedback.py',
            'knowledge_base.py',
            'risk_analyzer.py',
            'export.py',
            'summary.py',
            'utils.py',
            'interactive.py'
        ]

        for module in core_modules:
            module_path = project_root / 'openexec' / module
            assert module_path.exists(), f"Missing module: {module}"


class TestImports:
    """Test that all imports work correctly."""

    @pytest.fixture
    def project_root(self):
        """Get project root path and add to sys.path."""
        project_root = Path(__file__).parent.parent
        sys.path.insert(0, str(project_root))
        yield project_root
        # Remove from sys.path
        if str(project_root) in sys.path:
            sys.path.remove(str(project_root))

    def test_import_openexec_main(self, project_root):
        """Test that openexec.cli.main can be imported."""
        from openexec.cli import main

        assert callable(main)

    def test_import_openexec_agents(self, project_root):
        """Test that openexec.agents can be imported."""
        from openexec.agents import AgentRegistry

        assert AgentRegistry is not None

    def test_import_openexec_agents_interface(self, project_root):
        """Test that AgentReport can be imported."""
        from openexec.agents.interface import AgentReport

        assert AgentReport is not None

    def test_import_openexec_ai(self, project_root):
        """Test that openexec.ai can be imported."""
        from openexec.ai.client import AIClient

        assert AIClient is not None

    def test_import_openexec_orchestrator(self, project_root):
        """Test that Orchestrator can be imported."""
        from openexec.orchestrator import Orchestrator

        assert Orchestrator is not None


class TestGitignore:
    """Test that .gitignore is configured correctly."""

    @pytest.fixture
    def project_root(self):
        """Get project root path."""
        return Path(__file__).parent.parent

    def test_gitignore_exists(self, project_root):
        """Test that .gitignore exists."""
        gitignore_path = project_root / '.gitignore'
        assert gitignore_path.exists()

    def test_gitignore_contains_python_cache(self, project_root):
        """Test that .gitignore excludes Python cache."""
        gitignore_path = project_root / '.gitignore'
        content = gitignore_path.read_text()

        assert '__pycache__' in content or '__pycache__' in content

    def test_gitignore_contains_build_artifacts(self, project_root):
        """Test that .gitignore excludes build artifacts."""
        gitignore_path = project_root / '.gitignore'
        content = gitignore_path.read_text()

        assert '*.egg-info' in content or 'egg-info' in content or 'dist/' in content


class TestSampleDataFiles:
    """Test that sample data files exist and are valid."""

    @pytest.fixture
    def project_root(self):
        """Get project root path."""
        return Path(__file__).parent.parent

    def test_data_directory_exists(self, project_root):
        """Test that data directory exists."""
        data_dir = project_root / 'data'
        assert data_dir.exists()

    def test_company_background_exists(self, project_root):
        """Test that company_background.md exists."""
        filepath = project_root / 'data' / 'company_background.md'
        assert filepath.exists()

    def test_company_background_has_content(self, project_root):
        """Test that company_background.md has substantial content."""
        filepath = project_root / 'data' / 'company_background.md'
        content = filepath.read_text()

        assert len(content) > 1000, "company_background.md should have substantial content"
        assert '# Company Background' in content

    def test_team_structure_exists(self, project_root):
        """Test that team_structure.md exists."""
        filepath = project_root / 'data' / 'team_structure.md'
        assert filepath.exists()

    def test_team_structure_has_content(self, project_root):
        """Test that team_structure.md has substantial content."""
        filepath = project_root / 'data' / 'team_structure.md'
        content = filepath.read_text()

        assert len(content) > 1000, "team_structure.md should have substantial content"
        assert '# Team Structure' in content

    def test_case_studies_exists(self, project_root):
        """Test that case_studies.md exists."""
        filepath = project_root / 'data' / 'case_studies.md'
        assert filepath.exists()

    def test_case_studies_has_content(self, project_root):
        """Test that case_studies.md has substantial content."""
        filepath = project_root / 'data' / 'case_studies.md'
        content = filepath.read_text()

        assert len(content) > 2000, "case_studies.md should have substantial content"
        assert '# Case Studies' in content

    def test_industry_context_exists(self, project_root):
        """Test that industry_context.md exists."""
        filepath = project_root / 'data' / 'industry_context.md'
        assert filepath.exists()

    def test_industry_context_has_content(self, project_root):
        """Test that industry_context.md has substantial content."""
        filepath = project_root / 'data' / 'industry_context.md'
        content = filepath.read_text()

        assert len(content) > 1500, "industry_context.md should have substantial content"
        assert '# Industry Context' in content


class TestCLICommandHelp:
    """Test CLI command help and documentation."""

    @pytest.fixture
    def project_root(self):
        """Get project root path."""
        return Path(__file__).parent.parent

    def test_readme_exists(self, project_root):
        """Test that README.md exists."""
        readme_path = project_root / 'README.md'
        assert readme_path.exists()

    def test_readme_has_installation_guide(self, project_root):
        """Test that README contains installation guide."""
        readme_path = project_root / 'README.md'
        content = readme_path.read_text()

        assert 'pip install' in content.lower() or 'Installation' in content

    def test_readme_has_cli_reference(self, project_root):
        """Test that README contains CLI reference."""
        readme_path = project_root / 'README.md'
        content = readme_path.read_text()

        assert 'openexec run' in content or 'openexec setup' in content


class TestPackageMetadata:
    """Test package metadata in setup.py."""

    @pytest.fixture
    def project_root(self):
        """Get project root path."""
        return Path(__file__).parent.parent

    def test_setup_py_has_name(self, project_root):
        """Test that setup.py has package name."""
        setup_path = project_root / 'setup.py'
        with open(setup_path) as f:
            content = f.read()

        assert 'name=' in content
        assert 'openexec' in content

    def test_setup_py_has_version(self, project_root):
        """Test that setup.py has version."""
        setup_path = project_root / 'setup.py'
        with open(setup_path) as f:
            content = f.read()

        assert 'version=' in content

    def test_setup_py_has_description(self, project_root):
        """Test that setup.py has description."""
        setup_path = project_root / 'setup.py'
        with open(setup_path) as f:
            content = f.read()

        assert 'description=' in content or 'description=' in content


# Run tests
if __name__ == '__main__':
    pytest.main([__file__, '-v'])
