import datetime
import sqlalchemy
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .BaseModel import BaseModel, IDType, UUIDFKey


class AdmissionApplicationModel(BaseModel):
    __tablename__ = "admission_applications"

    applicant_id: Mapped[IDType] = UUIDFKey(
        ForeignKey("admission_applicants.id"),
        comment="applicant reference"
    )
    applied_date: Mapped[datetime.datetime] = mapped_column(
        default=None,
        nullable=True,
        server_default=sqlalchemy.sql.func.now(),
        comment="date of application"
    )
    accepted: Mapped[bool] = mapped_column(
        default=False,
        nullable=False,
        comment="application accepted by study office"
    )
    accepted_at: Mapped[datetime.datetime] = mapped_column(
        default=None,
        nullable=True,
        comment="date of application acceptance"
    )
    acceptedby_id: Mapped[IDType] = UUIDFKey(
        comment="user who accepted application (no FK)"
    )

    process_id: Mapped[IDType] = UUIDFKey(
        ForeignKey("admission_processes.id"),
        comment="admission process reference"
    )
    payment_id: Mapped[IDType] = UUIDFKey(
        ForeignKey("admission_payments.id"),
        comment="admission payment reference"
    )
    offer_id: Mapped[IDType] = UUIDFKey(
        ForeignKey("admission_offers.id"),
        comment="admission offer reference"
    )


    process = relationship(
        "AdmissionProcessModel",
        viewonly=True,
        uselist=False,
        lazy="joined"
    )
    payment = relationship(
        "AdmissionPaymentModel",
        viewonly=True,
        uselist=False,
        lazy="joined"
    )
    offer = relationship(
        "AdmissionOfferModel",
        viewonly=True,
        uselist=False,
        lazy="joined"
    )
    applicant = relationship(
        "AdmissionApplicantModel",
        viewonly=True,
        uselist=False,
        lazy="joined"
    )
