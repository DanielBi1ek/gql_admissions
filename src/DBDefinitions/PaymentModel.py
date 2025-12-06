from sqlalchemy.orm import Mapped, mapped_column

from sqlalchemy import ForeignKey
from .BaseModel import BaseModel, IDType, UUIDFKey


class PaymentModel(BaseModel):
    __tablename__ = "payments_evolution"

    # simple non-relational payment model — keep ids as plain UUID columns
    enrollment_id: Mapped[IDType] = UUIDFKey(ForeignKey("enrollments_evolution.id"), comment="enrollment reference")
    amount: Mapped[float] = mapped_column(default=0.0, nullable=True, comment="payment amount")
    currency: Mapped[str] = mapped_column(default="EUR", nullable=True, comment="currency")
    method: Mapped[str] = mapped_column(default=None, nullable=True, comment="payment method")
    status_id: Mapped[IDType] = mapped_column(default=None, nullable=True, comment="payment state")
