import typing
import datetime
import strawberry

from uoishelpers.resolvers import getLoadersFromInfo, PageResolver, createInputs2, ScalarResolver
from uoishelpers.gqlpermissions import OnlyForAuthentized
from uoishelpers.resolvers import getUserFromInfo

from .BaseGQLModel import BaseGQLModel, IDType

AdmissionProcessGQLModel = typing.Annotated["AdmissionProcessGQLModel", strawberry.lazy(".AdmissionProcessGQLModel")]
AdmissionPaymentGQLModel = typing.Annotated["AdmissionPaymentGQLModel", strawberry.lazy(".AdmissionPaymentGQLModel")]


@createInputs2
class AdmissionApplicationInputFilter:
    id: IDType
    applicant_user_id: IDType
    street: str
    house_number: str
    city: str
    postal_code: str
    applied_date: datetime.datetime
    process_id: IDType
    payment_id: IDType


@strawberry.federation.type(keys=["id"], description="Admission application submitted by a user")
class AdmissionApplicationGQLModel(BaseGQLModel):

    @classmethod
    def getLoader(cls, info: strawberry.types.Info):
        return getLoadersFromInfo(info).AdmissionApplicationModel

    applicant_user_id: typing.Optional[IDType] = strawberry.field(
        default=None,
        description="applicant user reference",
        permission_classes=[OnlyForAuthentized]
    )
    street: typing.Optional[str] = strawberry.field(
        default=None,
        description="street",
        permission_classes=[OnlyForAuthentized]
    )
    house_number: typing.Optional[str] = strawberry.field(
        default=None,
        description="house number",
        permission_classes=[OnlyForAuthentized]
    )
    city: typing.Optional[str] = strawberry.field(
        default=None,
        description="city",
        permission_classes=[OnlyForAuthentized]
    )
    postal_code: typing.Optional[str] = strawberry.field(
        default=None,
        description="postal code",
        permission_classes=[OnlyForAuthentized]
    )
    applied_date: typing.Optional[datetime.datetime] = strawberry.field(
        default=None,
        description="application date",
        permission_classes=[OnlyForAuthentized]
    )
    process_id: typing.Optional[IDType] = strawberry.field(
        default=None,
        description="admission process reference",
        permission_classes=[OnlyForAuthentized]
    )
    payment_id: typing.Optional[IDType] = strawberry.field(
        default=None,
        description="admission payment reference",
        permission_classes=[OnlyForAuthentized]
    )

    process: typing.Optional["AdmissionProcessGQLModel"] = strawberry.field(
        description="related admission process",
        permission_classes=[OnlyForAuthentized],
        resolver=ScalarResolver["AdmissionProcessGQLModel"](fkey_field_name="process_id")
    )
    payment: typing.Optional["AdmissionPaymentGQLModel"] = strawberry.field(
        description="related admission payment",
        permission_classes=[OnlyForAuthentized],
        resolver=ScalarResolver["AdmissionPaymentGQLModel"](fkey_field_name="payment_id")
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
    applicant_user_id: typing.Optional[IDType] = None
    street: typing.Optional[str] = None
    house_number: typing.Optional[str] = None
    city: typing.Optional[str] = None
    postal_code: typing.Optional[str] = None
    applied_date: typing.Optional[datetime.datetime] = None
    process_id: typing.Optional[IDType] = None
    payment_id: typing.Optional[IDType] = None


@strawberry.input(description="Input model for updating an admission application")
class AdmissionApplicationUpdateGQLModel:
    id: IDType
    lastchange: datetime.datetime
    applicant_user_id: typing.Optional[IDType] = None
    street: typing.Optional[str] = None
    house_number: typing.Optional[str] = None
    city: typing.Optional[str] = None
    postal_code: typing.Optional[str] = None
    applied_date: typing.Optional[datetime.datetime] = None
    process_id: typing.Optional[IDType] = None
    payment_id: typing.Optional[IDType] = None


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
