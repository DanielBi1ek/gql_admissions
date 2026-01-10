from sqlalchemy.orm import Mapped, mapped_column

from .BaseModel import BaseModel, IDType


class AdmissionApplicantModel(BaseModel):
    __tablename__ = "admission_applicants"

    applicant_user_id: Mapped[IDType] = mapped_column(
        default=None,
        nullable=True,
        comment="applicant user reference"
    )
    firstname: Mapped[str] = mapped_column(
        default=None,
        nullable=True,
        comment="applicant first name"
    )
    lastname: Mapped[str] = mapped_column(
        default=None,
        nullable=True,
        comment="applicant last name"
    )
    street: Mapped[str] = mapped_column(
        default=None,
        nullable=True,
        comment="street"
    )
    house_number: Mapped[str] = mapped_column(
        default=None,
        nullable=True,
        comment="house number"
    )
    city: Mapped[str] = mapped_column(
        default=None,
        nullable=True,
        comment="city"
    )
    phone_number: Mapped[str] = mapped_column(
        default=None,
        nullable=True,
        comment="phone number"
    )
    email: Mapped[str] = mapped_column(
        default=None,
        nullable=True,
        comment="email address"
    )
    databox_number: Mapped[str] = mapped_column(
        default=None,
        nullable=True,
        comment="databox number"
    )
