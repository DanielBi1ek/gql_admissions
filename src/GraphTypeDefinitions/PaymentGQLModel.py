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
