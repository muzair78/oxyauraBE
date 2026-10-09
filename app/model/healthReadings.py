import uuid
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, func, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.types import DECIMAL
from sqlalchemy.orm import relationship
from app.db.connection import Base


class HealthReading(Base):
    __tablename__ = "health_readings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    userId = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    weight_kg = Column(DECIMAL(5, 2), nullable=True)            # e.g. 72.50 kg
    bp_systolic = Column(Integer, nullable=True)                # e.g. 120 mmHg
    bp_diastolic = Column(Integer, nullable=True)               # e.g. 80 mmHg
    blood_sugar_mgdl = Column(DECIMAL(5, 2), nullable=True)     # e.g. 95.00 mg/dL
    sugar_context = Column(String(30), nullable=True)           # 'fasting' | 'before_meal' | 'after_meal'
    oxygen_spo2 = Column(DECIMAL(4, 1), nullable=True)          # e.g. 98.5 %
    heart_rate_bpm = Column(Integer, nullable=True)             # e.g. 72 bpm
    notes = Column(String(255), nullable=True)                  # optional entry notes

    logged_at = Column(DateTime(timezone=True), nullable=False) # user-selected measurement date/time
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationship
    user = relationship("User", backref="health_readings")
