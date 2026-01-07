from sqlalchemy.orm import Mapped, mapped_column

from .BaseModel import BaseModel


class StudyProgramModel(BaseModel):
    __tablename__ = "study_programs"

    name: Mapped[str] = mapped_column(
        default=None,
        nullable=True,
        comment="study program name"
    )
