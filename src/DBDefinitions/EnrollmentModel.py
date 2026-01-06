import datetime

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey

from .BaseModel import BaseModel, IDType, UUIDFKey


class EnrollmentModel(BaseModel):
    __tablename__ = "enrollments"

    # Foreign keys to tables in THIS database
    application_id: Mapped[IDType] = UUIDFKey(
        ForeignKey("admission_applications.id"),
        comment="foreign key to admission application"
    )
    study_program_id: Mapped[IDType] = UUIDFKey(
        ForeignKey("study_programs.id"),
        comment="foreign key to study program"
    )

    status_id: Mapped[IDType] = UUIDFKey(
        comment="enrollment status reference (no FK)"
    )


    # Fields
    enrolled_at: Mapped[datetime.datetime] = mapped_column(
        default=None,
        nullable=True,
        comment="enrollment date"
    )

    # Relationships
    application = relationship(
        "AdmissionApplicationModel",
        back_populates="enrollments",
        uselist=False
    )
    study_program = relationship(
        "StudyProgramModel",
        viewonly=True,
        uselist=False,
        lazy="joined"
    )
