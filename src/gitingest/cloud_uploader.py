"""Handles uploading generated content to cloud storage (S3)."""

import boto3
from botocore.exceptions import ClientError
import logging
import os

logger = logging.getLogger(__name__)

def upload_content_to_s3(content: str, bucket_name: str, object_name: str) -> str | None:
    """
    Uploads a string content to an S3 bucket as a text file.

    Parameters
    ----------
    content : str
        The string content to upload.
    bucket_name : str
        The target S3 bucket name.
    object_name : str
        The desired object name/key within the bucket (e.g., 'digests/my-repo-digest.txt').

    Returns
    -------
    str | None
        The URL of the uploaded object if successful, otherwise None.
        The URL format assumes the object is publicly readable or uses standard S3 path format.
    """
    s3_client = boto3.client('s3')
    region = s3_client.meta.region_name
    if not region:
        # Attempt to get region from environment or default if not configured in client
        region = os.environ.get('AWS_REGION', 'us-east-1') # Default to us-east-1 if not set

    try:
        # Encode the string content to bytes using UTF-8
        content_bytes = content.encode('utf-8')

        s3_client.put_object(
            Bucket=bucket_name,
            Key=object_name,
            Body=content_bytes,
            ContentType='text/plain; charset=utf-8' # Specify content type
        )
        logger.info(f"Successfully uploaded {object_name} to bucket {bucket_name}.")

        # Construct the object URL
        # Note: This assumes public read access or standard S3 virtual-hosted style URL.
        # For buckets in us-east-1, the region part might be omitted in the URL.
        # Adjust based on actual bucket settings and desired access pattern (e.g., presigned URLs).
        if region == 'us-east-1':
             url = f"https://{bucket_name}.s3.amazonaws.com/{object_name}"
        else:
             url = f"https://{bucket_name}.s3.{region}.amazonaws.com/{object_name}"

        return url

    except ClientError as e:
        logger.error(f"Failed to upload {object_name} to bucket {bucket_name}: {e}")
        return None
    except Exception as e:
        logger.error(f"An unexpected error occurred during S3 upload: {e}")
        return None 