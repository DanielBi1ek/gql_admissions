# StateModel.py
from sqlalchemy.orm import Mapped, mapped_column, relationship
import datetime
import sqlalchemy

from .BaseModel import BaseModel, IDType, UUIDFKey
import enum
class StateCategoryEnum(str, enum.Enum):
    ENROLLMENT_STATUS = "enrollment_status"
    PAYMENT_STATUS = "payment_status"
    EVENT_STATUS = "event_status"
    ADMISSION_STATUS = "admission_status"
class StateModel(BaseModel):
    __tablename__ = "states"

    name: Mapped[str] = mapped_column(default=None, nullable=True, comment="state name")
    description: Mapped[str] = mapped_column(default=None, nullable=True, comment="state description")
    category: Mapped[StateCategoryEnum] = mapped_column(
        sqlalchemy.Enum(StateCategoryEnum),
        default=StateCategoryEnum.ENROLLMENT_STATUS,
        nullable=True,
        comment="category of the state"
    )
    is_active: Mapped[bool] = mapped_column(
        default=True,
        nullable=True,
        comment="is the state active"
    )
