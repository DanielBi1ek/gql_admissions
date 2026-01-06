import datetime

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey

from .BaseModel import BaseModel, IDType, UUIDFKey


class PaymentModel(BaseModel):
    __tablename__ = "payments_evolution"

    # Foreign keys to tables in THIS database
    enrollment_id: Mapped[IDType] = UUIDFKey(
        ForeignKey("enrollments_evolution.id"),
        comment="enrollment reference"
    )
    payment_info_id: Mapped[IDType] = UUIDFKey(
        ForeignKey("admission_payment_infos.id"),
        comment="payment conditions reference"
    )
    student_id: Mapped[IDType] = UUIDFKey(
        comment="identified application/student reference (no FK)"
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
    payment_date: Mapped[datetime.datetime] = mapped_column(
        default=None,
        nullable=True,
        comment="date of payment"
    )


    # Relationships
    enrollment = relationship(
        "EnrollmentModel",
        back_populates="payments",
        uselist=False
    )
    payment_info = relationship(
        "PaymentInfoModel",
        viewonly=True,
        uselist=False,
        lazy="joined"
    )
