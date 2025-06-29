"""Tests for CLI argument validation to prevent malformed long options."""

import pytest
from click.testing import CliRunner
from gitingest.cli import main


class TestCLIMalformedArguments:
    """Test detection and handling of malformed arguments."""

    def test_original_bug_scenario_include_gitignored(self):
        """Test the exact scenario from bug report #319."""
        runner = CliRunner()
        result = runner.invoke(main, ["-i", "include-gitignored", "https://github.com/cyclotruc/gitingest"])
        
        assert result.exit_code == 2
        assert "Error: It looks like you meant" in result.output
        assert "--include-gitignored" in result.output
        assert "instead of '-i include-gitignored'" in result.output

    def test_valid_patterns_pass_validation(self):
        """Test that valid patterns pass validation without errors."""
        runner = CliRunner()
        valid_patterns = ["*.py", "*.js", "src/**"]
        
        for pattern in valid_patterns:
            result = runner.invoke(main, ["-i", pattern, "test_source"])
            assert result.exit_code != 2, f"Valid pattern should not fail: {pattern}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
