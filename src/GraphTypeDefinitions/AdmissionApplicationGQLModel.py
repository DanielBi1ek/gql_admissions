import typing
import datetime
import strawberry

from uoishelpers.resolvers import getLoadersFromInfo, PageResolver, createInputs2, VectorResolver, ScalarResolver
from uoishelpers.gqlpermissions import OnlyForAuthentized
from uoishelpers.resolvers import getUserFromInfo

from .BaseGQLModel import BaseGQLModel, IDType

AdmissionProcessGQLModel = typing.Annotated["AdmissionProcessGQLModel", strawberry.lazy(".AdmissionProcessGQLModel")]
EnrollmentGQLModel = typing.Annotated["EnrollmentGQLModel", strawberry.lazy(".EnrollmentGQLModel")]
EnrollmentInputFilter = typing.Annotated["EnrollmentInputFilter", strawberry.lazy(".EnrollmentGQLModel")]
PaymentGQLModel = typing.Annotated["PaymentGQLModel", strawberry.lazy(".PaymentGQLModel")]
PaymentInputFilter = typing.Annotated["PaymentInputFilter", strawberry.lazy(".PaymentGQLModel")]


@createInputs2
class AdmissionApplicationInputFilter:
    id: IDType
    process_id: IDType
    applicant_user_id: IDType
    applicant_name: str
    applicant_email: str
    applied_date: datetime.datetime
    status_id: IDType


@strawberry.federation.type(keys=["id"], description="Admission application by a specific applicant")
class AdmissionApplicationGQLModel(BaseGQLModel):

    @classmethod
    def getLoader(cls, info: strawberry.types.Info):
        return getLoadersFromInfo(info).AdmissionApplicationModel

    process_id: typing.Optional[IDType] = strawberry.field(default=None, description="admission process reference", permission_classes=[OnlyForAuthentized])
    applicant_user_id: typing.Optional[IDType] = strawberry.field(default=None, description="applicant user reference", permission_classes=[OnlyForAuthentized])
    applicant_name: typing.Optional[str] = strawberry.field(default=None, description="applicant full name", permission_classes=[OnlyForAuthentized])
    applicant_email: typing.Optional[str] = strawberry.field(default=None, description="applicant email", permission_classes=[OnlyForAuthentized])
    applied_date: typing.Optional[datetime.datetime] = strawberry.field(default=None, description="application date", permission_classes=[OnlyForAuthentized])
    status_id: typing.Optional[IDType] = strawberry.field(default=None, description="application status id", permission_classes=[OnlyForAuthentized])

    process: typing.Optional["AdmissionProcessGQLModel"] = strawberry.field(
        description="related admission process",
        permission_classes=[OnlyForAuthentized],
        resolver=ScalarResolver["AdmissionProcessGQLModel"](fkey_field_name="process_id")
    )
    enrollments: typing.List["EnrollmentGQLModel"] = strawberry.field(
        description="enrollments derived from this application",
        permission_classes=[OnlyForAuthentized],
        resolver=VectorResolver["EnrollmentGQLModel"](fkey_field_name="application_id", whereType=EnrollmentInputFilter)
    )
    payments: typing.List["PaymentGQLModel"] = strawberry.field(
        description="payments for this application",
        permission_classes=[OnlyForAuthentized],
        resolver=VectorResolver["PaymentGQLModel"](fkey_field_name="application_id", whereType=PaymentInputFilter)
    )


@strawberry.type(description="Admission application queries")
class AdmissionApplicationQuery:
    admission_application_by_id: typing.Optional[AdmissionApplicationGQLModel] = strawberry.field(
        description="get admission application by id",
        permission_classes=[OnlyForAuthentized],
        resolver=AdmissionApplicationGQLModel.load_with_loader
    )

    admission_application_page: typing.List[AdmissionApplicationGQLModel] = strawberry.field(
        description="page of admission applications",
        permission_classes=[OnlyForAuthentized],
        resolver=PageResolver[AdmissionApplicationGQLModel](whereType=AdmissionApplicationInputFilter)
    )


from uoishelpers.resolvers import InsertError, UpdateError, DeleteError
from uoishelpers.gqlpermissions.LoadDataExtension import LoadDataExtension


@strawberry.input(description="Input model for creating an admission application")
class AdmissionApplicationInsertGQLModel:
    process_id: typing.Optional[IDType] = None
    applicant_user_id: typing.Optional[IDType] = None
    applicant_name: typing.Optional[str] = None
    applicant_email: typing.Optional[str] = None
    applied_date: typing.Optional[datetime.datetime] = None
    status_id: typing.Optional[IDType] = None


@strawberry.input(description="Input model for updating an admission application")
class AdmissionApplicationUpdateGQLModel:
    id: IDType
    lastchange: datetime.datetime
    process_id: typing.Optional[IDType] = None
    applicant_user_id: typing.Optional[IDType] = None
    applicant_name: typing.Optional[str] = None
    applicant_email: typing.Optional[str] = None
    applied_date: typing.Optional[datetime.datetime] = None
    status_id: typing.Optional[IDType] = None


@strawberry.input(description="Input model for deleting an admission application")
class AdmissionApplicationDeleteGQLModel:
    id: IDType
    lastchange: datetime.datetime


@strawberry.type(description="Admission application mutations")
class AdmissionApplicationMutation:
    @strawberry.mutation(description="Insert an admission application", permission_classes=[OnlyForAuthentized])
    async def admission_application_insert(
        self,
        info: strawberry.Info,
        application: AdmissionApplicationInsertGQLModel
    ) -> typing.Union[AdmissionApplicationGQLModel, InsertError[AdmissionApplicationGQLModel]]:
        from uoishelpers.resolvers import Insert

        user = getUserFromInfo(info=info)
        application.createdby_id = user["id"]
        application.rbacobject_id = None

        return await Insert[AdmissionApplicationGQLModel].DoItSafeWay(info=info, entity=application)

    @strawberry.mutation(
        description="Update an admission application",
        permission_classes=[OnlyForAuthentized],
        extensions=[LoadDataExtension[UpdateError, AdmissionApplicationGQLModel]()]
    )
    async def admission_application_update(
        self,
        info: strawberry.Info,
        application: AdmissionApplicationUpdateGQLModel,
        db_row: typing.Any
    ) -> typing.Union[AdmissionApplicationGQLModel, UpdateError[AdmissionApplicationGQLModel]]:
        from uoishelpers.resolvers import Update

        user = getUserFromInfo(info=info)
        application.changedby_id = user["id"]

        return await Update[AdmissionApplicationGQLModel].DoItSafeWay(info=info, entity=application)

    @strawberry.mutation(
        description="Delete an admission application",
        permission_classes=[OnlyForAuthentized],
        extensions=[LoadDataExtension[DeleteError, AdmissionApplicationGQLModel]()]
    )
    async def admission_application_delete(
        self,
        info: strawberry.Info,
        application: AdmissionApplicationDeleteGQLModel,
        db_row: typing.Any
    ) -> typing.Optional[DeleteError[AdmissionApplicationGQLModel]]:
        from uoishelpers.resolvers import Delete

        return await Delete[AdmissionApplicationGQLModel].DoItSafeWay(info=info, entity=application)
