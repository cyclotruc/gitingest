""" Configuration manager module for loading and managing configuration. """

import os
from typing import Any

import yaml


class ConfigManager:
    """Configuration manager class for loading and managing configuration."""

    def __init__(self, config_file: str = "config.yaml") -> None:
        """
        Initialize the configuration manager.

        Parameters
        ----------
        config_file : str, optional
            The configuration file path, by default "config.yaml".
        """
        self.config_file = config_file
        self.config = self._load_config()
        self._init_directories()

    def _load_config(self) -> dict[str, Any]:
        """
        Load configuration from the config file.

        Returns
        -------
        dict[str, Any]
            The configuration dictionary.
        """
        try:
            with open(self.config_file, encoding="utf-8") as f:
                return yaml.safe_load(f)
        except Exception as e:
            print(f"Failed to load configuration file: {e}")
            return {}

    def _init_directories(self) -> None:
        """
        Initialize directories based on the configuration.
        """
        # Create output base directory
        os.makedirs(self.output_base_dir, exist_ok=True)
        # Create reports directory
        os.makedirs(self.reports_dir, exist_ok=True)
        # Create trees directory
        os.makedirs(self.trees_dir, exist_ok=True)
        # Create temporary directory
        os.makedirs(self.temp_dir, exist_ok=True)

    @property
    def tree_max_depth(self) -> int:
        """
        Get the maximum depth of the tree.

        Returns
        -------
        int
            The maximum depth of the tree.
        """
        return self.config.get("tree", {}).get("max_depth", 4)

    @property
    def max_file_size(self) -> int:
        """
        Get the maximum file size.

        Returns
        -------
        int
            The maximum file size.
        """
        return self.config.get("file", {}).get("max_size", 10 * 1024 * 1024)

    @property
    def file_encoding(self) -> str:
        """
        Get the file encoding.

        Returns
        -------
        str
            The file encoding.
        """
        return self.config.get("file", {}).get("encoding", "utf-8")

    # Input path related
    @property
    def input_base_dir(self) -> str:
        """
        Get the input base directory.

        Returns
        -------
        str
            The input base directory.
        """
        return self.config.get("paths", {}).get("input", {}).get("base_dir", os.getcwd())

    @property
    def github_repo(self) -> str:
        """
        Get the default GitHub repository address.

        Returns
        -------
        str
            The default GitHub repository address.
        """
        return self.config.get("paths", {}).get("input", {}).get("github", "")

    @property
    def gitlab_repo(self) -> str:
        """
        Get the default GitLab repository address.

        Returns
        -------
        str
            The default GitLab repository address.
        """
        return self.config.get("paths", {}).get("input", {}).get("gitlab", "")

    @property
    def output_base_dir(self) -> str:
        """
        Get the output base directory.

        Returns
        -------
        str
            The output base directory.
        """
        return self.config.get("paths", {}).get("output", {}).get("base_dir", "output")

    @property
    def reports_dir(self) -> str:
        """
        Get the reports directory.

        Returns
        -------
        str
            The reports directory.
        """
        reports = self.config.get("paths", {}).get("output", {}).get("reports", "reports")
        return os.path.join(self.output_base_dir, reports)

    @property
    def trees_dir(self) -> str:
        """
        Get the trees directory."

        Returns
        -------
        str
            The trees directory.
        """
        trees = self.config.get("paths", {}).get("output", {}).get("trees", "trees")
        return os.path.join(self.output_base_dir, trees)

    @property
    def temp_dir(self) -> str:
        """
        Get the temporary directory.

        Returns
        -------
        str
            The temporary directory.
        """
        temp = self.config.get("paths", {}).get("output", {}).get("temp", "temp")
        return os.path.join(self.output_base_dir, temp)

    @property
    def supported_formats(self) -> list[str]:
        """
        Get the supported output formats.

        Returns
        -------
        list[str]
            The supported output formats.
        """
        return self.config.get("output", {}).get("formats", ["md"])

    @property
    def default_format(self) -> str:
        """
        Get the default output format.

        Returns
        -------
        str
            The default output format.
        """
        return self.config.get("output", {}).get("default_format", "md")

    def get_output_file(self, format_type: str) -> str:
        """
        Get the output file name based on the format type.

        Parameters
        ----------
        format_type : str
            The format type.

        Returns
        -------
        str
            The output file name.
        """
        files = self.config.get("output", {}).get("files", {})
        return files.get(format_type, f"analysis_result.{format_type}")

    def get_output_path(self, filename: str, output_type: str = "reports") -> str:
        """
        Get the full output path based on the filename and output type.

        Parameters
        ----------
        filename : str
            The filename to be used.
        output_type : str, optional
            The type of output (reports, trees, temp), by default "reports".

        Returns
        -------
        str
            The full output path.
        """
        if output_type == "reports":
            base_dir = self.reports_dir
        elif output_type == "trees":
            base_dir = self.trees_dir
        elif output_type == "temp":
            base_dir = self.temp_dir
        else:
            base_dir = self.output_base_dir

        return os.path.join(base_dir, filename)

    @property
    def content_preview_length(self) -> int:
        """
        Get the content preview length.

        Returns
        -------
        int
            The content preview length.
        """
        return self.config.get("content", {}).get("preview_length", 1000)

    @property
    def supported_sources(self) -> list[str]:
        """
        Get the supported input sources.

        Returns
        -------
        list[str]
            The supported input sources.
        """
        return self.config.get("input", {}).get("supported_sources", ["local"])

    @property
    def default_source(self) -> str:
        """
        Get the default input source type.

        Returns
        -------
        str
            The default input source type.
        """
        return self.config.get("input", {}).get("default_source", "local")

    def validate_format(self, format_type: str) -> bool:
        """
        Validate if the output format is supported.

        Parameters
        ----------
        format_type : str
            The output format type.

        Returns
        -------
        bool
            True if the format is supported, False otherwise.
        """
        return format_type in self.supported_formats

    def validate_source(self, source_type: str) -> bool:
        """
        Validate if the input source is supported.

        Parameters
        ----------
        source_type : str
            The input source type.

        Returns
        -------
        bool
            True if the source is supported, False otherwise.
        """
        return source_type in self.supported_sources
