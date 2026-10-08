import os

import cloudinary
import cloudinary.uploader
from dotenv import load_dotenv
from fastapi import HTTPException, status

load_dotenv()

cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET"),
    secure=True,
)

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
    Upload a document to Cloudinary and return the secure URL.

    Args:
        file_bytes: Raw file content
        filename: Original filename (used as public_id)
        content_type: MIME type of the file

    Returns:
        Secure URL of the uploaded file
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

    # Strip extension for public_id; Cloudinary appends its own
    public_id = os.path.splitext(filename)[0]

    try:
        result = cloudinary.uploader.upload(
            file_bytes,
            public_id=public_id,
            folder="doctor/reports",
            resource_type="auto",
            overwrite=False,
            unique_filename=True,
        )
        return result["secure_url"]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Cloudinary upload failed: {str(e)}",
        )
