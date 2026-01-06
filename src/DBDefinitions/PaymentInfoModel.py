from sqlalchemy.orm import Mapped, mapped_column

from .BaseModel import BaseModel


class PaymentInfoModel(BaseModel):
    __tablename__ = "admission_payment_infos"

    account_number: Mapped[str] = mapped_column(
        default=None,
        nullable=True,
        comment="account number with bank code"
    )
    specific_symbol: Mapped[str] = mapped_column(
        default=None,
        nullable=True,
        comment="specific symbol"
    )
    constant_symbol: Mapped[str] = mapped_column(
        default=None,
        nullable=True,
        comment="constant symbol"
    )
    iban: Mapped[str] = mapped_column(
        default=None,
        nullable=True,
        comment="IBAN code"
    )
    swift: Mapped[str] = mapped_column(
        default=None,
        nullable=True,
        comment="SWIFT bank code"
    )
    amount: Mapped[float] = mapped_column(
        default=None,
        nullable=True,
        comment="required payment amount"
    )
