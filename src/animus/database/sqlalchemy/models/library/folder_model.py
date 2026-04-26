from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column

from animus.database.sqlalchemy.models.model import Model


class FolderModel(Model):
    __tablename__ = 'folders'

    id: Mapped[str] = mapped_column(String(26), primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    account_id: Mapped[str] = mapped_column(String(26), nullable=False, index=True)
    is_archived: Mapped[bool] = mapped_column(Boolean, nullable=False)
