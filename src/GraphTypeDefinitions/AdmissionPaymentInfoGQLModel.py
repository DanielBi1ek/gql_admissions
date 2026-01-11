import typing
import datetime
import strawberry

from uoishelpers.resolvers import getLoadersFromInfo, PageResolver, createInputs2, ScalarResolver
from uoishelpers.gqlpermissions import OnlyForAuthentized

from .BaseGQLModel import BaseGQLModel, IDType
from .admission_permissions import AdmissionsAdminPermission
from .db_errors import integrity_error_to_error

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

    @strawberry.field(
        description="page of admission payment info",
        permission_classes=[OnlyForAuthentized],
    )
    async def admission_payment_info_page(
        self,
        info: strawberry.Info,
        where: typing.Optional[AdmissionPaymentInfoInputFilter] = None,
        skip: typing.Optional[int] = 0,
        limit: typing.Optional[int] = 10,
        orderby: typing.Optional[str] = None,
        desc: typing.Optional[bool] = None,
        offset: typing.Optional[int] = None,
    ) -> typing.List[AdmissionPaymentInfoGQLModel]:
        if offset is not None:
            skip = offset
        loader = AdmissionPaymentInfoGQLModel.getLoader(info=info)
        wheredict = None if where is None else strawberry.asdict(where)
        rows = await loader.page(
            where=wheredict,
            skip=skip or 0,
            limit=limit,
            orderby=orderby,
            desc=desc,
        )
        return [AdmissionPaymentInfoGQLModel.from_dataclass(row) for row in rows]


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
    required_amount: typing.Optional[float] = strawberry.UNSET
    bank_account_id: typing.Optional[IDType] = strawberry.UNSET


@strawberry.input(description="Input model for deleting admission payment info")
class AdmissionPaymentInfoDeleteGQLModel:
    id: IDType
    lastchange: datetime.datetime


@strawberry.input(description="Input model for creating admission payment info with validation")
class AdmissionPaymentInfoCreateGQLModel:
    required_amount: float
    bank_account_id: IDType


