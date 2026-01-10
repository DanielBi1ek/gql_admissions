from sqlalchemy.orm import Mapped, mapped_column

from .BaseModel import BaseModel


class BankStatementModel(BaseModel):
    __tablename__ = "bank_statements"

    variable_symbol: Mapped[str] = mapped_column(
        default=None,
        nullable=True,
        comment="payment variable symbol"
    )
    amount_received: Mapped[float] = mapped_column(
        default=0.0,
        nullable=True,
        comment="amount received"
    )
