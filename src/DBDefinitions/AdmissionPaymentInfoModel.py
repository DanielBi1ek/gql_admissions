from sqlalchemy.orm import Mapped, mapped_column

from .BaseModel import BaseModel


class AdmissionPaymentInfoModel(BaseModel):
    __tablename__ = "admission_payment_infos"

    account_prefix: Mapped[str] = mapped_column(
        default=None,
        nullable=True,
        comment="bank account prefix"
    )
    account_number: Mapped[str] = mapped_column(
        default=None,
        nullable=True,
        comment="bank account number"
    )
    bank_code: Mapped[str] = mapped_column(
        default=None,
        nullable=True,
        comment="bank code"
    )
    required_amount: Mapped[float] = mapped_column(
        default=0.0,
        nullable=True,
        comment="required amount"
    )
