from __future__ import annotations

from datetime import datetime  # noqa: TC003
from typing import Any

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from animus.database.sqlalchemy.models.model import Model


class AnalysisDocumentModel(Model):
    __tablename__ = 'analysis_documents'

    analysis_id: Mapped[str] = mapped_column(
        String(26),
        ForeignKey('analyses.id', ondelete='CASCADE'),
        primary_key=True,
    )
    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    document_file_path: Mapped[str] = mapped_column(String, nullable=False)
    document_name: Mapped[str] = mapped_column(String, nullable=False)

    analysis: Mapped[Any] = relationship('AnalysisModel', back_populates='document')
