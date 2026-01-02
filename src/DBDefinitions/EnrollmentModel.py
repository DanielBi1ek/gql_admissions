from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey

from .BaseModel import BaseModel, IDType, UUIDFKey


class EnrollmentModel(BaseModel):
    __tablename__ = "enrollments_evolution"

    # Foreign keys to tables in THIS database
    admission_id: Mapped[IDType] = UUIDFKey(
        ForeignKey("admissions_evolution.id"),
        comment="foreign key to admission"
    )
    study_program_id: Mapped[IDType] = UUIDFKey(
        ForeignKey("study_programs.id"),
        comment="foreign key to study program"
    )

    # Status references external service - NO FK constraint


    # Fields
    payment: Mapped[float] = mapped_column(
        default=0.0,
        nullable=True,
        comment="enrollment payment amount"
    )

    # Relationships
    admission = relationship(
        "AdmissionModel",
        back_populates="enrollment_records",
        uselist=False
    )

    payments = relationship(
        "PaymentModel",
        back_populates="enrollment",
        uselist=True,
        cascade="save-update"
    )