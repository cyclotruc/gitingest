"""Pydantic models for the query form."""

from __future__ import annotations

from pydantic import BaseModel

# needed for type checking (pydantic)
from server.form_types import IntForm, OptStrForm, StrForm  # noqa: TC001 (typing-only-first-party-import)


class QueryForm(BaseModel):
    """Form data for the query.

    Attributes
    ----------
    input_text : str
        Text or URL supplied in the form.
    max_file_size : int
        The maximum allowed file size for the input, specified by the user.
    pattern_type : str
        The type of pattern used for the query (``include`` or ``exclude``).
    pattern : str
        Glob/regex pattern string.
    token : str | None
        GitHub personal access token (PAT) for accessing private repositories.

    """

    input_text: str
    max_file_size: int
    pattern_type: str
    pattern: str
    token: str | None = None

    @classmethod
    def as_form(
        cls,
        input_text: StrForm,
        max_file_size: IntForm,
        pattern_type: StrForm,
        pattern: StrForm,
        token: OptStrForm,
    ) -> QueryForm:
        """Create a QueryForm from FastAPI form parameters.

        Parameters
        ----------
        input_text : StrForm
            The input text provided by the user.
        max_file_size : IntForm
            The maximum allowed file size for the input.
        pattern_type : StrForm
            The type of pattern used for the query (``include`` or ``exclude``).
        pattern : StrForm
            Glob/regex pattern string.
        token : OptStrForm
            GitHub personal access token (PAT) for accessing private repositories.

        Returns
        -------
        QueryForm
            The QueryForm instance.

        """
        return cls(
            input_text=input_text,
            max_file_size=max_file_size,
            pattern_type=pattern_type,
            pattern=pattern,
            token=token,
        )
