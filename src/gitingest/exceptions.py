class InvalidPatternError(ValueError):
    def __init__(self, pattern: str) -> None:
        super().__init__(
            f"Pattern '{pattern}' contains invalid characters. Only alphanumeric characters, dash (-), "
            "underscore (_), dot (.), forward slash (/), plus (+), and asterisk (*) are allowed."
        )
