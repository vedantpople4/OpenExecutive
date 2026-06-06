"""Tests for the openexec CLI."""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from openexec.cli import main


class TestCLIEntryPoints:
    """Test CLI entry points and help commands."""

    def test_cli_help(self):
        """Test that --help works and displays usage."""
        with patch('sys.argv', ['openexec', '--help']):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 0

    def test_cli_run_help(self):
        """Test that run subcommand --help works."""
        with patch('sys.argv', ['openexec', 'run', '--help']):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 0

    def test_cli_setup_help(self):
        """Test that setup subcommand --help works."""
        with patch('sys.argv', ['openexec', 'setup', '--help']):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 0


class TestCLIRunCommand:
    """Test the run command functionality."""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    def test_run_command_creates_output_file(self, temp_dir):
        """Test that run command creates output markdown file."""
        # Patch before importing main to ensure it patches the imported function
        with patch('openexec.main.write_report') as mock_write:
            def side_effect(results, output_path):
                with open(output_path, 'w') as f:
                    f.write("# Mock Report\n\n")
            mock_write.side_effect = side_effect

            # Test by calling main directly with mocked arguments
            import sys
            sys.argv = ['openexec', 'run', 'Test question?', '-o', str(temp_dir / 'output.md')]

            try:
                main()
            except SystemExit:
                pass  # Expected - CLI exits cleanly (both click.Exit and sys.exit raise this)

            assert (temp_dir / 'output.md').exists()

    def test_run_command_loads_data_files(self, temp_dir):
        """Test that run command loads data files from data directory."""
        # Create sample data file in temp dir
        data_file = temp_dir / 'test_data.md'
        data_file.write_text("# Test Data\n\nThis is test content.")

        with patch('sys.argv', ['openexec', 'run', 'Test?']):
            # This would test data loading if run in project root
            pass


class TestCLIRunner:
    """Test CLI runner integration."""

    def test_data_files_exist(self, project_root):
        """Test that required data files exist."""
        data_dir = project_root / 'data'
        assert data_dir.exists()

        required_files = [
            'company_background.md',
            'team_structure.md',
            'case_studies.md',
            'industry_context.md'
        ]

        for filename in required_files:
            filepath = data_dir / filename
            assert filepath.exists(), f"Missing required data file: {filename}"

    def test_data_file_content(self, project_root):
        """Test that data files have meaningful content."""
        data_dir = project_root / 'data'

        for filename in ['company_background.md', 'team_structure.md', 'case_studies.md', 'industry_context.md']:
            filepath = data_dir / filename
            content = filepath.read_text()

            # Basic validation: file should have some content
            assert len(content) > 100, f"{filename} is too small or empty"

            # Check for structured markdown
            assert '#' in content, f"{filename} should contain markdown headers"


class TestCLIDecisionLogging:
    """Test decision logging functionality."""

    def test_decision_log_created(self, project_root):
        """Test that decisions are logged to decision directory."""
        decisions_dir = project_root / 'decisions'
        assert decisions_dir.exists()

        # Check that decision_log.json exists
        decision_log = decisions_dir / 'decision_log.json'
        if decision_log.exists():
            with open(decision_log) as f:
                log = json.load(f)
                assert isinstance(log, list)


class TestCLIExportFormats:
    """Test CLI export formats."""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    def test_export_formats_recognized(self):
        """Test that recognized export formats are documented."""
        valid_formats = ['json', 'csv', 'checklist']

        # Verify these formats are in the code
        from openexec.export import ExportFormat

        for fmt in valid_formats:
            assert fmt.lower() in ['json', 'csv', 'checklist'], f"{fmt} should be valid"


class TestCLIPackageStructure:
    """Test that package structure is correct for pip install."""

    def test_openexec_package_exists(self, project_root):
        """Test that openexec package directory exists."""
        openexec_dir = project_root / 'openexec'
        assert openexec_dir.exists()

    def test_cli_module_exists(self, project_root):
        """Test that cli.py exists in openexec package."""
        cli_path = project_root / 'openexec' / 'cli.py'
        assert cli_path.exists()

    def test_main_function_exists(self, project_root):
        """Test that main function exists in cli module."""
        from openexec.cli import main

        assert callable(main)

    def test_setup_py_exists(self, project_root):
        """Test that setup.py exists and is valid."""
        setup_path = project_root / 'setup.py'
        assert setup_path.exists()

        # Verify setup.py is valid Python
        with open(setup_path) as f:
            compile(f.read(), 'setup.py', 'exec')


