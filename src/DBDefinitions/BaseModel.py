import uuid
import sqlalchemy
import datetime

from sqlalchemy import ForeignKey
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import MappedAsDataclass, Mapped, mapped_column

def UUIDFKey(ForeignKeyArg=None, **kwargs):
    # Allow passing a ForeignKey object or string as positional arg to mapped_column
    args = ()
    if ForeignKeyArg is not None:
        args = (ForeignKeyArg,)
    newkwargs = {
        **kwargs,
        "index": True, 
        "primary_key": False, 
        "default": None,
        "nullable": True,
        "comment": kwargs.get("comment", "foreign key")
    }
    return mapped_column(*args, **newkwargs)

def UUIDColumn(**kwargs):
    newkwargs = {
        **kwargs,
        "index": True,
        "primary_key": True,
        "default_factory": uuid.uuid4,
        "comment": "primary key"
    }
    return mapped_column(**newkwargs)

###########################################################################################################################
#
# zde definujte sve SQLAlchemy modely
# je-li treba, muzete definovat modely obsahujici jen id polozku, na ktere se budou odkazovat
#

IDType = uuid.UUID

class BaseModel(MappedAsDataclass, DeclarativeBase):
    id: Mapped[IDType] = UUIDColumn(index=True, primary_key=True, default_factory=uuid.uuid4)

    created: Mapped[datetime.datetime] = mapped_column(
        default=None,
        nullable=True,
        server_default=sqlalchemy.sql.func.now(),
        comment="date time of creation"
    )
    lastchange: Mapped[datetime.datetime] = mapped_column(
        default=None,
        nullable=True,
        server_default=sqlalchemy.sql.func.now(),
        comment="date time stamp"
    )

    # REMOVE ForeignKey constraints - users table is in gql_ug service
    createdby_id: Mapped[IDType] = UUIDFKey(
        comment="id of user who created this entity (no FK)"
    )
    changedby_id: Mapped[IDType] = UUIDFKey(
        comment="id of user who changed this entity (no FK)"
    )
    rbacobject_id: Mapped[IDType] = UUIDFKey(
        comment="id rbacobject (no FK)"
    )