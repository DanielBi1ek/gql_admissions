import datetime

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey

from .BaseModel import BaseModel, IDType, UUIDFKey


class PaymentModel(BaseModel):
    __tablename__ = "payments"

    # Foreign keys to tables in THIS database
    application_id: Mapped[IDType] = UUIDFKey(
        ForeignKey("admission_applications.id"),
        comment="application reference"
    )
    payment_info_id: Mapped[IDType] = UUIDFKey(
        ForeignKey("admission_payment_infos.id"),
        comment="payment conditions reference"
    )
    payer_id: Mapped[IDType] = UUIDFKey(
        comment="payer user reference (no FK)"
    )
    status_id: Mapped[IDType] = UUIDFKey(
        comment="payment status reference (no FK)"
    )

    # Payment fields
    bank_unique_data: Mapped[str] = mapped_column(
        default=None,
        nullable=True,
        comment="unique bank payment identifier"
    )
    variable_symbol: Mapped[str] = mapped_column(
        default=None,
        nullable=True,
        comment="variable symbol provided by payer"
    )
    amount: Mapped[float] = mapped_column(
        default=0.0,
        nullable=True,
        comment="payment amount"
    )
    currency: Mapped[str] = mapped_column(
        default="EUR",
        nullable=True,
        comment="currency"
    )
    method: Mapped[str] = mapped_column(
        default=None,
        nullable=True,
        comment="payment method"
    )
    paid_at: Mapped[datetime.datetime] = mapped_column(
        default=None,
        nullable=True,
        comment="date of payment"
    )


    # Relationships
    application = relationship(
        "AdmissionApplicationModel",
        back_populates="payments",
        uselist=False
    )
    payment_info = relationship(
        "PaymentInfoModel",
        viewonly=True,
        uselist=False,
        lazy="joined"
    )
