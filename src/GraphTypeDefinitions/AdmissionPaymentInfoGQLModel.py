import typing
import datetime
import strawberry

from uoishelpers.resolvers import getLoadersFromInfo, createInputs2, ScalarResolver
from uoishelpers.gqlpermissions import OnlyForAuthentized

from .BaseGQLModel import BaseGQLModel, IDType
from .admission_permissions import AdmissionsAdminPermission
from .db_errors import integrity_error_to_error
from .pagination import resolve_page
from .validation import (
    build_error,
    resolve_unset,
    validate_fk_exists,
    validate_numeric,
    validate_positive,
    validate_required,
)
from . import error_codes as codes

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
        return await resolve_page(
            info,
            AdmissionPaymentInfoGQLModel,
            where,
            skip,
            limit,
            orderby,
            desc,
            offset,
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

        error = validate_numeric(
            payment_info.required_amount,
            error_cls=InsertError[AdmissionPaymentInfoGQLModel],
            location="admissionPaymentInfoCreate",
            input_obj=payment_info,
        )
        if error is not None:
            return error
        error = validate_positive(
            payment_info.required_amount,
            error_cls=InsertError[AdmissionPaymentInfoGQLModel],
            location="admissionPaymentInfoCreate",
            input_obj=payment_info,
        )
        if error is not None:
            return error

        bank_account_loader = getLoadersFromInfo(info).AdmissionBankAccountModel
        error = await validate_fk_exists(
            bank_account_loader,
            payment_info.bank_account_id,
            error_cls=InsertError[AdmissionPaymentInfoGQLModel],
            location="admissionPaymentInfoCreate",
            input_obj=payment_info,
            msg="Bank account not found",
            code=codes.ERR_BANK_ACCOUNT_NOT_FOUND,
        )
        if error is not None:
            return error

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
            return build_error(
                InsertError[AdmissionPaymentInfoGQLModel],
                msg="Missing required value",
                code=codes.ERR_MISSING_REQUIRED,
                location="admissionPaymentInfoInsert",
                input_obj=payment_info,
            )
        error = validate_numeric(
            payment_info.required_amount,
            error_cls=InsertError[AdmissionPaymentInfoGQLModel],
            location="admissionPaymentInfoInsert",
            input_obj=payment_info,
        )
        if error is not None:
            return error
        error = validate_positive(
            payment_info.required_amount,
            error_cls=InsertError[AdmissionPaymentInfoGQLModel],
            location="admissionPaymentInfoInsert",
            input_obj=payment_info,
        )
        if error is not None:
            return error
        bank_account_loader = getLoadersFromInfo(info).AdmissionBankAccountModel
        error = await validate_fk_exists(
            bank_account_loader,
            payment_info.bank_account_id,
            error_cls=InsertError[AdmissionPaymentInfoGQLModel],
            location="admissionPaymentInfoInsert",
            input_obj=payment_info,
            msg="Bank account not found",
            code=codes.ERR_BANK_ACCOUNT_NOT_FOUND,
        )
        if error is not None:
            return error

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

        new_required = resolve_unset(payment_info.required_amount, db_row.required_amount)
        error = validate_required(
            new_required,
            error_cls=UpdateError[AdmissionPaymentInfoGQLModel],
            location="admissionPaymentInfoUpdate",
            input_obj=payment_info,
        )
        if error is not None:
            return error
        error = validate_numeric(
            new_required,
            error_cls=UpdateError[AdmissionPaymentInfoGQLModel],
            location="admissionPaymentInfoUpdate",
            input_obj=payment_info,
        )
        if error is not None:
            return error
        error = validate_positive(
            new_required,
            error_cls=UpdateError[AdmissionPaymentInfoGQLModel],
            location="admissionPaymentInfoUpdate",
            input_obj=payment_info,
        )
        if error is not None:
            return error

        if payment_info.bank_account_id is not strawberry.UNSET:
            bank_account_loader = getLoadersFromInfo(info).AdmissionBankAccountModel
            error = await validate_fk_exists(
                bank_account_loader,
                payment_info.bank_account_id,
                error_cls=UpdateError[AdmissionPaymentInfoGQLModel],
                location="admissionPaymentInfoUpdate",
                input_obj=payment_info,
                msg="Bank account not found",
                code=codes.ERR_BANK_ACCOUNT_NOT_FOUND,
            )
            if error is not None:
                return error

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
