import typing
import datetime
import strawberry

from uoishelpers.resolvers import getLoadersFromInfo, PageResolver, createInputs2
from uoishelpers.gqlpermissions import OnlyForAuthentized

from .BaseGQLModel import BaseGQLModel, IDType


@createInputs2
class PaymentInfoInputFilter:
    id: IDType
    account_number: str
    specific_symbol: str
    constant_symbol: str
    iban: str
    swift: str
    amount: float


@strawberry.federation.type(keys=["id"], description="Payment conditions for admissions")
class PaymentInfoGQLModel(BaseGQLModel):

    @classmethod
    def getLoader(cls, info: strawberry.types.Info):
        return getLoadersFromInfo(info).PaymentInfoModel

    account_number: typing.Optional[str] = strawberry.field(
        default=None,
        description="account number with bank code",
        permission_classes=[OnlyForAuthentized]
    )
    specific_symbol: typing.Optional[str] = strawberry.field(
        default=None,
        description="specific symbol",
        permission_classes=[OnlyForAuthentized]
    )
    constant_symbol: typing.Optional[str] = strawberry.field(
        default=None,
        description="constant symbol",
        permission_classes=[OnlyForAuthentized]
    )
    iban: typing.Optional[str] = strawberry.field(
        default=None,
        description="IBAN code",
        permission_classes=[OnlyForAuthentized]
    )
    swift: typing.Optional[str] = strawberry.field(
        default=None,
        description="SWIFT bank code",
        permission_classes=[OnlyForAuthentized]
    )
    amount: typing.Optional[float] = strawberry.field(
        default=None,
        description="required payment amount",
        permission_classes=[OnlyForAuthentized]
    )


@strawberry.type(description="Payment info queries")
class PaymentInfoQuery:
    payment_info_by_id: typing.Optional[PaymentInfoGQLModel] = strawberry.field(
        description="get payment info by id",
        permission_classes=[OnlyForAuthentized],
        resolver=PaymentInfoGQLModel.load_with_loader
    )

    payment_info_page: typing.List[PaymentInfoGQLModel] = strawberry.field(
        description="page of payment infos",
        permission_classes=[OnlyForAuthentized],
        resolver=PageResolver[PaymentInfoGQLModel](whereType=PaymentInfoInputFilter)
    )


from uoishelpers.resolvers import InsertError, UpdateError, DeleteError
from uoishelpers.gqlpermissions.LoadDataExtension import LoadDataExtension


@strawberry.input(description="Input model for creating payment info")
class PaymentInfoInsertGQLModel:
    account_number: typing.Optional[str] = None
    specific_symbol: typing.Optional[str] = None
    constant_symbol: typing.Optional[str] = None
    iban: typing.Optional[str] = None
    swift: typing.Optional[str] = None
    amount: typing.Optional[float] = None


@strawberry.input(description="Input model for updating payment info")
class PaymentInfoUpdateGQLModel:
    id: IDType
    lastchange: datetime.datetime
    account_number: typing.Optional[str] = None
    specific_symbol: typing.Optional[str] = None
    constant_symbol: typing.Optional[str] = None
    iban: typing.Optional[str] = None
    swift: typing.Optional[str] = None
    amount: typing.Optional[float] = None


@strawberry.input(description="Input model for deleting payment info")
class PaymentInfoDeleteGQLModel:
    id: IDType
    lastchange: datetime.datetime


@strawberry.type(description="Payment info mutations")
class PaymentInfoMutation:
    @strawberry.mutation(
        description="Insert a payment info record",
        permission_classes=[OnlyForAuthentized]
    )
    async def payment_info_insert(
        self,
        info: strawberry.Info,
        payment_info: PaymentInfoInsertGQLModel
    ) -> typing.Union[PaymentInfoGQLModel, InsertError[PaymentInfoGQLModel]]:
        import uuid

        try:
            loader = getLoadersFromInfo(info).PaymentInfoModel

            payment_info_data = {
                "id": uuid.uuid4(),
                "account_number": payment_info.account_number,
                "specific_symbol": payment_info.specific_symbol,
                "constant_symbol": payment_info.constant_symbol,
                "iban": payment_info.iban,
                "swift": payment_info.swift,
                "amount": payment_info.amount,
                "rbacobject_id": None,
                "createdby_id": uuid.UUID("66d8a57c-9ff3-40c3-a019-07808b5150a2"),
                "changedby_id": None,
            }

            from ..DBDefinitions.PaymentInfoModel import PaymentInfoModel
            db_row = PaymentInfoModel(**payment_info_data)

            session = loader.session
            session.add(db_row)
            await session.commit()
            await session.refresh(db_row)

            return PaymentInfoGQLModel.from_dataclass(db_row)

        except Exception as e:
            return InsertError[PaymentInfoGQLModel](
                msg=str(e),
                _input=payment_info
            )

    @strawberry.mutation(
        description="Update a payment info record",
        permission_classes=[OnlyForAuthentized],
        extensions=[LoadDataExtension[UpdateError, PaymentInfoGQLModel]()]
    )
    async def payment_info_update(
        self,
        info: strawberry.Info,
        payment_info: PaymentInfoUpdateGQLModel,
        db_row: typing.Any
    ) -> typing.Union[PaymentInfoGQLModel, UpdateError[PaymentInfoGQLModel]]:
        try:
            loader = getLoadersFromInfo(info).PaymentInfoModel
            session = loader.session

            if payment_info.account_number is not None:
                db_row.account_number = payment_info.account_number
            if payment_info.specific_symbol is not None:
                db_row.specific_symbol = payment_info.specific_symbol
            if payment_info.constant_symbol is not None:
                db_row.constant_symbol = payment_info.constant_symbol
            if payment_info.iban is not None:
                db_row.iban = payment_info.iban
            if payment_info.swift is not None:
                db_row.swift = payment_info.swift
            if payment_info.amount is not None:
                db_row.amount = payment_info.amount

            db_row.lastchange = datetime.datetime.now()

            session.add(db_row)
            await session.commit()
            await session.refresh(db_row)

            return PaymentInfoGQLModel.from_dataclass(db_row)

        except Exception as e:
            return UpdateError[PaymentInfoGQLModel](
                msg=str(e),
                _input=payment_info
            )

    @strawberry.mutation(
        description="Delete a payment info record",
        permission_classes=[OnlyForAuthentized],
        extensions=[LoadDataExtension[DeleteError, PaymentInfoGQLModel]()]
    )
    async def payment_info_delete(
        self,
        info: strawberry.Info,
        payment_info: PaymentInfoDeleteGQLModel,
        db_row: typing.Any
    ) -> typing.Optional[DeleteError[PaymentInfoGQLModel]]:
        try:
            loader = getLoadersFromInfo(info).PaymentInfoModel
            session = loader.session

            await session.delete(db_row)
            await session.commit()

            return None

        except Exception as e:
            return DeleteError[PaymentInfoGQLModel](
                msg=str(e),
                _input=payment_info
            )
