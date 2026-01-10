import typing
import datetime
import strawberry

from uoishelpers.resolvers import getLoadersFromInfo, PageResolver, createInputs2, ScalarResolver
from uoishelpers.gqlpermissions import OnlyForAuthentized

from .BaseGQLModel import BaseGQLModel, IDType

AdmissionBankAccountGQLModel = typing.Annotated["AdmissionBankAccountGQLModel", strawberry.lazy(".AdmissionBankAccountGQLModel")]


@createInputs2
class AdmissionPaymentInfoInputFilter:
    id: IDType
    required_amount: float
    bank_account_id: IDType


@strawberry.federation.type(keys=["id"], description="Payment info template for admission fees")
class AdmissionPaymentInfoGQLModel(BaseGQLModel):

    @classmethod
    def getLoader(cls, info: strawberry.types.Info):
        return getLoadersFromInfo(info).AdmissionPaymentInfoModel

    required_amount: typing.Optional[float] = strawberry.field(
        default=None,
        description="required amount",
        permission_classes=[OnlyForAuthentized]
    )
    bank_account_id: typing.Optional[IDType] = strawberry.field(
        default=None,
        description="bank account reference",
        permission_classes=[OnlyForAuthentized]
    )

    bank_account: typing.Optional["AdmissionBankAccountGQLModel"] = strawberry.field(
        description="bank account details",
        permission_classes=[OnlyForAuthentized],
        resolver=ScalarResolver["AdmissionBankAccountGQLModel"](fkey_field_name="bank_account_id")
    )


@strawberry.type(description="Admission payment info queries")
class AdmissionPaymentInfoQuery:
    admission_payment_info_by_id: typing.Optional[AdmissionPaymentInfoGQLModel] = strawberry.field(
        description="get admission payment info by id",
        permission_classes=[OnlyForAuthentized],
        resolver=AdmissionPaymentInfoGQLModel.load_with_loader
    )

    admission_payment_info_page: typing.List[AdmissionPaymentInfoGQLModel] = strawberry.field(
        description="page of admission payment info",
        permission_classes=[OnlyForAuthentized],
        resolver=PageResolver[AdmissionPaymentInfoGQLModel](whereType=AdmissionPaymentInfoInputFilter)
    )


from uoishelpers.resolvers import InsertError, UpdateError, DeleteError
from uoishelpers.gqlpermissions.LoadDataExtension import LoadDataExtension


@strawberry.input(description="Input model for creating admission payment info")
class AdmissionPaymentInfoInsertGQLModel:
    required_amount: typing.Optional[float] = None
    bank_account_id: typing.Optional[IDType] = None


@strawberry.input(description="Input model for updating admission payment info")
class AdmissionPaymentInfoUpdateGQLModel:
    id: IDType
    lastchange: datetime.datetime
    required_amount: typing.Optional[float] = None
    bank_account_id: typing.Optional[IDType] = None


@strawberry.input(description="Input model for deleting admission payment info")
class AdmissionPaymentInfoDeleteGQLModel:
    id: IDType
    lastchange: datetime.datetime


@strawberry.type(description="Admission payment info mutations")
class AdmissionPaymentInfoMutation:
    @strawberry.mutation(description="Insert admission payment info", permission_classes=[OnlyForAuthentized])
    async def admission_payment_info_insert(
        self,
        info: strawberry.Info,
        payment_info: AdmissionPaymentInfoInsertGQLModel
    ) -> typing.Union[AdmissionPaymentInfoGQLModel, InsertError[AdmissionPaymentInfoGQLModel]]:
        from uoishelpers.resolvers import Insert

        return await Insert[AdmissionPaymentInfoGQLModel].DoItSafeWay(info=info, entity=payment_info)

    @strawberry.mutation(
        description="Update admission payment info",
        permission_classes=[OnlyForAuthentized],
        extensions=[LoadDataExtension[UpdateError, AdmissionPaymentInfoGQLModel]()]
    )
    async def admission_payment_info_update(
        self,
        info: strawberry.Info,
        payment_info: AdmissionPaymentInfoUpdateGQLModel,
        db_row: typing.Any
    ) -> typing.Union[AdmissionPaymentInfoGQLModel, UpdateError[AdmissionPaymentInfoGQLModel]]:
        from uoishelpers.resolvers import Update

        return await Update[AdmissionPaymentInfoGQLModel].DoItSafeWay(info=info, entity=payment_info)

    @strawberry.mutation(
        description="Delete admission payment info",
        permission_classes=[OnlyForAuthentized],
        extensions=[LoadDataExtension[DeleteError, AdmissionPaymentInfoGQLModel]()]
    )
    async def admission_payment_info_delete(
        self,
        info: strawberry.Info,
        payment_info: AdmissionPaymentInfoDeleteGQLModel,
        db_row: typing.Any
    ) -> typing.Optional[DeleteError[AdmissionPaymentInfoGQLModel]]:
        from uoishelpers.resolvers import Delete

        return await Delete[AdmissionPaymentInfoGQLModel].DoItSafeWay(info=info, entity=payment_info)
