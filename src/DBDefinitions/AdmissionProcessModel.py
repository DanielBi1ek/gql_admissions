from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .BaseModel import BaseModel, IDType, UUIDFKey


class AdmissionProcessModel(BaseModel):
    __tablename__ = "admission_processes"

    name: Mapped[str] = mapped_column(
        default=None,
        nullable=True,
        comment="admission process name"
    )
    payment_id: Mapped[IDType] = UUIDFKey(
        ForeignKey("admission_payments.id"),
        comment="waiting admission payment reference"
    )

    payment = relationship(
        "AdmissionPaymentModel",
        viewonly=True,
        uselist=False,
        lazy="joined"
    )
