from sqlalchemy.orm import Mapped, mapped_column

from .BaseModel import BaseModel, IDType


class AdmissionApplicantModel(BaseModel):
    __tablename__ = "admission_applicants"

    applicant_user_id: Mapped[IDType] = mapped_column(
        default=None,
        nullable=False,
        unique=True,
        index=True,
        comment="applicant user reference"
    )
    firstname: Mapped[str] = mapped_column(
        default=None,
        nullable=False,
        comment="applicant first name"
    )
    lastname: Mapped[str] = mapped_column(
        default=None,
        nullable=False,
        comment="applicant last name"
    )
    street: Mapped[str] = mapped_column(
        default=None,
        nullable=False,
        comment="street"
    )
    house_number: Mapped[str] = mapped_column(
        default=None,
        nullable=False,
        comment="house number"
    )
    city: Mapped[str] = mapped_column(
        default=None,
        nullable=False,
        comment="city"
    )
    phone_number: Mapped[str] = mapped_column(
        default=None,
        nullable=False,
        comment="phone number"
    )
    email: Mapped[str] = mapped_column(
        default=None,
        nullable=False,
        comment="email address"
    )
    databox_number: Mapped[str] = mapped_column(
        default=None,
        nullable=True,
        comment="databox number"
    )
