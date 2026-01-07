import datetime
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .BaseModel import BaseModel, IDType, UUIDFKey


class ExamModel(BaseModel):
    __tablename__ = "exams"

    program_id: Mapped[IDType] = UUIDFKey(
        ForeignKey("study_programs.id"),
        comment="study program reference"
    )
    application_start_date: Mapped[datetime.datetime] = mapped_column(
        default=None,
        nullable=True,
        comment="start date for applications"
    )
    application_end_date: Mapped[datetime.datetime] = mapped_column(
        default=None,
        nullable=True,
        comment="end date for applications"
    )
    payment_info_id: Mapped[IDType] = UUIDFKey(
        ForeignKey("admission_payment_infos.id"),
        comment="payment info reference"
    )

    program = relationship(
        "StudyProgramModel",
        viewonly=True,
        uselist=False,
        lazy="joined"
    )
    payment_info = relationship(
        "AdmissionPaymentInfoModel",
        viewonly=True,
        uselist=False,
        lazy="joined"
    )
