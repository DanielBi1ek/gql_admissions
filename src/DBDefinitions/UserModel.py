from sqlalchemy.orm import Mapped, mapped_column

from .BaseModel import BaseModel


class UserModel(BaseModel):
    __tablename__ = "users"

    display_name: Mapped[str] = mapped_column(
        default=None,
        nullable=True,
        comment="user display name"
    )
