import typing
import datetime
import strawberry

from uoishelpers.resolvers import getLoadersFromInfo, PageResolver, createInputs2, ScalarResolver
from uoishelpers.gqlpermissions import OnlyForAuthentized
from uoishelpers.resolvers import getUserFromInfo

from .BaseGQLModel import BaseGQLModel, IDType

AdmissionPaymentGQLModel = typing.Annotated["AdmissionPaymentGQLModel", strawberry.lazy(".AdmissionPaymentGQLModel")]
AdmissionApplicationGQLModel = typing.Annotated["AdmissionApplicationGQLModel", strawberry.lazy(".AdmissionApplicationGQLModel")]


@createInputs2
class AdmissionProcessInputFilter:
    id: IDType
    payment_id: IDType


@strawberry.federation.type(keys=["id"], description="Admission process that points to a pending payment")
class AdmissionProcessGQLModel(BaseGQLModel):

    @classmethod
    def getLoader(cls, info: strawberry.types.Info):
        return getLoadersFromInfo(info).AdmissionProcessModel

    payment_id: typing.Optional[IDType] = strawberry.field(
        default=None,
        description="waiting payment reference",
        permission_classes=[OnlyForAuthentized]
    )

    payment: typing.Optional["AdmissionPaymentGQLModel"] = strawberry.field(
        description="pending payment",
        permission_classes=[OnlyForAuthentized],
        resolver=ScalarResolver["AdmissionPaymentGQLModel"](fkey_field_name="payment_id")
    )
    @strawberry.field(
        description="related admission application",
        permission_classes=[OnlyForAuthentized]
    )
    async def application(self, info: strawberry.types.Info) -> typing.Optional["AdmissionApplicationGQLModel"]:
        from sqlalchemy import select
        from src.DBDefinitions import AdmissionApplicationModel
        from .AdmissionApplicationGQLModel import AdmissionApplicationGQLModel

        loader = getLoadersFromInfo(info).AdmissionApplicationModel
        stmt = select(AdmissionApplicationModel.id).where(AdmissionApplicationModel.process_id == self.id)
        result = await loader.session.execute(stmt)
        application_id = result.scalars().first()
        return None if application_id is None else AdmissionApplicationGQLModel(id=application_id)


@strawberry.type(description="Admission process queries")
class AdmissionProcessQuery:
    admission_process_by_id: typing.Optional[AdmissionProcessGQLModel] = strawberry.field(
        description="get admission process by id",
        permission_classes=[OnlyForAuthentized],
        resolver=AdmissionProcessGQLModel.load_with_loader
    )

    admission_process_page: typing.List[AdmissionProcessGQLModel] = strawberry.field(
        description="page of admission processes",
        permission_classes=[OnlyForAuthentized],
        resolver=PageResolver[AdmissionProcessGQLModel](whereType=AdmissionProcessInputFilter)
    )


from uoishelpers.resolvers import InsertError, UpdateError, DeleteError
from uoishelpers.gqlpermissions.LoadDataExtension import LoadDataExtension


@strawberry.input(description="Input model for creating an admission process")
class AdmissionProcessInsertGQLModel:
    payment_id: typing.Optional[IDType] = None


@strawberry.input(description="Input model for updating an admission process")
class AdmissionProcessUpdateGQLModel:
    id: IDType
    lastchange: datetime.datetime
    payment_id: typing.Optional[IDType] = None


@strawberry.input(description="Input model for deleting an admission process")
class AdmissionProcessDeleteGQLModel:
    id: IDType
    lastchange: datetime.datetime


@strawberry.type(description="Admission process mutations")
class AdmissionProcessMutation:
    @strawberry.mutation(description="Insert an admission process", permission_classes=[OnlyForAuthentized])
    async def admission_process_insert(
        self,
        info: strawberry.Info,
        process: AdmissionProcessInsertGQLModel
    ) -> typing.Union[AdmissionProcessGQLModel, InsertError[AdmissionProcessGQLModel]]:
        from uoishelpers.resolvers import Insert

        user = getUserFromInfo(info=info)
        process.createdby_id = user["id"]
        process.rbacobject_id = None

        return await Insert[AdmissionProcessGQLModel].DoItSafeWay(info=info, entity=process)

    @strawberry.mutation(
        description="Update an admission process",
        permission_classes=[OnlyForAuthentized],
        extensions=[LoadDataExtension[UpdateError, AdmissionProcessGQLModel]()]
    )
    async def admission_process_update(
        self,
        info: strawberry.Info,
        process: AdmissionProcessUpdateGQLModel,
        db_row: typing.Any
    ) -> typing.Union[AdmissionProcessGQLModel, UpdateError[AdmissionProcessGQLModel]]:
        from uoishelpers.resolvers import Update

        user = getUserFromInfo(info=info)
        process.changedby_id = user["id"]

        return await Update[AdmissionProcessGQLModel].DoItSafeWay(info=info, entity=process)

    @strawberry.mutation(
        description="Delete an admission process",
        permission_classes=[OnlyForAuthentized],
        extensions=[LoadDataExtension[DeleteError, AdmissionProcessGQLModel]()]
    )
    async def admission_process_delete(
        self,
        info: strawberry.Info,
        process: AdmissionProcessDeleteGQLModel,
        db_row: typing.Any
    ) -> typing.Optional[DeleteError[AdmissionProcessGQLModel]]:
        from uoishelpers.resolvers import Delete

        return await Delete[AdmissionProcessGQLModel].DoItSafeWay(info=info, entity=process)
