import sqlalchemy
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .BaseModel import BaseModel, IDType, UUIDFKey


class AdmissionPaymentInfoModel(BaseModel):
    __tablename__ = "admission_payment_infos"
    __table_args__ = (
        sqlalchemy.CheckConstraint(
            "required_amount > 0",
            name="ck_admission_payment_infos_required_amount_gt0"
        ),
    )

    required_amount: Mapped[float] = mapped_column(
        default=0.0,
        nullable=False,
        comment="required amount"
    )
    bank_account_id: Mapped[IDType] = UUIDFKey(
        ForeignKey("admission_bank_accounts.id"),
        nullable=False,
        comment="bank account reference"
    )

    bank_account = relationship(
        "AdmissionBankAccountModel",
        viewonly=True,
        uselist=False,
        lazy="joined"
    )
