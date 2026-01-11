import sqlalchemy
from sqlalchemy.orm import Mapped, mapped_column

from .BaseModel import BaseModel


class AdmissionBankAccountModel(BaseModel):
    __tablename__ = "admission_bank_accounts"
    __table_args__ = (
        sqlalchemy.UniqueConstraint(
            "account_prefix",
            "account_number",
            "bank_code",
            name="uq_admission_bank_accounts_identity",
        ),
    )

    account_prefix: Mapped[str] = mapped_column(
        default=None,
        nullable=False,
        comment="bank account prefix"
    )
    account_number: Mapped[str] = mapped_column(
        default=None,
        nullable=False,
        comment="bank account number"
    )
    bank_code: Mapped[str] = mapped_column(
        default=None,
        nullable=False,
        comment="bank code"
    )
    description: Mapped[str] = mapped_column(
        default=None,
        nullable=True,
        comment="bank account description"
    )
