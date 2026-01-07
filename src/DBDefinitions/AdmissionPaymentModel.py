import datetime
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .BaseModel import BaseModel, IDType, UUIDFKey


class AdmissionPaymentModel(BaseModel):
    __tablename__ = "admission_payments"

    required_amount: Mapped[float] = mapped_column(
        default=0.0,
        nullable=True,
        comment="required amount"
    )
    paid_at: Mapped[datetime.datetime] = mapped_column(
        default=None,
        nullable=True,
        comment="payment date"
    )
    bank_payment_id: Mapped[IDType] = UUIDFKey(
        ForeignKey("bank_statement_payments.id"),
        comment="reference to bank statement payment"
    )

    bank_payment = relationship(
        "BankStatementPaymentModel",
        viewonly=True,
        uselist=False,
        lazy="joined"
    )
