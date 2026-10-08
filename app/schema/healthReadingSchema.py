from datetime import datetime
from decimal import Decimal
from uuid import UUID
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field


# Valid sugar context values
SugarContext = Literal["fasting", "before_meal", "after_meal"]


class HealthReadingCreate(BaseModel):
    userId: UUID = Field(..., description="UUID of the user logging the reading")
    weight_kg: Decimal | None = Field(None, ge=0, le=999.99, decimal_places=2, description="Weight in kg")
    bp_systolic: int | None = Field(None, ge=0, le=999, description="Systolic blood pressure (mmHg)")
    bp_diastolic: int | None = Field(None, ge=0, le=999, description="Diastolic blood pressure (mmHg)")
    blood_sugar_mgdl: Decimal | None = Field(None, ge=0, le=999.99, decimal_places=2, description="Blood glucose (mg/dL)")
    sugar_context: SugarContext | None = Field(None, description="Context: fasting, before_meal, after_meal")
    oxygen_spo2: Decimal | None = Field(None, ge=0, le=100, decimal_places=1, description="Oxygen saturation (%)")
    heart_rate_bpm: int | None = Field(None, ge=0, le=999, description="Heart rate (bpm)")
    notes: str | None = Field(None, max_length=255, description="Optional notes")
    logged_at: datetime = Field(..., description="Date/time when the reading was taken")


class HealthReadingUpdate(BaseModel):
    weight_kg: Decimal | None = Field(None, ge=0, le=999.99, decimal_places=2)
    bp_systolic: int | None = Field(None, ge=0, le=999)
    bp_diastolic: int | None = Field(None, ge=0, le=999)
    blood_sugar_mgdl: Decimal | None = Field(None, ge=0, le=999.99, decimal_places=2)
    sugar_context: SugarContext | None = None
    oxygen_spo2: Decimal | None = Field(None, ge=0, le=100, decimal_places=1)
    heart_rate_bpm: int | None = Field(None, ge=0, le=999)
    notes: str | None = Field(None, max_length=255)
    logged_at: datetime | None = None


class HealthReadingResponse(BaseModel):
    id: UUID
    userId: UUID
    weight_kg: Decimal | None = None
    bp_systolic: int | None = None
    bp_diastolic: int | None = None
    blood_sugar_mgdl: Decimal | None = None
    sugar_context: str | None = None
    oxygen_spo2: Decimal | None = None
    heart_rate_bpm: int | None = None
    notes: str | None = None
    logged_at: datetime
    created_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)
