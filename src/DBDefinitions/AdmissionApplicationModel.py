import datetime
import sqlalchemy
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .BaseModel import BaseModel, IDType, UUIDFKey


class AdmissionApplicationModel(BaseModel):
    __tablename__ = "admission_applications"

    process_id: Mapped[IDType] = UUIDFKey(
        ForeignKey("admission_processes.id"),
        comment="admission process reference"
    )
    applicant_user_id: Mapped[IDType] = UUIDFKey(
        comment="applicant user reference (no FK)"
    )
    applicant_name: Mapped[str] = mapped_column(
        default=None,
        nullable=True,
        comment="applicant full name"
    )
    applicant_email: Mapped[str] = mapped_column(
        default=None,
        nullable=True,
        comment="applicant email"
    )
    applied_date: Mapped[datetime.datetime] = mapped_column(
        default=None,
        nullable=True,
        server_default=sqlalchemy.sql.func.now(),
        comment="date of application"
    )
    status_id: Mapped[IDType] = UUIDFKey(
        comment="application status reference (no FK)"
    )

    process = relationship(
        "AdmissionProcessModel",
        viewonly=True,
        uselist=False,
        lazy="joined"
    )
    enrollments = relationship(
        "EnrollmentModel",
        back_populates="application",
        uselist=True,
        cascade="save-update"
    )
    payments = relationship(
        "PaymentModel",
        back_populates="application",
        uselist=True,
        cascade="save-update"
    )