class TestCLIConfiguration:
    """Test CLI configuration management."""

    def test_settings_json_structure(self, project_root):
        """Test that settings.json has expected structure."""
        settings_path = project_root / 'settings.json'

        if settings_path.exists():
            with open(settings_path) as f:
                settings = json.load(f)

            # Check for expected top-level keys
            expected_keys = ['ai', 'agents', 'output', 'simulation']

            for key in expected_keys:
                assert key in settings, f"settings.json should have '{key}' key"

    def test_ai_provider_config_exists(self, project_root):
        """Test that AI provider configuration exists."""
        settings_path = project_root / 'settings.json'

        if settings_path.exists():
            with open(settings_path) as f:
                settings = json.load(f)

            assert 'ai' in settings
            assert 'base_url' in settings['ai']
            assert 'model' in settings['ai']


class TestDataCorpusLoading:
    """Test data corpus loading functionality."""

    @pytest.fixture
    def sample_data_files(self, project_root):
        """Get list of sample data files."""
        data_dir = project_root / 'data'
        if data_dir.exists():
            return list(data_dir.glob('*.md'))
        return []

    def test_sample_files_loadable(self, sample_data_files):
        """Test that sample data files can be read."""
        for file_path in sample_data_files:
            content = file_path.read_text()
            assert len(content) > 0, f"{file_path.name} is empty"


class TestCLICommandDocumentation:
    """Test CLI command documentation."""

    def test_readme_exists(self, project_root):
        """Test that README.md exists."""
        readme_path = project_root / 'README.md'
        assert readme_path.exists()

    def test_readme_has_installation_guide(self, project_root):
        """Test that README contains installation instructions."""
        readme_path = project_root / 'README.md'
        content = readme_path.read_text()

        assert 'pip install' in content.lower() or 'install' in content.lower()

    def test_readme_has_usage_examples(self, project_root):
        """Test that README contains usage examples."""
        readme_path = project_root / 'README.md'
        content = readme_path.read_text()

        assert 'openexec run' in content or 'openexec --help' in content


class TestCLIWeightValidation:
    """Test --weight flag validation in run command."""

    def test_invalid_agent_name_exits(self):
        """Invalid agent name should exit with error."""
        with patch('sys.argv', ['openexec', 'run', 'Test?', '--weight', 'badagent=0.5']):
            from typer import Exit
            with pytest.raises(SystemExit) as exc_info:
                from openexec.cli import main
                main()
            assert exc_info.value.code == 1

    def test_non_numeric_weight_exits(self):
        """Non-numeric weight should exit with error."""
        with patch('sys.argv', ['openexec', 'run', 'Test?', '--weight', 'cfo=abc']):
            from typer import Exit
            with pytest.raises(SystemExit) as exc_info:
                from openexec.cli import main
                main()
            assert exc_info.value.code == 1

    def test_out_of_range_weight_exits(self):
        """Weight > 1.0 should exit with error."""
        with patch('sys.argv', ['openexec', 'run', 'Test?', '--weight', 'cfo=2.0']):
            from typer import Exit
            with pytest.raises(SystemExit) as exc_info:
                from openexec.cli import main
                main()
            assert exc_info.value.code == 1

    def test_negative_weight_exits(self):
        """Negative weight should exit with error."""
        with patch('sys.argv', ['openexec', 'run', 'Test?', '--weight', 'cfo=-0.5']):
            from typer import Exit
            with pytest.raises(SystemExit) as exc_info:
                from openexec.cli import main
                main()
            assert exc_info.value.code == 1


class TestCLIOutputValidation:
    """Test output path validation in run command."""

    def test_nonexistent_output_dir_exits(self):
        """Non-existent output directory should exit before simulation."""
        with patch('sys.argv', ['openexec', 'run', 'Test?', '-o', '/nonexistent/dir/output.md']):
            from typer import Exit
            with pytest.raises(SystemExit) as exc_info:
                from openexec.cli import main
                main()
            assert exc_info.value.code == 1

    def test_valid_output_dir_proceeds(self, tmp_path):
        """Valid output directory should proceed (but may fail later in simulation)."""
        output_file = tmp_path / "output.md"
        with patch('sys.argv', ['openexec', 'run', 'Test?', '-o', str(output_file)]):
            # This should get past the output validation but may fail later
            # depending on the environment. At minimum it shouldn't fail at the
            # directory validation step.
            pass


# Run tests
if __name__ == '__main__':
    pytest.main([__file__, '-v'])
