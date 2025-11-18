"""
S3 Storage Client
Handles file uploads/downloads to S3-compatible object storage
"""
import boto3
from botocore.exceptions import ClientError
from loguru import logger
from typing import Optional
from datetime import datetime, timedelta

from core.config import settings


class S3StorageClient:
    """
    S3-compatible object storage client

    Supports:
    - AWS S3
    - MinIO
    - DigitalOcean Spaces
    - Wasabi
    - Any S3-compatible service
    """

    def __init__(self):
        """Initialize S3 client with configuration"""
        self.bucket_name = settings.S3_BUCKET_NAME

        # Initialize boto3 client
        self.s3 = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_REGION,
            endpoint_url=settings.S3_ENDPOINT_URL  # For MinIO/compatible services
        )

        logger.info(f"S3 client initialized for bucket: {self.bucket_name}")

    def upload_bytes(
        self,
        key: str,
        data: bytes,
        content_type: str = "application/octet-stream",
        metadata: Optional[dict] = None
    ) -> bool:
        """
        Upload bytes to S3

        Args:
            key: S3 object key (path)
            data: File data as bytes
            content_type: MIME type
            metadata: Optional metadata dict

        Returns:
            True if successful, False otherwise
        """
        try:
            extra_args = {
                'ContentType': content_type,
                'ServerSideEncryption': 'AES256',  # Encrypt at rest
            }

            if metadata:
                extra_args['Metadata'] = metadata

            self.s3.put_object(
                Bucket=self.bucket_name,
                Key=key,
                Body=data,
                **extra_args
            )

            logger.info(f"Uploaded file to S3: {key} ({len(data)} bytes)")
            return True

        except ClientError as e:
            logger.error(f"Failed to upload to S3: {e}")
            return False

    def download_bytes(self, key: str) -> Optional[bytes]:
        """
        Download file from S3 as bytes

        Args:
            key: S3 object key

        Returns:
            File data as bytes, or None if failed
        """
        try:
            response = self.s3.get_object(
                Bucket=self.bucket_name,
                Key=key
            )

            data = response['Body'].read()
            logger.info(f"Downloaded file from S3: {key} ({len(data)} bytes)")
            return data

        except ClientError as e:
            logger.error(f"Failed to download from S3: {e}")
            return None

    def presign_download(
        self,
        key: str,
        expires_seconds: int = 600  # 10 minutes
    ) -> str:
        """
        Generate presigned download URL

        Args:
            key: S3 object key
            expires_seconds: URL expiration time (default 10 minutes)

        Returns:
            Presigned URL
        """
        try:
            url = self.s3.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': self.bucket_name,
                    'Key': key
                },
                ExpiresIn=expires_seconds
            )

            logger.debug(f"Generated presigned URL for {key} (expires in {expires_seconds}s)")
            return url

        except ClientError as e:
            logger.error(f"Failed to generate presigned URL: {e}")
            return ""

    def presign_upload(
        self,
        key: str,
        content_type: str,
        expires_seconds: int = 300  # 5 minutes
    ) -> dict:
        """
        Generate presigned upload URL (for direct client uploads)

        Args:
            key: S3 object key
            content_type: MIME type
            expires_seconds: URL expiration time

        Returns:
            Dict with 'url' and 'fields' for multipart upload
        """
        try:
            response = self.s3.generate_presigned_post(
                Bucket=self.bucket_name,
                Key=key,
                Fields={
                    'Content-Type': content_type,
                    'x-amz-server-side-encryption': 'AES256'
                },
                Conditions=[
                    {'Content-Type': content_type},
                    ['content-length-range', 1, 52428800]  # 1 byte to 50 MB
                ],
                ExpiresIn=expires_seconds
            )

            logger.debug(f"Generated presigned upload URL for {key}")
            return response

        except ClientError as e:
            logger.error(f"Failed to generate presigned upload URL: {e}")
            return {}

    def delete_object(self, key: str) -> bool:
        """
        Delete object from S3

        Args:
            key: S3 object key

        Returns:
            True if successful
        """
        try:
            self.s3.delete_object(
                Bucket=self.bucket_name,
                Key=key
            )

            logger.info(f"Deleted file from S3: {key}")
            return True

        except ClientError as e:
            logger.error(f"Failed to delete from S3: {e}")
            return False

    def object_exists(self, key: str) -> bool:
        """
        Check if object exists in S3

        Args:
            key: S3 object key

        Returns:
            True if exists
        """
        try:
            self.s3.head_object(
                Bucket=self.bucket_name,
                Key=key
            )
            return True

        except ClientError:
            return False

    def get_object_metadata(self, key: str) -> Optional[dict]:
        """
        Get object metadata without downloading content

        Args:
            key: S3 object key

        Returns:
            Metadata dict or None
        """
        try:
            response = self.s3.head_object(
                Bucket=self.bucket_name,
                Key=key
            )

            return {
                'size': response['ContentLength'],
                'content_type': response.get('ContentType'),
                'last_modified': response['LastModified'],
                'metadata': response.get('Metadata', {})
            }

        except ClientError as e:
            logger.error(f"Failed to get object metadata: {e}")
            return None

    def list_objects(
        self,
        prefix: str = "",
        max_keys: int = 1000
    ) -> list:
        """
        List objects with given prefix

        Args:
            prefix: Key prefix to filter
            max_keys: Maximum number of keys to return

        Returns:
            List of object keys
        """
        try:
            response = self.s3.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=prefix,
                MaxKeys=max_keys
            )

            if 'Contents' not in response:
                return []

            return [obj['Key'] for obj in response['Contents']]

        except ClientError as e:
            logger.error(f"Failed to list objects: {e}")
            return []


# Singleton instance
s3_client = S3StorageClient() if settings.S3_BUCKET_NAME else None
