import datetime
import sqlalchemy
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .BaseModel import BaseModel, IDType, UUIDFKey


class AdmissionApplicationModel(BaseModel):
    __tablename__ = "admission_applications"

    applicant_user_id: Mapped[IDType] = UUIDFKey(
        comment="applicant user reference (no FK)"
    )
    street: Mapped[str] = mapped_column(
        default=None,
        nullable=True,
        comment="street"
    )
    house_number: Mapped[str] = mapped_column(
        default=None,
        nullable=True,
        comment="house number"
    )
    city: Mapped[str] = mapped_column(
        default=None,
        nullable=True,
        comment="city"
    )
    postal_code: Mapped[str] = mapped_column(
        default=None,
        nullable=True,
        comment="postal code"
    )
    applied_date: Mapped[datetime.datetime] = mapped_column(
        default=None,
        nullable=True,
        server_default=sqlalchemy.sql.func.now(),
        comment="date of application"
    )
    process_id: Mapped[IDType] = UUIDFKey(
        ForeignKey("admission_processes.id"),
        comment="admission process reference"
    )
    payment_id: Mapped[IDType] = UUIDFKey(
        ForeignKey("admission_payments.id"),
        comment="admission payment reference"
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
