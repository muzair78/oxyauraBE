from sqlalchemy import Column, Integer, DateTime, ForeignKey, func, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector
from app.db.connection import Base


class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id = Column(Integer, primary_key=True)
    reportId = Column(UUID(as_uuid=True), ForeignKey("reports.id", ondelete="CASCADE"), nullable=False)
    userId = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    chunkIndex = Column(Integer, nullable=False)        # order of the chunk in the document
    content = Column(Text, nullable=False)              # raw text of the chunk
    embedding = Column(Vector(384), nullable=True)      # HuggingFace all-MiniLM-L6-v2 = 384 dims

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    # Relationships
    report = relationship("Report", back_populates="chunks")
    user = relationship("User", backref="chunks")
