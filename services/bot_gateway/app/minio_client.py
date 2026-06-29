from minio import Minio
from minio.error import S3Error
import os
from typing import Optional

MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "localhost:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "minioadmin")
MINIO_BUCKET = os.getenv("MINIO_BUCKET", "photos")

minio_client = Minio(
    MINIO_ENDPOINT,
    access_key=MINIO_ACCESS_KEY,
    secret_key=MINIO_SECRET_KEY,
    secure=False
)

def ensure_bucket_exists():
    try:
        if not minio_client.bucket_exists(MINIO_BUCKET):
            minio_client.make_bucket(MINIO_BUCKET)
    except S3Error as e:
        print(f"Error ensuring bucket exists: {e}")

async def download_photo(file_name: str) -> Optional[bytes]:
    try:
        response = minio_client.get_object(MINIO_BUCKET, file_name)
        return response.read()
    except S3Error as e:
        print(f"Error downloading photo from MinIO: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error downloading photo: {e}")
        return None