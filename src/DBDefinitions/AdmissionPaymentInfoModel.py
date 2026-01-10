from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .BaseModel import BaseModel, IDType, UUIDFKey


class AdmissionPaymentInfoModel(BaseModel):
    __tablename__ = "admission_payment_infos"

    required_amount: Mapped[float] = mapped_column(
        default=0.0,
        nullable=True,
        comment="required amount"
    )
    bank_account_id: Mapped[IDType] = UUIDFKey(
        ForeignKey("admission_bank_accounts.id"),
        comment="bank account reference"
    )

    bank_account = relationship(
        "AdmissionBankAccountModel",
        viewonly=True,
        uselist=False,
        lazy="joined"
    )
