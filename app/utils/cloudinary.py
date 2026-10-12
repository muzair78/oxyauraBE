import os
import uuid

from azure.storage.blob import BlobServiceClient, ContentSettings
from dotenv import load_dotenv
from fastapi import HTTPException, status

load_dotenv()

_connection_string = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
_container_name = os.getenv("AZURE_STORAGE_CONTAINER", "doctor-reports")

blob_service_client = BlobServiceClient.from_connection_string(_connection_string)
container_client = blob_service_client.get_container_client(_container_name)

ALLOWED_MIME_TYPES = {
    "application/pdf",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "image/jpeg",
    "image/png",
    "image/webp",
}

MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB


def upload_document(file_bytes: bytes, filename: str, content_type: str) -> str:
    """
    Upload a document to Azure Blob Storage and return the public URL.

    Args:
        file_bytes: Raw file content
        filename: Original filename
        content_type: MIME type of the file

    Returns:
        URL of the uploaded blob
    """
    if content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type: {content_type}. Allowed: PDF, DOC, DOCX, JPEG, PNG, WEBP.",
        )

    if len(file_bytes) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File size exceeds the 10 MB limit.",
        )

    # Use a UUID prefix to avoid name collisions
    name, ext = os.path.splitext(filename)
    blob_name = f"{name}_{uuid.uuid4().hex}{ext}"

    try:
        blob_client = container_client.get_blob_client(blob_name)
        blob_client.upload_blob(
            file_bytes,
            overwrite=False,
            content_settings=ContentSettings(content_type=content_type),
        )
        return blob_client.url
    except Exception as e:
        print(f"[Azure Upload Error] {type(e).__name__}: {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Azure Blob Storage upload failed: {str(e)}",
        )
