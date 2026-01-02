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

    # Payment fields
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
    payment_date: Mapped[str] = mapped_column(
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