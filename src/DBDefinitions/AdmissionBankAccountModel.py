from sqlalchemy.orm import Mapped, mapped_column

from .BaseModel import BaseModel


class AdmissionBankAccountModel(BaseModel):
    __tablename__ = "admission_bank_accounts"

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
    description: Mapped[str] = mapped_column(
        default=None,
        nullable=True,
        comment="bank account description"
    )
