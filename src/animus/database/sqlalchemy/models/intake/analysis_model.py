from __future__ import annotations

from typing import Any

from sqlalchemy import JSON, Boolean, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from animus.database.sqlalchemy.models.model import Model


class AnalysisModel(Model):
    __tablename__ = 'analyses'

    id: Mapped[str] = mapped_column(String(26), primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    folder_id: Mapped[str | None] = mapped_column(String(26), nullable=True)
    account_id: Mapped[str] = mapped_column(String(26), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String, nullable=False)
    is_archived: Mapped[bool] = mapped_column(Boolean, nullable=False)
    precedents_search_courts: Mapped[list[str] | None] = mapped_column(
        JSON,
        nullable=True,
    )
    precedents_search_precedent_kinds: Mapped[list[str] | None] = mapped_column(
        JSON,
        nullable=True,
    )
    precedents_search_limit: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    petitions: Mapped[list[Any]] = relationship(
        'PetitionModel', back_populates='analysis'
    )
