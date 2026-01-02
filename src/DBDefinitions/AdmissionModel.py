from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
import datetime
import sqlalchemy

from .BaseModel import BaseModel, IDType, UUIDFKey


class AdmissionModel(BaseModel):
    __tablename__ = "admissions_evolution"

    # Admission fields
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
 # Relationships
    enrollment_records = relationship(
        "EnrollmentModel",
        back_populates="admission",
        uselist=True,
        cascade="save-update"
    )