"""
Tests for the query parsing functionality.

These tests verify that the query parsing module correctly handles various input parameters,
including the submodules flag, and produces appropriate ParsedQuery objects.
"""

import pytest

from gitingest.query_parsing import parse_query


@pytest.mark.asyncio
async def test_parse_query_with_submodules():
    """Test that parse_query correctly handles include_submodules parameter."""
    parsed = await parse_query(
        source="https://github.com/user/repo", max_file_size=1000, from_web=True, include_submodules=True
    )
    assert parsed.include_submodules is True


@pytest.mark.asyncio
async def test_parse_query_without_submodules():
    """Test that parse_query defaults to not including submodules."""
    parsed = await parse_query(source="https://github.com/user/repo", max_file_size=1000, from_web=True)
    assert parsed.include_submodules is False
