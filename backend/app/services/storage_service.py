import logging
import os
import uuid
from typing import Optional

import boto3
from botocore.config import Config
from botocore.exceptions import BotoCoreError, ClientError

from app.config import settings

logger = logging.getLogger(__name__)


class StorageService:
    def __init__(self) -> None:
        self.bucket = settings.R2_BUCKET_NAME
        self.public_url = settings.R2_PUBLIC_URL
        self.account_id = settings.R2_ACCOUNT_ID
        self.access_key = settings.R2_ACCESS_KEY_ID
        self.secret_key = settings.R2_SECRET_ACCESS_KEY
        self._client = None

    def _is_configured(self) -> bool:
        return all([self.bucket, self.account_id, self.access_key, self.secret_key])

    def _normalize_key(self, key: str) -> str:
        raw = (key or "").strip()
        if not raw:
            return ""
        if raw.startswith("http://") or raw.startswith("https://"):
            from urllib.parse import urlparse, unquote

            path = unquote(urlparse(raw).path).lstrip("/")
            if self.bucket and path.startswith(self.bucket + "/"):
                return path[len(self.bucket) + 1 :]
            return path
        raw = raw.lstrip("/")
        if self.bucket and raw.startswith(self.bucket + "/"):
            return raw[len(self.bucket) + 1 :]
        return raw

    def _get_client(self):
        if self._client is not None:
            return self._client
        endpoint_url = f"https://{self.account_id}.r2.cloudflarestorage.com"
        region = getattr(settings, "R2_REGION", None) or "auto"
        self._client = boto3.client(
            "s3",
            endpoint_url=endpoint_url,
            region_name=region,
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key,
            config=Config(
                signature_version="s3v4",
                connect_timeout=5,
                read_timeout=15,
                retries={"max_attempts": 3, "mode": "standard"},
            ),
        )
        return self._client

    def upload_bytes(
        self,
        data: bytes,
        filename: str,
        content_type: Optional[str] = None,
        prefix: str = "resumes",
    ) -> Optional[str]:
        if not self._is_configured():
            return None

        safe_name = os.path.basename(filename).replace("\\", "_").replace("/", "_")
        key = f"{prefix}/{uuid.uuid4()}_{safe_name}"
        extra = {}
        if content_type:
            extra["ContentType"] = content_type

        try:
            client = self._get_client()
            client.put_object(Bucket=self.bucket, Key=key, Body=data, **extra)
            if self.public_url:
                return f"{self.public_url.rstrip('/')}/{key}"
            return client.generate_presigned_url(
                "get_object",
                Params={"Bucket": self.bucket, "Key": key},
                ExpiresIn=3600,
            )
        except (ClientError, BotoCoreError) as exc:
            logger.exception("R2 upload failed")
            return None

    def get_url_for_key(self, key: str, disposition: Optional[str] = None, filename: Optional[str] = None) -> Optional[str]:
        if not self._is_configured():
            return None
        cleaned = self._normalize_key(key)
        if not cleaned:
            return None
        # If we need a specific Content-Disposition override (like attachment), we must bypass 
        # the direct static public URL and generate a presigned URL to inject the ResponseContentDisposition header.
        if self.public_url and not disposition:
            return f"{self.public_url.rstrip('/')}/{cleaned}"
        try:
            client = self._get_client()
            params = {"Bucket": self.bucket, "Key": cleaned}
            if disposition:
                filename_str = filename or os.path.basename(cleaned)
                params["ResponseContentDisposition"] = f'{disposition}; filename="{filename_str}"'
            return client.generate_presigned_url(
                "get_object",
                Params=params,
                ExpiresIn=3600,
            )
        except (ClientError, BotoCoreError) as exc:
            logger.exception("R2 presign failed")
            return None

    def get_object_stream(self, key: str):
        if not self._is_configured():
            return None
        cleaned = self._normalize_key(key)
        if not cleaned:
            return None
        try:
            client = self._get_client()
            obj = client.get_object(Bucket=self.bucket, Key=cleaned)
            return obj.get("Body"), obj.get("ContentLength")
        except (ClientError, BotoCoreError) as exc:
            logger.exception("R2 get_object failed")
            return None


storage_service = StorageService()
