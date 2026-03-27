from sqlalchemy import Boolean, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from animus.database.sqlalchemy.models.model import Model


class AnalysisModel(Model):
    __tablename__ = 'analyses'

    id: Mapped[str] = mapped_column(String(26), primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    folder_id: Mapped[str | None] = mapped_column(String(26), nullable=True)
    account_id: Mapped[str] = mapped_column(String(26), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String, nullable=False)
    is_archived: Mapped[bool] = mapped_column(Boolean, nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
