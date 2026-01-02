import typing
import datetime
import strawberry

from uoishelpers.resolvers import getLoadersFromInfo, PageResolver, createInputs2, ScalarResolver
from uoishelpers.gqlpermissions import OnlyForAuthentized

from .BaseGQLModel import BaseGQLModel, IDType

# Forward references
EnrollmentGQLModel = typing.Annotated["EnrollmentGQLModel", strawberry.lazy(".EnrollmentGQLModel")]


@createInputs2
class PaymentInputFilter:
    id: IDType
    enrollment_id: IDType
    amount: float
    currency: str
    method: str
    #status_id: IDType
    payment_date: datetime.datetime


@strawberry.federation.type(keys=["id"], description="Payment for enrollment")
class PaymentGQLModel(BaseGQLModel):

    @classmethod
    def getLoader(cls, info: strawberry.types.Info):
        return getLoadersFromInfo(info).PaymentModel

    enrollment_id: typing.Optional[IDType] = strawberry.field(
        default=None,
        description="enrollment reference",
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

    payment_date: typing.Optional[datetime.datetime] = strawberry.field(
        default=None,
        description="date of payment",
        permission_classes=[OnlyForAuthentized]
    )

    # Relationships
    enrollment: typing.Optional["EnrollmentGQLModel"] = strawberry.field(
        description="related enrollment",
        permission_classes=[OnlyForAuthentized],
        resolver=ScalarResolver["EnrollmentGQLModel"](fkey_field_name="enrollment_id")
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


# Mutations
from uoishelpers.resolvers import InsertError, UpdateError, DeleteError
from uoishelpers.gqlpermissions.LoadDataExtension import LoadDataExtension


@strawberry.input(description="Input model for creating a payment")
class PaymentInsertGQLModel:
    enrollment_id: IDType = strawberry.field(description="Enrollment reference")
    amount: float = strawberry.field(description="Payment amount")
    currency: typing.Optional[str] = strawberry.field(default="EUR", description="Currency code")
    method: typing.Optional[str] = strawberry.field(default=None, description="Payment method")
    #status_id: IDType = strawberry.field(description="Payment status")
    payment_date: typing.Optional[datetime.datetime] = strawberry.field(default=None, description="Date of payment")


@strawberry.input(description="Input model for updating a payment")
class PaymentUpdateGQLModel:
    id: IDType = strawberry.field(description="Payment id")
    lastchange: datetime.datetime = strawberry.field(description="Last change timestamp")
    amount: typing.Optional[float] = None
    currency: typing.Optional[str] = None
    method: typing.Optional[str] = None
    #status_id: typing.Optional[IDType] = None
    payment_date: typing.Optional[datetime.datetime] = None


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

        print("=" * 80)
        print("DEBUG: payment_insert CALLED!!!")
        print(f"DEBUG: enrollment_id: {payment.enrollment_id}")
        print(f"DEBUG: amount: {payment.amount}")
        print(f"DEBUG: currency: {payment.currency}")
        print(f"DEBUG: method: {payment.method}")
        #print(f"DEBUG: status_id: {payment.status_id}")
        print("=" * 80)

        try:
            loader = getLoadersFromInfo(info).PaymentModel

            payment_data = {
                "id": uuid.uuid4(),
                "enrollment_id": payment.enrollment_id,
                "amount": payment.amount,
                "currency": payment.currency,
                "method": payment.method,
               # "status_id": payment.status_id,
                "rbacobject_id": None,
                "createdby_id": uuid.UUID("66d8a57c-9ff3-40c3-a019-07808b5150a2"),
                "changedby_id": None,
                "payment_date": None,
            }

            print(f"DEBUG: Creating payment with data: {payment_data}")

            from ..DBDefinitions.PaymentModel import PaymentModel
            db_row = PaymentModel(**payment_data)

            session = loader.session
            session.add(db_row)
            await session.commit()
            await session.refresh(db_row)

            print(f"DEBUG: Insert successful! ID: {db_row.id}")

            return PaymentGQLModel.from_dataclass(db_row)

        except Exception as e:
            print(f"DEBUG: Exception during insert: {type(e).__name__}: {str(e)}")
            print(f"DEBUG: Full exception details:")
            import traceback
            traceback.print_exc()

            return InsertError[PaymentGQLModel](
                msg=f"{type(e).__name__}: {str(e)}",
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
        print("=" * 80)
        print("DEBUG: payment_update CALLED!!!")
        print(f"DEBUG: id: {payment.id}")
        print("=" * 80)

        try:
            loader = getLoadersFromInfo(info).PaymentModel
            session = loader.session

            if payment.amount is not None:
                db_row.amount = payment.amount
            if payment.currency is not None:
                db_row.currency = payment.currency
            if payment.method is not None:
                db_row.method = payment.method
            #if payment.status_id is not None:
             #   db_row.status_id = payment.status_id

            import datetime
            db_row.lastchange = datetime.datetime.now()

            session.add(db_row)
            await session.commit()
            await session.refresh(db_row)

            print(f"DEBUG: Update successful!")

            return PaymentGQLModel.from_dataclass(db_row)

        except Exception as e:
            print(f"DEBUG: Exception during update: {type(e).__name__}: {str(e)}")
            import traceback
            traceback.print_exc()

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
        print("=" * 80)
        print("DEBUG: payment_delete CALLED!!!")
        print(f"DEBUG: id: {payment.id}")
        print("=" * 80)

        try:
            loader = getLoadersFromInfo(info).PaymentModel
            session = loader.session

            await session.delete(db_row)
            await session.commit()

            print(f"DEBUG: Delete successful!")

            return None

        except Exception as e:
            print(f"DEBUG: Exception during delete: {type(e).__name__}: {str(e)}")
            import traceback
            traceback.print_exc()

            return DeleteError[PaymentGQLModel](
                msg=str(e),
                _input=payment
            )