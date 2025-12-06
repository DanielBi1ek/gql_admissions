from sqlalchemy.orm import Mapped, mapped_column

from .BaseModel import BaseModel, IDType


class UserModel(BaseModel):
    __tablename__ = "users"

    # Minimal placeholder: only inheriting BaseModel.id and audit fields is enough
    # Add a display name for convenience
    display_name: Mapped[str] = mapped_column(default=None, nullable=True, comment="user display name")

