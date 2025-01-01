import argparse
import json
import subprocess
from typing import Any

from config_manager import ConfigManager
from gitingest.ingest import ingest

# Load configuration
config = ConfigManager()


def generate_tree(directory: str, max_depth: int | None = None) -> str:
    """
    Generate a directory tree structure

    Parameters
    ----------
    directory : str
        Directory path to analyze.
    max_depth : int | None
        Maximum depth of the tree, by default None.

    Returns
    -------
    str
        String representation of the directory tree.
    """
    if max_depth is None:
        max_depth = config.tree_max_depth

    try:
        result = subprocess.run(["tree", "-L", str(max_depth)], cwd=directory, capture_output=True, text=True)
        return result.stdout
    except Exception as e:
        return f"Failed to generate tree: {e}"


def analyze_tree_and_suggest_patterns(tree_output: str) -> tuple[list[str], list[str]]:
    """
    Analyze the directory tree and suggest include/exclude patterns

    Parameters
    ----------
    tree_output : str
        String representation of the directory tree.

    Returns
    -------
    tuple[list[str], list[str]]
        List of include patterns and list of exclude patterns.
    """
    #
    include_patterns = [
        "**/*.py",
        "README.md",
        "CHANGELOG.md",
        "LICENSE",
        "requirements.txt",
        "pyproject.toml",
        "setup.py",
        "setup.cfg",
        "MANIFEST.in",
        "docs/**/*.md",
    ]

    exclude_patterns = [
        "**/*.pyc",
        "**/__pycache__/**",
        "**/*.so" "**/*.pyd",
        "**/*.dll",
        "**/*.dylib",
        "**/*.egg",
        "**/*.whl",
        "**/*.exe",
        "**/*.png",
        "**/*.jpg",
        "**/*.jpeg",
        "**/*.gif",
        "**/*.ico",
        "**/*.svg",
        "**/*.mp4",
        "**/*.mov",
        "**/*.avi",
        "**/*.mp3",
        "**/*.wav",
        "**/.git/**",
        "**/.idea/**",
        "**/.vscode/**",
        "**/.env",
        "**/.env.*",
        "**/node_modules/**",
        "**/venv/**",
        "**/env/**",
        "**/build/**",
        "**/dist/**",
        "**/.pytest_cache/**",
        "**/.coverage",
        "**/htmlcov/**",
        "**/*.min.js",
        "**/*.min.css",
        "**/*.map",
        "**/webpack.stats.json",
        "**/ui/**/*.js",
        "**/ui/**/*.css",
        "**/ui/build/**",
        "**/ui/dist/**",
        "**/tests/**",
        "**/test_*.py",
        "**/*_test.py",
        "**/*.ipynb",
        "**/.ipynb_checkpoints/**",
    ]

    return include_patterns, exclude_patterns


def smart_ingest(directory: str, max_file_size: int | None = None, output_format: str | None = None) -> dict[str, Any]:
    """
    Perform smart ingest analysis on the given directory and return the report.

    Parameters
    ----------
    directory : str
        Directory path to analyze.
    max_file_size : int
        Maximum file size to analyze, by default None.
    output_format : str
        Output format of the report, by default None.

    Returns
    -------
    dict[str, Any]
        Report of the analysis.

    Raises
    ------
    ValueError
        If the output format is not supported.
    """
    if max_file_size is None:
        max_file_size = config.max_file_size
    if output_format is None:
        output_format = config.default_format

    if not config.validate_format(output_format):
        raise ValueError(f"Unsupported output format: {output_format}")

    # Step 1: Generate directory tree
    print("Step 1: Generating directory tree...", end="\n\n")
    tree_output = generate_tree(directory)
    print(tree_output)

    # Save the tree output to a file
    tree_file = config.get_output_path(config.get_output_file("tree"), "trees")
    with open(tree_file, "w", encoding=config.file_encoding) as f:
        f.write(tree_output)

    # Step 2: Analyze the directory structure and suggest filter patterns
    print("Step 2: Analyzing directory structure and suggesting filter patterns...")
    include_patterns, exclude_patterns = analyze_tree_and_suggest_patterns(tree_output)

    print("Suggested include patterns:", end="\n\n")
    for pattern in include_patterns:
        print(f"  - {pattern}")

    print("Suggested exclude patterns:", end="\n\n")
    for pattern in exclude_patterns:
        print(f"  - {pattern}")

    # Step 3: Execute file analysis
    print("\nStep 3: Executing file analysis...")
    try:
        summary, tree, content = ingest(
            source=directory,
            max_file_size=max_file_size,
            include_patterns=include_patterns,
            exclude_patterns=exclude_patterns,
            output=config.get_output_path(config.get_output_file(output_format), "reports"),
        )

        # Report
        report = {
            "directory_tree": tree_output,
            "suggested_patterns": {
                "include": include_patterns,
                "exclude": exclude_patterns,
            },
            "analysis_result": {
                "summary": summary,
                "tree": tree,
                "content": (
                    content[: config.content_preview_length] + "..."
                    if len(content) > config.content_preview_length
                    else content
                ),
            },
        }

        # Save the report to a JSON file
        json_file = config.get_output_path(config.get_output_file("json"), "reports")
        with open(json_file, "w", encoding=config.file_encoding) as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        return report

    except Exception as e:
        return {
            "error": f"分析过程中出错: {e}",
            "directory_tree": tree_output,
            "suggested_patterns": {
                "include": include_patterns,
                "exclude": exclude_patterns,
            },
        }


def main() -> None:
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Intelligent directory analysis tool")
    parser.add_argument("--source", "-s", type=str, default=config.input_base_dir, help="Directory to analyze")
    parser.add_argument(
        "--source-type",
        "-t",
        type=str,
        choices=config.supported_sources,
        default=config.default_source,
        help="Input source type",
    )
    parser.add_argument("--max-depth", "-d", type=int, default=config.tree_max_depth, help="Maximum depth of the tree")
    parser.add_argument(
        "--max-size", "-m", type=int, default=config.max_file_size, help="Maximum file size to analyze"
    )
    parser.add_argument("--output-dir", "-o", type=str, default=config.output_base_dir, help="Output base directory")
    parser.add_argument(
        "--format",
        "-f",
        type=str,
        choices=config.supported_formats,
        default=config.default_format,
        help="Output format of the report",
    )

    args = parser.parse_args()

    print(f"Start analyzing directory: {args.source}")
    print(f"Configuration information:")
    print(f"- Input source type: {args.source_type}")
    print(f"- Directory tree depth: {args.max_depth}")
    print(f"- Maximum file size: {args.max_size / 1024 / 1024:.2f}MB")
    print(f"- Output base directory: {args.output_dir}")
    print(f"- Output format: {args.format}")

    # Perform smart ingest analysis
    result = smart_ingest(directory=args.source, max_file_size=args.max_size, output_format=args.format)

    print(f"\nAnalysis completed! Output file:")
    print(f"1. Directory tree: {config.get_output_path(config.get_output_file('tree'), 'trees')}")
    print(f"2. Analysis report: {config.get_output_path(config.get_output_file(args.format), 'reports')}")
    print(f"3. JSON report: {config.get_output_path(config.get_output_file('json'), 'reports')}")


if __name__ == "__main__":
    main()
