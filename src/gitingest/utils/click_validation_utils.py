"""Click validation utilities for detecting malformed CLI arguments."""

import re
from typing import Set, Tuple
import click


class ClickArgumentValidator:
    """Validator for Click command arguments to catch malformed long options."""

    def __init__(self):
        self.known_long_options: Set[str] = {
            "include-gitignored", "exclude-pattern", "include-pattern", 
            "max-size", "output", "token", "branch", "help", "version"
        }
        self.malformed_pattern = re.compile(r"^([a-zA-Z][a-zA-Z0-9-]{2,})$")

    def validate_pattern_option(self, ctx, param, value, option_name):  # pylint: disable=unused-argument
        """Validate pattern options to catch malformed long options."""
        if not value:
            return value

        for pattern in value:
            self._check_pattern_for_malformed_option(ctx, pattern, option_name)
        
        return value

    def _check_pattern_for_malformed_option(self, ctx, pattern, option_name):
        """Check if a pattern looks like a malformed long option."""
        match = self.malformed_pattern.match(pattern)
        if not match:
            return

        potential_option = match.group(1)
        
        # Account for Click consuming the first character
        possible_reconstructions = [
            potential_option,
            "i" + potential_option,  # -include-gitignored -> -i nclude-gitignored
            "e" + potential_option,  # -exclude-pattern -> -e xclude-pattern  
            "o" + potential_option,  # -output -> -o utput
            "t" + potential_option,  # -token -> -t oken
            "m" + potential_option,  # -max-size -> -m ax-size
            "b" + potential_option,  # -branch -> -b ranch
            "h" + potential_option,  # -help -> -h elp
            "v" + potential_option,  # -version -> -v ersion
        ]
        
        # Check if any reconstruction matches a known long option
        for reconstructed in possible_reconstructions:
            if reconstructed in self.known_long_options:
                self._show_known_option_error(ctx, pattern, reconstructed, option_name)
                return
        
        # Check for other patterns that suggest malformed long options
        if self._looks_like_malformed_long_option(potential_option):
            likely_original = "i" + potential_option if option_name == "include-pattern" else "e" + potential_option
            self._show_malformed_option_error(ctx, pattern, likely_original, option_name)

    def _looks_like_malformed_long_option(self, potential_option):
        """Check if a string looks like a malformed long option using heuristics."""
        if "-" in potential_option and len(potential_option) > 4:
            return True
        
        long_option_indicators = [
            "nclude", "xclude", "clude-gitignored", "clude-pattern",
            "utput", "nput", "oken", "ranch", "max", "min", "size", 
            "format", "verbose", "quiet", "help", "version", "config", "debug", "force"
        ]
        
        potential_lower = potential_option.lower()
        return any(indicator in potential_lower for indicator in long_option_indicators)

    def _show_known_option_error(self, ctx, pattern, reconstructed_option, option_name):
        """Show error message for known long options that were malformed."""
        short_opt = "-i" if option_name == "include-pattern" else "-e"
        
        click.echo("", err=True)
        click.echo(f"Error: It looks like you meant '--{reconstructed_option}' instead of '{short_opt} {pattern}'", err=True)
        click.echo("", err=True)
        click.echo("Correct usage:", err=True)
        click.echo(f"  gitingest --{reconstructed_option} <source>", err=True)
        click.echo("", err=True)
        click.echo(f"If you meant to use {option_name}, please verify the pattern: '{pattern}'", err=True)
        click.echo("", err=True)
        click.echo("Examples:", err=True)
        click.echo(f"  gitingest --{reconstructed_option} https://github.com/user/repo", err=True)
        click.echo(f"  gitingest {short_opt} '*.py' https://github.com/user/repo", err=True)
        ctx.exit(2)

    def _show_malformed_option_error(self, ctx, pattern, likely_original, option_name):
        """Show error message for potentially malformed long options."""
        short_opt = "-i" if option_name == "include-pattern" else "-e"
        
        click.echo("", err=True)
        click.echo(f"Error: The pattern '{pattern}' looks like a malformed long option.", err=True)
        click.echo("", err=True)
        click.echo(f"If you meant a long option, use '--{likely_original}' (double dash).", err=True)
        click.echo(f"If you meant {option_name}, please verify: '{pattern}'", err=True)
        click.echo("", err=True)
        click.echo("Examples:", err=True)
        click.echo(f"  gitingest --{likely_original} <source>  # Long option", err=True)
        click.echo(f"  gitingest {short_opt} '*.py' <source>    # {option_name.title()}", err=True)
        ctx.exit(2)


# Global validator instance
_validator = ClickArgumentValidator()


def validate_include_patterns(ctx, param, value):
    """Click callback to validate include patterns for malformed long options."""
    return _validator.validate_pattern_option(ctx, param, value, "include-pattern")


def validate_exclude_patterns(ctx, param, value):
    """Click callback to validate exclude patterns for malformed long options."""
    return _validator.validate_pattern_option(ctx, param, value, "exclude-pattern")
