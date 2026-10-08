from datetime import datetime
from decimal import Decimal
from uuid import UUID
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class HealthReadingCreate(BaseModel):
    userId: UUID = Field(..., description="ID of the user logging the reading")
    weight_kg: Optional[Decimal] = Field(None, ge=0, le=500, description="Weight in kilograms")
    bp_systolic: Optional[int] = Field(None, ge=0, le=300, description="Systolic blood pressure in mmHg")
    bp_diastolic: Optional[int] = Field(None, ge=0, le=200, description="Diastolic blood pressure in mmHg")
    blood_sugar_mgdl: Optional[Decimal] = Field(None, ge=0, le=2000, description="Blood sugar in mg/dL")
    sugar_context: Optional[str] = Field(None, pattern="^(fasting|before_meal|after_meal)$", description="Context of blood sugar reading")
    oxygen_spo2: Optional[Decimal] = Field(None, ge=0, le=100, description="Oxygen saturation percentage")
    heart_rate_bpm: Optional[int] = Field(None, ge=0, le=300, description="Heart rate in beats per minute")
    notes: Optional[str] = Field(None, max_length=255, description="Optional notes")
    logged_at: datetime = Field(..., description="Date and time of the measurement")


class HealthReadingResponse(BaseModel):
    id: UUID
    userId: UUID
    weight_kg: Optional[Decimal] = None
    bp_systolic: Optional[int] = None
    bp_diastolic: Optional[int] = None
    blood_sugar_mgdl: Optional[Decimal] = None
    sugar_context: Optional[str] = None
    oxygen_spo2: Optional[Decimal] = None
    heart_rate_bpm: Optional[int] = None
    notes: Optional[str] = None
    logged_at: datetime
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class HealthReadingUpdate(BaseModel):
    weight_kg: Optional[Decimal] = Field(None, ge=0, le=500)
    bp_systolic: Optional[int] = Field(None, ge=0, le=300)
    bp_diastolic: Optional[int] = Field(None, ge=0, le=200)
    blood_sugar_mgdl: Optional[Decimal] = Field(None, ge=0, le=2000)
    sugar_context: Optional[str] = Field(None, pattern="^(fasting|before_meal|after_meal)$")
    oxygen_spo2: Optional[Decimal] = Field(None, ge=0, le=100)
    heart_rate_bpm: Optional[int] = Field(None, ge=0, le=300)
    notes: Optional[str] = Field(None, max_length=255)
    logged_at: Optional[datetime] = None
