import typing
import datetime
import strawberry

from uoishelpers.resolvers import getLoadersFromInfo, PageResolver, createInputs2, ScalarResolver
from uoishelpers.gqlpermissions import OnlyForAuthentized

from .BaseGQLModel import BaseGQLModel, IDType
from .unified_rbac_extensions import (
    create_insert_permissions,
    create_update_permissions,
    create_delete_permissions,
    EDITOR_ROLES,
    ADMIN_ROLES,
)
from uoishelpers.resolvers import InsertError, UpdateError, DeleteError


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
    applicant_user_id: typing.Optional[IDType] = strawberry.UNSET
    street: typing.Optional[str] = strawberry.UNSET
    house_number: typing.Optional[str] = strawberry.UNSET
    city: typing.Optional[str] = strawberry.UNSET
    postal_code: typing.Optional[str] = strawberry.UNSET
    applied_date: typing.Optional[datetime.datetime] = strawberry.UNSET
    process_id: typing.Optional[IDType] = strawberry.UNSET
    payment_id: typing.Optional[IDType] = strawberry.UNSET


@strawberry.input(description="Input model for deleting an admission application")
class AdmissionApplicationDeleteGQLModel:
    id: IDType
    lastchange: datetime.datetime


@strawberry.type(description="Admission application mutations")
class AdmissionApplicationMutation:
    @strawberry.field(
        description="Insert an admission application",
        extensions=create_insert_permissions(
            InsertError,
            AdmissionApplicationGQLModel,
            required_roles=EDITOR_ROLES
        )
    )
    async def admission_application_insert(
        self,
        info: strawberry.Info,
        application: AdmissionApplicationInsertGQLModel
    ) -> typing.Union[AdmissionApplicationGQLModel, InsertError[AdmissionApplicationGQLModel]]:
        from uoishelpers.resolvers import Insert

        # Debug logging
        user = info.context.get("user", {})
        print(f"[INSERT] User: {user.get('fullname')} ({user.get('id')})")
        print(f"[INSERT] Roles: {user.get('roles', [])}")

        return await Insert[AdmissionApplicationGQLModel].DoItSafeWay(info=info, entity=application)

    @strawberry.field(
        description="Update an admission application",
        extensions=create_update_permissions(
            UpdateError,
            AdmissionApplicationGQLModel,
            required_roles=EDITOR_ROLES
        )
    )
    async def admission_application_update(
        self,
        info: strawberry.Info,
        application: AdmissionApplicationUpdateGQLModel
    ) -> typing.Union[AdmissionApplicationGQLModel, UpdateError[AdmissionApplicationGQLModel]]:
        from uoishelpers.resolvers import Update

        # Debug logging
        user = info.context.get("user", {})
        print(f"[UPDATE] User: {user.get('fullname')} ({user.get('id')})")
        print(f"[UPDATE] Roles: {user.get('roles', [])}")
        print(f"[UPDATE] Target ID: {application.id}")

        return await Update[AdmissionApplicationGQLModel].DoItSafeWay(info=info, entity=application)

    @strawberry.field(
        description="Delete an admission application",
        extensions=create_delete_permissions(
            DeleteError,
            AdmissionApplicationGQLModel,
            required_roles=ADMIN_ROLES
        )
    )
    async def admission_application_delete(
        self,
        info: strawberry.Info,
        application: AdmissionApplicationDeleteGQLModel
    ) -> typing.Optional[DeleteError[AdmissionApplicationGQLModel]]:
        from uoishelpers.resolvers import Delete

        # Debug logging
        user = info.context.get("user", {})
        print(f"[DELETE] User: {user.get('fullname')} ({user.get('id')})")
        print(f"[DELETE] Roles: {user.get('roles', [])}")
        print(f"[DELETE] Target ID: {application.id}")

        return await Delete[AdmissionApplicationGQLModel].DoItSafeWay(info=info, entity=application)