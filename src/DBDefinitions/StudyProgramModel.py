# StudyProgramModel.py
from sqlalchemy.orm import Mapped, mapped_column

from .BaseModel import BaseModel, IDType, UUIDFKey


class StudyProgramModel(BaseModel):
    __tablename__ = "study_programs"

    # Override rbacobject_id to be nullable
    rbacobject_id: Mapped[IDType] = UUIDFKey(comment="id rbacobject", nullable=True, default=None)
    name: Mapped[str] = mapped_column(default=None, nullable=True, comment="study program name")
    name_en: Mapped[str] = mapped_column(default=None, nullable=True, comment="study program name in English")
    code: Mapped[str] = mapped_column(default=None, nullable=True, comment="study program code")
    description: Mapped[str] = mapped_column(default=None, nullable=True, comment="study program description")
    degree_level: Mapped[str] = mapped_column(default=None, nullable=True, comment="bachelor, master, phd")
    duration_years: Mapped[int] = mapped_column(default=3, nullable=True, comment="program duration in years")
    credits: Mapped[int] = mapped_column(default=180, nullable=True, comment="total ECTS credits")