from sqlalchemy.orm import Mapped, mapped_column
import datetime

from .BaseModel import BaseModel, IDType


class AdmissionModel(BaseModel):
    __tablename__ = "admissions_evolution"

    # Simple non-relational admission model
    applicant_name: Mapped[str] = mapped_column(default=None, nullable=True, comment="applicant full name")
    applicant_email: Mapped[str] = mapped_column(default=None, nullable=True, comment="applicant email")
    status: Mapped[str] = mapped_column(default="pending", nullable=True, comment="admission status")