@strawberry.type(description="Admission payment info mutations")
class AdmissionPaymentInfoMutation:
    @strawberry.mutation(
        description="Create admission payment info with validation",
        permission_classes=[OnlyForAuthentized, AdmissionsAdminPermission]
    )
    async def admission_payment_info_create(
        self,
        info: strawberry.Info,
        payment_info: AdmissionPaymentInfoCreateGQLModel
    ) -> typing.Union[AdmissionPaymentInfoGQLModel, InsertError[AdmissionPaymentInfoGQLModel]]:
        from sqlalchemy.exc import IntegrityError
        from uoishelpers.resolvers import Insert

        if not isinstance(payment_info.required_amount, (int, float)):
            return InsertError[AdmissionPaymentInfoGQLModel](
                msg="Required amount must be numeric",
                code="7a62fb9b-3d7f-4e23-8a3b-44a7e9bce31f",
                location="admissionPaymentInfoCreate",
                _input=payment_info
            )
        if payment_info.required_amount <= 0:
            return InsertError[AdmissionPaymentInfoGQLModel](
                msg="Required amount must be greater than 0",
                code="f2a1d19b-0e5f-4c2b-b2e9-9f40b81d3bd5",
                location="admissionPaymentInfoCreate",
                _input=payment_info
            )

        bank_account_loader = getLoadersFromInfo(info).AdmissionBankAccountModel
        bank_account = await bank_account_loader.load(payment_info.bank_account_id)
        if bank_account is None:
            return InsertError[AdmissionPaymentInfoGQLModel](
                msg="Bank account not found",
                code="9c3b5b1a-7b7f-4fb6-8e75-1e8a9c4b2d6f",
                location="admissionPaymentInfoCreate",
                _input=payment_info
            )

        entity = AdmissionPaymentInfoInsertGQLModel(
            required_amount=payment_info.required_amount,
            bank_account_id=payment_info.bank_account_id
        )
        try:
            return await Insert[AdmissionPaymentInfoGQLModel].DoItSafeWay(info=info, entity=entity)
        except IntegrityError as exc:
            return integrity_error_to_error(
                exc,
                InsertError[AdmissionPaymentInfoGQLModel],
                "admissionPaymentInfoCreate",
                payment_info
            )

    @strawberry.mutation(
        description="Insert admission payment info",
        permission_classes=[OnlyForAuthentized, AdmissionsAdminPermission]
    )
    async def admission_payment_info_insert(
        self,
        info: strawberry.Info,
        payment_info: AdmissionPaymentInfoInsertGQLModel
    ) -> typing.Union[AdmissionPaymentInfoGQLModel, InsertError[AdmissionPaymentInfoGQLModel]]:
        from sqlalchemy.exc import IntegrityError
        from uoishelpers.resolvers import Insert

        if payment_info.required_amount is None or payment_info.bank_account_id is None:
            return InsertError[AdmissionPaymentInfoGQLModel](
                msg="Missing required value",
                code="a3c2a8f9-3f19-4e88-a5a0-1a7a4f6f0f8d",
                location="admissionPaymentInfoInsert",
                _input=payment_info
            )
        if not isinstance(payment_info.required_amount, (int, float)):
            return InsertError[AdmissionPaymentInfoGQLModel](
                msg="Required amount must be numeric",
                code="7a62fb9b-3d7f-4e23-8a3b-44a7e9bce31f",
                location="admissionPaymentInfoInsert",
                _input=payment_info
            )
        if payment_info.required_amount <= 0:
            return InsertError[AdmissionPaymentInfoGQLModel](
                msg="Required amount must be greater than 0",
                code="f2a1d19b-0e5f-4c2b-b2e9-9f40b81d3bd5",
                location="admissionPaymentInfoInsert",
                _input=payment_info
            )
        bank_account_loader = getLoadersFromInfo(info).AdmissionBankAccountModel
        bank_account = await bank_account_loader.load(payment_info.bank_account_id)
        if bank_account is None:
            return InsertError[AdmissionPaymentInfoGQLModel](
                msg="Bank account not found",
                code="9c3b5b1a-7b7f-4fb6-8e75-1e8a9c4b2d6f",
                location="admissionPaymentInfoInsert",
                _input=payment_info
            )

        try:
            return await Insert[AdmissionPaymentInfoGQLModel].DoItSafeWay(info=info, entity=payment_info)
        except IntegrityError as exc:
            return integrity_error_to_error(
                exc,
                InsertError[AdmissionPaymentInfoGQLModel],
                "admissionPaymentInfoInsert",
                payment_info
            )

    @strawberry.mutation(
        description="Update admission payment info",
        permission_classes=[OnlyForAuthentized, AdmissionsAdminPermission],
        extensions=[LoadDataExtension[UpdateError, AdmissionPaymentInfoGQLModel]()]
    )
    async def admission_payment_info_update(
        self,
        info: strawberry.Info,
        payment_info: AdmissionPaymentInfoUpdateGQLModel,
        db_row: typing.Any
    ) -> typing.Union[AdmissionPaymentInfoGQLModel, UpdateError[AdmissionPaymentInfoGQLModel]]:
        from sqlalchemy.exc import IntegrityError
        from uoishelpers.resolvers import Update

        new_required = db_row.required_amount if payment_info.required_amount is strawberry.UNSET else payment_info.required_amount
        if new_required is None:
            return UpdateError[AdmissionPaymentInfoGQLModel](
                msg="Missing required value",
                code="a3c2a8f9-3f19-4e88-a5a0-1a7a4f6f0f8d",
                location="admissionPaymentInfoUpdate",
                _input=payment_info
            )
        if not isinstance(new_required, (int, float)):
            return UpdateError[AdmissionPaymentInfoGQLModel](
                msg="Required amount must be numeric",
                code="7a62fb9b-3d7f-4e23-8a3b-44a7e9bce31f",
                location="admissionPaymentInfoUpdate",
                _input=payment_info
            )
        if new_required <= 0:
            return UpdateError[AdmissionPaymentInfoGQLModel](
                msg="Required amount must be greater than 0",
                code="f2a1d19b-0e5f-4c2b-b2e9-9f40b81d3bd5",
                location="admissionPaymentInfoUpdate",
                _input=payment_info
            )

        if payment_info.bank_account_id is not strawberry.UNSET:
            bank_account_loader = getLoadersFromInfo(info).AdmissionBankAccountModel
            bank_account = await bank_account_loader.load(payment_info.bank_account_id)
            if bank_account is None:
                return UpdateError[AdmissionPaymentInfoGQLModel](
                    msg="Bank account not found",
                    code="9c3b5b1a-7b7f-4fb6-8e75-1e8a9c4b2d6f",
                    location="admissionPaymentInfoUpdate",
                    _input=payment_info
                )

        try:
            return await Update[AdmissionPaymentInfoGQLModel].DoItSafeWay(info=info, entity=payment_info)
        except IntegrityError as exc:
            return integrity_error_to_error(
                exc,
                UpdateError[AdmissionPaymentInfoGQLModel],
                "admissionPaymentInfoUpdate",
                payment_info
            )

    @strawberry.mutation(
        description="Delete admission payment info",
        permission_classes=[OnlyForAuthentized, AdmissionsAdminPermission],
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
