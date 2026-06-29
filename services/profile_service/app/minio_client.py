from minio import Minio
from minio.error import S3Error
import os
import io
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

async def upload_photo(file_data: bytes, file_name: str) -> Optional[str]:
    try:
        ensure_bucket_exists()
        
        # Check if object already exists to avoid overwriting if not desired, 
        # or just overwrite. Here we overwrite.
        minio_client.put_object(
            MINIO_BUCKET,
            file_name,
            data=io.BytesIO(file_data),
            length=len(file_data),
            content_type="image/jpeg" # Assuming JPEG for simplicity
        )
        return f"/{MINIO_BUCKET}/{file_name}"
    except S3Error as e:
        print(f"Error uploading photo to MinIO: {e}")
        return None

async def get_photo_url(file_name: str) -> Optional[str]:
    try:
        # In a real app, you might generate a presigned URL if the bucket is private
        # For now, assuming public access or internal access via endpoint
        return f"http://{MINIO_ENDPOINT}/{MINIO_BUCKET}/{file_name}"
    except Exception as e:
        print(f"Error generating photo URL: {e}")
        return None