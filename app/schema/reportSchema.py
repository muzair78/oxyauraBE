from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, ConfigDict, EmailStr, Field


class ReportCreate(BaseModel):
    userId: UUID = Field(..., description="ID of the user who owns this report")
    documentType: str = Field(..., min_length=1, max_length=255, description="Type of the document")
    url: str = Field(..., description="URL of the document")


class ReportUpdate(BaseModel):
    documentType: str | None = Field(None, min_length=1, max_length=255, description="Type of the document")
    url: str | None = Field(None, description="URL of the document")


class ReportResponse(BaseModel):
    id: UUID
    userId: UUID
    documentType: str | None = None
    url: str
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class ReportUserInfo(BaseModel):
    id: UUID
    fullname: str
    email: EmailStr
    created_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class ReportWithUser(BaseModel):
    id: UUID
    documentName: str | None = None
    documentType: str | None = None
    url: str
    created_at: datetime | None = None
    updated_at: datetime | None = None
    user: ReportUserInfo

    model_config = ConfigDict(from_attributes=True)
