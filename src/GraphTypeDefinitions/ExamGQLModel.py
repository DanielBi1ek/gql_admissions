import typing
import datetime
import strawberry

from uoishelpers.resolvers import getLoadersFromInfo, PageResolver, createInputs2, ScalarResolver
from uoishelpers.gqlpermissions import OnlyForAuthentized

from .BaseGQLModel import BaseGQLModel, IDType

AdmissionPaymentInfoGQLModel = typing.Annotated["AdmissionPaymentInfoGQLModel", strawberry.lazy(".AdmissionPaymentInfoGQLModel")]


@createInputs2
class ExamInputFilter:
    id: IDType
    program_id: IDType
    application_start_date: datetime.datetime
    application_end_date: datetime.datetime
    payment_info_id: IDType


@strawberry.federation.type(keys=["id"], description="Admission exam offer for a study program")
class ExamGQLModel(BaseGQLModel):

    @classmethod
    def getLoader(cls, info: strawberry.types.Info):
        return getLoadersFromInfo(info).ExamModel

    program_id: typing.Optional[IDType] = strawberry.field(
        default=None,
        description="study program reference",
        permission_classes=[OnlyForAuthentized]
    )
    application_start_date: typing.Optional[datetime.datetime] = strawberry.field(
        default=None,
        description="application start",
        permission_classes=[OnlyForAuthentized]
    )
    application_end_date: typing.Optional[datetime.datetime] = strawberry.field(
        default=None,
        description="application end",
        permission_classes=[OnlyForAuthentized]
    )
    payment_info_id: typing.Optional[IDType] = strawberry.field(
        default=None,
        description="payment info reference",
        permission_classes=[OnlyForAuthentized]
    )

    payment_info: typing.Optional["AdmissionPaymentInfoGQLModel"] = strawberry.field(
        description="payment info",
        permission_classes=[OnlyForAuthentized],
        resolver=ScalarResolver["AdmissionPaymentInfoGQLModel"](fkey_field_name="payment_info_id")
    )


@strawberry.type(description="Exam queries")
class ExamQuery:
    exam_by_id: typing.Optional[ExamGQLModel] = strawberry.field(
        description="get exam by id",
        permission_classes=[OnlyForAuthentized],
        resolver=ExamGQLModel.load_with_loader
    )

    exam_page: typing.List[ExamGQLModel] = strawberry.field(
        description="page of exams",
        permission_classes=[OnlyForAuthentized],
        resolver=PageResolver[ExamGQLModel](whereType=ExamInputFilter)
    )


from uoishelpers.resolvers import InsertError, UpdateError, DeleteError
from uoishelpers.gqlpermissions.LoadDataExtension import LoadDataExtension


@strawberry.input(description="Input model for creating an exam")
class ExamInsertGQLModel:
    program_id: typing.Optional[IDType] = None
    application_start_date: typing.Optional[datetime.datetime] = None
    application_end_date: typing.Optional[datetime.datetime] = None
    payment_info_id: typing.Optional[IDType] = None


@strawberry.input(description="Input model for updating an exam")
class ExamUpdateGQLModel:
    id: IDType
    lastchange: datetime.datetime
    program_id: typing.Optional[IDType] = None
    application_start_date: typing.Optional[datetime.datetime] = None
    application_end_date: typing.Optional[datetime.datetime] = None
    payment_info_id: typing.Optional[IDType] = None


@strawberry.input(description="Input model for deleting an exam")
class ExamDeleteGQLModel:
    id: IDType
    lastchange: datetime.datetime


@strawberry.type(description="Exam mutations")
class ExamMutation:
    @strawberry.mutation(description="Insert an exam", permission_classes=[OnlyForAuthentized])
    async def exam_insert(
        self,
        info: strawberry.Info,
        exam: ExamInsertGQLModel
    ) -> typing.Union[ExamGQLModel, InsertError[ExamGQLModel]]:
        from uoishelpers.resolvers import Insert

        return await Insert[ExamGQLModel].DoItSafeWay(info=info, entity=exam)

    @strawberry.mutation(
        description="Update an exam",
        permission_classes=[OnlyForAuthentized],
        extensions=[LoadDataExtension[UpdateError, ExamGQLModel]()]
    )
    async def exam_update(
        self,
        info: strawberry.Info,
        exam: ExamUpdateGQLModel,
        db_row: typing.Any
    ) -> typing.Union[ExamGQLModel, UpdateError[ExamGQLModel]]:
        from uoishelpers.resolvers import Update

        return await Update[ExamGQLModel].DoItSafeWay(info=info, entity=exam)

    @strawberry.mutation(
        description="Delete an exam",
        permission_classes=[OnlyForAuthentized],
        extensions=[LoadDataExtension[DeleteError, ExamGQLModel]()]
    )
    async def exam_delete(
        self,
        info: strawberry.Info,
        exam: ExamDeleteGQLModel,
        db_row: typing.Any
    ) -> typing.Optional[DeleteError[ExamGQLModel]]:
        from uoishelpers.resolvers import Delete

        return await Delete[ExamGQLModel].DoItSafeWay(info=info, entity=exam)
