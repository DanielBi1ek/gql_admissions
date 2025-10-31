import uuid
import strawberry
import datetime
import typing
import asyncio

from utils.Dataloaders import getLoadersFromInfo
from .userGQLModel import UserGQLModel  # if you have it
from .eventGQLModel import EventGQLModel

@strawberry.federation.type(
    keys=["id"],
    description="""Entity representing an admission record""",
)
class AdmissionGQLModel:
    @classmethod
    async def resolve_reference(cls, info: strawberry.types.Info, id: uuid.UUID):
        if id is not None:
            loaders = getLoadersFromInfo(info)
            admissionloader = loaders.admissions
            return await admissionloader.load(id=id)
        return None

    # Fields (must match AdmissionModel columns)
    id: uuid.UUID
    user_id: uuid.UUID
    program_id: uuid.UUID
    status: str
    created_at: datetime.datetime
    lastchange: typing.Optional[datetime.datetime]

    @strawberry.field(description="linked user")
    async def user(self, info: strawberry.types.Info) -> typing.Optional[UserGQLModel]:
        loaders = getLoadersFromInfo(info)
        return await UserGQLModel.resolve_reference(info=info, id=self.user_id)

    @strawberry.field(description="linked program/event")
    async def program(self, info: strawberry.types.Info) -> typing.Optional[EventGQLModel]:
        loaders = getLoadersFromInfo(info)
        return await EventGQLModel.resolve_reference(info=info, id=self.program_id)


@strawberry.field(description="returns admission by ID")
async def admission_by_id(info: strawberry.types.Info, id: uuid.UUID) -> typing.Optional[AdmissionGQLModel]:
    return await AdmissionGQLModel.resolve_reference(info, id)

@strawberry.input(description="input model for admission insert")
class AdmissionInsertGQLModel:
    user_id: uuid.UUID
    program_id: uuid.UUID
    status: str = strawberry.field(default="pending")
    created_at: typing.Optional[datetime.datetime] = strawberry.field(
        default_factory=lambda: datetime.datetime.now()
    )

@strawberry.input(description="input model for admission update")
class AdmissionUpdateGQLModel:
    id: uuid.UUID
    lastchange: datetime.datetime
    status: typing.Optional[str] = None

@strawberry.type(description="result of admission mutation")
class AdmissionResultGQLModel:
    id: typing.Optional[uuid.UUID]
    msg: str

    @strawberry.field(description="returns the admission")
    async def admission(self, info: strawberry.types.Info) -> typing.Optional[AdmissionGQLModel]:
        return await AdmissionGQLModel.resolve_reference(info, self.id)


@strawberry.mutation(description="insert new admission")
async def admission_insert(
    self, info: strawberry.types.Info, admission: AdmissionInsertGQLModel
) -> AdmissionResultGQLModel:
    loader = getLoadersFromInfo(info).admissions
    row = await loader.insert(admission)
    return AdmissionResultGQLModel(id=row.id, msg="ok")


@strawberry.mutation(description="update admission")
async def admission_update(
    self, info: strawberry.types.Info, admission: AdmissionUpdateGQLModel
) -> AdmissionResultGQLModel:
    loader = getLoadersFromInfo(info).admissions
    row = await loader.update(admission)
    msg = "ok" if row else "fail"
    return AdmissionResultGQLModel(id=admission.id, msg=msg)

