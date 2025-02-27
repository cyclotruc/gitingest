"""
Tests for the query parsing functionality.

These tests verify that the query parsing module correctly handles various input parameters,
including the submodules flag, and produces appropriate ParsedQuery objects.
"""

from unittest.mock import patch

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


@pytest.mark.asyncio
async def test_parse_query_with_tag():
    """Test that parse_query correctly handles tag parameter."""
    with patch("gitingest.query_parsing.fetch_remote_branch_list") as mock_branch_list:
        with patch("gitingest.query_parsing.fetch_remote_tag_list") as mock_tag_list:
            mock_branch_list.return_value = []  # No matching branch
            mock_tag_list.return_value = ["v1.0.0"]  # Tag exists

            parsed = await parse_query(
                source="https://github.com/user/repo/tree/v1.0.0", max_file_size=1000, from_web=True
            )
            assert parsed.tag == "v1.0.0"
            assert parsed.branch is None
            assert parsed.commit is None


@pytest.mark.asyncio
async def test_parse_query_tag_priority():
    """Test that branch is prioritized over tag when both could match."""
    with patch("gitingest.query_parsing.fetch_remote_branch_list") as mock_branch_list:
        with patch("gitingest.query_parsing.fetch_remote_tag_list") as mock_tag_list:
            mock_branch_list.return_value = ["v1.0.0"]  # Same name exists as branch
            mock_tag_list.return_value = ["v1.0.0"]  # Same name exists as tag

            parsed = await parse_query(
                source="https://github.com/user/repo/tree/v1.0.0", max_file_size=1000, from_web=True
            )
            assert parsed.branch == "v1.0.0"  # Branch should be chosen over tag
            assert parsed.tag is None


@pytest.mark.asyncio
async def test_parse_query_tag_fallback():
    """Test that tag is used when branch doesn't exist."""
    with patch("gitingest.query_parsing.fetch_remote_branch_list") as mock_branch_list:
        with patch("gitingest.query_parsing.fetch_remote_tag_list") as mock_tag_list:
            mock_branch_list.return_value = []  # No matching branch
            mock_tag_list.return_value = ["v1.0.0"]  # Tag exists

            parsed = await parse_query(
                source="https://github.com/user/repo/tree/v1.0.0", max_file_size=1000, from_web=True
            )
            assert parsed.branch is None
            assert parsed.tag == "v1.0.0"
