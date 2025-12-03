import shutil
import os
import uuid
from pathlib import Path
from fastapi import UploadFile
from abc import ABC, abstractmethod
from app.core.config import settings
from app.core.exceptions import FileError

class StorageProvider(ABC):
    @abstractmethod
    async def upload(self, file: UploadFile, directory: str) -> str:
        """Upload a file and return its public/accessible URL"""
        pass

    @abstractmethod
    async def delete(self, file_url: str) -> bool:
        """Delete a file given its URL"""
        pass

    @abstractmethod
    async def generate_download_url(self, file_url: str, original_filename: str = None) -> str:
        """Generate a secure download URL (signed URL or local stream endpoint)"""
        pass

class LocalStorageProvider(StorageProvider):
    def __init__(self, base_dir: str = "static/uploads"):
        # Use absolute path relative to backend root
        backend_root = Path(__file__).resolve().parents[2]
        self.base_dir = backend_root / base_dir
        self.base_dir.mkdir(parents=True, exist_ok=True)

    async def upload(self, file: UploadFile, directory: str) -> str:
        try:
            # Create target directory
            target_dir = self.base_dir / directory
            target_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate unique filename
            file_ext = os.path.splitext(file.filename)[1]
            unique_filename = f"{uuid.uuid4()}{file_ext}"
            file_path = target_dir / unique_filename
            
            # Save file
            # Reset file pointer to beginning just in case
            await file.seek(0)
            
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
                
            # Return "URL" - for local dev, we'll return the absolute path
            # In production with Nginx, this would be a relative URL
            return str(file_path)
            
        except Exception as e:
            raise FileError(f"Failed to save file locally: {str(e)}")

    async def delete(self, file_url: str) -> bool:
        try:
            file_path = Path(file_url)
            if file_path.exists():
                os.remove(file_path)
                return True
            return False
        except Exception as e:
            raise FileError(f"Failed to delete local file: {str(e)}")

    async def generate_download_url(self, file_url: str, original_filename: str = None) -> str:
        """
        For local storage, we return a URL to our internal download endpoint.
        The endpoint will verify the user's token and stream the file.
        Format: /api/v1/downloads/stream?path={encoded_path}&filename={name}
        """
        # In a real app, we might encrypt this path or use a token
        # For now, we'll pass the path and let the endpoint verify ownership via DB
        import urllib.parse
        encoded_path = urllib.parse.quote(file_url)
        encoded_name = urllib.parse.quote(original_filename or "document")
        return f"{settings.API_V1_STR}/downloads/stream?path={encoded_path}&filename={encoded_name}"

class S3StorageProvider(StorageProvider):
    def __init__(self):
        try:
            import boto3
            from botocore.exceptions import ClientError
        except ImportError:
            raise ImportError("boto3 is required for S3 storage. Install it with `pip install boto3`.")
            
        self.bucket_name = settings.STORAGE_BUCKET_NAME
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_REGION,
            endpoint_url=settings.AWS_ENDPOINT_URL
        )

    async def upload(self, file: UploadFile, directory: str) -> str:
        try:
            file_ext = os.path.splitext(file.filename)[1]
            unique_filename = f"{uuid.uuid4()}{file_ext}"
            key = f"{directory}/{unique_filename}"
            
            # Reset file pointer
            await file.seek(0)
            
            # Upload
            self.s3_client.upload_fileobj(
                file.file,
                self.bucket_name,
                key,
                ExtraArgs={'ContentType': file.content_type}
            )
            
            return key
            
        except Exception as e:
            raise FileError(f"Failed to upload to S3: {str(e)}")

    async def delete(self, file_url: str) -> bool:
        try:
            # file_url here is actually the key
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=file_url)
            return True
        except Exception as e:
            raise FileError(f"Failed to delete from S3: {str(e)}")

    async def generate_download_url(self, file_url: str, original_filename: str = None) -> str:
        try:
            # Generate presigned URL
            params = {
                'Bucket': self.bucket_name,
                'Key': file_url,
                'ResponseContentDisposition': f'attachment; filename="{original_filename}"' if original_filename else 'attachment'
            }
            
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params=params,
                ExpiresIn=3600  # 1 hour
            )
            return url
        except Exception as e:
            raise FileError(f"Failed to generate S3 download URL: {str(e)}")

# Factory to get the configured provider
def get_storage_provider() -> StorageProvider:
    if settings.STORAGE_TYPE.lower() in ["s3", "gcs"]:
        return S3StorageProvider()
    return LocalStorageProvider()
