""" Custom exceptions for the Gitingest package. """


class InvalidPatternError(ValueError):
    """
    Exception raised when a pattern contains invalid characters.
    This exception is used to signal that a pattern provided for some operation
    contains characters that are not allowed. The valid characters for the pattern
    include alphanumeric characters, dash (-), underscore (_), dot (.), forward slash (/),
    plus (+), and asterisk (*).
    Parameters
    ----------
    pattern : str
        The invalid pattern that caused the error.
    """

    def __init__(self, pattern: str) -> None:
        super().__init__(
            f"Pattern '{pattern}' contains invalid characters. Only alphanumeric characters, dash (-), "
            "underscore (_), dot (.), forward slash (/), plus (+), and asterisk (*) are allowed."
        )


class AsyncTimeoutError(Exception):
    """
    Exception raised when an async operation exceeds its timeout limit.

    This exception is used by the `async_timeout` decorator to signal that the wrapped
    asynchronous function has exceeded the specified time limit for execution.
    """


class MaxFilesReachedError(Exception):
    """Exception raised when the maximum number of files is reached."""

    def __init__(self, max_files: int) -> None:
        super().__init__(f"Maximum number of files ({max_files}) reached.")


class MaxFileSizeReachedError(Exception):
    """Exception raised when the maximum file size is reached."""

    def __init__(self, max_size: int):
        super().__init__(f"Maximum file size limit ({max_size/1024/1024:.1f}MB) reached.")


class AlreadyVisitedError(Exception):
    """Exception raised when a symlink target has already been visited."""

    def __init__(self, path: str) -> None:
        super().__init__(f"Symlink target already visited: {path}")


class InvalidNotebookError(Exception):
    """Exception raised when a Jupyter notebook is invalid or cannot be processed."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
