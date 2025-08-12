from __future__ import annotations

import boto3

from app.core.config import get_settings

settings = get_settings()

session = boto3.session.Session(
    aws_access_key_id=settings.s3_access_key,
    aws_secret_access_key=settings.s3_secret_key,
)
s3 = session.client("s3", endpoint_url=settings.s3_endpoint_url)

ALLOWED_CT = {"application/pdf", "image/png", "image/jpeg", "text/plain"}


def presign_get(key: str, expires: int = 300) -> str:
    return s3.generate_presigned_url(
        "get_object",
        Params={"Bucket": settings.s3_bucket, "Key": key},
        ExpiresIn=int(expires),
    )


def presign_put(key: str, content_type: str, expires: int = 300) -> str:
    if content_type not in ALLOWED_CT:
        raise ValueError("disallowed content type")
    return s3.generate_presigned_url(
        "put_object",
        Params={
            "Bucket": settings.s3_bucket,
            "Key": key,
            "ContentType": content_type,
        },
        ExpiresIn=int(expires),
    )


