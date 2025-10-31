import sqlalchemy
import datetime
from sqlalchemy.schema import Column
from sqlalchemy import Uuid, String, DateTime, ForeignKey, Float

from .baseDBModel import BaseModel
from .uuid import uuid


class AdmissionModel(BaseModel):
    __tablename__ = "admissions"

    id = Column(Uuid, primary_key=True, default=uuid)
    user_id = Column(Uuid, index=True, comment="student user id")  # no ForeignKey
    program_id = Column(Uuid, index=True, comment="program (event) id")  # no ForeignKey
    status = Column(String)
    created_at = Column(DateTime, default=datetime.datetime.now)
    lastchange = Column(DateTime, default=datetime.datetime.now)


class PaymentModel(BaseModel):
    __tablename__ = "payments"
    id = Column(Uuid, primary_key=True, comment="primary key", default=uuid)
    admission_id = Column(ForeignKey("admissions.id"), nullable=False, index=True, comment="linked admission id")
    amount = Column(Float, nullable=False, comment="payment amount")
    payment_date = Column(DateTime, default=datetime.datetime.now, comment="date when payment was made")
    lastchange = Column(DateTime, default=datetime.datetime.now)


class EnrollmentModel(BaseModel):
    __tablename__ = "enrollments"

    id = Column(Uuid, primary_key=True, default=uuid)
    user_id = Column(Uuid, index=True)
    program_id = Column(Uuid, index=True)
    start_date = Column(DateTime)
    end_date = Column(DateTime)
    lastchange = Column(DateTime, default=datetime.datetime.now)
