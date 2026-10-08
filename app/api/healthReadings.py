from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from langchain_groq import ChatGroq

from app.db.connection import get_db
from app.model.healthReadings import HealthReading
from app.schema.healthReadingsSchema import (
    HealthReadingCreate,
    HealthReadingResponse,
    HealthReadingUpdate,
)


router = APIRouter(
    prefix="/health-readings",
    tags=["Health Readings"],
)


@router.post(
    "/",
    response_model=HealthReadingResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Log a health reading",
    description="Store a new daily health reading for a user.",
)
async def create_health_reading(
    body: HealthReadingCreate,
    db: AsyncSession = Depends(get_db),
):
    print("Incoming data:", body.model_dump())  # ← add this
    
    reading = HealthReading(**body.model_dump())
    db.add(reading)
    await db.commit()
    await db.refresh(reading)
    return reading


@router.get(
    "/user/{user_id}",
    response_model=HealthReadingResponse,
    status_code=status.HTTP_200_OK,
    summary="Get latest health reading for a user",
    description="Fetch the most recent health reading for a specific user.",
)
async def get_user_health_readings(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(HealthReading)
        .where(HealthReading.userId == user_id)
        .order_by(HealthReading.logged_at.desc())
        .limit(1)
    )
    reading = result.scalar_one_or_none()

    if not reading:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No health readings found for this user.",
        )

    return reading


@router.get(
    "/{reading_id}",
    response_model=HealthReadingResponse,
    status_code=status.HTTP_200_OK,
    summary="Get a single health reading",
    description="Fetch a specific health reading by its ID.",
)
async def get_health_reading(
    reading_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(HealthReading).where(HealthReading.id == reading_id)
    )
    reading = result.scalar_one_or_none()

    if not reading:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Health reading not found.",
        )

    return reading


@router.patch(
    "/{reading_id}",
    response_model=HealthReadingResponse,
    status_code=status.HTTP_200_OK,
    summary="Update a health reading",
    description="Partially update an existing health reading.",
)
async def update_health_reading(
    reading_id: UUID,
    body: HealthReadingUpdate,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(HealthReading).where(HealthReading.id == reading_id)
    )
    reading = result.scalar_one_or_none()

    if not reading:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Health reading not found.",
        )

    # Only update fields that were explicitly provided
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(reading, field, value)

    await db.commit()
    await db.refresh(reading)
    return reading


@router.delete(
    "/{reading_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete a health reading",
    description="Delete a health reading by its ID.",
)
async def delete_health_reading(
    reading_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(HealthReading).where(HealthReading.id == reading_id)
    )
    reading = result.scalar_one_or_none()

    if not reading:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Health reading not found.",
        )

    await db.delete(reading)
    await db.commit()

    return {"message": "Health reading deleted successfully."}
