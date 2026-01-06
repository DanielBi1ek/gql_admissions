import typing
import datetime
import strawberry

from uoishelpers.resolvers import getLoadersFromInfo, PageResolver, createInputs2, ScalarResolver
from uoishelpers.gqlpermissions import OnlyForAuthentized
from uoishelpers.resolvers import getUserFromInfo

from .BaseGQLModel import BaseGQLModel, IDType

PaymentInfoGQLModel = typing.Annotated["PaymentInfoGQLModel", strawberry.lazy(".PaymentInfoGQLModel")]
StudyProgramGQLModel = typing.Annotated["StudyProgramGQLModel", strawberry.lazy(".StudyProgramGQLModel")]


@createInputs2
class AdmissionProcessInputFilter:
    id: IDType
    name: str
    name_en: str
    program_id: IDType
    payment_info_id: IDType
    application_start_date: datetime.datetime
    application_end_date: datetime.datetime
    exam_start_date: datetime.datetime
    exam_end_date: datetime.datetime
    decision_deadline: datetime.datetime
    payment_deadline: datetime.datetime
    enrollment_date: datetime.datetime
    condition_deadline: datetime.datetime
    condition_extended_deadline: datetime.datetime


@strawberry.federation.type(keys=["id"], description="Admission process with timelines and rules")
class AdmissionProcessGQLModel(BaseGQLModel):

    @classmethod
    def getLoader(cls, info: strawberry.types.Info):
        return getLoadersFromInfo(info).AdmissionProcessModel

    name: typing.Optional[str] = strawberry.field(default=None, description="process name", permission_classes=[OnlyForAuthentized])
    name_en: typing.Optional[str] = strawberry.field(default=None, description="process name (English)", permission_classes=[OnlyForAuthentized])
    program_id: typing.Optional[IDType] = strawberry.field(default=None, description="study program reference", permission_classes=[OnlyForAuthentized])
    payment_info_id: typing.Optional[IDType] = strawberry.field(default=None, description="payment info reference", permission_classes=[OnlyForAuthentized])

    application_start_date: typing.Optional[datetime.datetime] = strawberry.field(default=None, description="application start", permission_classes=[OnlyForAuthentized])
    application_end_date: typing.Optional[datetime.datetime] = strawberry.field(default=None, description="application end", permission_classes=[OnlyForAuthentized])
    exam_start_date: typing.Optional[datetime.datetime] = strawberry.field(default=None, description="exam start", permission_classes=[OnlyForAuthentized])
    exam_end_date: typing.Optional[datetime.datetime] = strawberry.field(default=None, description="exam end", permission_classes=[OnlyForAuthentized])
    decision_deadline: typing.Optional[datetime.datetime] = strawberry.field(default=None, description="decision deadline", permission_classes=[OnlyForAuthentized])
    payment_deadline: typing.Optional[datetime.datetime] = strawberry.field(default=None, description="payment deadline", permission_classes=[OnlyForAuthentized])
    enrollment_date: typing.Optional[datetime.datetime] = strawberry.field(default=None, description="enrollment date", permission_classes=[OnlyForAuthentized])
    condition_deadline: typing.Optional[datetime.datetime] = strawberry.field(default=None, description="conditions deadline", permission_classes=[OnlyForAuthentized])
    condition_extended_deadline: typing.Optional[datetime.datetime] = strawberry.field(default=None, description="extended conditions deadline", permission_classes=[OnlyForAuthentized])

    payment_info: typing.Optional["PaymentInfoGQLModel"] = strawberry.field(
        description="payment conditions",
        permission_classes=[OnlyForAuthentized],
        resolver=ScalarResolver["PaymentInfoGQLModel"](fkey_field_name="payment_info_id")
    )
    study_program: typing.Optional["StudyProgramGQLModel"] = strawberry.field(
        description="study program",
        permission_classes=[OnlyForAuthentized],
        resolver=ScalarResolver["StudyProgramGQLModel"](fkey_field_name="program_id")
    )


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
    name: typing.Optional[str] = None
    name_en: typing.Optional[str] = None
    program_id: typing.Optional[IDType] = None
    payment_info_id: typing.Optional[IDType] = None
    application_start_date: typing.Optional[datetime.datetime] = None
    application_end_date: typing.Optional[datetime.datetime] = None
    exam_start_date: typing.Optional[datetime.datetime] = None
    exam_end_date: typing.Optional[datetime.datetime] = None
    decision_deadline: typing.Optional[datetime.datetime] = None
    payment_deadline: typing.Optional[datetime.datetime] = None
    enrollment_date: typing.Optional[datetime.datetime] = None
    condition_deadline: typing.Optional[datetime.datetime] = None
    condition_extended_deadline: typing.Optional[datetime.datetime] = None


@strawberry.input(description="Input model for updating an admission process")
class AdmissionProcessUpdateGQLModel:
    id: IDType
    lastchange: datetime.datetime
    name: typing.Optional[str] = None
    name_en: typing.Optional[str] = None
    program_id: typing.Optional[IDType] = None
    payment_info_id: typing.Optional[IDType] = None
    application_start_date: typing.Optional[datetime.datetime] = None
    application_end_date: typing.Optional[datetime.datetime] = None
    exam_start_date: typing.Optional[datetime.datetime] = None
    exam_end_date: typing.Optional[datetime.datetime] = None
    decision_deadline: typing.Optional[datetime.datetime] = None
    payment_deadline: typing.Optional[datetime.datetime] = None
    enrollment_date: typing.Optional[datetime.datetime] = None
    condition_deadline: typing.Optional[datetime.datetime] = None
    condition_extended_deadline: typing.Optional[datetime.datetime] = None


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
