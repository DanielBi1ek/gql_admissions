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
    status_id: Mapped[IDType] = UUIDFKey(
        comment="admission status reference (no FK)"
    )
    name: Mapped[str] = mapped_column(
        default=None,
        nullable=True,
        comment="name of the admission entry"
    )
    name_en: Mapped[str] = mapped_column(
        default=None,
        nullable=True,
        comment="English name of the admission entry"
    )
    program_id: Mapped[IDType] = UUIDFKey(
        ForeignKey("study_programs.id"),
        comment="study program for the admission"
    )
    payment_info_id: Mapped[IDType] = UUIDFKey(
        ForeignKey("admission_payment_infos.id"),
        comment="payment conditions reference"
    )
    application_start_date: Mapped[datetime.datetime] = mapped_column(
        default=None,
        nullable=True,
        comment="start date for applications"
    )
    application_last_date: Mapped[datetime.datetime] = mapped_column(
        default=None,
        nullable=True,
        comment="last date for application submission"
    )
    end_date: Mapped[datetime.datetime] = mapped_column(
        default=None,
        nullable=True,
        comment="end date of admission process"
    )
    condition_date: Mapped[datetime.datetime] = mapped_column(
        default=None,
        nullable=True,
        comment="deadline for fulfilling conditions"
    )
    payment_date: Mapped[datetime.datetime] = mapped_column(
        default=None,
        nullable=True,
        comment="deadline for payment"
    )
    condition_extended_date: Mapped[datetime.datetime] = mapped_column(
        default=None,
        nullable=True,
        comment="extended deadline for fulfilling conditions"
    )
    request_condition_extend_date: Mapped[datetime.datetime] = mapped_column(
        default=None,
        nullable=True,
        comment="deadline for requesting condition extension"
    )
    request_extra_conditions_date: Mapped[datetime.datetime] = mapped_column(
        default=None,
        nullable=True,
        comment="deadline for requesting extra conditions"
    )
    request_extra_date_date: Mapped[datetime.datetime] = mapped_column(
        default=None,
        nullable=True,
        comment="deadline for requesting extra exam date"
    )
    exam_start_date: Mapped[datetime.datetime] = mapped_column(
        default=None,
        nullable=True,
        comment="first possible exam date"
    )
    exam_last_date: Mapped[datetime.datetime] = mapped_column(
        default=None,
        nullable=True,
        comment="last possible exam date"
    )
    student_entry_date: Mapped[datetime.datetime] = mapped_column(
        default=None,
        nullable=True,
        comment="student entry/enrollment date"
    )

    # Relationships
    enrollment_records = relationship(
        "EnrollmentModel",
        back_populates="admission",
        uselist=True,
        cascade="save-update"
    )
    payment_info = relationship(
        "PaymentInfoModel",
        viewonly=True,
        uselist=False,
        lazy="joined"
    )
    study_program = relationship(
        "StudyProgramModel",
        viewonly=True,
        uselist=False,
        lazy="joined"
    )
