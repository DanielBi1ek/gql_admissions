import typing
import datetime
import strawberry

from uoishelpers.resolvers import getLoadersFromInfo, createInputs2, ScalarResolver

from .BaseGQLModel import BaseGQLModel, IDType
from .admission_permissions import (
    ADMISSION_READ_PERMISSION, ADMISSION_ADMIN_PERMISSION,
    admission_field
)
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

    # Using centralized permission system - no more repetitive permission_classes!
    required_amount: typing.Optional[float] = admission_field(
        default=None,
        description="required amount"
    )
    bank_account_id: typing.Optional[IDType] = admission_field(
        default=None,
        description="bank account reference"
    )

    bank_account: typing.Optional["AdmissionBankAccountGQLModel"] = admission_field(
        description="bank account details",
        resolver=ScalarResolver["AdmissionBankAccountGQLModel"](fkey_field_name="bank_account_id")
    )


@strawberry.type(description="Admission payment info queries")
class AdmissionPaymentInfoQuery:
    admission_payment_info_by_id: typing.Optional[AdmissionPaymentInfoGQLModel] = strawberry.field(
        description="get admission payment info by id",
        permission_classes=ADMISSION_READ_PERMISSION,
        resolver=AdmissionPaymentInfoGQLModel.load_with_loader
    )

    @strawberry.field(
        description="page of admission payment info",
        permission_classes=ADMISSION_READ_PERMISSION
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


AdmissionPaymentInfoGQLModelInsertError = typing.Annotated[
    InsertError[AdmissionPaymentInfoGQLModel], strawberry.lazy("uoishelpers.resolvers")
]
AdmissionPaymentInfoGQLModelUpdateError = typing.Annotated[
    UpdateError[AdmissionPaymentInfoGQLModel], strawberry.lazy("uoishelpers.resolvers")
]
AdmissionPaymentInfoGQLModelDeleteError = typing.Annotated[
    DeleteError[AdmissionPaymentInfoGQLModel], strawberry.lazy("uoishelpers.resolvers")
]


@strawberry.type(description="Result of admission payment info operations")
class AdmissionPaymentInfoGQLModelResult(AdmissionPaymentInfoGQLModel):
    pass


@strawberry.type(description="Admission payment info mutations")
class AdmissionPaymentInfoMutation:
    @strawberry.field(
        description="Insert admission payment info",
        permission_classes=ADMISSION_ADMIN_PERMISSION
    )
    async def admission_payment_info_insert(
        self,
        info: strawberry.Info,
        payment_info: AdmissionPaymentInfoInsertGQLModel,
    ) -> typing.Union[AdmissionPaymentInfoGQLModelResult, AdmissionPaymentInfoGQLModelInsertError]:
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
            result = await Insert[AdmissionPaymentInfoGQLModel].DoItSafeWay(info=info, entity=payment_info)
            # Convert the result to the proper result type
            return AdmissionPaymentInfoGQLModelResult(**result.__dict__)
        except IntegrityError as exc:
            return integrity_error_to_error(
                exc,
                InsertError[AdmissionPaymentInfoGQLModel],
                "admissionPaymentInfoInsert",
                payment_info
            )

    @strawberry.field(
        description="Update admission payment info",
        permission_classes=ADMISSION_ADMIN_PERMISSION
    )
    async def admission_payment_info_update(
        self,
        info: strawberry.Info,
        payment_info: AdmissionPaymentInfoUpdateGQLModel,
    ) -> typing.Union[AdmissionPaymentInfoGQLModelResult, AdmissionPaymentInfoGQLModelUpdateError]:
        from sqlalchemy.exc import IntegrityError
        from uoishelpers.resolvers import Update

        # Load existing data to validate against
        loader = getLoadersFromInfo(info).AdmissionPaymentInfoModel
        db_row = await loader.load(payment_info.id)
        if db_row is None:
            return build_error(
                UpdateError[AdmissionPaymentInfoGQLModel],
                msg="Payment info not found",
                code=codes.ERR_NOT_FOUND,
                location="admissionPaymentInfoUpdate",
                input_obj=payment_info,
            )

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
            result = await Update[AdmissionPaymentInfoGQLModel].DoItSafeWay(info=info, entity=payment_info)
            # Convert the result to the proper result type
            return AdmissionPaymentInfoGQLModelResult(**result.__dict__)
        except IntegrityError as exc:
            return integrity_error_to_error(
                exc,
                UpdateError[AdmissionPaymentInfoGQLModel],
                "admissionPaymentInfoUpdate",
                payment_info
            )

    @strawberry.field(
        description="Delete admission payment info",
        permission_classes=ADMISSION_ADMIN_PERMISSION
    )
    async def admission_payment_info_delete(
        self,
        info: strawberry.Info,
        payment_info: AdmissionPaymentInfoDeleteGQLModel,
    ) -> typing.Union[AdmissionPaymentInfoGQLModelResult, AdmissionPaymentInfoGQLModelDeleteError]:
        from uoishelpers.resolvers import Delete

        # Load the entity before deletion to get complete data for result
        loader = getLoadersFromInfo(info).AdmissionPaymentInfoModel
        db_row = await loader.load(payment_info.id)
        if db_row is None:
            return build_error(
                DeleteError[AdmissionPaymentInfoGQLModel],
                msg="Payment info not found",
                code=codes.ERR_NOT_FOUND,
                location="admissionPaymentInfoDelete",
                input_obj=payment_info,
            )

        # Perform the deletion
        result = await Delete[AdmissionPaymentInfoGQLModel].DoItSafeWay(info=info, entity=payment_info)

        # Check if deletion failed
        if isinstance(result, DeleteError):
            return result

        # Return the deleted entity data as result
        return AdmissionPaymentInfoGQLModelResult(
            id=db_row.id,
            required_amount=db_row.required_amount,
            bank_account_id=db_row.bank_account_id,
            created=db_row.created,
            lastchange=db_row.lastchange,
            createdby_id=db_row.createdby_id,
            changedby_id=db_row.changedby_id,
            rbacobject_id=db_row.rbacobject_id
        )
