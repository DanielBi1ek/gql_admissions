from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
import datetime

from .BaseModel import BaseModel, IDType, UUIDFKey


class AdmissionProcessModel(BaseModel):
    __tablename__ = "admission_processes"

    name: Mapped[str] = mapped_column(
        default=None,
        nullable=True,
        comment="admission process name"
    )
    name_en: Mapped[str] = mapped_column(
        default=None,
        nullable=True,
        comment="admission process name (English)"
    )
    program_id: Mapped[IDType] = UUIDFKey(
        ForeignKey("study_programs.id"),
        comment="study program for this admission process"
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
    application_end_date: Mapped[datetime.datetime] = mapped_column(
        default=None,
        nullable=True,
        comment="last date for application submission"
    )
    exam_start_date: Mapped[datetime.datetime] = mapped_column(
        default=None,
        nullable=True,
        comment="first possible exam date"
    )
    exam_end_date: Mapped[datetime.datetime] = mapped_column(
        default=None,
        nullable=True,
        comment="last possible exam date"
    )
    decision_deadline: Mapped[datetime.datetime] = mapped_column(
        default=None,
        nullable=True,
        comment="deadline for admission decision"
    )
    payment_deadline: Mapped[datetime.datetime] = mapped_column(
        default=None,
        nullable=True,
        comment="deadline for application fee payment"
    )
    enrollment_date: Mapped[datetime.datetime] = mapped_column(
        default=None,
        nullable=True,
        comment="planned enrollment date"
    )
    condition_deadline: Mapped[datetime.datetime] = mapped_column(
        default=None,
        nullable=True,
        comment="deadline for fulfilling conditions"
    )
    condition_extended_deadline: Mapped[datetime.datetime] = mapped_column(
        default=None,
        nullable=True,
        comment="extended deadline for conditions"
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
