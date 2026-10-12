import uuid
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.connection import get_db
from app.model.reports import Report
from app.model.document_chunks import DocumentChunk
from app.schema.reportSchema import ReportResponse, ReportWithUser
from app.utils.cloudinary import upload_document
from app.utils.text_extractor import extract_text
from app.utils.text_splitter import split_text
from app.utils.embeddings import get_embeddings

router = APIRouter(
    prefix="/reports",
    tags=["Reports"],
)


@router.post(
    "/upload",
    response_model=ReportResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a document",
    description="Upload a document file to Cloudinary, extract text, split into chunks, embed and store in pgvector.",
)
async def upload_report(
    userId: str = Form(..., description="UUID of the user uploading the document"),
    documentType: str = Form(..., description="Type of the document"),
    file: UploadFile = File(..., description="Document file to upload (PDF, DOC, DOCX, JPEG, PNG, WEBP)"),
    db: AsyncSession = Depends(get_db),
):
    # Validate userId is a proper UUID
    try:
        user_uuid = uuid.UUID(userId)
    except ValueError as e:
        print(f"[Upload Error] Invalid userId: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid userId. Must be a valid UUID.",
        )

    # 1. Read file bytes
    file_bytes = await file.read()

    # 2. Upload to Cloudinary and get secure URL
    url = upload_document(
        file_bytes=file_bytes,
        filename=file.filename,
        content_type=file.content_type,
    )

    # 3. Save report record in DB
    report = Report(
        userId=user_uuid,
        documentName=file.filename,
        documentType=documentType.strip(),
        url=url,
    )
    db.add(report)
    await db.flush()        # get report.id without full commit yet
    await db.refresh(report)

    # 4. Extract text from file
    try:
        raw_text = extract_text(
            file_bytes=file_bytes,
            content_type=file.content_type,
            filename=file.filename,
        )
    except ValueError as e:
        # Unsupported file type for text extraction — skip vectorization
        raw_text = ""
        print(f"[Upload Error] Text extraction failed: {e}")

    # 5. Split → embed → store chunks if text was extracted
    if raw_text.strip():
        chunks = split_text(raw_text)

        if chunks:
            # 6. Generate embeddings for all chunks in one API call
            embeddings = get_embeddings(chunks)

            # 7. Bulk insert document_chunks
            chunk_rows = [
                DocumentChunk(
                    reportId=report.id,
                    userId=user_uuid,
                    chunkIndex=idx,
                    content=chunk,
                    embedding=embedding,
                )
                for idx, (chunk, embedding) in enumerate(zip(chunks, embeddings))
            ]
            db.add_all(chunk_rows)

    # 8. Commit everything together
    await db.commit()
    await db.refresh(report)

    return report


@router.get(
    "/user/{user_id}",
    response_model=list[ReportResponse],
    status_code=status.HTTP_200_OK,
    summary="Get all reports for a user",
    description="Fetch all document reports belonging to a specific user.",
)
async def get_user_reports(
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Report).where(Report.userId == user_id).order_by(Report.created_at.desc())
    )
    reports = result.scalars().all()
    return reports


@router.delete(
    "/{report_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete a report",
    description="Delete a report record by its ID.",
)
async def delete_report(
    report_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Report).where(Report.id == report_id))
    report = result.scalar_one_or_none()

    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found.",
        )

    await db.delete(report)
    await db.commit()

    return {"message": "Report deleted successfully."}


@router.get(
    "/all",
    response_model=list[ReportWithUser],
    status_code=status.HTTP_200_OK,
    summary="Get all reports with user data",
    description="Fetch all reports across all users, each including the related user's information.",
)
async def get_all_reports(
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Report).order_by(Report.created_at.desc())
    )
    reports = result.scalars().all()
    return reports
