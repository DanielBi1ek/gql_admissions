from sqlalchemy.orm import Mapped, mapped_column

from sqlalchemy import ForeignKey
from .BaseModel import BaseModel, IDType, UUIDFKey


class EnrollmentModel(BaseModel):
    __tablename__ = "enrollments_evolution"

    # Keep simple non-relational columns (no foreign key constraints)
    admission_id: Mapped[IDType] = UUIDFKey(ForeignKey("admissions_evolution.id"), comment="admission reference")
    study_program_id: Mapped[IDType] = mapped_column(default=None, nullable=True, index=True, comment="program enrolled")
    status_id: Mapped[IDType] = mapped_column(default=None, nullable=True, comment="enrollment state")
