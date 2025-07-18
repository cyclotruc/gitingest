"""S3 utility functions for uploading and managing digest files."""

from __future__ import annotations

import hashlib
import os
from typing import Any

import boto3
from botocore.exceptions import ClientError


class S3UploadError(Exception):
    """Custom exception for S3 upload failures."""


def is_s3_enabled() -> bool:
    """Check if S3 is enabled via environment variables."""
    return os.getenv("S3_ENABLED", "false").lower() == "true"


def get_s3_config() -> dict[str, Any]:
    """Get S3 configuration from environment variables."""
    return {
        "endpoint_url": os.getenv("S3_ENDPOINT"),
        "aws_access_key_id": os.getenv("S3_ACCESS_KEY"),
        "aws_secret_access_key": os.getenv("S3_SECRET_KEY"),
        "region_name": os.getenv("S3_REGION", "us-east-1"),
    }


def get_s3_bucket_name() -> str:
    """Get S3 bucket name from environment variables."""
    return os.getenv("S3_BUCKET_NAME", "gitingest-bucket")


def get_s3_alias_host() -> str | None:
    """Get S3 alias host for public URLs."""
    return os.getenv("S3_ALIAS_HOST")


def generate_s3_file_path(
    source: str,
    user_name: str,
    repo_name: str,
    branch: str | None,
    commit: str | None,
    include_patterns: set[str] | None,
    ignore_patterns: set[str],
) -> str:
    """Generate S3 file path with proper naming convention.

    Format: /ingest/<provider>/<repo-owner>/<repo-name>/<branch>/<commit-ID>/<exclude&include hash>.txt
    The commit-ID is always included in the URL. If no specific commit is provided,
    the actual commit hash from the cloned repository is used.

    Args:
        source: Git host (github, gitlab, etc.)
        user_name: Repository owner/user
        repo_name: Repository name
        branch: Branch name (if available)
        commit: Commit hash (should always be available now)
        include_patterns: Include patterns set
        ignore_patterns: Ignore patterns set

    Returns:
        S3 file path string

    """
    # Extract source from URL or default to "unknown"
    if "github.com" in source:
        git_source = "github"
    elif "gitlab.com" in source:
        git_source = "gitlab"
    elif "bitbucket.org" in source:
        git_source = "bitbucket"
    else:
        git_source = "unknown"

    # Use branch, fallback to "main" if neither branch nor commit
    branch_name = branch or "main"

    # Create hash of exclude/include patterns for uniqueness
    patterns_str = f"include:{sorted(include_patterns) if include_patterns else []}"
    patterns_str += f"exclude:{sorted(ignore_patterns)}"

    patterns_hash = hashlib.sha256(patterns_str.encode()).hexdigest()[:16]

    # Commit should always be available now, but provide fallback just in case
    commit_id = commit or "HEAD"

    # Format: /ingest/<provider>/<repo-owner>/<repo-name>/<branch>/<commit-ID>/<hash>.txt
    return f"ingest/{git_source}/{user_name}/{repo_name}/{branch_name}/{commit_id}/{patterns_hash}.txt"


def create_s3_client() -> boto3.client:
    """Create and return an S3 client with configuration from environment."""
    config = get_s3_config()
    return boto3.client("s3", **config)


def upload_to_s3(content: str, s3_file_path: str, ingest_id: str) -> str:
    """Upload content to S3 and return the public URL.

    Args:
        content: The digest content to upload
        s3_file_path: The S3 file path
        ingest_id: The ingest ID to store as S3 object tag

    Returns:
        Public URL to access the uploaded file

    Raises:
        Exception: If upload fails

    """
    if not is_s3_enabled():
        msg = "S3 is not enabled"
        raise ValueError(msg)

    try:
        s3_client = create_s3_client()
        bucket_name = get_s3_bucket_name()

        # Upload the content with ingest_id as tag
        s3_client.put_object(
            Bucket=bucket_name,
            Key=s3_file_path,
            Body=content.encode("utf-8"),
            ContentType="text/plain",
            Tagging=f"ingest_id={ingest_id}",
        )

        # Generate public URL
        alias_host = get_s3_alias_host()
        if alias_host:
            # Use alias host if configured
            return f"{alias_host.rstrip('/')}/{s3_file_path}"
        # Fallback to direct S3 URL
        endpoint = get_s3_config()["endpoint_url"]
        if endpoint:
            return f"{endpoint.rstrip('/')}/{bucket_name}/{s3_file_path}"
        return f"https://{bucket_name}.s3.{get_s3_config()['region_name']}.amazonaws.com/{s3_file_path}"

    except ClientError as e:
        msg = f"Failed to upload to S3: {e}"
        raise S3UploadError(msg) from e


def _build_s3_url(key: str) -> str:
    """Build S3 URL for a given key."""
    alias_host = get_s3_alias_host()
    if alias_host:
        return f"{alias_host.rstrip('/')}/{key}"
    endpoint = get_s3_config()["endpoint_url"]
    if endpoint:
        bucket_name = get_s3_bucket_name()
        return f"{endpoint.rstrip('/')}/{bucket_name}/{key}"
    bucket_name = get_s3_bucket_name()
    return f"https://{bucket_name}.s3.{get_s3_config()['region_name']}.amazonaws.com/{key}"


def _check_object_tags(s3_client: boto3.client, bucket_name: str, key: str, target_ingest_id: str) -> bool:
    """Check if an S3 object has the matching ingest_id tag."""
    try:
        tags_response = s3_client.get_object_tagging(Bucket=bucket_name, Key=key)
        tags = {tag["Key"]: tag["Value"] for tag in tags_response.get("TagSet", [])}
        return tags.get("ingest_id") == target_ingest_id
    except ClientError:
        return False


def get_s3_url_for_ingest_id(ingest_id: str) -> str | None:
    """Get S3 URL for a given ingest ID if it exists.

    This is used by the download endpoint to redirect to S3 if available.
    Searches for files using S3 object tags to find the matching ingest_id.

    Args:
        ingest_id: The ingest ID

    Returns:
        S3 URL if file exists, None otherwise

    """
    if not is_s3_enabled():
        return None

    try:
        s3_client = create_s3_client()
        bucket_name = get_s3_bucket_name()

        # List all objects in the ingest/ prefix and check their tags
        paginator = s3_client.get_paginator("list_objects_v2")
        page_iterator = paginator.paginate(
            Bucket=bucket_name,
            Prefix="ingest/",
        )

        for page in page_iterator:
            if "Contents" not in page:
                continue

            for obj in page["Contents"]:
                key = obj["Key"]
                if _check_object_tags(s3_client, bucket_name, key, ingest_id):
                    return _build_s3_url(key)

    except ClientError:
        pass

    return None
