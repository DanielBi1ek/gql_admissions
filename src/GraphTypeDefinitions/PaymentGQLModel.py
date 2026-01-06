import typing
import datetime
import strawberry

from uoishelpers.resolvers import getLoadersFromInfo, PageResolver, createInputs2, ScalarResolver
from uoishelpers.gqlpermissions import OnlyForAuthentized

from .BaseGQLModel import BaseGQLModel, IDType

# Forward references
AdmissionApplicationGQLModel = typing.Annotated["AdmissionApplicationGQLModel", strawberry.lazy(".AdmissionApplicationGQLModel")]
PaymentInfoGQLModel = typing.Annotated["PaymentInfoGQLModel", strawberry.lazy(".PaymentInfoGQLModel")]


@createInputs2
class PaymentInputFilter:
    id: IDType
    application_id: IDType
    payment_info_id: IDType
    payer_id: IDType
    status_id: IDType
    bank_unique_data: str
    variable_symbol: str
    amount: float
    currency: str
    method: str
    paid_at: datetime.datetime


@strawberry.federation.type(keys=["id"], description="Payment record for an admission application")
class PaymentGQLModel(BaseGQLModel):

    @classmethod
    def getLoader(cls, info: strawberry.types.Info):
        return getLoadersFromInfo(info).PaymentModel

    application_id: typing.Optional[IDType] = strawberry.field(
        default=None,
        description="application reference",
        permission_classes=[OnlyForAuthentized]
    )
    payment_info_id: typing.Optional[IDType] = strawberry.field(
        default=None,
        description="payment conditions reference",
        permission_classes=[OnlyForAuthentized]
    )
    payer_id: typing.Optional[IDType] = strawberry.field(
        default=None,
        description="payer user reference",
        permission_classes=[OnlyForAuthentized]
    )
    status_id: typing.Optional[IDType] = strawberry.field(
        default=None,
        description="payment status id",
        permission_classes=[OnlyForAuthentized]
    )
    bank_unique_data: typing.Optional[str] = strawberry.field(
        default=None,
        description="unique bank payment identifier",
        permission_classes=[OnlyForAuthentized]
    )
    variable_symbol: typing.Optional[str] = strawberry.field(
        default=None,
        description="variable symbol provided by payer",
        permission_classes=[OnlyForAuthentized]
    )

    amount: typing.Optional[float] = strawberry.field(
        default=None,
        description="payment amount",
        permission_classes=[OnlyForAuthentized]
    )

    currency: typing.Optional[str] = strawberry.field(
        default=None,
        description="currency code",
        permission_classes=[OnlyForAuthentized]
    )

    method: typing.Optional[str] = strawberry.field(
        default=None,
        description="payment method",
        permission_classes=[OnlyForAuthentized]
    )

    paid_at: typing.Optional[datetime.datetime] = strawberry.field(
        default=None,
        description="date of payment",
        permission_classes=[OnlyForAuthentized]
    )

    application: typing.Optional["AdmissionApplicationGQLModel"] = strawberry.field(
        description="related admission application",
        permission_classes=[OnlyForAuthentized],
        resolver=ScalarResolver["AdmissionApplicationGQLModel"](fkey_field_name="application_id")
    )
    payment_info: typing.Optional["PaymentInfoGQLModel"] = strawberry.field(
        description="payment conditions reference",
        permission_classes=[OnlyForAuthentized],
        resolver=ScalarResolver["PaymentInfoGQLModel"](fkey_field_name="payment_info_id")
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


from uoishelpers.resolvers import InsertError, UpdateError, DeleteError
from uoishelpers.gqlpermissions.LoadDataExtension import LoadDataExtension


@strawberry.input(description="Input model for creating a payment")
class PaymentInsertGQLModel:
    application_id: IDType = strawberry.field(description="Application reference")
    payment_info_id: typing.Optional[IDType] = strawberry.field(default=None, description="Payment info reference")
    payer_id: typing.Optional[IDType] = strawberry.field(default=None, description="Payer reference")
    status_id: typing.Optional[IDType] = strawberry.field(default=None, description="Payment status")
    bank_unique_data: typing.Optional[str] = strawberry.field(default=None, description="Bank unique identifier")
    variable_symbol: typing.Optional[str] = strawberry.field(default=None, description="Variable symbol")
    amount: float = strawberry.field(description="Payment amount")
    currency: typing.Optional[str] = strawberry.field(default="EUR", description="Currency code")
    method: typing.Optional[str] = strawberry.field(default=None, description="Payment method")
    paid_at: typing.Optional[datetime.datetime] = strawberry.field(default=None, description="Date of payment")


@strawberry.input(description="Input model for updating a payment")
class PaymentUpdateGQLModel:
    id: IDType = strawberry.field(description="Payment id")
    lastchange: datetime.datetime = strawberry.field(description="Last change timestamp")
    payment_info_id: typing.Optional[IDType] = None
    payer_id: typing.Optional[IDType] = None
    status_id: typing.Optional[IDType] = None
    bank_unique_data: typing.Optional[str] = None
    variable_symbol: typing.Optional[str] = None
    amount: typing.Optional[float] = None
    currency: typing.Optional[str] = None
    method: typing.Optional[str] = None
    paid_at: typing.Optional[datetime.datetime] = None


@strawberry.input(description="Input model for deleting a payment")
class PaymentDeleteGQLModel:
    id: IDType = strawberry.field(description="Payment id")
    lastchange: datetime.datetime = strawberry.field(description="Last change timestamp")


@strawberry.type(description="Payment mutations")
class PaymentMutation:
    @strawberry.mutation(
        description="Insert a payment record",
        permission_classes=[OnlyForAuthentized]
    )
    async def payment_insert(
            self,
            info: strawberry.Info,
            payment: PaymentInsertGQLModel
    ) -> typing.Union[PaymentGQLModel, InsertError[PaymentGQLModel]]:
        import uuid

        try:
            loader = getLoadersFromInfo(info).PaymentModel

            payment_data = {
                "id": uuid.uuid4(),
                "application_id": payment.application_id,
                "payment_info_id": payment.payment_info_id,
                "payer_id": payment.payer_id,
                "status_id": payment.status_id,
                "bank_unique_data": payment.bank_unique_data,
                "variable_symbol": payment.variable_symbol,
                "amount": payment.amount,
                "currency": payment.currency,
                "method": payment.method,
                "rbacobject_id": None,
                "createdby_id": uuid.UUID("66d8a57c-9ff3-40c3-a019-07808b5150a2"),
                "changedby_id": None,
                "paid_at": payment.paid_at,
            }

            from ..DBDefinitions.PaymentModel import PaymentModel
            db_row = PaymentModel(**payment_data)

            session = loader.session
            session.add(db_row)
            await session.commit()
            await session.refresh(db_row)

            return PaymentGQLModel.from_dataclass(db_row)

        except Exception as e:
            return InsertError[PaymentGQLModel](
                msg=str(e),
                _input=payment
            )

    @strawberry.mutation(
        description="Update a payment record",
        permission_classes=[OnlyForAuthentized],
        extensions=[LoadDataExtension[UpdateError, PaymentGQLModel]()]
    )
    async def payment_update(
            self,
            info: strawberry.Info,
            payment: PaymentUpdateGQLModel,
            db_row: typing.Any
    ) -> typing.Union[PaymentGQLModel, UpdateError[PaymentGQLModel]]:
        try:
            loader = getLoadersFromInfo(info).PaymentModel
            session = loader.session

            if payment.status_id is not None:
                db_row.status_id = payment.status_id
            if payment.payment_info_id is not None:
                db_row.payment_info_id = payment.payment_info_id
            if payment.payer_id is not None:
                db_row.payer_id = payment.payer_id
            if payment.bank_unique_data is not None:
                db_row.bank_unique_data = payment.bank_unique_data
            if payment.variable_symbol is not None:
                db_row.variable_symbol = payment.variable_symbol
            if payment.amount is not None:
                db_row.amount = payment.amount
            if payment.currency is not None:
                db_row.currency = payment.currency
            if payment.method is not None:
                db_row.method = payment.method
            if payment.paid_at is not None:
                db_row.paid_at = payment.paid_at

            db_row.lastchange = datetime.datetime.now()

            session.add(db_row)
            await session.commit()
            await session.refresh(db_row)

            return PaymentGQLModel.from_dataclass(db_row)

        except Exception as e:
            return UpdateError[PaymentGQLModel](
                msg=str(e),
                _input=payment
            )

    @strawberry.mutation(
        description="Delete a payment record",
        permission_classes=[OnlyForAuthentized],
        extensions=[LoadDataExtension[DeleteError, PaymentGQLModel]()]
    )
    async def payment_delete(
            self,
            info: strawberry.Info,
            payment: PaymentDeleteGQLModel,
            db_row: typing.Any
    ) -> typing.Optional[DeleteError[PaymentGQLModel]]:
        try:
            loader = getLoadersFromInfo(info).PaymentModel
            session = loader.session

            await session.delete(db_row)
            await session.commit()

            return None

        except Exception as e:
            return DeleteError[PaymentGQLModel](
                msg=str(e),
                _input=payment
            )
