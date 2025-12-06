import typing
import datetime
import strawberry

from uoishelpers.resolvers import getLoadersFromInfo, PageResolver, ScalarResolver, createInputs2
from uoishelpers.gqlpermissions import OnlyForAuthentized

from .BaseGQLModel import BaseGQLModel, IDType

EnrollmentGQLModel = typing.Annotated["EnrollmentGQLModel", strawberry.lazy(".EnrollmentGQLModel")]

@createInputs2
class PaymentInputFilter:
    id: IDType
    enrollment_id: IDType
    status_id: IDType

@strawberry.federation.type(keys=["id"], description="Payment related to an enrollment")
class PaymentGQLModel(BaseGQLModel):

    @classmethod
    def getLoader(cls, info: strawberry.types.Info):
        return getLoadersFromInfo(info).PaymentModel

    enrollment_id: typing.Optional[IDType] = strawberry.field(default=None, description="enrollment reference", permission_classes=[OnlyForAuthentized])
    amount: typing.Optional[float] = strawberry.field(default=None, description="payment amount", permission_classes=[OnlyForAuthentized])
    currency: typing.Optional[str] = strawberry.field(default=None, description="currency", permission_classes=[OnlyForAuthentized])
    method: typing.Optional[str] = strawberry.field(default=None, description="payment method", permission_classes=[OnlyForAuthentized])
    status_id: typing.Optional[IDType] = strawberry.field(default=None, description="payment state", permission_classes=[OnlyForAuthentized])

    enrollment: typing.Optional[EnrollmentGQLModel] = strawberry.field(
        description="related enrollment",
        permission_classes=[OnlyForAuthentized],
        resolver=ScalarResolver[EnrollmentGQLModel](fkey_field_name="enrollment_id")
    )

@strawberry.type(description="Payment queries")
class PaymentQuery:
    payment_by_id: typing.Optional[PaymentGQLModel] = strawberry.field(
        description="get payment by id",
        permission_classes=[OnlyForAuthentized],
        resolver=PaymentGQLModel.load_with_loader
    )

    payment_page: typing.List[PaymentGQLModel] = strawberry.field(
        description="page of payments",
        permission_classes=[OnlyForAuthentized],
        resolver=PageResolver[PaymentGQLModel](whereType=PaymentInputFilter)
    )

# mutations
from uoishelpers.resolvers import InputModelMixin, InsertError, Insert, UpdateError, Update, DeleteError, Delete
from uoishelpers.gqlpermissions.LoadDataExtension import LoadDataExtension
from uoishelpers.gqlpermissions.RbacProviderExtension import RbacProviderExtension
from uoishelpers.gqlpermissions.RbacInsertProviderExtension import RbacInsertProviderExtension
from uoishelpers.gqlpermissions.UserRoleProviderExtension import UserRoleProviderExtension
from uoishelpers.gqlpermissions.UserAccessControlExtension import UserAccessControlExtension

@strawberry.input(
    description="Input model for creating a payment"
)
class PaymentInsertGQLModel(InputModelMixin):
    getLoader = PaymentGQLModel.getLoader
    id: typing.Optional[IDType] = strawberry.field(default=None)
    enrollment_id: typing.Optional[IDType] = strawberry.field(default=None)
    amount: typing.Optional[float] = strawberry.field(default=None)
    currency: typing.Optional[str] = strawberry.field(default=None)
    method: typing.Optional[str] = strawberry.field(default=None)
    status_id: typing.Optional[IDType] = strawberry.field(default=None)

    createdby_id: strawberry.Private[IDType] = None

@strawberry.input(
    description="Input model for updating a payment"
)
class PaymentUpdateGQLModel:
    id: IDType = strawberry.field()
    lastchange: datetime.datetime = strawberry.field()
    enrollment_id: typing.Optional[IDType] = strawberry.field(default=None)
    amount: typing.Optional[float] = strawberry.field(default=None)
    currency: typing.Optional[str] = strawberry.field(default=None)
    method: typing.Optional[str] = strawberry.field(default=None)
    status_id: typing.Optional[IDType] = strawberry.field(default=None)
    changedby_id: strawberry.Private[IDType] = None

@strawberry.input(
    description="Input model for deleting a payment"
)
class PaymentDeleteGQLModel:
    id: IDType = strawberry.field()
    lastchange: datetime.datetime = strawberry.field()

@strawberry.type(description="Payment mutations")
class PaymentMutation:
    @strawberry.mutation(
        description="Insert a payment",
        permission_classes=[OnlyForAuthentized],
        extensions=[
            UserAccessControlExtension[InsertError, PaymentGQLModel](roles=[]),
            UserRoleProviderExtension[InsertError, PaymentGQLModel](),
            RbacInsertProviderExtension[InsertError, PaymentGQLModel](),
            LoadDataExtension[InsertError, PaymentGQLModel](
                getLoader=PaymentGQLModel.getLoader,
                primary_key_name="enrollment_id"
            )
        ],
    )
    async def payment_insert(self, info: strawberry.Info, payment: PaymentInsertGQLModel, rbacobject_id: IDType, user_roles: typing.List[dict]) -> typing.Union[PaymentGQLModel, InsertError[PaymentGQLModel]]:
        return await Insert[PaymentGQLModel].DoItSafeWay(info=info, entity=payment)

    @strawberry.mutation(
        description="Update a payment",
        permission_classes=[OnlyForAuthentized],
        extensions=[
            LoadDataExtension[UpdateError, PaymentGQLModel](),
            UserRoleProviderExtension[UpdateError, PaymentGQLModel](),
            RbacProviderExtension[UpdateError, PaymentGQLModel](),
            UserAccessControlExtension[UpdateError, PaymentGQLModel](roles=[]),
        ],
    )
    async def payment_update(self, info: strawberry.Info, payment: PaymentUpdateGQLModel) -> typing.Union[PaymentGQLModel, UpdateError[PaymentGQLModel]]:
        return await Update[PaymentGQLModel].DoItSafeWay(info=info, entity=payment)

    @strawberry.mutation(
        description="Delete a payment",
        permission_classes=[OnlyForAuthentized],
        extensions=[
            LoadDataExtension[DeleteError, PaymentGQLModel](),
            UserRoleProviderExtension[DeleteError, PaymentGQLModel](),
            RbacProviderExtension[DeleteError, PaymentGQLModel](),
            UserAccessControlExtension[DeleteError, PaymentGQLModel](roles=[]),
        ],
    )
    async def payment_delete(self, info: strawberry.Info, payment: PaymentDeleteGQLModel) -> typing.Optional[DeleteError[PaymentGQLModel]]:
        return await Delete[PaymentGQLModel].DoItSafeWay(info=info, entity=payment)
